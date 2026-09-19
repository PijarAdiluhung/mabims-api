from __future__ import annotations

import calendar as pycalendar
import hashlib
import json
import math
import re
import threading
import warnings
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import TypeVar
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, Response
from scalar_fastapi import AgentScalarConfig, Theme, get_scalar_api_reference
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .calendar import SOURCE_MABIMS, CalendarService
from .config import APP_VERSION, BUILD_HASH, Settings
from .coverage import (
    RETRO_SOURCE,
    RETRO_WARNING,
    load_coverage,
)
from .coverage import (
    Coverage as CoverageBounds,
)
from .divergences import (
    Divergence,
    as_payload,
    load_divergences,
    table_version,
)
from .events import find_events
from .fallback import MemoryFallbackStore
from .hilal import history as _history
from .hilal import imagepack as _imagepack
from .hilal.astro import lunar_age_hours, moonset_local, phase_angle_deg
from .hilal.chart import bare_chart_png_bytes, build_chart_data, chart_png_bytes
from .hilal.images import image_path, store
from .hilal.mapcard import map_png_bytes
from .hilal.service import (
    MONTH_NAMES_ID,
    MonthNotResolvable,
    SightingEvening,
    resolve_sighting_evening,
)
from .i18n import t
from .mabims_computed import COMPUTED_SOURCE, MabimsCalcProvider, next_hijri_month
from .mabims_sites import MultiSiteSighting, Site, SiteSighting, sighting_on_date, site_by_name
from .schemas import (
    ConversionInput,
    ConversionOutput,
    ConvertResponse,
    Coverage,
    DecidingSite,
    EventItem,
    EventsInput,
    EventsResponse,
    HealthResponse,
    HilalEvening,
    HilalHistoryInput,
    HilalHistoryItem,
    HilalHistoryResponse,
    HilalInfoResponse,
    HilalInput,
    HilalMonth,
    HilalPrevMonth,
    MetaResponse,
    MonthInput,
    MonthResponse,
    NextDate,
    RangeInput,
    RangeItem,
    RangeResponse,
    Source,
    TableResponse,
    TodayResponse,
    YearInput,
    YearResponse,
)
from .timeutil import (
    HEALTHZ_HEADERS,
    IMMUTABLE_CACHE_HEADERS,
    SHORT_CACHE_HEADERS,
    dynamic_cache_headers,
    etag_from_bytes,
    etag_headers,
    etag_matches,
    resolve_tz,
    tz_label,
)

COMPUTED_WARNING = (
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria "
    "(moon altitude >= 3 deg and elongation >= 6.4 deg at local sunset, seen anywhere "
    "across the coastal observation sites of Indonesia)."
)
BORDERLINE_WARNING_TEMPLATE = (
    "Hijri month {ym} is close to the Neo MABIMS visibility threshold; the officially "
    "announced date may shift by one day."
)
COMPUTED_METHOD = "neo-mabims-multisite"
MAX_RANGE_DAYS = 45
RETRO_QUERY_DESC = t("query.retro")
NEXT_QUERY_DESC = t("query.next")
BARE_QUERY_DESC = t("query.bare")
HILAL_CACHE = {"Cache-Control": "public, max-age=86400, s-maxage=86400"}
HILAL_ALT_MIN_DEG = 3.0
HILAL_ELONG_MIN_DEG = 6.4
# Supersampling factor for the bare (panel-less) web hero cards.
HILAL_BARE_SCALE = 2.0
DOWNLOAD_QUERY_DESC = t("query.download")


def _err(status: int, code: str, description: str) -> dict:
    """Build a spec-problem entry for one error code.

    Message strings come from ERROR_MESSAGES so the generated reference shows
    the real thing instead of ``"..."``.
    """
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ErrorBody"},
                "example": {
                    "error": {
                        "code": code,
                        "message": ERROR_MESSAGES.get(
                            code, "See /api/v1/meta for coverage."
                        ),
                    }
                },
            }
        },
    }


ERROR_MESSAGES = {
    "invalid_date": "'1999-13-45' is not a valid ISO date (YYYY-MM-DD).",
    "invalid_calendar": "The 'calendar' parameter must be 'gregorian' or 'hijri'.",
    "invalid_timezone": "Unknown timezone: Foo/Bar",
    "missing_parameter": "You must provide a 'date' query parameter.",
    "invalid_retro": "'retro' must be 'true' or 'false'.",
    "invalid_next": "'next' must be 'true' or 'false'.",
    "invalid_bare": "'bare' must be 'true' or 'false'.",
    "invalid_download": "'download' must be 'true' or 'false'.",
    "invalid_step": "Only step='day' is supported.",
    "invalid_range": "'start' must be on or before 'end'.",
    "invalid_month": "'month' must be between 1 and 12.",
    "invalid_year": "'year' is out of supported bounds.",
    "out_of_coverage": "No calendar pair exists for 2022-01-01; check /api/v1/meta for coverage.",
    "date_out_of_supported_range": "Supported range is 2023-01-23 through 2100-01-01 (gregorian).",
    "date_not_found": "No calendar pair exists for 2026-07-31 (hijri). See /api/v1/meta for coverage.",
    "not_found": "Not Found",
    "rate_limit_exceeded": "Rate limit exceeded (240 per 1 minute). Wait 60s before retrying.",
    "render_failed": "Could not render chart: RenderError",
    "computation_unavailable": "Could not compute hilal data: EphemerisError",
}


# Common error responses reused across endpoints.
_ERR_400 = _err(400, "missing_parameter", "Bad Request — validation error")
_ERR_404 = _err(404, "date_not_found", "Not Found")
_ERR_404_ROUTE = _err(404, "not_found", "Not Found")
_ERR_429 = _err(429, "rate_limit_exceeded", "Rate Limit Exceeded")
_ERR_500 = _err(500, "render_failed", "Internal Server Error")
_ERR_503 = _err(503, "computation_unavailable", "Service Unavailable")


# Range covered by the pre-generated image set (bundled core + documented range)
# and the hard render cap for the PNG endpoints: outside it, /hilal/viz and
# /hilal/map refuse instead of rendering on demand.
HILAL_IMAGE_MIN_YEAR = 1444
HILAL_IMAGE_MAX_YEAR = 1475


def _hilal_render_year_check(year: int) -> None:
    if not HILAL_IMAGE_MIN_YEAR <= year <= HILAL_IMAGE_MAX_YEAR:
        raise ApiError(
            "out_of_coverage",
            f"Hilal images are available for Hijri years "
            f"{HILAL_IMAGE_MIN_YEAR}-{HILAL_IMAGE_MAX_YEAR}, got {year}.",
        )

# The map card renders a 0.25 deg grid (~260 MB peak), so serialize renders to
# stay inside the container memory cap; results are deterministic per evening.
_MAP_SEMAPHORE = threading.Semaphore(1)


@lru_cache(maxsize=64)
def _map_png_cached(
    evening_iso: str,
    vis_month: str,
    vis_year: int,
    hijri_label: str,
    hero_name: str,
    hero_lat: float,
    hero_lon: float,
    hero_alt: float,
    hero_elong: float,
    bare: bool = False,
) -> bytes:
    return map_png_bytes(
        evening=date.fromisoformat(evening_iso),
        vis_month=vis_month,
        vis_year=vis_year,
        hijri_label=hijri_label,
        hero=(hero_name, hero_lat, hero_lon, hero_alt, hero_elong),
        bare=bare,
        scale=HILAL_BARE_SCALE,
    )


