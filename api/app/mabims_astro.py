from __future__ import annotations

import math
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from pathlib import Path

SABANG_LAT_DEG = 5.0 + 53.0 / 60.0
SABANG_LON_DEG = 95.0 + 19.0 / 60.0
ALT_MIN_DEG = 3.0
ELONG_MIN_DEG = 6.4
WIB = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class CriteriaResult:
    evaluated_on: date
    alt_deg: float
    elong_deg: float

    @property
    def visible(self) -> bool:
        return bool(self.alt_deg >= ALT_MIN_DEG and self.elong_deg >= ELONG_MIN_DEG)


class _Ephemeris:
    def __init__(self) -> None:
        from skyfield import almanac
        from skyfield.api import Loader, wgs84

        directory = os.environ.get("MABIMS_EPHEMERIS_DIR")
        path = Path(directory) if directory else Path(tempfile.gettempdir()) / "mabims-ephemeris"
        path.mkdir(parents=True, exist_ok=True)
        loader = Loader(str(path))
        self.ts = loader.timescale(builtin=True)
        self.eph = loader("de421.bsp")
        self._almanac = almanac
        self._earth = self.eph["earth"]
        self._moon = self.eph["moon"]
        self._sun = self.eph["sun"]
        self._site = wgs84.latlon(SABANG_LAT_DEG, SABANG_LON_DEG)
        self._topo = self._earth + self._site


_lock = threading.Lock()


@lru_cache(maxsize=1)
def _eph() -> _Ephemeris:
    with _lock:
        return _Ephemeris()


def _sunset_utc(d: date) -> datetime:
    eph = _eph()
    start_local = datetime.combine(d, time(0, 0), tzinfo=WIB)
    end_local = start_local + timedelta(days=1)
    f = eph._almanac.sunrise_sunset(eph.eph, eph._site)
    times, events = eph._almanac.find_discrete(
        eph.ts.from_datetime(start_local), eph.ts.from_datetime(end_local), f
    )
    for t, ev in zip(times, events):
        if not ev:
            return t.utc_datetime()
    raise ValueError(f"no sunset found for {d}")


def _refraction_deg(alt_deg: float) -> float:
    h = max(alt_deg, -1.0)
    arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11)))
    return arcmin / 60.0


def eph_ts_from_utc(dt_utc: datetime):
    return _eph().ts.from_datetime(dt_utc.astimezone(timezone.utc))


def criteria_on_day29(month_start: date) -> CriteriaResult:
    day29 = month_start + timedelta(days=28)
    sunset = _sunset_utc(day29)
    t = eph_ts_from_utc(sunset)

    eph = _eph()
    geo = eph._earth.at(t)
    moon_apparent = geo.observe(eph._moon).apparent()
    sun_apparent = geo.observe(eph._sun).apparent()
    elong = moon_apparent.separation_from(sun_apparent).degrees

    ra, dec, _dist = moon_apparent.radec(epoch=t)
    lat = math.radians(SABANG_LAT_DEG)
    dec_r = math.radians(dec.degrees)
    lst_deg = (t.gast * 15.0 + SABANG_LON_DEG) % 360.0
    ha_deg = ((lst_deg - ra.hours * 15.0 + 180.0) % 360.0) - 180.0
    ha = math.radians(ha_deg)
    sin_alt = math.sin(dec_r) * math.sin(lat) + math.cos(dec_r) * math.cos(lat) * math.cos(ha)
    alt_geo = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    alt_refracted = alt_geo + _refraction_deg(alt_geo)

    return CriteriaResult(evaluated_on=day29, alt_deg=alt_refracted, elong_deg=elong)


def month_length(month_start: date) -> int:
    return 29 if criteria_on_day29(month_start).visible else 30


def next_month_start(month_start: date) -> date:
    return month_start + timedelta(days=month_length(month_start))
