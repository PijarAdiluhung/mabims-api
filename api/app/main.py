from __future__ import annotations

import calendar as pycalendar
import hashlib
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import TypeVar

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .calendar import SOURCE_MABIMS, CalendarService
from .config import APP_VERSION, Settings
from .coverage import (
    RETRO_SOURCE,
    RETRO_WARNING,
    load_coverage,
)
from .coverage import (
    Coverage as CoverageBounds,
)
from .events import find_events
from .fallback import FALLBACK_SOURCE, AladhanProvider, FallbackStore, MemoryFallbackStore
from .hilal.astro import lunar_age_hours, moonset_local, phase_angle_deg, sunset_utc
from .hilal.chart import build_chart_data, chart_png_bytes
from .hilal.service import MONTH_NAMES_ID, MonthNotResolvable, resolve_sighting_evening
from .mabims_astro import (
    SABANG_LAT_DEG,
    SABANG_LON_DEG,
    WIB,
    EveningObservation,
    observation_on_sunset,
)
from .mabims_computed import COMPUTED_SOURCE, MabimsCalcProvider, next_hijri_month
from .schemas import (
    ConversionInput,
    ConversionOutput,
    ConvertResponse,
    Coverage,
    EventItem,
    EventsInput,
    EventsResponse,
    HealthResponse,
    HilalEvening,
    HilalInfoResponse,
    HilalInput,
    HilalMonth,
    HilalPrevMonth,
    MetaResponse,
    MonthInput,
    MonthResponse,
    RangeInput,
    RangeItem,
    RangeResponse,
    RetroCoverage,
    Source,
    TableResponse,
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
    resolve_tz,
    tz_label,
)

FALLBACK_WARNING = (
    "Date is outside MABIMS table coverage; served from the Umm al-Qura fallback "
    "and may differ from MABIMS by around one day."
)
COMPUTED_WARNING = (
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria "
    "(hilal altitude >= 3 deg and elongation >= 6.4 deg at Sabang sunset)."
)
BORDERLINE_WARNING_TEMPLATE = (
    "Hijri month {ym} is close to the Neo MABIMS visibility threshold; the officially "
    "announced date may shift by one day."
)
COMPUTED_METHOD = "neo-mabims-sabang"
MAX_RANGE_DAYS = 45
RETRO_QUERY_DESC = "Set true to allow computed retro dates below the curated table"
HILAL_CACHE = {"Cache-Control": "public, max-age=86400, s-maxage=86400"}
HILAL_ALT_MIN_DEG = 3.0
HILAL_ELONG_MIN_DEG = 6.4

_HIJRI_YEARS_PER_GREGORIAN = 365.2425 / 354.36792

SABANG_TZ = "Asia/Jakarta"
SABANG_DISPLAY = "Sabang \u00b7 Indonesia"
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
    """Geocentric MABIMS criteria plus observer-clock facts for one evening."""

    __slots__ = ("criteria", "sunset_local", "moonset_local", "illumination_pct", "age_hours")

    def __init__(
        self,
        criteria: EveningObservation,
        sunset_local: str,
        moonset_local: str,
        illumination_pct: float,
        age_hours: float,
    ) -> None:
        self.criteria = criteria
        self.sunset_local = sunset_local
        self.moonset_local = moonset_local
        self.illumination_pct = illumination_pct
        self.age_hours = age_hours