def _attachment_headers(kind: str, year: int, month: int, enabled: bool) -> dict[str, str]:
    """Force a browser download (cross-origin `download` attrs are ignored)."""
    if not enabled:
        return {}
    return {"Content-Disposition": f'attachment; filename="hilal-{kind}-{year:04d}-{month:02d}.png"'}


def _render_viz_png(
    res: SightingEvening,
    sighting: SightingObservation,
    ms_site: SiteSighting,
    alt_ok: bool,
    elong_ok: bool,
    bare: bool = False,
) -> bytes:
    sky = sighting.multisite.sky_for(ms_site.site)
    data = build_chart_data(
        hijri_label=res.evening_label,
        evening_date=res.evening_date,
        vis_month=res.target_name,
        sunset=sighting.sunset_local,
        moonset=sighting.moonset_local,
        moon_alt=ms_site.alt_deg,
        moon_az=sky.moon_az_deg,
        sun_alt=sky.sun_alt_deg,
        sun_az=sky.sun_az_deg,
        elong=ms_site.elong_deg,
        illum=sighting.illumination_pct / 100.0,
        decider=ms_site.site,
        dec_alt=ms_site.alt_refracted_deg,
        dec_elong=ms_site.elong_deg,
        sites_checked=len(sighting.multisite.sites),
        alt_ok=alt_ok,
        elong_ok=elong_ok,
        alt_margin=ms_site.alt_refracted_deg - HILAL_ALT_MIN_DEG,
        elong_margin=ms_site.elong_deg - HILAL_ELONG_MIN_DEG,
    )
    if bare:
        return bare_chart_png_bytes(data, HILAL_BARE_SCALE)
    return chart_png_bytes(data)


def _render_map_png(
    res: SightingEvening,
    sighting: SightingObservation,
    ms_site: SiteSighting,
    bare: bool = False,
) -> bytes:
    site = sighting.site
    return map_png_bytes(
        evening=res.evening_date,
        vis_month=res.target_name,
        vis_year=res.target_year,
        hijri_label=res.evening_label,
        hero=(site.name, site.lat_deg, site.lon_deg, ms_site.alt_refracted_deg, ms_site.elong_deg),
        bare=bare,
        scale=HILAL_BARE_SCALE,
    )

_HIJRI_YEARS_PER_GREGORIAN = 365.2425 / 354.36792
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

GREGORIAN_MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def _parse_date_parts(iso: str, calendar: str) -> dict:
    y, m, d = (int(iso[0:4]), int(iso[5:7]), int(iso[8:10]))
    names = MONTH_NAMES_ID if calendar == "hijri" else GREGORIAN_MONTH_NAMES
    return {"day": d, "month": m, "month_name": names[m], "year": y}


class SightingObservation:
    """Multi-site MABIMS verdict plus decider-site observer facts for one evening."""

    __slots__ = (
        "multisite",
        "site",
        "sunset_local",
        "moonset_local",
        "illumination_pct",
        "age_hours",
    )

    def __init__(
        self,
        multisite: MultiSiteSighting,
        site: Site,
        sunset_local: str,
        moonset_local: str,
        illumination_pct: float,
        age_hours: float,
    ) -> None:
        self.multisite = multisite
        self.site = site
        self.sunset_local = sunset_local
        self.moonset_local = moonset_local
        self.illumination_pct = illumination_pct
        self.age_hours = age_hours


def observe_sighting_evening(evening_date: date) -> SightingObservation:
    """Compose the full hilal payload for a sighting evening.

    The verdict (alt/elong/visible) and the whole scene come from the
    multi-site model in ``mabims_sites``: the deciding site when visible,
    the closest-miss site otherwise. Sunset, moonset, illumination and age
    are computed at that same site's sunset instant, displayed in the
    site's own timezone.
    """
    ms = sighting_on_date(evening_date)
    chosen = ms.deciding_site or ms.best_site
    site = site_by_name(chosen.site)
    sky = ms.sky_for(chosen.site)
    tz = ZoneInfo(site.tz)
    phase = phase_angle_deg(sky.sunset_utc)
    return SightingObservation(
        multisite=ms,
        site=site,
        sunset_local=sky.sunset_utc.astimezone(tz).strftime("%H:%M"),
        moonset_local=moonset_local(evening_date, site.tz, site.lat_deg, site.lon_deg),
        illumination_pct=(1.0 - math.cos(math.radians(phase))) / 2.0 * 100.0,
        age_hours=lunar_age_hours(sky.sunset_utc),
    )


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
    )


_INT_MESSAGE = "{name} must be a plain integer (no leading '+', decimals or spaces)."


def _parse_int(raw: str | None, name: str) -> int:
    """Manual integer query parameter for the uniform 400 error envelope.

    Replaces FastAPI's native int coercion (which leaks a raw 422
    ``{"detail": [...]}`` shape) with ``missing_parameter`` /
    ``invalid_{name}`` codes in the same envelope as every other error.
    """
    if raw is None or raw == "":
        raise ApiError(
            "missing_parameter",
            f"You must provide a '{name}' query parameter.",
        )
    if not raw.isdigit():
        raise ApiError(f"invalid_{name}", _INT_MESSAGE.format(name=name))
    return int(raw)


def _json_response(request: Request, content: dict, headers: dict[str, str]) -> Response:
    body = json.dumps(content, separators=(",", ":")).encode()
    etag = etag_from_bytes(body)
    cache = {**headers, **etag_headers(etag)}
    if etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers=cache)
    return JSONResponse(content=content, headers=cache)


def _png_response(request: Request, png: bytes, attach: dict[str, str]) -> Response:
    """Serve a hilal PNG with ETag/304 support and optional attachment headers."""
    etag = etag_from_bytes(png)
    cache = {**HILAL_CACHE, **etag_headers(etag), **attach}
    if etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers=cache)
    return Response(content=png, media_type="image/png", headers=cache)


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ApiError("invalid_date", f"'{value}' is not a valid ISO date (YYYY-MM-DD).") from None


_HIJRI_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _parse_hijri_date(value: str) -> str:
    """Validate a Hijri ``YYYY-MM-DD`` string without Gregorian date rules.

    ``date.fromisoformat`` validates against the Gregorian calendar, so a
    legitimate Hijri date like ``1368-02-30`` (30 Safar — a 30-day month) would
    be rejected as a nonexistent Gregorian Feb 30 — and ``datetime.date`` cannot
    even represent ``February 30`` in any year. Hijri months are 29/30 days, so
    the syntactically valid day range is 1–30; whether a specific day exists in
    a given month is left to the data lookup (``date_not_found``). Returns the
    normalized ISO string and never constructs a ``date`` object.

    Like the Gregorian path, the input is *not* stripped: leading/trailing
    whitespace is rejected outright (``invalid_date``).
    """
    normalized = value or ""
    match = _HIJRI_DATE_RE.match(normalized)
    if match is None:
        raise ApiError("invalid_date", f"'{value}' is not a valid ISO date (YYYY-MM-DD).")
    year, month, day = (int(g) for g in match.groups())
    if not 1 <= month <= 12 or not 1 <= day <= 30:
        raise ApiError("invalid_date", f"'{value}' is not a valid ISO date (YYYY-MM-DD).")
    return f"{year:04d}-{month:02d}-{day:02d}"


