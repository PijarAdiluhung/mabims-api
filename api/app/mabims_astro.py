from __future__ import annotations

import math
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
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


@dataclass(frozen=True)
class EveningObservation:
    """Full geocentric hisab of a sunset instant (MABIMS reference frame).

    All angles follow the Indonesian geocentric convention used by the curated
    table and the computed tier — deliberately NOT topocentric, so the verdict
    always agrees with ``month_length``.
    """

    evaluated_on: date
    moon_alt_deg: float  # geocentric, refraction-corrected
    moon_az_deg: float  # geocentric, degrees from north, clockwise
    sun_alt_deg: float  # geocentric geometric
    sun_az_deg: float
    elongation_deg: float

    @property
    def visible(self) -> bool:
        return bool(self.moon_alt_deg >= ALT_MIN_DEG and self.elongation_deg >= ELONG_MIN_DEG)


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
    for t, ev in zip(times, events, strict=True):
        if not ev:
            return t.utc_datetime()
    raise ValueError(f"no sunset found for {d}")


def _refraction_deg(alt_deg: float) -> float:
    h = max(alt_deg, -1.0)
    arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11)))
    return arcmin / 60.0


def eph_ts_from_utc(dt_utc: datetime):
    return _eph().ts.from_datetime(dt_utc.astimezone(UTC))


def _geo_altaz(t, ra_hours: float, dec_deg: float) -> tuple[float, float]:
    """Geocentric (geometric altitude, azimuth from north clockwise) at Sabang."""
    lat = math.radians(SABANG_LAT_DEG)
    dec_r = math.radians(dec_deg)
    lst_deg = (t.gast * 15.0 + SABANG_LON_DEG) % 360.0
    ha_deg = ((lst_deg - ra_hours * 15.0 + 180.0) % 360.0) - 180.0
    ha = math.radians(ha_deg)
    sin_alt = math.sin(dec_r) * math.sin(lat) + math.cos(dec_r) * math.cos(lat) * math.cos(ha)
    alt_geo = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    az_denom = math.cos(ha) * math.sin(lat) - math.tan(dec_r) * math.cos(lat)
    az_north = (math.degrees(math.atan2(math.sin(ha), az_denom)) + 180.0) % 360.0
    return alt_geo, az_north


def observation_on_sunset(d: date) -> EveningObservation:
    """Single source of truth for the hisab of sunset on ``d``.

    Used both by the month-length engine (via :func:`criteria_on_sunset`) and
    by the /hilal endpoints, so a verdict can never contradict the tables.
    """
    sunset = _sunset_utc(d)
    t = eph_ts_from_utc(sunset)

    eph = _eph()
    geo = eph._earth.at(t)
    moon_apparent = geo.observe(eph._moon).apparent()
    sun_apparent = geo.observe(eph._sun).apparent()

    moon_ra, moon_dec, _dist = moon_apparent.radec(epoch=t)
    sun_ra, sun_dec, _dist_sun = sun_apparent.radec(epoch=t)
    moon_alt, moon_az = _geo_altaz(t, moon_ra.hours, moon_dec.degrees)
    sun_alt, sun_az = _geo_altaz(t, sun_ra.hours, sun_dec.degrees)

    return EveningObservation(
        evaluated_on=d,
        moon_alt_deg=moon_alt + _refraction_deg(moon_alt),
        moon_az_deg=moon_az,
        sun_alt_deg=sun_alt,
        sun_az_deg=sun_az,
        elongation_deg=moon_apparent.separation_from(sun_apparent).degrees,
    )


def criteria_on_sunset(d: date) -> CriteriaResult:
    obs = observation_on_sunset(d)
    return CriteriaResult(evaluated_on=d, alt_deg=obs.moon_alt_deg, elong_deg=obs.elongation_deg)


def criteria_on_day29(month_start: date) -> CriteriaResult:
    return criteria_on_sunset(month_start + timedelta(days=28))


def new_moon_utc_before(day: date) -> datetime | None:
    """UTC instant of the last new-moon conjunction strictly before ``day`` (WIB)."""
    from skyfield.almanac import find_discrete, moon_phases

    eph = _eph()
    upper = datetime.combine(day + timedelta(days=1), time.min, tzinfo=WIB)
    t_upper = eph.ts.from_datetime(upper)
    t_lower = eph.ts.tt_jd(t_upper.tt - 40.0)
    times, phases = find_discrete(t_lower, t_upper, moon_phases(eph.eph))
    result = None
    for t, phase in zip(times, phases, strict=True):
        if phase == 0:
            result = t.utc_datetime()
    return result


def month_length(month_start: date) -> int:
    return 29 if criteria_on_day29(month_start).visible else 30


def next_month_start(month_start: date) -> date:
    return month_start + timedelta(days=month_length(month_start))
