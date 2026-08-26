"""
Astronomical calculations using Skyfield.
Computes moon position, elongation, phase, age, and illumination.
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass

from skyfield import api as sf_api
from skyfield.toposlib import wgs84
from skyfield.almanac import find_discrete, moon_phases


# ── Load ephemeris once ──
_eph = None
_ts = None


def _get_eph():
    global _eph, _ts
    if _eph is None:
        _eph = sf_api.load('de421.bsp')
        _ts = sf_api.load.timescale()
    return _eph, _ts


@dataclass
class CelestialData:
    """Astronomical data for the Moon at a specific time and location."""
    # Moon
    moon_alt: float       # degrees above horizon
    moon_az: float        # degrees from North (0=N, 90=E)
    moon_distance_km: float

    # Sun
    sun_alt: float
    sun_az: float

    # Derived
    elongation: float     # angular Sun-Moon separation (degrees)
    phase_angle: float    # angle at Moon between Sun and Earth (degrees)
    illumination: float   # fraction 0.0 - 1.0
    lunar_age_days: float # days since last new moon
    position_angle: float # PA of the Moon's bright limb from North (degrees)
    b_angle: float        # B-angle: tilt of the Moon's axis (degrees)

    # Context
    sunset_alt: float     # Sun altitude at calculation time (should be ~0 at sunset)


def calculate_at_sunset(
    gregorian_date: datetime,
    maghrib_hour: int,
    maghrib_min: int,
    lat: float,
    lon: float,
    utc_offset: float = 7.0,  # WIB = UTC+7
) -> CelestialData:
    """
    Calculate astronomical data for the Moon at Maghrib/sunset time.

    Args:
        gregorian_date: The date (Gregorian)
        maghrib_hour, maghrib_min: Maghrib time in local timezone
        lat, lon: Observer coordinates
        utc_offset: Hours ahead of UTC (default 7 for WIB)

    Returns:
        CelestialData with all computed values
    """
    eph, ts = _get_eph()

    # Build UTC time from local Maghrib time
    local_dt = gregorian_date.replace(hour=maghrib_hour, minute=maghrib_min, second=0)
    utc_dt = local_dt - timedelta(hours=utc_offset)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day,
               utc_dt.hour, utc_dt.minute, utc_dt.second)

    # Observer
    earth = eph['earth']
    observer = earth + wgs84.latlon(lat, lon)

    # ── Moon position ──
    moon_astrometric = observer.at(t).observe(eph['moon'])
    moon_apparent = moon_astrometric.apparent()
    moon_alt, moon_az, moon_dist = moon_apparent.altaz()
    moon_alt_deg = moon_alt.degrees
    moon_az_deg = moon_az.degrees
    moon_dist_km = moon_dist.km

    # ── Sun position ──
    sun_astrometric = observer.at(t).observe(eph['sun'])
    sun_apparent = sun_astrometric.apparent()
    sun_alt, sun_az, _ = sun_apparent.altaz()
    sun_alt_deg = sun_alt.degrees
    sun_az_deg = sun_az.degrees

    # ── Elongation (angular separation Sun-Moon) ──
    elongation_deg = sun_apparent.separation_from(moon_apparent).degrees

    # ── Phase angle (angle at Moon between Sun and Earth) ──
    # This determines illumination fraction
    # Phase angle ψ: cos(ψ) = (d² + dm² - ds²) / (2 * d * dm)
    # where d = Moon-Earth, dm = Moon-Sun, ds = Sun-Earth
    # Or we can use the elongation + parallax approach

    # From Skyfield: phase angle from elongation
    # For a simple approximation:
    # illumination = (1 - cos(elongation)) / 2  [approximate]
    # More accurate: use the actual geometry

    # Get Moon's ecliptic longitude and latitude for B-angle
    moon_ecliptic = moon_apparent.ecliptic_latlon()
    moon_ecl_lon = moon_ecliptic[1].degrees  # longitude
    moon_ecl_lat = moon_ecliptic[0].degrees  # latitude

    # Sun ecliptic longitude
    sun_ecliptic = sun_apparent.ecliptic_latlon()
    sun_ecl_lon = sun_ecliptic[1].degrees

    # Phase angle (more accurate calculation)
    # The phase angle is the angle Sun-Moon-Earth
    # Using the formula: cos(ψ) = -cos(elongation) when Moon is near ecliptic
    # But we need to account for the Moon's ecliptic latitude

    # Actually, let's use Skyfield's built-in if available
    # Skyfield doesn't directly give phase angle, so we compute it from geometry

    # Distance vectors
    moon_pos = (eph['moon'] - eph['earth']).at(t)
    sun_pos = (eph['sun'] - eph['earth']).at(t)

    moon_vec = moon_pos.position.au
    sun_vec = sun_pos.position.au

    moon_dist_au = moon_pos.distance().au
    sun_dist_au = sun_pos.distance().au

    # Phase angle ψ at Moon (angle between Sun and Earth as seen from Moon)
    # cos(ψ) = (ms² + me² - se²) / (2 * ms * me)
    # where ms = Moon-Sun distance, me = Moon-Earth, se = Sun-Earth
    ms_vec = sun_vec - moon_vec  # Moon to Sun
    me_vec = -moon_vec           # Moon to Earth
    se_vec = -sun_vec            # Sun to Earth (not needed directly)

    ms = math.sqrt(sum(x**2 for x in ms_vec))
    me = math.sqrt(sum(x**2 for x in me_vec))
    se = math.sqrt(sum(x**2 for x in se_vec))

    cos_phase = (ms**2 + me**2 - se**2) / (2 * ms * me)
    cos_phase = max(-1, min(1, cos_phase))  # clamp for safety
    phase_angle_rad = math.acos(cos_phase)
    phase_angle_deg = math.degrees(phase_angle_rad)

    # Illumination fraction
    illumination = (1 + math.cos(phase_angle_rad)) / 2

    # ── Position Angle (PA) of the bright limb ──
    # PA is measured from North celestial pole toward East
    # The bright limb faces the Sun
    # PA = atan2(sun_az - moon_az_component, ...) projected onto the sky

    # Position angle of the Sun from the Moon (as seen from Earth)
    # This is approximately the PA of the bright limb
    pa_rad = math.atan2(
        math.sin(math.radians(sun_az_deg - moon_az_deg)) * math.cos(math.radians(sun_alt_deg)),
        math.sin(math.radians(sun_alt_deg)) - math.sin(math.radians(moon_alt_deg)) * math.cos(
            math.radians(elongation_deg)
        )
    )
    # Simpler approximation: PA of Sun relative to Moon
    delta_az = math.radians(sun_az_deg - moon_az_deg)
    delta_alt = math.radians(sun_alt_deg - moon_alt_deg)

    # Position angle of the bright limb (from North, through East)
    # This tells us where the illuminated side is
    pa_deg = math.degrees(math.atan2(
        math.sin(delta_az) * math.cos(math.radians(sun_alt_deg)),
        math.cos(math.radians(moon_alt_deg)) * math.sin(math.radians(sun_alt_deg)) -
        math.sin(math.radians(moon_alt_deg)) * math.cos(math.radians(sun_alt_deg)) * math.cos(delta_az)
    ))

    # ── B-angle: tilt of the Moon's rotation axis ──
    # This is the Moon's ecliptic latitude, essentially
    # It determines how much the crescent "tilts"
    b_angle_deg = moon_ecl_lat

    # ── Lunar Age ──
    # Find the most recent new moon before this date
    lunar_age = _find_lunar_age(t, ts, eph)

    return CelestialData(
        moon_alt=moon_alt_deg,
        moon_az=moon_az_deg,
        moon_distance_km=moon_dist_km,
        sun_alt=sun_alt_deg,
        sun_az=sun_az_deg,
        elongation=elongation_deg,
        phase_angle=phase_angle_deg,
        illumination=illumination,
        lunar_age_days=lunar_age,
        position_angle=pa_deg,
        b_angle=b_angle_deg,
        sunset_alt=sun_alt_deg,
    )


def _find_lunar_age(t, ts, eph) -> float:
    """
    Find the number of days since the last new moon (conjunction).
    Uses Skyfield's almanac to find moon phases.
    """
    # Search window: 40 days before to 5 days after
    # A synodic month is ~29.53 days
    t_utc = t.utc_datetime()
    t_start = ts.utc(t_utc - timedelta(days=40))
    t_end = ts.utc(t_utc + timedelta(days=5))

    try:
        # moon_phases returns phase 0-3: 0=new, 1=first quarter, 2=full, 3=last quarter
        times, phases = find_discrete(t_start, t_end, moon_phases(eph))
        if len(phases) > 0:
            # Find the last new moon (phase == 0) before t
            last_new_moon = None
            for i in range(len(phases)):
                if phases[i] == 0:  # New Moon
                    ti = times[i]
                    ti_utc = ti.utc_datetime()
                    if ti_utc <= t_utc:
                        last_new_moon = ti_utc
            if last_new_moon:
                age = (t_utc - last_new_moon).total_seconds() / 86400
                return age
            else:
                # If no new moon found before t in the window,
                # the next new moon is coming — moon is in last days of old month
                # Return negative age to indicate pre-conjunction
                for i in range(len(phases)):
                    if phases[i] == 0:
                        ti = times[i]
                        age = (t_utc - ti.utc_datetime()).total_seconds() / 86400
                        return age  # Will be negative
    except Exception as e:
        print(f"Warning: lunar age calculation failed: {e}")

    # Fallback: approximate from phase angle
    return 0.0


def get_moon_phase_name(illumination: float) -> str:
    """Return a human-readable phase name."""
    if illumination < 0.01:
        return "New Moon"
    elif illumination < 0.25:
        return "Waxing Crescent"
    elif illumination < 0.49:
        return "First Quarter"
    elif illumination < 0.51:
        return "Full Moon"
    elif illumination < 0.75:
        return "Waning Gibbous"
    elif illumination < 0.99:
        return "Last Quarter"
    else:
        return "Waxing Gibbous"


def find_moonset(
    gregorian_date: datetime,
    lat: float,
    lon: float,
    utc_offset: float = 7.0,
) -> str:
    """
    Find moonset time (when moon altitude crosses below 0°).
    Returns formatted time string or "N/A".
    """
    from skyfield.api import utc

    eph, ts = _get_eph()

    # Search window: from morning to midnight
    search_start_local = gregorian_date.replace(hour=6, minute=0, second=0)
    search_end_local = gregorian_date.replace(hour=23, minute=59, second=0)

    search_start_utc = search_start_local - timedelta(hours=utc_offset)
    search_end_utc = search_end_local - timedelta(hours=utc_offset)

    # Add timezone info for Skyfield
    search_start_utc = search_start_utc.replace(tzinfo=utc)
    search_end_utc = search_end_utc.replace(tzinfo=utc)

    t_start = ts.utc(search_start_utc)
    t_end = ts.utc(search_end_utc)

    earth = eph['earth']
    observer = earth + wgs84.latlon(lat, lon)

    # Sample at intervals and find where altitude crosses 0
    num_samples = 48
    times = ts.linspace(t_start, t_end, num_samples)

    prev_alt = None
    prev_t = None
    for t in times:
        moon_astrometric = observer.at(t).observe(eph['moon'])
        moon_apparent = moon_astrometric.apparent()
        alt, _, _ = moon_apparent.altaz()
        alt_deg = alt.degrees

        if prev_alt is not None and prev_alt >= 0 and alt_deg < 0:
            # Crossed below horizon — interpolate
            frac = prev_alt / (prev_alt - alt_deg)
            # Simple linear interpolation between the two times
            # Get UTC timestamps as floats
            t0_utc = prev_t.utc_datetime().timestamp()
            t1_utc = t.utc_datetime().timestamp()
            cross_utc_ts = t0_utc + (t1_utc - t0_utc) * frac
            cross_utc = datetime.utcfromtimestamp(cross_utc_ts)
            cross_local = cross_utc + timedelta(hours=utc_offset)
            return cross_local.strftime('%H:%M')

        prev_alt = alt_deg
        prev_t = t

    return "N/A"


# ── Quick test ──
if __name__ == '__main__':
    from datetime import datetime

    # Test: Feb 17, 2026 at 18:15 UTC+7 (Jakarta, 29 Sha'ban)
    print("=== Testing Astronomy Module ===\n")

    data = calculate_at_sunset(
        gregorian_date=datetime(2026, 2, 17),
        maghrib_hour=18,
        maghrib_min=15,
        lat=-6.2088,
        lon=106.8456,
        utc_offset=7.0,
    )

    print(f"Moon Altitude:    {data.moon_alt:+.2f}°")
    print(f"Moon Azimuth:     {data.moon_az:.2f}°")
    print(f"Sun Altitude:     {data.sun_alt:+.2f}°")
    print(f"Elongation:       {data.elongation:.2f}°")
    print(f"Phase Angle:      {data.phase_angle:.2f}°")
    print(f"Illumination:     {data.illumination*100:.2f}%")
    print(f"Lunar Age:        {data.lunar_age_days:.2f} days")
    print(f"Position Angle:   {data.position_angle:.2f}°")
    print(f"B-Angle:          {data.b_angle:.2f}°")
    print(f"Phase:            {get_moon_phase_name(data.illumination)}")
    print(f"Distance:         {data.moon_distance_km:,.0f} km")


def get_illumination_at(date, maghrib_hour=18, maghrib_min=0, days_ahead=1,
                        lat=-6.2088, lon=106.8456):
    """Get moon illumination at a future time (for phase box visibility)."""
    eph, ts = _get_eph()

    # Calculate time days_ahead later
    future_date = date + timedelta(days=days_ahead)
    t = ts.utc(
        future_date.year, future_date.month, future_date.day,
        maghrib_hour, maghrib_min, 0
    )

    # Observer
    earth = eph['earth']
    observer = earth + wgs84.latlon(lat, lon)

    # Moon and Sun positions
    moon_pos = (eph['moon'] - eph['earth']).at(t)
    sun_pos = (eph['sun'] - eph['earth']).at(t)

    moon_vec = moon_pos.position.au
    sun_vec = sun_pos.position.au

    # Phase angle
    ms_vec = sun_vec - moon_vec
    me_vec = -moon_vec
    se_vec = -sun_vec

    ms = math.sqrt(sum(x**2 for x in ms_vec))
    me = math.sqrt(sum(x**2 for x in me_vec))
    se = math.sqrt(sum(x**2 for x in se_vec))

    cos_phase = (ms**2 + me**2 - se**2) / (2 * ms * me)
    cos_phase = max(-1, min(1, cos_phase))
    phase_angle_rad = math.acos(cos_phase)

    return (1 + math.cos(phase_angle_rad)) / 2
