from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG, _eph, _refraction_deg

H0_SUN_DEG = -0.8333  # sunset convention (refraction + solar radius), as skyfield sunrise_sunset
SUNSET_WINDOW_START_H = 9.5  # 09:30 UTC covers sunsets for lon 95..124 E
SUNSET_WINDOW_END_H = 13.5
GRID_STEP_MIN = 5
SITES_PATH = Path(__file__).resolve().parents[1] / "data" / "hilal_sites.json"


@dataclass(frozen=True)
class Site:
    name: str
    lat_deg: float
    lon_deg: float
    elev_m: float
    tz: str = "Asia/Jakarta"


@dataclass(frozen=True)
class SiteSky:
    """Observer-scene facts at one site's own sunset instant."""

    site: str
    moon_az_deg: float  # topocentric, degrees from north clockwise
    sun_alt_deg: float  # topocentric geometric
    sun_az_deg: float
    sunset_utc: datetime


@dataclass(frozen=True)
class SiteSighting:
    """Criteria at one site's local sunset: topocentric alt, geocentric elongation."""

    site: str
    alt_deg: float  # topocentric geometric
    alt_refracted_deg: float
    elong_deg: float  # geocentric apparent

    @property
    def visible(self) -> bool:
        return bool(self.alt_refracted_deg >= ALT_MIN_DEG and self.elong_deg >= ELONG_MIN_DEG)

    @property
    def margin_deg(self) -> float:
        return min(self.alt_refracted_deg - ALT_MIN_DEG, self.elong_deg - ELONG_MIN_DEG)


@dataclass(frozen=True)
class MultiSiteSighting:
    """"Seen anywhere in Indonesia" verdict for one evening (day 29).

    Kemenag convention: topocentric ruyyat altitude, geocentric elongation,
    hilal may be seen at any site across the archipelago. Validated 100%
    against the curated table (see tests/test_mabims_sites.py).
    """

    evaluated_on: date
    sites: tuple[SiteSighting, ...]
    sky: tuple[SiteSky, ...] | None = None

    @property
    def visible(self) -> bool:
        return any(s.visible for s in self.sites)

    @property
    def deciding_site(self) -> SiteSighting | None:
        seen = [s for s in self.sites if s.visible]
        return max(seen, key=lambda s: s.margin_deg) if seen else None

    @property
    def best_site(self) -> SiteSighting:
        """Highest-margin site regardless of verdict (for diagnostics)."""
        return max(self.sites, key=lambda s: s.margin_deg)

    def sky_for(self, site_name: str) -> SiteSky:
        """Scene facts for the named site (requires batched construction)."""
        if self.sky is None:
            raise ValueError(f"sky facts unavailable for {site_name}")
        return next(s for s in self.sky if s.site == site_name)

    @property
    def month_length(self) -> int:
        return 29 if self.visible else 30


@lru_cache(maxsize=1)
def load_sites() -> tuple[Site, ...]:
    raw = json.loads(SITES_PATH.read_text(encoding="utf-8"))
    return tuple(
        Site(
            name=item["name"],
            lat_deg=item["lat"],
            lon_deg=item["lon"],
            elev_m=item["elev_m"],
            tz=item.get("tz", "Asia/Jakarta"),
        )
        for item in raw["sites"]
    )


def site_by_name(name: str) -> Site:
    return next(s for s in load_sites() if s.name == name)


def _refraction_deg_arr(alt_deg: np.ndarray) -> np.ndarray:
    """Vectorized Bennett refraction (same formula as mabims_astro._refraction_deg)."""
    h = np.maximum(alt_deg, -1.0)
    return 1.02 / np.tan(np.radians(h + 10.3 / (h + 5.11))) / 60.0