def observe_sighting_evening(evening_date: date) -> SightingObservation:
    """Compose the full hilal payload for a sighting evening at Sabang.

    Criteria values (alt/elong/azimuth) come from the geocentric hisab in
    ``mabims_astro`` — the same function that drives month lengths. Sunset,
    moonset, illumination and age are observer-clock facts.
    """
    criteria = observation_on_sunset(evening_date)
    sunset_dt = sunset_utc(evening_date, SABANG_TZ, SABANG_LAT_DEG, SABANG_LON_DEG)
    phase = phase_angle_deg(sunset_dt)
    return SightingObservation(
        criteria=criteria,
        sunset_local=sunset_dt.astimezone(WIB).strftime("%H:%M"),
        moonset_local=moonset_local(evening_date, SABANG_TZ, SABANG_LAT_DEG, SABANG_LON_DEG),
        illumination_pct=(1.0 - math.cos(math.radians(phase))) / 2.0 * 100.0,
        age_hours=lunar_age_hours(sunset_dt),
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


def _json_response(content: dict, headers: dict[str, str]) -> JSONResponse:
    body = json.dumps(content, separators=(",", ":")).encode()
    etag = etag_from_bytes(body)
    merged = {**headers, **etag_headers(etag)}
    return JSONResponse(content=content, headers=merged)


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
    """
    normalized = (value or "").strip()
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


def create_app(settings: Settings | None = None, fallback_provider=None, computed_provider=None) -> FastAPI:
    settings = settings or Settings()

    data_path = settings.data_dir / "calendar_data.json"
    raw_bytes = data_path.read_bytes()
    data_version = hashlib.sha256(raw_bytes).hexdigest()[:12]

    stores: list = []
    computed_store: MemoryFallbackStore | None = None
    aladhan_store: FallbackStore | None = None
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

    if settings.enable_fallback and settings.enable_aladhan:
        provider = fallback_provider or AladhanProvider(settings.aladhan_base_url)
        aladhan_store = FallbackStore(settings.fallback_dir or settings.data_dir, provider)
        aladhan_store.load_existing()
        stores.append(aladhan_store)

    service = CalendarService(data_path, stores=stores)
    bounds: CoverageBounds = load_coverage(settings.data_dir)

    app = FastAPI(
        title="MABIMS API",
        version=APP_VERSION,
        tags=[
            {"name": "Health", "description": "Liveness probes"},
            {"name": "Today", "description": "Today's Hijri date (timezone-aware)"},
            {"name": "Convert", "description": "Single date conversion"},
            {"name": "Range", "description": "Bulk date range conversion"},
            {"name": "Month", "description": "All days in a calendar month"},
            {"name": "Year", "description": "All days in a calendar year"},
            {"name": "Events", "description": "Islamic observances"},
            {"name": "Hilal", "description": "Hilal visibility data and charts"},
            {"name": "Meta", "description": "API metadata and coverage"},
        ],
    )

    def _rate_limit_key(request: Request) -> str:
        if xff := request.headers.get("x-real-ip"):
            return xff
        return request.client.host if request.client else "unknown"

    limiter = Limiter(key_func=_rate_limit_key, default_limits=[settings.rate_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

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

    def _parse_retro(raw: str | None) -> bool:
        if raw is None or raw == "":
            return False
        lowered = raw.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise ApiError("invalid_retro", "'retro' must be 'true' or 'false'.")

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
        elif source == FALLBACK_SOURCE:
            warnings.append(FALLBACK_WARNING)
        return warnings

    def _aggregate(items: list) -> tuple[str, list[str]]:
        sources = {item.source for item in items}
        if FALLBACK_SOURCE in sources:
            aggregate = FALLBACK_SOURCE
        elif COMPUTED_SOURCE in sources:
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
        summary="Liveness probe",
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def healthz(request: Request):
        return JSONResponse(
            content={"status": "ok", "version": APP_VERSION},
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

    @app.api_route(
        "/api/v1/meta",
        response_model=MetaResponse,
        tags=["Meta"],
        summary="API metadata",
        description="Returns data version, coverage range, and computed status.",
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def meta(request: Request):
        computed_active, computed_months = computed_store.summary() if computed_store else (False, [])
        retro_info = None
        if active_computed is not None:
            retro_info = RetroCoverage(
                first=bounds.seed_first or bounds.retro_floor,
                floor=bounds.retro_floor,
            )
        payload = MetaResponse(
            version=APP_VERSION,
            data_version=data_version,
            coverage=Coverage(first=service.coverage_first_g, last=service.coverage_last_g),
            computed_active=computed_active,
            computed_months=computed_months,
            method=COMPUTED_METHOD if active_computed is not None else None,
            retro=retro_info,
            docs_url=settings.docs_url,
        )
        return _json_response(payload.model_dump(), SHORT_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/table",
        response_model=TableResponse,
        tags=["Table"],
        summary="Full calendar table",
        description="Returns the complete MABIMS calendar table for offline use.",
        methods=["GET", "HEAD"],
    )
    @limiter.exempt
    def table(request: Request):
        payload = TableResponse(
            version=data_version,
            gregorian_to_hijri=service.g2h,
            hijri_to_gregorian=service.h2g,
        )
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/convert",
        response_model=ConvertResponse,
        tags=["Convert"],
        summary="Convert a single date",
        description="Convert a date between Gregorian and Hijri calendars.",
        methods=["GET", "HEAD"],
    )
    def convert(
        request: Request,
        date_: str | None = Query(default=None, alias="date"),
        calendar: str = Query(default="gregorian"),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        if not date_:
            raise ApiError("missing_parameter", "You must provide a 'date' query parameter.")
        cal = _validate_calendar(calendar)
        is_retro = _parse_retro(retro)
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
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/today",
        response_model=ConvertResponse,
        tags=["Today"],
        summary="Today's Hijri date",
        description="Returns today's Hijri date, timezone-aware.",
        methods=["GET", "HEAD"],
    )
    def today(request: Request, tz: str | None = Query(default=None)):
        try:
            tzo = resolve_tz(tz)
        except ValueError as exc:
            raise ApiError("invalid_timezone", str(exc)) from exc
        today_iso = datetime.now(tzo).date().isoformat()
        value, source = _resolve_pair(today_iso, "gregorian")
        payload = ConvertResponse(
            input=ConversionInput(date=today_iso, calendar="gregorian", tz=tz_label(tzo)),
            output=ConversionOutput(date=value, calendar="hijri", **_parse_date_parts(value, "hijri")),
            source=source,
            warnings=_warnings_for(source, value),
        )
        return _json_response(payload.model_dump(), dynamic_cache_headers(tzo))

    @app.api_route(
        "/api/v1/today/{target_date}",
        response_model=ConvertResponse,
        tags=["Today"],
        summary="Hijri date for a fixed Gregorian date",
        description="Immutable endpoint — CDN-cacheable forever. Date format: YYYY-MM-DD.",
        methods=["GET", "HEAD"],
    )
    def today_on(
        request: Request,
        target_date: str,
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        is_retro = _parse_retro(retro)
        target = _parse_iso_date(target_date)
        value, source = _resolve_pair(target.isoformat(), "gregorian", is_retro)
        payload = ConvertResponse(
            input=ConversionInput(date=target.isoformat(), calendar="gregorian"),
            output=ConversionOutput(date=value, calendar="hijri", **_parse_date_parts(value, "hijri")),
            source=source,
            warnings=_warnings_for(source, value),
        )
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

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
        summary="Bulk date conversion",
        description="Convert a date range between Gregorian and Hijri. Maximum 45 days.",
        methods=["GET", "HEAD"],
    )
    def range_(
        request: Request,
        start: str = Query(...),
        end: str = Query(...),
        calendar: str = Query(default="gregorian"),
        step: str = Query(default="day"),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        cal = _validate_calendar(calendar)
        is_retro = _parse_retro(retro)
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
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/events",
        response_model=EventsResponse,
        tags=["Events"],
        summary="Islamic events for a year",
        description="Curated Islamic observances: 1 Muharram, Maulid, Ramadan, Eid.",
        methods=["GET", "HEAD"],
    )
    def events(
        request: Request,
        year: int = Query(...),
        calendar: str = Query(default="hijri"),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        cal = _validate_calendar(calendar)
        is_retro = _parse_retro(retro)
        if not 1000 <= year <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")
        items = [
            EventItem(
                event=definition.slug,
                name=definition.name,
                gregorian=g_iso,
                hijri=h_iso,
                source=service.lookup(h_iso, "hijri").source,
            )
            for definition, g_iso, h_iso in find_events(service, year, cal, retro=is_retro)
        ]
        _relabel_retro(items, is_retro)
        aggregate_source, warnings = _aggregate(items)
        payload = EventsResponse(
            input=EventsInput(year=year, calendar=cal),
            count=len(items),
            events=items,
            warnings=warnings,
        )
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/month",
        response_model=MonthResponse,
        tags=["Month"],
        summary="All days in a month",
        description="Calendar-grid sugar over /range. Returns every day in the given month.",
        methods=["GET", "HEAD"],
    )
    def month(
        request: Request,
        year: int = Query(...),
        month: int = Query(...),
        calendar: str = Query(default="hijri"),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        cal = _validate_calendar(calendar)
        is_retro = _parse_retro(retro)
        if not 1 <= month <= 12:
            raise ApiError("invalid_month", "'month' must be between 1 and 12.")
        if not 1000 <= year <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")

        if cal == "gregorian":
            days_in_month = pycalendar.monthrange(year, month)[1]
            start_d = date(year, month, 1)
            end_d = date(year, month, days_in_month)
            _check_supported(start_d.isoformat(), cal, is_retro)
            _check_supported(end_d.isoformat(), cal, is_retro)
            items = _collect_items(start_d.isoformat(), end_d.isoformat(), cal, is_retro)
        else:
            _check_supported(f"{year:04d}-{month:02d}-01", cal, is_retro)
            items = _hijri_month_items(year, month, is_retro)
            if not items:
                raise ApiError(
                    "out_of_coverage",
                    f"Hijri month {year:04d}-{month:02d} is outside available coverage; see /api/v1/meta.",
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
            input=MonthInput(year=year, month=month, calendar=cal),
            count=len(items),
            items=items,
            warnings=warnings,
        )
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

    @app.api_route(
        "/api/v1/year",
        response_model=YearResponse,
        tags=["Year"],
        summary="All days in a year",
        description="Returns every day in all 12 months of a Hijri or Gregorian year.",
        methods=["GET", "HEAD"],
    )
    def year(
        request: Request,
        year: int = Query(...),
        calendar: str = Query(default="hijri"),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        cal = _validate_calendar(calendar)
        is_retro = _parse_retro(retro)
        if not 1 <= year <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")

        all_items: list[RangeItem] = []
        months: dict[int, list[RangeItem]] = {}

        for m in range(1, 13):
            if cal == "gregorian":
                days_in_month = pycalendar.monthrange(year, m)[1]
                start_d = date(year, m, 1)
                end_d = date(year, m, days_in_month)
                _check_supported(start_d.isoformat(), cal, is_retro)
                _check_supported(end_d.isoformat(), cal, is_retro)
                items = _collect_items(start_d.isoformat(), end_d.isoformat(), cal, is_retro)
            else:
                _check_supported(f"{year:04d}-{m:02d}-01", cal, is_retro)
                items = _hijri_month_items(year, m, is_retro)
                if not items:
                    raise ApiError(
                        "out_of_coverage",
                        f"Hijri month {year:04d}-{m:02d} is outside available coverage; see /api/v1/meta.",
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
            input=YearInput(year=year, calendar=cal),
            count=len(all_items),
            months=months,
            warnings=warnings,
        )
        return _json_response(payload.model_dump(), IMMUTABLE_CACHE_HEADERS)

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
        crit = sighting.criteria
        alt_ok = crit.moon_alt_deg >= HILAL_ALT_MIN_DEG
        elong_ok = crit.elongation_deg >= HILAL_ELONG_MIN_DEG
        source = service.lookup(evening_g, "gregorian").source
        if retro and source == COMPUTED_SOURCE and evening_g < bounds.curated_first:
            source = RETRO_SOURCE
        warnings = _warnings_for(
            source, f"{res.prev_year:04d}-{res.prev_month:02d}-15"
        )
        return res, sighting, alt_ok, elong_ok, source, warnings

    @app.api_route(
        "/api/v1/hilal/info",
        response_model=HilalInfoResponse,
        tags=["Hilal"],
        summary="Hilal visibility data",
        description="Geocentric hisab data for the evening deciding a Hijri month start (Sabang).",
        methods=["GET", "HEAD"],
    )
    @limiter.limit("60/hour")
    def hilal_info(
        request: Request,
        month: int = Query(...),
        year: int = Query(...),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        res, sighting, alt_ok, elong_ok, source, warnings = _hilal_context(
            month, year, _parse_retro(retro)
        )
        crit = sighting.criteria
        payload = HilalInfoResponse(
            input=HilalInput(month=month, year=year),
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
                moon_alt_deg=round(crit.moon_alt_deg, 2),
                moon_az_deg=round(crit.moon_az_deg, 2),
                sun_alt_deg=round(crit.sun_alt_deg, 2),
                elongation_deg=round(crit.elongation_deg, 2),
                illumination_pct=round(sighting.illumination_pct, 2),
                age_hours=round(sighting.age_hours, 1),
                alt_ok=alt_ok,
                elong_ok=elong_ok,
                visible=alt_ok and elong_ok,
            ),
            source=source,
            warnings=warnings,
        )
        return _json_response(payload.model_dump(), HILAL_CACHE)

    @app.api_route(
        "/api/v1/hilal/viz",
        tags=["Hilal"],
        summary="Hilal sky chart PNG",
        description="Renders a 720x1280 PNG chart of hilal visibility with MABIMS criteria table.",
        methods=["GET", "HEAD"],
    )
    @limiter.limit("30/hour")
    def hilal_viz(
        request: Request,
        month: int = Query(...),
        year: int = Query(...),
        retro: str | None = Query(default=None, description=RETRO_QUERY_DESC),
    ):
        res, sighting, alt_ok, elong_ok, _source, _warnings = _hilal_context(
            month, year, _parse_retro(retro)
        )
        crit = sighting.criteria
        data = build_chart_data(
            hijri_label=res.evening_label,
            evening_date=res.evening_date,
            location_display=SABANG_DISPLAY,
            visibility_label=(
                f"VISIBILITAS 1 {res.target_name} {res.target_year} H".upper()
            ),
            sunset=sighting.sunset_local,
            moonset=sighting.moonset_local,
            moon_alt=crit.moon_alt_deg,
            moon_az=crit.moon_az_deg,
            sun_alt=crit.sun_alt_deg,
            sun_az=crit.sun_az_deg,
            elong=crit.elongation_deg,
            illum=sighting.illumination_pct / 100.0,
            alt_ok=alt_ok,
            elong_ok=elong_ok,
            alt_margin=crit.moon_alt_deg - HILAL_ALT_MIN_DEG,
            elong_margin=crit.elongation_deg - HILAL_ELONG_MIN_DEG,
        )
        try:
            png = chart_png_bytes(data)
        except Exception as exc:
            raise ApiError(
                "render_failed",
                f"Could not render chart: {exc.__class__.__name__}",
                500,
            ) from exc
        return Response(
            content=png,
            media_type="image/png",
            headers={**HILAL_CACHE, **etag_headers(etag_from_bytes(png))},
        )

    return app


app = create_app()