def _validate_calendar(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized not in ("gregorian", "hijri"):
        raise ApiError("invalid_calendar", "The 'calendar' parameter must be 'gregorian' or 'hijri'.")
    return normalized


def _hijri_bound_year(anchor_hijri: tuple[int, int], anchor_gregorian: date, gregorian_year: int) -> int:
    offset_years = gregorian_year - anchor_gregorian.year
    return anchor_hijri[0] + round(offset_years * _HIJRI_YEARS_PER_GREGORIAN)


def _host_of(origin: str) -> str:
    host = origin.split("://", 1)[-1]
    return host.split("/", 1)[0].lower()


def _origin_allowed(origin: str, settings: Settings) -> bool:
    if "*" in settings.allowed_origins or origin in settings.allowed_origins:
        return True
    host = _host_of(origin)
    for suffix in settings.origin_suffixes:
        suffix_host = _host_of(suffix if "://" in suffix else f"https://{suffix}")
        if host == suffix_host or host.endswith(f".{suffix_host}"):
            return True
    return False


def create_app(settings: Settings | None = None, computed_provider=None) -> FastAPI:
    settings = settings or Settings()

    data_path = settings.data_dir / "calendar_data.json"
    raw_bytes = data_path.read_bytes()
    data_version = hashlib.sha256(raw_bytes).hexdigest()[:12]

    stores: list = []
    computed_store: MemoryFallbackStore | None = None
    active_computed: MabimsCalcProvider | None = computed_provider

    if settings.enable_fallback and settings.enable_computed:
        anchor_raw = json.loads(raw_bytes)
        first_h = min(anchor_raw["hijri_to_gregorian"])
        anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
        anchor_gregorian = date.fromisoformat(anchor_raw["hijri_to_gregorian"][first_h])
        if active_computed is None:
            active_computed = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
        seed_path = settings.data_dir / "computed_seed.json"
        if seed_path.exists():
            try:
                seed_raw = json.loads(seed_path.read_text(encoding="utf-8"))
                active_computed.seed_from_pairs(
                    seed_raw["hijri_to_gregorian"],
                    margins=seed_raw.get("margins"),
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        computed_store = MemoryFallbackStore(settings.fallback_dir or settings.data_dir, active_computed)
        stores.append(computed_store)

    service = CalendarService(data_path, stores=stores)
    bounds: CoverageBounds = load_coverage(settings.data_dir)
    divergences: dict[str, Divergence] = load_divergences(settings.data_dir)

    app = FastAPI(
        title="MABIMS API",
        version=APP_VERSION,
        redoc_url=None,
        docs_url=None,
        openapi_url="/openapi.json",
        description=t("app.description"),
        servers=[{"url": settings.openapi_server, "description": "Live API"}],
        openapi_tags=[
            {"name": "Today", "description": t("tag.today")},
            {"name": "Convert", "description": t("tag.convert")},
            {"name": "Range", "description": t("tag.range")},
            {"name": "Month", "description": t("tag.month")},
            {"name": "Year", "description": t("tag.year")},
            {"name": "Events", "description": t("tag.events")},
            {"name": "Hilal", "description": t("tag.hilal")},
            {"name": "Meta", "description": t("tag.meta")},
            {"name": "Health", "description": t("tag.health")},
        ],
    )

    def _rate_limit_key(request: Request) -> str:
        if xff := request.headers.get("x-real-ip"):
            return xff
        return request.client.host if request.client else "unknown"

    limiter = Limiter(key_func=_rate_limit_key, default_limits=[settings.rate_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    def handle_rate_limit(request: Request, exc: RateLimitExceeded):
        # Uniform error envelope; slowapi's stock handler leaks
        # {"error": "<string>"} and no Retry-After.
        limit = exc.limit.limit if exc.limit else None
        window = limit.multiples * limit.GRANULARITY.seconds if limit else 60
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(window)},
            content={
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": (
                        f"Rate limit exceeded ({limit}). Wait {window}s before retrying."
                    ),
                }
            },
        )

    def handle_starlette_http(request: Request, exc: StarletteHTTPException):
        # Unhandled starlette errors (404 unknown path, 405 method) leak the
        # raw {"detail": ...} shape; route into the same envelope.
        code = {404: "not_found", 405: "method_not_allowed"}.get(
            exc.status_code, "error"
        )
        return _error(code, str(exc.detail), exc.status_code)

    def handle_validation(request: Request, exc: RequestValidationError):
        # Residual 422s (should be none once every param is parsed manually)
        # still get the uniform envelope instead of FastAPI's {"detail":[...]}.
        first = exc.errors()[0]
        loc = [part for part in first.get("loc", []) if part != "query"]
        name = str(loc[-1]) if loc else "parameter"
        if first.get("type") == "missing":
            return _error(
                "missing_parameter",
                f"You must provide a '{name}' query parameter.",
                400,
            )
        return _error(
            f"invalid_{name}",
            f"The '{name}' parameter is invalid.",
            400,
        )

    app.add_exception_handler(RateLimitExceeded, handle_rate_limit)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, handle_starlette_http)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, handle_validation)  # type: ignore[arg-type]

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError):
        return _error(exc.code, exc.message, exc.status)

    @app.middleware("http")
    async def origin_gate(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method == "OPTIONS":
            response = Response(status_code=204)
        else:
            if origin and not _origin_allowed(origin, settings):
                resp = _error(
                    "forbidden_origin",
                    f"Origin '{origin}' is not allowed to access this API.",
                    403,
                )
                resp.headers["Access-Control-Allow-Origin"] = "*"
                resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
                resp.headers["Access-Control-Max-Age"] = "600"
                return resp
            response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Max-Age"] = "600"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def _parse_bool(raw: str | None, name: str) -> bool:
        """Strict-ish boolean flag: ``true``/``false`` (any case) or ``1``/``0``.

        Anything else is a clean 400 ``invalid_{name}`` instead of FastAPI's
        raw 422 shape, so URL booleans stay unambiguous across clients while
        staying lenient enough for clients that send ``1``/``0``.
        """
        if raw is None or raw == "":
            return False
        lowered = raw.lower()
        if lowered in ("true", "1"):
            return True
        if lowered in ("false", "0"):
            return False
        raise ApiError(
            f"invalid_{name}",
            f"'{name}' must be 'true' or 'false'.",
        )


    def _resolve_pair(date_iso: str, calendar: str, retro: bool = False) -> tuple[str, Source]:
        _check_supported(date_iso, calendar, retro)
        try:
            result = service.resolve(date_iso, calendar, retro=retro)
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(
                "computation_unavailable",
                f"Could not compute the date {date_iso}: {exc.__class__.__name__}",
                503,
            ) from exc
        if result.value is None:
            raise ApiError(
                "date_not_found",
                f"No calendar pair exists for {date_iso} ({calendar}). See /api/v1/meta for coverage.",
                404,
            )
        source = result.source
        gregorian_iso = result.value if calendar == "hijri" else date_iso
        if retro and source == COMPUTED_SOURCE and gregorian_iso < bounds.curated_first:
            source = RETRO_SOURCE
        if calendar == "hijri":
            resolved_gregorian = result.value
            if (
                resolved_gregorian < bounds.lower_bound(retro)
                or resolved_gregorian > bounds.forward_ceil
            ):
                raise ApiError("date_out_of_supported_range", _supported_range_message(retro))
        return result.value, source

    def _supported_range_message(retro: bool = False) -> str:
        message = (
            f"Supported range is {bounds.lower_bound(retro)} through "
            f"{bounds.forward_ceil} (gregorian)."
        )
        if not retro and active_computed is not None:
            message += (
                f" Pass retro=true for computed dates back to {bounds.retro_floor}."
            )
        return message

    def _check_supported(date_iso: str, calendar: str, retro: bool = False) -> None:
        lower = bounds.lower_bound(retro)
        upper = bounds.forward_ceil
        if calendar == "gregorian":
            if date_iso < lower or date_iso > upper:
                raise ApiError("date_out_of_supported_range", _supported_range_message(retro))
            return
        if active_computed is None:
            return
        anchor_h = active_computed.anchor_hijri
        anchor_g = active_computed.anchor_gregorian
        low_year = _hijri_bound_year(anchor_h, anchor_g, int(lower[:4])) - 2
        high_year = _hijri_bound_year(anchor_h, anchor_g, int(upper[:4])) + 2
        year = int(date_iso[0:4])
        if year < low_year or year > high_year:
            raise ApiError("date_out_of_supported_range", _supported_range_message(retro))

    def _divergence_warnings(hijri_value: str | None) -> list[str]:
        """Loud notification when the requested hijri month was overridden by
        a Sidang Isbat decree (its start, or the previous month's length)."""
        if not hijri_value or not divergences:
            return []
        ym = hijri_value[0:7]
        div = next((d for d in divergences.values() if ym in d.affected_months), None)
        if div is None:
            return []
        return [div.warning(MONTH_NAMES_ID.get(div.month, ""))]

    def _warnings_for(source: str, hijri_value: str | None = None) -> list[str]:
        warnings: list[str] = []
        if source == COMPUTED_SOURCE:
            warnings.append(COMPUTED_WARNING)
            if hijri_value:
                ym = hijri_value[0:7]
                borderline = set(active_computed.borderline_months()) if active_computed else set()
                if ym in borderline:
                    warnings.append(BORDERLINE_WARNING_TEMPLATE.format(ym=ym))
        elif source == RETRO_SOURCE:
            warnings.append(RETRO_WARNING)
            if hijri_value:
                ym = hijri_value[0:7]
                borderline = set(active_computed.borderline_months()) if active_computed else set()
                if ym in borderline:
                    warnings.append(BORDERLINE_WARNING_TEMPLATE.format(ym=ym))
        warnings.extend(_divergence_warnings(hijri_value))
        return warnings

    def _aggregate(items: list) -> tuple[str, list[str]]:
        sources = {item.source for item in items}
        if COMPUTED_SOURCE in sources:
            aggregate = COMPUTED_SOURCE
        elif RETRO_SOURCE in sources:
            aggregate = RETRO_SOURCE
        else:
            aggregate = SOURCE_MABIMS
        warnings: list[str] = []
        seen: set[str] = set()
        for item in items:
            for warning in _warnings_for(item.source, item.hijri):
                if warning not in seen:
                    seen.add(warning)
                    warnings.append(warning)
        return aggregate, warnings

    _Relabelable = TypeVar("_Relabelable", RangeItem, EventItem)

    def _relabel_retro(items: list[_Relabelable], retro: bool) -> list[_Relabelable]:
        """Tag computed items below the curated table as ``mabims-retro``."""
        if not retro:
            return items
        for item in items:
            if item.source == COMPUTED_SOURCE and item.gregorian < bounds.curated_first:
                item.source = RETRO_SOURCE
        return items

    @app.api_route(
        "/healthz",
        response_model=HealthResponse,
        tags=["Health"],
        summary=t("healthz.summary"),
        description=t("healthz.description"),
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def healthz(request: Request):
        return JSONResponse(
            content={"status": "ok", "version": APP_VERSION, "build_hash": BUILD_HASH},
            headers=HEALTHZ_HEADERS,
        )

    @app.get("/favicon.ico", include_in_schema=False)
    @limiter.exempt
    def favicon():
        icon = STATIC_DIR / "favicon.ico"
        return Response(
            content=icon.read_bytes(),
            media_type="image/x-icon",
            headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
        )

    @app.get("/docs", include_in_schema=False)
    @limiter.exempt
    async def custom_docs():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=app.title + " — Swagger UI",
            swagger_favicon_url="/favicon.ico",
        )

    @app.api_route(
        "/api/v1/meta",
        response_model=MetaResponse,
        tags=["Meta"],
        summary=t("meta.summary"),
        description=t("meta.description"),
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def meta(request: Request):
        computed_active, computed_months = computed_store.summary() if computed_store else (False, [])
        payload = MetaResponse(
            version=APP_VERSION,
            data_version=data_version,
            coverage=Coverage(first=service.coverage_first_g, last=service.coverage_last_g),
            computed_active=computed_active,
            computed_months=computed_months,
            method=COMPUTED_METHOD if active_computed is not None else None,
            docs_url=settings.docs_url,
            hilal_image_range=[HILAL_IMAGE_MIN_YEAR, HILAL_IMAGE_MAX_YEAR],
            divergences=as_payload(divergences),
            table_version=table_version(settings.data_dir, divergences),
        )
        return _json_response(request, payload.model_dump(), SHORT_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/table",
        response_model=TableResponse,
        tags=["Table"],
        summary=t("table.summary"),
        description=t("table.description"),
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def table(request: Request):
        payload = TableResponse(
            version=data_version,
            gregorian_to_hijri=service.g2h,
            hijri_to_gregorian=service.h2g,
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/convert",
        response_model=ConvertResponse,
        tags=["Convert"],
        summary=t("convert.summary"),
        description=t("convert.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "missing_parameter", "Missing date parameter or invalid calendar"),
            404: _ERR_404,
            429: _ERR_429,
        },
    )
    def convert(
        request: Request,
        date_: str | None = Query(
            default=None,
            alias="date",
            description=t("query.date"),
        ),
        calendar: str = Query(default="gregorian", description=t("query.calendar")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        if not date_:
            raise ApiError("missing_parameter", "You must provide a 'date' query parameter.")
        cal = _validate_calendar(calendar)
        is_retro = _parse_bool(retro, "retro")
        target_iso = _parse_hijri_date(date_) if cal == "hijri" else _parse_iso_date(date_).isoformat()
        value, source = _resolve_pair(target_iso, cal, is_retro)
        opposite = "hijri" if cal == "gregorian" else "gregorian"
        hijri_value = value if cal == "gregorian" else target_iso
        payload = ConvertResponse(
            input=ConversionInput(date=target_iso, calendar=cal),
            output=ConversionOutput(date=value, calendar=opposite, **_parse_date_parts(value, opposite)),
            source=source,
            warnings=_warnings_for(source, hijri_value),
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/today",
        response_model=TodayResponse,
        tags=["Today"],
        summary=t("today.summary"),
        description=t("today.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_timezone", "Invalid timezone or next parameter"),
            404: _ERR_404,
            429: _ERR_429,
        },
    )
    def today(
        request: Request,
        tz: str | None = Query(default=None, description=t("query.tz")),
        next: str | None = Query(default=None, description=NEXT_QUERY_DESC),
    ):
        try:
            tzo = resolve_tz(tz)
        except ValueError as exc:
            raise ApiError("invalid_timezone", str(exc)) from exc
        want_next = _parse_bool(next, "next")
        today_iso = datetime.now(tzo).date().isoformat()
        value, source = _resolve_pair(today_iso, "gregorian")
        next_value: NextDate | None = None
        if want_next:
            tomorrow = date.fromordinal(date.fromisoformat(today_iso).toordinal() + 1)
            next_iso, next_source = _resolve_pair(tomorrow.isoformat(), "gregorian")
            next_value = NextDate(
                date=next_iso,
                calendar="hijri",
                **_parse_date_parts(next_iso, "hijri"),
                source=next_source,
            )
        payload = TodayResponse(
            input=ConversionInput(date=today_iso, calendar="gregorian", tz=tz_label(tzo)),
            output=ConversionOutput(date=value, calendar="hijri", **_parse_date_parts(value, "hijri")),
            source=source,
            warnings=_warnings_for(source, value),
            next=next_value,
        )
        dumped = payload.model_dump(exclude={"next"} if not want_next else None)
        return _json_response(request, dumped, dynamic_cache_headers(tzo))

    @app.api_route(
        "/api/v1/today/{target_date}",
        response_model=ConvertResponse,
        tags=["Today"],
        summary=t("today_on.summary"),
        description=t("today_on.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_date", "Invalid date or retro parameter"),
            404: _ERR_404,
            429: _ERR_429,
        },
    )
    def today_on(
        request: Request,
        target_date: str,
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        is_retro = _parse_bool(retro, "retro")
        target = _parse_iso_date(target_date)
        value, source = _resolve_pair(target.isoformat(), "gregorian", is_retro)
        payload = ConvertResponse(
            input=ConversionInput(date=target.isoformat(), calendar="gregorian"),
            output=ConversionOutput(date=value, calendar="hijri", **_parse_date_parts(value, "hijri")),
            source=source,
            warnings=_warnings_for(source, value),
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    def _hijri_month_items(year: int, month: int, retro: bool = False) -> list[RangeItem]:
        """All days of a Hijri month, served from whichever tier covers it.

        A Hijri month is 29 or 30 days, never 31 — days are probed by exact
        Hijri ISO date and the first missing day ends the month, so a
        fabricated ``day 31`` can never be produced. When the curated table
        fully covers the month it is served as-is (authoritative — a computed
        pad could wrongly extend an official 29-day month to 30). When the
        table is absent or truncated mid-month, the computed store is ensured
        and ``lookup`` fills the gap (curated days still win where present).
        """
        prefix = f"{year:04d}-{month:02d}-"
        curated = sorted(k for k in service.h2g if k.startswith(prefix))
        if curated:
            last_day = int(curated[-1][8:10])
            contiguous = len(curated) == last_day
            if contiguous and last_day in (29, 30):
                # Curated dates are always >= curated_first, never retro.
                return [
                    RangeItem(
                        gregorian=service.h2g[h_iso],
                        hijri=h_iso,
                        source=SOURCE_MABIMS,
                    )
                    for h_iso in curated
                ]
        service.ensure_hijri_month(year, month, retro=retro)
        items: list[RangeItem] = []
        for day in range(1, 31):
            h_iso = f"{prefix}{day:02d}"
            result = service.lookup(h_iso, "hijri")
            if result.value is None:
                break
            items.append(
                RangeItem(gregorian=result.value, hijri=h_iso, source=result.source)
            )
        return _relabel_retro(items, retro)

    def _collect_items(start_iso: str, end_iso: str, cal: str, retro: bool = False) -> list[RangeItem]:
        if cal == "hijri":
            return _collect_hijri_items(start_iso, end_iso, retro)
        start = date.fromisoformat(start_iso)
        end = date.fromisoformat(end_iso)
        service.ensure_range(start.isoformat(), end.isoformat(), cal, retro=retro)
        items: list[RangeItem] = []
        cursor = start
        while cursor <= end:
            iso = cursor.isoformat()
            result = service.lookup(iso, cal)
            if result.value is None:
                raise ApiError(
                    "out_of_coverage",
                    f"No calendar pair exists for {iso}; check /api/v1/meta for coverage.",
                    400,
                )
            items.append(
                RangeItem(
                    gregorian=iso,
                    hijri=result.value,
                    source=result.source,
                )
            )
            cursor = date.fromordinal(cursor.toordinal() + 1)
        return _relabel_retro(items, retro)

    def _collect_hijri_items(start_iso: str, end_iso: str, retro: bool = False) -> list[RangeItem]:
        """Bulk convert a Hijri range by walking whole Hijri months.

        Hijri months are 29/30 days, so stepping with ``date.fromordinal``
        (used by the Gregorian path) would fabricate nonexistent ``day 31``\u2019s
        and break on every month boundary. Instead we iterate month keys and
        clip each month's items to the requested slice.

        Everything stays string-based: a valid Hijri day like ``Safar 30``
        cannot be represented by ``datetime.date`` (Gregorian Feb 30 does not
        exist), so we never build ``date`` objects here.

        The requested ``start`` and ``end`` must themselves be real Hijri
        dates: a day like ``30`` in a 29-day month is a valid ISO string yet
        has no calendar pair, so it is rejected up front instead of silently
        clipping the range.
        """
        for bound in (start_iso, end_iso):
            service.ensure_hijri_month(int(bound[0:4]), int(bound[5:7]), retro=retro)
            lookup = service.lookup(bound, "hijri")
            if lookup.value is None:
                raise ApiError(
                    "date_not_found",
                    f"No calendar pair exists for {bound} (hijri). "
                    "See /api/v1/meta for coverage.",
                    404,
                )
        items: list[RangeItem] = []
        cy = int(start_iso[0:4])
        cm = int(start_iso[5:7])
        ey = int(end_iso[0:4])
        em = int(end_iso[5:7])
        while (cy, cm) <= (ey, em):
            month_items = _hijri_month_items(cy, cm, retro)
            if not month_items:
                raise ApiError(
                    "out_of_coverage",
                    f"No calendar pair exists for {cy:04d}-{cm:02d}; "
                    "check /api/v1/meta for coverage.",
                    400,
                )
            for item in month_items:
                if start_iso <= item.hijri <= end_iso:
                    items.append(item)
            cy, cm = next_hijri_month(cy, cm)
        return items

    @app.api_route(
        "/api/v1/range",
        response_model=RangeResponse,
        tags=["Range"],
        summary=t("range.summary"),
        description=t("range.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_range", "Invalid range, step, calendar, or date out of coverage"),
            429: _ERR_429,
        },
    )
    def range_(
        request: Request,
        start: str | None = Query(default=None, description=t("query.start_date")),
        end: str | None = Query(default=None, description=t("query.end_date")),
        calendar: str = Query(default="gregorian", description=t("query.calendar")),
        step: str = Query(default="day", description=t("query.step")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        if not start:
            raise ApiError("missing_parameter", "You must provide a 'start' query parameter.")
        if not end:
            raise ApiError("missing_parameter", "You must provide an 'end' query parameter.")
        cal = _validate_calendar(calendar)
        is_retro = _parse_bool(retro, "retro")
        if step != "day":
            raise ApiError("invalid_step", "Only step='day' is supported.")
        if cal == "hijri":
            start_iso = _parse_hijri_date(start)
            end_iso = _parse_hijri_date(end)
            if start_iso > end_iso:
                raise ApiError("invalid_range", "'start' must be on or before 'end'.")
            _check_supported(start_iso, cal, is_retro)
            _check_supported(end_iso, cal, is_retro)
            items = _collect_items(start_iso, end_iso, cal, is_retro)
        else:
            start_d = _parse_iso_date(start)
            end_d = _parse_iso_date(end)
            if start_d > end_d:
                raise ApiError("invalid_range", "'start' must be on or before 'end'.")
            span = (end_d - start_d).days + 1
            if span > MAX_RANGE_DAYS:
                raise ApiError("range_too_large", f"Range is limited to {MAX_RANGE_DAYS} days.")
            _check_supported(start_d.isoformat(), cal, is_retro)
            _check_supported(end_d.isoformat(), cal, is_retro)
            items = _collect_items(start_d.isoformat(), end_d.isoformat(), cal, is_retro)
        aggregate_source, warnings = _aggregate(items)
        payload = RangeResponse(
            input=RangeInput(start=start_iso if cal == "hijri" else start_d.isoformat(),
                             end=end_iso if cal == "hijri" else end_d.isoformat(),
                             calendar=cal),
            count=len(items),
            items=items,
            warnings=warnings,
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/events",
        response_model=EventsResponse,
        tags=["Events"],
        summary=t("events.summary"),
        description=t("events.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_year", "Invalid year or calendar parameter"),
            429: _ERR_429,
        },
    )
    def events(
        request: Request,
        year: str | None = Query(default=None, description=t("query.events_year")),
        calendar: str = Query(default="hijri", description=t("query.calendar")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        year_int = _parse_int(year, "year")
        cal = _validate_calendar(calendar)
        is_retro = _parse_bool(retro, "retro")
        if not 1000 <= year_int <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")
        items = [
            EventItem(
                event=definition.slug,
                name=definition.name,
                gregorian=g_iso,
                hijri=h_iso,
                source=service.lookup(h_iso, "hijri").source,
            )
            for definition, g_iso, h_iso in find_events(service, year_int, cal, retro=is_retro)
        ]
        _relabel_retro(items, is_retro)
        aggregate_source, warnings = _aggregate(items)
        payload = EventsResponse(
            input=EventsInput(year=year_int, calendar=cal),
            count=len(items),
            events=items,
            warnings=warnings,
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/month",
        response_model=MonthResponse,
        tags=["Month"],
        summary=t("month.summary"),
        description=t("month.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_month", "Invalid month, year, calendar, or date out of coverage"),
            429: _ERR_429,
        },
    )
    def month(
        request: Request,
        year: str | None = Query(default=None, description=t("query.hijri_year")),
        month: str | None = Query(default=None, description=t("query.month")),
        calendar: str = Query(default="hijri", description=t("query.calendar")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        year_int = _parse_int(year, "year")
        month_int = _parse_int(month, "month")
        cal = _validate_calendar(calendar)
        is_retro = _parse_bool(retro, "retro")
        if not 1 <= month_int <= 12:
            raise ApiError("invalid_month", "'month' must be between 1 and 12.")
        if not 1000 <= year_int <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")

        if cal == "gregorian":
            days_in_month = pycalendar.monthrange(year_int, month_int)[1]
            start_d = date(year_int, month_int, 1)
            end_d = date(year_int, month_int, days_in_month)
            _check_supported(start_d.isoformat(), cal, is_retro)
            _check_supported(end_d.isoformat(), cal, is_retro)
            items = _collect_items(start_d.isoformat(), end_d.isoformat(), cal, is_retro)
        else:
            _check_supported(f"{year_int:04d}-{month_int:02d}-01", cal, is_retro)
            items = _hijri_month_items(year_int, month_int, is_retro)
            if not items:
                raise ApiError(
                    "out_of_coverage",
                    "Hijri month "
                    f"{year_int:04d}-{month_int:02d} is outside available coverage; see /api/v1/meta.",
                    400,
                )
            start_d = date.fromisoformat(items[0].gregorian)
            end_d = date.fromisoformat(items[-1].gregorian)
            if (
                start_d.isoformat() < bounds.lower_bound(is_retro)
                or end_d.isoformat() > bounds.forward_ceil
            ):
                raise ApiError("date_out_of_supported_range", _supported_range_message(is_retro))

        aggregate_source, warnings = _aggregate(items)
        payload = MonthResponse(
            input=MonthInput(year=year_int, month=month_int, calendar=cal),
            count=len(items),
            items=items,
            warnings=warnings,
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/year",
        response_model=YearResponse,
        tags=["Year"],
        summary=t("year.summary"),
        description=t("year.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_year", "Invalid year, calendar, or date out of coverage"),
            429: _ERR_429,
        },
    )
    def year(
        request: Request,
        year: str | None = Query(default=None, description=t("query.hijri_year")),
        calendar: str = Query(default="hijri", description=t("query.calendar")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        year_int = _parse_int(year, "year")
        cal = _validate_calendar(calendar)
        is_retro = _parse_bool(retro, "retro")
        if not 1 <= year_int <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")

        all_items: list[RangeItem] = []
        months: dict[int, list[RangeItem]] = {}

        for m in range(1, 13):
            if cal == "gregorian":
                days_in_month = pycalendar.monthrange(year_int, m)[1]
                start_d = date(year_int, m, 1)
                end_d = date(year_int, m, days_in_month)
                _check_supported(start_d.isoformat(), cal, is_retro)
                _check_supported(end_d.isoformat(), cal, is_retro)
                items = _collect_items(start_d.isoformat(), end_d.isoformat(), cal, is_retro)
            else:
                _check_supported(f"{year_int:04d}-{m:02d}-01", cal, is_retro)
                items = _hijri_month_items(year_int, m, is_retro)
                if not items:
                    raise ApiError(
                        "out_of_coverage",
                        "Hijri month "
                        f"{year_int:04d}-{m:02d} is outside available coverage; see /api/v1/meta.",
                        400,
                    )
                start_d = date.fromisoformat(items[0].gregorian)
                end_d = date.fromisoformat(items[-1].gregorian)
                if (
                    start_d.isoformat() < bounds.lower_bound(is_retro)
                    or end_d.isoformat() > bounds.forward_ceil
                ):
                    raise ApiError("date_out_of_supported_range", _supported_range_message(is_retro))
            months[m] = items
            all_items.extend(items)

        aggregate_source, warnings = _aggregate(all_items)
        payload = YearResponse(
            input=YearInput(year=year_int, calendar=cal),
            count=len(all_items),
            months=months,
            warnings=warnings,
        )
        return _json_response(request, payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    def _hilal_context(month: int, year: int, retro: bool = False):
        try:
            res = resolve_sighting_evening(service, year, month, retro=retro)
        except MonthNotResolvable as exc:
            raise ApiError("out_of_coverage", str(exc), 400) from None
        evening_g = res.evening_date.isoformat()
        if evening_g < bounds.lower_bound(retro) or evening_g > bounds.forward_ceil:
            raise ApiError("date_out_of_supported_range", _supported_range_message(retro))
        try:
            sighting = observe_sighting_evening(res.evening_date)
        except Exception as exc:
            raise ApiError(
                "computation_unavailable",
                f"Could not compute hilal data: {exc.__class__.__name__}",
                503,
            ) from exc
        ms = sighting.multisite
        ms_site = ms.deciding_site or ms.best_site
        alt_ok = ms_site.alt_refracted_deg >= HILAL_ALT_MIN_DEG
        elong_ok = ms_site.elong_deg >= HILAL_ELONG_MIN_DEG
        visible = ms.visible
        source = service.lookup(evening_g, "gregorian").source
        if retro and source == COMPUTED_SOURCE and evening_g < bounds.curated_first:
            source = RETRO_SOURCE
        warnings = _warnings_for(
            source, f"{res.prev_year:04d}-{res.prev_month:02d}-15"
        )
        return res, sighting, alt_ok, elong_ok, visible, ms_site, source, warnings

    @app.api_route(
        "/api/v1/hilal/info",
        response_model=HilalInfoResponse,
        tags=["Hilal"],
        summary=t("hilal_info.summary"),
        description=t("hilal_info.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "out_of_coverage", "Month out of coverage or date out of supported range"),
            429: _ERR_429,
            503: _ERR_503,
        },
    )
    @limiter.limit("60/hour")
    def hilal_info(
        request: Request,
        month: str | None = Query(default=None, description=t("query.hijri_month")),
        year: str | None = Query(default=None, description=t("query.hilal_year")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        month_int = _parse_int(month, "month")
        year_int = _parse_int(year, "year")
        res, sighting, alt_ok, elong_ok, visible, ms_site, source, warnings = _hilal_context(
            month_int, year_int, _parse_bool(retro, "retro")
        )
        sky = sighting.multisite.sky_for(ms_site.site)
        payload = HilalInfoResponse(
            input=HilalInput(month=month_int, year=year_int),
            month=HilalMonth(
                name=res.target_name,
                number=res.target_month,
                year=res.target_year,
                start=res.target_start.isoformat(),
            ),
            previous_month=HilalPrevMonth(
                name=res.prev_name,
                number=res.prev_month,
                year=res.prev_year,
                length=res.prev_length,
            ),
            evening=HilalEvening(
                hijri_date=res.evening_label,
                hijri_day=res.evening_day,
                gregorian_date=res.evening_date.isoformat(),
                sunset=sighting.sunset_local,
                moonset=sighting.moonset_local,
                moon_alt_deg=round(ms_site.alt_refracted_deg, 2),
                moon_az_deg=round(sky.moon_az_deg, 2),
                sun_alt_deg=round(sky.sun_alt_deg, 2),
                elongation_deg=round(ms_site.elong_deg, 2),
                illumination_pct=round(sighting.illumination_pct, 2),
                age_hours=round(sighting.age_hours, 1),
                deciding_site=DecidingSite(
                    name=sighting.site.name,
                    lat=sighting.site.lat_deg,
                    lon=sighting.site.lon_deg,
                    elev_m=sighting.site.elev_m,
                    tz=sighting.site.tz,
                ),
                sites_checked=len(sighting.multisite.sites),
                alt_ok=alt_ok,
                elong_ok=elong_ok,
                visible=visible,
            ),
            source=source,
            warnings=warnings,
        )
        return _json_response(request, payload.model_dump(), HILAL_CACHE)

    @app.api_route(
        "/api/v1/hilal/history",
        response_model=HilalHistoryResponse,
        tags=["Hilal"],
        summary=t("hilal_history.summary"),
        description=t("hilal_history.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "invalid_range", "Invalid date range"),
            429: _ERR_429,
            503: _ERR_503,
        },
    )
    @limiter.limit("240/minute")
    def hilal_history(
        request: Request,
        start: str | None = Query(default=None, alias="from", description=t("query.history_from")),
        end: str | None = Query(default=None, alias="to", description=t("query.history_to")),
    ):
        span = _history.index_range()
        if span is None:
            raise ApiError(
                "computation_unavailable",
                "Hilal history index is not available on this deployment.",
                503,
            )
        first, last = span
        start = start or first
        end = end or last
        if start > end:
            raise ApiError("invalid_range", "'from' must not be after 'to'.")
        months = [HilalHistoryItem.model_validate(item) for item in _history.items(start, end)]
        payload = HilalHistoryResponse(
            input=HilalHistoryInput.model_validate({"from": start, "to": end}),
            count=len(months),
            range=Coverage(first=first, last=last),
            months=months,
        )
        return _json_response(request, payload.model_dump(by_alias=True), HILAL_CACHE)

    @app.api_route(
        "/api/v1/hilal/viz",
        tags=["Hilal"],
        summary=t("hilal_viz.summary"),
        description=t("hilal_viz.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "out_of_coverage", "Year out of image range or date out of coverage"),
            429: _ERR_429,
            500: _err(500, "render_failed", "Chart rendering failed"),
            503: _ERR_503,
        },
    )
    @limiter.limit("30/hour")
    def hilal_viz(
        request: Request,
        month: str | None = Query(default=None, description=t("query.hijri_month")),
        year: str | None = Query(default=None, description=t("query.hilal_year")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
        bare: str | None = Query(default=None, description=BARE_QUERY_DESC),
        download: str | None = Query(default=None, description=DOWNLOAD_QUERY_DESC),
    ):
        month_int = _parse_int(month, "month")
        year_int = _parse_int(year, "year")
        is_bare = _parse_bool(bare, "bare")
        is_download = _parse_bool(download, "download")
        _hilal_render_year_check(year_int)
        res, sighting, alt_ok, elong_ok, _visible, ms_site, _source, _warnings = _hilal_context(
            month_int, year_int, _parse_bool(retro, "retro")
        )
        _imagepack.ensure_pack()
        kind = "viz-bare" if is_bare else "viz"
        attach = _attachment_headers("viz", res.target_year, res.target_month, is_download)
        cached = image_path(kind, res.target_year, res.target_month)
        if cached is not None:
            return _png_response(request, cached.read_bytes(), attach)
        try:
            png = _render_viz_png(res, sighting, ms_site, alt_ok, elong_ok, bare=is_bare)
        except Exception as exc:
            raise ApiError(
                "render_failed",
                f"Could not render chart: {exc.__class__.__name__}",
                500,
            ) from exc
        store(kind, res.target_year, res.target_month, png)
        return _png_response(request, png, attach)

    @app.api_route(
        "/api/v1/hilal/map",
        tags=["Hilal"],
        summary=t("hilal_map.summary"),
        description=t("hilal_map.description"),
        methods=["GET", "HEAD"],
        responses={
            400: _err(400, "out_of_coverage", "Year out of image range or date out of coverage"),
            429: _ERR_429,
            500: _err(500, "render_failed", "Map rendering failed"),
            503: _ERR_503,
        },
    )
    @limiter.limit("30/hour")
    def hilal_map(
        request: Request,
        month: str | None = Query(default=None, description=t("query.hijri_month")),
        year: str | None = Query(default=None, description=t("query.hilal_year")),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
        bare: str | None = Query(default=None, description=BARE_QUERY_DESC),
        download: str | None = Query(default=None, description=DOWNLOAD_QUERY_DESC),
    ):
        month_int = _parse_int(month, "month")
        year_int = _parse_int(year, "year")
        is_bare = _parse_bool(bare, "bare")
        is_download = _parse_bool(download, "download")
        _hilal_render_year_check(year_int)
        res, sighting, _alt_ok, _elong_ok, _visible, ms_site, _source, _warnings = _hilal_context(
            month_int, year_int, _parse_bool(retro, "retro")
        )
        _imagepack.ensure_pack()
        kind = "map-bare" if is_bare else "map"
        attach = _attachment_headers("map", res.target_year, res.target_month, is_download)
        cached = image_path(kind, res.target_year, res.target_month)
        if cached is not None:
            return _png_response(request, cached.read_bytes(), attach)
        site = sighting.site
        try:
            with _MAP_SEMAPHORE:
                png = _map_png_cached(
                    res.evening_date.isoformat(),
                    res.target_name,
                    res.target_year,
                    res.evening_label,
                    site.name,
                    site.lat_deg,
                    site.lon_deg,
                    ms_site.alt_refracted_deg,
                    ms_site.elong_deg,
                    is_bare,
                )
        except Exception as exc:
            raise ApiError(
                "render_failed",
                f"Could not render map: {exc.__class__.__name__}",
                500,
            ) from exc
        store(kind, res.target_year, res.target_month, png)
        return _png_response(request, png, attach)

    _TAG_ORDER = [
        "Today",
        "Convert",
        "Range",
        "Month",
        "Year",
        "Events",
        "Hilal",
        "Meta",
        "Health",
    ]
    _base_openapi = app.openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Duplicate Operation ID .*_head .*",
                category=UserWarning,
            )
            schema = _base_openapi()
        tags = {t["name"]: t for t in schema.get("tags", [])}
        ordered = [tags[name] for name in _TAG_ORDER if name in tags]
        ordered += [t for n, t in tags.items() if n not in _TAG_ORDER]
        schema["tags"] = ordered

        def rank(path: str) -> tuple[int, int]:
            p = schema["paths"][path]
            for op in p.values():
                for tag in op.get("tags", []):
                    if tag == "Table":
                        return (999, 0)
                    if tag in _TAG_ORDER:
                        return (_TAG_ORDER.index(tag), 0)
            return (998, 0)

        keep = sorted(
            (p for p in schema["paths"] if rank(p)[0] != 999),
            key=rank,
        )
        schema["paths"] = {
            p: {m: op for m, op in schema["paths"][p].items() if m != "head"}
            for p in keep
        }

        # Boolean-style query flags are parsed as strict strings at runtime
        # (true/false, any case, plus 1/0); declare them as booleans in the
        # generated reference so interactive clients render value toggles.
        flag_params = {"retro", "next", "bare", "download"}
        for params in [
            op.get("parameters", [])
            for path in schema["paths"].values()
            for op in path.values()
        ]:
            for param in params:
                if param.get("name") in flag_params:
                    param["schema"] = {"type": "boolean", "default": False}
                    param.pop("anyOf", None)

        tag_info = schema["info"]
        tag_info.setdefault("contact", {"name": "PIXO Studio", "email": "halo@pixostudio.id"})
        tag_info.setdefault("license", {"name": "MIT", "url": "https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE"})
        schema.setdefault("externalDocs", {
            "description": "Full docs, demo, FAQ and API reference",
            "url": settings.docs_url,
        })

        param_examples = {
            "date": "2025-01-03",
            "target_date": "2025-01-03",
            "calendar": "gregorian",
            "tz": "Asia/Jakarta",
            "retro": False,
            "next": False,
            "bare": False,
            "download": False,
            "year": "2026",
            "month": "3",
            "start": "2025-01-01",
            "end": "2025-01-31",
            "step": "day",
            "from": "1446-01",
            "to": "1446-12",
        }
        for op in (op for path in schema["paths"].values() for op in path.values()):
            for param in op.get("parameters", []):
                example = param_examples.get(param.get("name"))
                if example is not None:
                    param["example"] = example

        schemas = schema.setdefault("components", {}).setdefault("schemas", {})
        if "ErrorBody" not in schemas:
            # Shared error envelope referenced by every error response.
            schemas["ErrorBody"] = {
                "title": "ErrorBody",
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Stable machine-readable error code.",
                        "examples": ["invalid_date", "rate_limit_exceeded"],
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable explanation of what went wrong.",
                    },
                },
            }
            schemas["ErrorResponse"] = {
                "title": "ErrorResponse",
                "type": "object",
                "required": ["error"],
                "properties": {
                    "error": {"$ref": "#/components/schemas/ErrorBody"},
                },
            }
        for path in schema["paths"].values():
            for op in path.values():
                op.get("responses", {}).pop("422", None)

        head_note = (
            "HEAD works identically (same headers, no body). Conditional GETs "
            "are honored: send If-None-Match with a previous ETag to receive "
            "a 304 Not Modified."
        )
        for path in schema["paths"]:
            op = schema["paths"][path].get("get")
            if not op:
                continue
            desc = op.setdefault("description", "")
            if head_note not in desc:
                op["description"] = (desc + "\n\n" + head_note).strip()

        cacheable = {
            "/api/v1/today": "max-age=60, s-maxage until midnight in the requested timezone",
            "/api/v1/today/{target_date}": "max-age=86400",
            "/api/v1/convert": "max-age=86400",
            "/api/v1/range": "max-age=86400",
            "/api/v1/month": "max-age=86400",
            "/api/v1/year": "max-age=86400",
            "/api/v1/events": "max-age=86400",
            "/api/v1/hilal/info": "public, max-age=86400",
            "/api/v1/hilal/history": "public, max-age=86400",
            "/api/v1/hilal/viz": "public, max-age=86400",
            "/api/v1/hilal/map": "public, max-age=86400",
        }
        for path, ttl in cacheable.items():
            op = schema["paths"].get(path, {}).get("get")
            if not op:
                continue
            op.setdefault("responses", {})["304"] = {
                "description": (
                    f"Not Modified — the If-None-Match header matched the current "
                    f"ETag. Cache-Control: {ttl}."
                ),
                "headers": {
                    "ETag": {
                        "description": (
                            "Entity tag of the 200 body; compare weakly with If-None-Match."
                        ),
                        "schema": {"type": "string"},
                    },
                    "Cache-Control": {"schema": {"type": "string"}},
                },
            }

        for png_path, opname in (
            ("/api/v1/hilal/viz", "get"),
            ("/api/v1/hilal/map", "get"),
        ):
            op = schema["paths"].get(png_path, {}).get(opname)
            if op and "200" in op.get("responses", {}):
                op["responses"]["200"] = {
                    "description": "Hilal card PNG (720×1280; bare variant 1440×1520)",
                    "content": {"image/png": {}},
                }

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    @app.get("/playground", include_in_schema=False)
    async def playground_html():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title="MABIMS API — Playground",
            scalar_favicon_url="/favicon.ico",
            theme=Theme.BLUE_PLANET,
            force_dark_mode_state="dark",
            hide_models=True,
            show_sidebar=True,
            default_open_all_tags=False,
            agent=AgentScalarConfig(disabled=True),
            hidden_clients=["ruby", "rust", "scala", "elixir", "clj", "c"],
            custom_css="""
            /* logo */
            .logo {
                background: url('/logo.png') no-repeat left center;
                background-size: contain;
                height: 40px;
                margin: 16px;
            }
            """,
        )

    return app


app = create_app()


