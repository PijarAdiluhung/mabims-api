from __future__ import annotations

import calendar as pycalendar
import hashlib
from datetime import date, datetime

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .calendar import SOURCE_MABIMS, CalendarService, MonthKey
from .config import APP_VERSION, Settings
from .fallback import FALLBACK_SOURCE, AladhanProvider, FallbackStore
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
MAX_RANGE_DAYS = 400


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


def _host_of(origin: str) -> str:
    host = origin.split("://", 1)[-1]
    return host.split("/", 1)[0].lower()


def _origin_allowed(origin: str, settings: Settings) -> bool:
    if origin in settings.allowed_origins:
        return True
    host = _host_of(origin)
    for suffix in settings.origin_suffixes:
        suffix_host = _host_of(suffix if "://" in suffix else f"https://{suffix}")
        if host == suffix_host or host.endswith(f".{suffix_host}"):
            return True
    return False


def create_app(settings: Settings | None = None, fallback_provider=None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="MABIMS Date Converter API", version=APP_VERSION)

    store: FallbackStore | None = None
    if settings.enable_fallback:
        provider = fallback_provider or AladhanProvider(settings.aladhan_base_url)
        store = FallbackStore(settings.fallback_dir or settings.data_dir, provider)
        store.load_existing()
    service = CalendarService(settings.data_dir / "calendar_data.json", store)
    data_version = hashlib.sha256(
        (settings.data_dir / "calendar_data.json").read_bytes()
    ).hexdigest()[:12]

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
        result = service.resolve(date_iso, calendar)
        if result.value is None:
            raise ApiError(
                "date_not_found",
                f"No calendar pair exists for {date_iso} ({calendar}). See /api/v1/meta for coverage.",
                404,
            )
        return result.value, result.source

    def _warnings_for(source: str) -> list[str]:
        return [FALLBACK_WARNING] if source == FALLBACK_SOURCE else []

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
        fallback_active, fallback_months = service.fallback_summary()
        payload = MetaResponse(
            version=APP_VERSION,
            data_version=data_version,
            coverage=Coverage(first=service.coverage_first_g, last=service.coverage_last_g),
            fallback_active=fallback_active,
            fallback_months=fallback_months,
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
        payload = ConvertResponse(
            input=ConversionInput(date=target.isoformat(), calendar=cal),
            output=ConversionOutput(date=value, calendar=opposite),
            source=source,
            warnings=_warnings_for(source),
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
            warnings=_warnings_for(source),
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
            warnings=_warnings_for(source),
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
        items = _collect_items(start_d, end_d, cal)
        aggregate_source = SOURCE_MABIMS
        if any(item.source != SOURCE_MABIMS for item in items):
            aggregate_source = FALLBACK_SOURCE
        payload = RangeResponse(
            input={"start": start_d.isoformat(), "end": end_d.isoformat(), "calendar": cal},
            count=len(items),
            items=items,
            warnings=[FALLBACK_WARNING] if aggregate_source == FALLBACK_SOURCE else [],
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
            items = _collect_items(start_d, end_d, cal)
        else:
            prefix = f"{year:04d}-{month:02d}-"
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

        aggregate_source = FALLBACK_SOURCE if any(i.source != SOURCE_MABIMS for i in items) else SOURCE_MABIMS
        payload = RangeResponse(
            input={"year": year, "month": month, "calendar": cal},
            count=len(items),
            items=items,
            warnings=[FALLBACK_WARNING] if aggregate_source == FALLBACK_SOURCE else [],
        )
        return JSONResponse(content=payload.model_dump(), headers=IMMUTABLE_CACHE_HEADERS)

    return app


app = create_app()
