from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TZ = ZoneInfo("Asia/Jakarta")

MIN_CACHE_TTL_SECONDS = 30
DAY_TTL_SECONDS = 86_400

_OFFSET_RE = re.compile(r"^(?:UTC)?([+-])?(\d{1,2})(?::(\d{2}))?$", re.IGNORECASE)


def resolve_tz(value: str | None) -> timezone | ZoneInfo:
    if not value or not value.strip():
        return DEFAULT_TZ
    candidate = value.strip()
    try:
        return ZoneInfo(candidate)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        pass
    match = _OFFSET_RE.match(candidate.replace(" ", ""))
    if match:
        sign = -1 if match.group(1) == "-" else 1
        hours = int(match.group(2))
        minutes = int(match.group(3) or 0)
        if hours > 23 or minutes > 59:
            raise ValueError(f"Invalid UTC offset: {candidate}")
        return timezone(sign * timedelta(hours=hours, minutes=minutes))
    raise ValueError(f"Unknown timezone: {candidate}")


def tz_label(tz: timezone | ZoneInfo) -> str:
    return str(tz)


def seconds_until_midnight(now: datetime) -> int:
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    remaining = int((tomorrow - now).total_seconds())
    return max(remaining, MIN_CACHE_TTL_SECONDS)


IMMUTABLE_CACHE_HEADERS = {"Cache-Control": f"public, max-age={DAY_TTL_SECONDS}, s-maxage={DAY_TTL_SECONDS}"}


def dynamic_cache_headers(tz: timezone | ZoneInfo) -> dict[str, str]:
    ttl = seconds_until_midnight(datetime.now(tz))
    return {"Cache-Control": f"public, max-age=60, s-maxage={ttl}"}


NO_STORE_HEADERS = {"Cache-Control": "no-store"}
SHORT_CACHE_HEADERS = {"Cache-Control": "public, max-age=300"}


def etag_from_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def etag_headers(etag: str) -> dict[str, str]:
    return {"ETag": f'"{etag}"'}
