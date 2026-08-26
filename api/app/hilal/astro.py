"""Topocentric hilal astronomy for arbitrary observers (Skyfield, de421.bsp).

Generalizes the Sabang-fixed ephemeris in ``app.mabims_astro`` to any lat/lon:
sunset via the almanac, moon/sun alt-az at that instant, elongation,
illumination, lunar age and moonset.
"""

from __future__ import annotations

import math
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Observation:
    sunset_local: str  # "HH:MM"
    moonset_local: str  # "HH:MM"
    sun_alt: float
    sun_az: float
    moon_alt: float  # refraction-corrected
    moon_az: float
    elongation: float
    illumination: float  # 0..1
    age_hours: float  # hours since last new moon; negative = conjunction ahead


class _Ephemeris:
    def __init__(self) -> None:
        from skyfield.api import Loader, wgs84

        directory = os.environ.get("MABIMS_EPHEMERIS_DIR")
        path = Path(directory) if directory else Path(tempfile.gettempdir()) / "mabims-ephemeris"
        path.mkdir(parents=True, exist_ok=True)
        loader = Loader(str(path))
        self.ts = loader.timescale(builtin=True)
        self.eph = loader("de421.bsp")
        self._wgs84 = wgs84

    def topos(self, lat: float, lon: float):
        return self._wgs84.latlon(lat, lon)

    def observer(self, lat: float, lon: float):
        return self.eph["earth"] + self.topos(lat, lon)


_lock = threading.Lock()


@lru_cache(maxsize=1)
def _eph() -> _Ephemeris:
    with _lock:
        return _Ephemeris()


@lru_cache(maxsize=32)
def _observer(lat: float, lon: float):
    return _eph().observer(lat, lon)


@lru_cache(maxsize=32)
def _topos(lat: float, lon: float):
    return _eph().topos(lat, lon)


def _refraction_deg(alt_deg: float) -> float:
    h = max(alt_deg, -1.0)
    arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11)))
    return arcmin / 60.0


def sunset_utc(d: date, tz_name: str, lat: float, lon: float) -> datetime:
    """UTC instant of sunset on local date ``d`` for the observer."""
    from skyfield.almanac import find_discrete, sunrise_sunset

    eph = _eph()
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(d, time(0, 0), tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    t0 = eph.ts.from_datetime(start_local)
    t1 = eph.ts.from_datetime(end_local)
    times, events = find_discrete(t0, t1, sunrise_sunset(eph.eph, _topos(lat, lon)))
    for t, ev in zip(times, events, strict=True):
        if not ev:
            return t.utc_datetime()
    raise ValueError(f"no sunset found for {d} at ({lat}, {lon})")


def _moon_phase_angle_deg(dt_utc: datetime) -> float:
    from skyfield.almanac import moon_phase

    eph = _eph()
    t = eph.ts.from_datetime(dt_utc)
    return float(moon_phase(eph.eph, t).degrees)


def _lunar_age_hours(dt_utc: datetime) -> float:
    from skyfield.almanac import find_discrete, moon_phases

    eph = _eph()
    t = eph.ts.from_datetime(dt_utc)
    t_start = eph.ts.tt_jd(t.tt - 40.0)
    t_end = eph.ts.tt_jd(t.tt + 5.0)
    times, phases = find_discrete(t_start, t_end, moon_phases(eph.eph))
    last_new: datetime | None = None
    next_new: datetime | None = None
    for ti, ph in zip(times, phases, strict=True):
        if ph != 0:
            continue
        t_utc = ti.utc_datetime()
        if ti.tt <= t.tt:
            last_new = t_utc
        elif next_new is None:
            next_new = t_utc
    if last_new is not None:
        return float((dt_utc - last_new).total_seconds() / 3600.0)
    if next_new is not None:
        return float((dt_utc - next_new).total_seconds() / 3600.0)
    return 0.0


def moonset_local(d: date, tz_name: str, lat: float, lon: float) -> str:
    """Local moonset time "HH:MM" between 06:00 and 24:00 on ``d``, or "N/A"."""
    eph = _eph()
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(d, time(6, 0), tzinfo=tz)
    end_local = datetime.combine(d, time(23, 59), tzinfo=tz)
    times = eph.ts.linspace(eph.ts.from_datetime(start_local), eph.ts.from_datetime(end_local), 48)
    prev_alt = None
    prev_t = None
    for t in times:
        alt = float(_observer(lat, lon).at(t).observe(eph.eph["moon"]).apparent().altaz()[0].degrees)
        if prev_alt is not None and prev_t is not None and prev_alt >= 0 > alt:
            frac = prev_alt / (prev_alt - alt)
            t0 = prev_t.utc_datetime().timestamp()
            t1 = t.utc_datetime().timestamp()
            cross = datetime.fromtimestamp(t0 + (t1 - t0) * frac, tz=tz)
            return cross.strftime("%H:%M")
        prev_alt = alt
        prev_t = t
    return "N/A"


def observe_at_sunset(d: date, tz_name: str, lat: float, lon: float) -> Observation:
    """Full hilal observation for the sunset ending local date ``d``."""
    eph = _eph()
    sunset = sunset_utc(d, tz_name, lat, lon)
    t = eph.ts.from_datetime(sunset)
    topo = _observer(lat, lon)

    moon = topo.at(t).observe(eph.eph["moon"]).apparent()
    sun = topo.at(t).observe(eph.eph["sun"]).apparent()

    moon_alt, moon_az, _ = moon.altaz()
    sun_alt, sun_az, _ = sun.altaz()
    moon_alt_deg = float(moon_alt.degrees) + _refraction_deg(float(moon_alt.degrees))
    sun_alt_deg = float(sun_alt.degrees)
    moon_az_deg = float(moon_az.degrees) % 360.0
    sun_az_deg = float(sun_az.degrees) % 360.0

    elong = float(moon.separation_from(sun).degrees)
    phase_angle = _moon_phase_angle_deg(sunset)
    illumination = (1.0 - math.cos(math.radians(phase_angle))) / 2.0
    age_hours = _lunar_age_hours(sunset)

    sunset_local = sunset.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")
    moonset = moonset_local(d, tz_name, lat, lon)

    return Observation(
        sunset_local=sunset_local,
        moonset_local=moonset,
        sun_alt=sun_alt_deg,
        sun_az=sun_az_deg,
        moon_alt=moon_alt_deg,
        moon_az=moon_az_deg,
        elongation=elong,
        illumination=illumination,
        age_hours=age_hours,
    )