def _evaluate_batch(day29_dates: list[date]) -> dict[str, np.ndarray]:
    """Vectorized per-site sunset + moon criteria for many day-29 dates.

    Pass 1: sun altitude on a minute grid (all dates x all sites in one
    batched skyfield call) -> per-site sunset via interpolated crossing of
    -0.8333 deg (same convention as skyfield's sunrise_sunset, elevation 0).
    Pass 2: topocentric moon altitude (apparent().altaz(), includes
    aberration + nutation) and geocentric apparent elongation at each
    site's sunset.

    Returns (n_dates, n_sites) arrays under keys "alt", "elong", "sunset_jd",
    "moon_az", "sun_alt", "sun_az", plus "sunset_dts" (flat aware datetimes).
    Raises RuntimeError if any site's sunset falls outside the search window.
    """
    from skyfield.api import wgs84

    eph = _eph()
    n = len(day29_dates)
    sites = load_sites()
    S = len(sites)
    G = int((SUNSET_WINDOW_END_H - SUNSET_WINDOW_START_H) * 60 / GRID_STEP_MIN) + 1
    step_days = GRID_STEP_MIN / 1440.0

    lats = np.array([s.lat_deg for s in sites])
    lons = np.array([s.lon_deg for s in sites])
    elevs = np.array([s.elev_m for s in sites])

    base = eph.ts.utc(
        [d.year for d in day29_dates],
        [d.month for d in day29_dates],
        [d.day for d in day29_dates],
        int(SUNSET_WINDOW_START_H),
        int((SUNSET_WINDOW_START_H % 1) * 60),
        0,
    ).tt  # (n,)
    tt_mk = base[:, None] + np.arange(G) * step_days  # (n, G)

    # pass 1: sun altitude grid (elevation 0, standard sunset convention)
    observer = eph._earth + wgs84.latlon(
        np.tile(lats, n * G), np.tile(lons, n * G), elevation_m=np.zeros(n * G * S)
    )
    sun_alt = (
        observer.at(eph.ts.tt_jd(np.repeat(tt_mk.ravel(), S)))
        .observe(eph._sun)
        .apparent()
        .altaz()[0]
        .degrees
    ).reshape(n, G, S)

    below = sun_alt < H0_SUN_DEG
    prev = np.concatenate([below[:, :1], below[:, :-1]], axis=1)
    cross = below & ~prev  # downward crossing at grid index k
    has = cross.any(axis=1)  # (n, S)
    k_idx = np.argmax(cross, axis=1)

    mi, si = np.meshgrid(np.arange(n), np.arange(S), indexing="ij")
    a_prev = sun_alt[mi, np.maximum(k_idx - 1, 0), si]
    a_cross = sun_alt[mi, k_idx, si]
    denom = np.where(a_prev == a_cross, 1.0, a_prev - a_cross)
    frac = np.where(has, (a_prev - H0_SUN_DEG) / denom, 0.0)
    sunset_jd = base[:, None] + (k_idx - 1 + frac) * step_days  # (n, S)

    # pass 2: moon + sun at every site's sunset (topo scene + geo elongation)
    sites_rep = wgs84.latlon(
        np.tile(lats, n), np.tile(lons, n), elevation_m=np.tile(elevs, n)
    )
    t_moon = eph.ts.tt_jd(sunset_jd.ravel())
    site_obs = (eph._earth + sites_rep).at(t_moon)
    m_obs = site_obs.observe(eph._moon).apparent()
    alt, moon_az, _ = m_obs.altaz()
    alt = alt.degrees.reshape(n, S)
    moon_az = moon_az.degrees.reshape(n, S)
    sun_obs_topo = site_obs.observe(eph._sun).apparent()
    sun_alt, sun_az, _ = sun_obs_topo.altaz()
    sun_alt = sun_alt.degrees.reshape(n, S)
    sun_az = sun_az.degrees.reshape(n, S)
    geo_moon = eph._earth.at(t_moon).observe(eph._moon).apparent()
    elong = geo_moon.separation_from(
        eph._earth.at(t_moon).observe(eph._sun).apparent()
    ).degrees.reshape(n, S)
    sunset_dts = eph.ts.tt_jd(sunset_jd.ravel()).utc_datetime()

    if not has.all():
        missing = np.argwhere(~has).tolist()
        raise RuntimeError(
            f"multi-site sunset search failed for {len(missing)} site-month pairs "
            f"(outside {SUNSET_WINDOW_START_H}-{SUNSET_WINDOW_END_H} UTC window): {missing}"
        )
    return {
        "alt": alt,
        "elong": elong,
        "sunset_jd": sunset_jd,
        "moon_az": moon_az,
        "sun_alt": sun_alt,
        "sun_az": sun_az,
        "sunset_dts": sunset_dts,
    }


def _sighting_from_row(
    d: date, sites: tuple[Site, ...], i: int, res: dict[str, np.ndarray]
) -> MultiSiteSighting:
    row = [
        SiteSighting(
            site=s.name,
            alt_deg=float(res["alt"][i, j]),
            alt_refracted_deg=float(res["alt"][i, j]) + _refraction_deg(float(res["alt"][i, j])),
            elong_deg=float(res["elong"][i, j]),
        )
        for j, s in enumerate(sites)
    ]
    sky = tuple(
        SiteSky(
            site=s.name,
            moon_az_deg=float(res["moon_az"][i, j]),
            sun_alt_deg=float(res["sun_alt"][i, j]),
            sun_az_deg=float(res["sun_az"][i, j]),
            sunset_utc=res["sunset_dts"][i * len(sites) + j],
        )
        for j, s in enumerate(sites)
    )
    return MultiSiteSighting(evaluated_on=d, sites=tuple(row), sky=sky)


def sightings_on_dates(day29_dates: list[date]) -> list[MultiSiteSighting]:
    """Batched multi-site sightings for many dates (one vectorized call)."""
    if not day29_dates:
        return []
    res = _evaluate_batch(day29_dates)
    sites = load_sites()
    return [_sighting_from_row(d, sites, i, res) for i, d in enumerate(day29_dates)]


def sighting_on_date(d: date) -> MultiSiteSighting:
    return sightings_on_dates([d])[0]


def sighting_on_day29(month_start: date) -> MultiSiteSighting:
    """Criteria at sunset of day 29 of the Hijri month starting ``month_start``."""
    return sighting_on_date(month_start + timedelta(days=28))


def month_lengths(month_starts: list[date]) -> list[int]:
    return [s.month_length for s in sightings_on_dates([m + timedelta(days=28) for m in month_starts])]
