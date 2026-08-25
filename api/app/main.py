from __future__ import annotations

import calendar as pycalendar
import hashlib
import json
from datetime import date, datetime

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .calendar import SOURCE_MABIMS, CalendarService, MonthKey
from .config import APP_VERSION, Settings
from .fallback import FALLBACK_SOURCE, AladhanProvider, FallbackStore, MemoryFallbackStore
from .mabims_computed import COMPUTED_SOURCE, MabimsCalcProvider
from .precomputed import PRECOMPUTED_FILENAME, PrecomputedDataError, PrecomputedStore
from .schemas import (
    ConvertResponse,
    ConversionInput,
    ConversionOutput,
    Coverage,
    HealthResponse,
    MetaResponse,
    RangeItem,
    RangeResponse,
)
from .timeutil import (
    IMMUTABLE_CACHE_HEADERS,
    NO_STORE_HEADERS,
    SHORT_CACHE_HEADERS,
    dynamic_cache_headers,
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
MAX_RANGE_DAYS = 400
MIN_SUPPORTED_GREGORIAN = "1945-01-01"
SUPPORTED_FORWARD_YEARS = 30
EPHEMERIS_LAST_SUPPORTED_DAY = date(2053, 8, 1)

_HIJRI_YEARS_PER_GREGORIAN = 365.2425 / 354.36792


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


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ApiError("invalid_date", f"'{value}' is not a valid ISO date (YYYY-MM-DD).")


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
    precomputed_store: PrecomputedStore | None = None
    active_computed: MabimsCalcProvider | None = computed_provider

    if settings.enable_fallback and settings.enable_computed:
        anchor_raw = json.loads(raw_bytes)
        first_h = min(anchor_raw["hijri_to_gregorian"])
        anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
        anchor_gregorian = date.fromisoformat(anchor_raw["hijri_to_gregorian"][first_h])
        if active_computed is None:
            active_computed = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
        computed_store = MemoryFallbackStore(settings.fallback_dir or settings.data_dir, active_computed)
        stores.append(computed_store)
        try:
            precomputed_store = PrecomputedStore(settings.data_dir / PRECOMPUTED_FILENAME)
        except (PrecomputedDataError, OSError, ValueError):
            precomputed_store = None
        if precomputed_store is not None:
            stores.insert(0, precomputed_store)
            seed = getattr(active_computed, "seed_from_pairs", None)
            if seed is not None:
                try:
                    seed(precomputed_store.h2g)
                except ValueError:
                    pass

    if settings.enable_fallback and settings.enable_aladhan:
        provider = fallback_provider or AladhanProvider(settings.aladhan_base_url)
        aladhan_store = FallbackStore(settings.fallback_dir or settings.data_dir, provider)
        aladhan_store.load_existing()
        stores.append(aladhan_store)

    service = CalendarService(data_path, stores=stores)

    app = FastAPI(title="MABIMS Date Converter API", version=APP_VERSION)

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
                return _error(
                    "forbidden_origin",
                    f"Origin '{origin}' is not allowed to access this API.",
                    403,
                )
            response = await call_next(request)
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "600"
            existing_vary = response.headers.get("Vary")
            response.headers["Vary"] = f"{existing_vary}, Origin" if existing_vary else "Origin"
        return response

    def _resolve_pair(date_iso: str, calendar: str) -> tuple[str, str]:
        _check_supported(date_iso, calendar)
        try:
            result = service.resolve(date_iso, calendar)
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
        if calendar == "hijri":
            resolved_gregorian = result.value
            if (
                resolved_gregorian < MIN_SUPPORTED_GREGORIAN
                or resolved_gregorian > _max_supported_gregorian().isoformat()
            ):
                raise ApiError("date_out_of_supported_range", _supported_range_message())
        return result.value, result.source

    def _max_supported_gregorian() -> date:
        today = date.today()
        try:
            forward_cap = today.replace(year=today.year + SUPPORTED_FORWARD_YEARS)
        except ValueError:
            forward_cap = today.replace(year=today.year + SUPPORTED_FORWARD_YEARS, day=28)
        return min(forward_cap, EPHEMERIS_LAST_SUPPORTED_DAY)

    def _supported_range_message() -> str:
        return (
            f"Supported range is {MIN_SUPPORTED_GREGORIAN} through "
            f"{_max_supported_gregorian().isoformat()} (gregorian)."
        )

    def _check_supported(date_iso: str, calendar: str) -> None:
        max_g = _max_supported_gregorian().isoformat()
        if calendar == "gregorian":
            if date_iso < MIN_SUPPORTED_GREGORIAN or date_iso > max_g:
                raise ApiError("date_out_of_supported_range", _supported_range_message())
            return
        if active_computed is None:
            return
        anchor_h = active_computed.anchor_hijri
        anchor_g = active_computed.anchor_gregorian
        low_year = _hijri_bound_year(anchor_h, anchor_g, 1945) - 2
        high_year = _hijri_bound_year(anchor_h, anchor_g, _max_supported_gregorian().year) + 2
        year = int(date_iso[0:4])
        if year < low_year or year > high_year:
            raise ApiError("date_out_of_supported_range", _supported_range_message())

    def _warnings_for(source: str, hijri_value: str | None = None) -> list[str]:
        warnings: list[str] = []
        if source == COMPUTED_SOURCE:
            warnings.append(COMPUTED_WARNING)
            if hijri_value:
                ym = hijri_value[0:7]
                borderline = set(active_computed.borderline_months()) if active_computed else set()
                if precomputed_store is not None:
                    borderline |= precomputed_store.borderline
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

    @app.api_route("/healthz", response_model=None, methods=["GET", "HEAD"])
    @limiter.exempt
    def healthz(request: Request):
        return JSONResponse(
            content={"status": "ok", "version": APP_VERSION},
            headers=NO_STORE_HEADERS,
        )

    @app.api_route("/api/v1/meta", response_model=None, methods=["GET", "HEAD"])
    @limiter.exempt
    def meta(request: Request):
        fallback_active, fallback_months = aladhan_store.summary() if aladhan_store else (False, [])
        computed_active, computed_months = computed_store.summary() if computed_store else (False, [])
        if precomputed_store is not None:
            pre_active, pre_labels = precomputed_store.summary()
            computed_active = computed_active or pre_active
            computed_months = sorted(set(computed_months) | set(pre_labels))
        payload = MetaResponse(
            version=APP_VERSION,
            data_version=data_version,
            coverage=Coverage(first=service.coverage_first_g, last=service.coverage_last_g),
            fallback_active=fallback_active,
            fallback_months=fallback_months,
            computed_active=computed_active,
            computed_months=computed_months,
            method=COMPUTED_METHOD if active_computed is not None else None,
            docs_url=settings.docs_url,
        )
        return JSONResponse(content=payload.model_dump(), headers=SHORT_CACHE_HEADERS)

    @app.api_route("/api/v1/convert", response_model=None, methods=["GET", "HEAD"])
    def convert(
        request: Request,
        date_: str | None = Query(default=None, alias="date"),
        calendar: str = Query(default="gregorian"),
    ):
        if not date_:
            raise ApiError("missing_parameter", "You must provide a 'date' query parameter.")
        cal = _validate_calendar(calendar)
        target = _parse_iso_date(date_)
        value, source = _resolve_pair(target.isoformat(), cal)
        opposite = "hijri" if cal == "gregorian" else "gregorian"
        hijri_value = value if cal == "gregorian" else target.isoformat()
        payload = ConvertResponse(
            input=ConversionInput(date=target.isoformat(), calendar=cal),
            output=ConversionOutput(date=value, calendar=opposite),
            source=source,
            warnings=_warnings_for(source, hijri_value),
        )
        return JSONResponse(content=payload.model_dump(), headers=IMMUTABLE_CACHE_HEADERS)

    @app.api_route("/api/v1/today", response_model=None, methods=["GET", "HEAD"])
    def today(request: Request, tz: str | None = Query(default=None)):
        try:
            tzo = resolve_tz(tz)
        except ValueError as exc:
            raise ApiError("invalid_timezone", str(exc))
        today_iso = datetime.now(tzo).date().isoformat()
        value, source = _resolve_pair(today_iso, "gregorian")
        payload = ConvertResponse(
            input=ConversionInput(date=today_iso, calendar="gregorian", tz=tz_label(tzo)),
            output=ConversionOutput(date=value, calendar="hijri"),
            source=source,
            warnings=_warnings_for(source, value),
        )
        return JSONResponse(content=payload.model_dump(), headers=dynamic_cache_headers(tzo))

    @app.api_route("/api/v1/today/{target_date}", response_model=None, methods=["GET", "HEAD"])
    def today_on(request: Request, target_date: str):
        target = _parse_iso_date(target_date)
        value, source = _resolve_pair(target.isoformat(), "gregorian")
        payload = ConvertResponse(
            input=ConversionInput(date=target.isoformat(), calendar="gregorian"),
            output=ConversionOutput(date=value, calendar="hijri"),
            source=source,
            warnings=_warnings_for(source, value),
        )
        return JSONResponse(content=payload.model_dump(), headers=IMMUTABLE_CACHE_HEADERS)

    def _collect_items(start: date, end: date, cal: str) -> list[RangeItem]:
        service.ensure_range(start.isoformat(), end.isoformat(), cal)
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
                    gregorian=iso if cal == "gregorian" else result.value,
                    hijri=result.value if cal == "gregorian" else iso,
                    source=result.source,
                )
            )
            cursor = date.fromordinal(cursor.toordinal() + 1)
        return items

    @app.api_route("/api/v1/range", response_model=None, methods=["GET", "HEAD"])
    def range_(
        request: Request,
        start: str = Query(...),
        end: str = Query(...),
        calendar: str = Query(default="gregorian"),
        step: str = Query(default="day"),
    ):
        cal = _validate_calendar(calendar)
        if step != "day":
            raise ApiError("invalid_step", "Only step='day' is supported.")
        start_d = _parse_iso_date(start)
        end_d = _parse_iso_date(end)
        if start_d > end_d:
            raise ApiError("invalid_range", "'start' must be on or before 'end'.")
        span = (end_d - start_d).days + 1
        if span > MAX_RANGE_DAYS:
            raise ApiError("range_too_large", f"Range is limited to {MAX_RANGE_DAYS} days.")
        _check_supported(start_d.isoformat(), cal)
        _check_supported(end_d.isoformat(), cal)
        items = _collect_items(start_d, end_d, cal)
        aggregate_source, warnings = _aggregate(items)
        payload = RangeResponse(
            input={"start": start_d.isoformat(), "end": end_d.isoformat(), "calendar": cal},
            count=len(items),
            items=items,
            warnings=warnings,
        )
        return JSONResponse(content=payload.model_dump(), headers=IMMUTABLE_CACHE_HEADERS)

    @app.api_route("/api/v1/month", response_model=None, methods=["GET", "HEAD"])
    def month(
        request: Request,
        year: int = Query(...),
        month: int = Query(...),
        calendar: str = Query(default="gregorian"),
    ):
        cal = _validate_calendar(calendar)
        if not 1 <= month <= 12:
            raise ApiError("invalid_month", "'month' must be between 1 and 12.")
        if not 1000 <= year <= 3000:
            raise ApiError("invalid_year", "'year' is out of supported bounds.")

        if cal == "gregorian":
            days_in_month = pycalendar.monthrange(year, month)[1]
            start_d = date(year, month, 1)
            end_d = date(year, month, days_in_month)
            _check_supported(start_d.isoformat(), cal)
            _check_supported(end_d.isoformat(), cal)
            items = _collect_items(start_d, end_d, cal)
        else:
            prefix = f"{year:04d}-{month:02d}-"
            _check_supported(f"{prefix}01", cal)
            has_main_data = any(key.startswith(prefix) for key in service.h2g)
            if not has_main_data:
                service.ensure_hijri_month(year, month)
            pairs: list[tuple[str, str]] = []
            for h_iso, g_iso in service.h2g.items():
                if h_iso.startswith(prefix):
                    pairs.append((g_iso, h_iso))
            pairs.sort()
            if not pairs:
                raise ApiError(
                    "out_of_coverage",
                    f"Hijri month {prefix[:-1]} is outside available coverage; see /api/v1/meta.",
                    400,
                )
            items = [
                RangeItem(gregorian=g, hijri=h, source=service.lookup(h, "hijri").source)
                for g, h in pairs
            ]
            start_d = date.fromisoformat(pairs[0][0])
            end_d = date.fromisoformat(pairs[-1][0])
            if (
                start_d.isoformat() < MIN_SUPPORTED_GREGORIAN
                or end_d.isoformat() > _max_supported_gregorian().isoformat()
            ):
                raise ApiError("date_out_of_supported_range", _supported_range_message())

        aggregate_source, warnings = _aggregate(items)
        payload = RangeResponse(
            input={"year": year, "month": month, "calendar": cal},
            count=len(items),
            items=items,
            warnings=warnings,
        )
        return JSONResponse(content=payload.model_dump(), headers=IMMUTABLE_CACHE_HEADERS)

    return app


app = create_app()
