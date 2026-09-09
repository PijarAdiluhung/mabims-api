"""Multi-site hilal criteria (app.mabims_sites) — golden tests.

Validates the "seen anywhere in Indonesia" model (topocentric apparent
moon altitude with Bennett refraction + geocentric elongation at each
site's local sunset, 25 coastal sites) against the curated Kemenag
table, and pins the reference decisions discovered during validation:
  - 1447-06 needs refraction (decider's geometric altitude 2.91 < 3.0)
  - 1446-08 is the tightest month in the table (margin +0.006 deg)
"""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from app.mabims_sites import Site, load_sites, month_lengths, sighting_on_date, sighting_on_day29

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "calendar_data.json"


def _curated_month_starts() -> list[tuple[date, str]]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return sorted(
        (date.fromisoformat(g), h)
        for g, h in raw["gregorian_to_hijri"].items()
        if h.endswith("-01")
    )


# ── site data ──


def test_sites_data_valid():
    sites = load_sites()
    assert 20 <= len(sites) <= 100
    names = [s.name for s in sites]
    assert len(names) == len(set(names))
    for s in sites:
        assert -11.5 <= s.lat_deg <= 6.5
        assert 94.0 <= s.lon_deg <= 125.0
        assert s.elev_m >= 0
        assert s.tz in {"Asia/Jakarta", "Asia/Makassar"}


# ── curated table ⇔ multi-site criteria consistency ──


def test_curated_table_matches_multisite_criteria():
    """Regression guard: the multi-site verdict must equal the curated
    table for every month boundary (refraction variant)."""
    starts = _curated_month_starts()
    predicted = month_lengths([g for g, _ in starts[:-1]])
    actual = [(starts[i + 1][0] - starts[i][0]).days for i in range(len(starts) - 1)]
    assert predicted == actual


# ── pinned reference decisions ──


def test_refraction_is_required_1447_06():
    """The 1447-06 decider sits below 3.0 deg geometric altitude: without
    Bennett refraction the curated 29-day month is unreproducible."""
    r = sighting_on_day29(date(2025, 11, 22))
    best = r.best_site
    assert best.alt_deg < 3.0 < best.alt_refracted_deg
    assert best.elong_deg >= 6.4
    assert r.visible
    assert r.month_length == 29


def test_golden_1446_08_tightest_month():
    r = sighting_on_day29(date(2025, 1, 31))
    assert r.month_length == 29
    assert r.deciding_site is not None
    assert r.deciding_site.site == "Lhoknga / Tgk. Chiek Kuta Karang"
    assert 0.0 < r.deciding_site.margin_deg < 0.02
    assert r.deciding_site.elong_deg == pytest.approx(6.4055, abs=0.01)


# ── robustness ──


def test_missing_sunset_raises(monkeypatch):
    """A site whose sunset falls outside the search window must fail loudly."""
    far_east = (Site(name="Pacific", lat_deg=0.0, lon_deg=150.0, elev_m=0.0),)
    monkeypatch.setattr("app.mabims_sites.load_sites", lambda: far_east)
    with pytest.raises(RuntimeError, match="sunset search failed"):
        sighting_on_date(date(2025, 2, 28))


def test_batch_matches_scalar_reference():
    """Batched pipeline ≈ exact scalar skyfield (find_discrete sunset)."""
    from skyfield import almanac
    from skyfield.api import wgs84

    from app.mabims_astro import WIB, _eph, _refraction_deg

    d = date(2025, 2, 28)
    r = sighting_on_date(d)
    sites = load_sites()
    eph = _eph()

    worst_alt = worst_elong = 0.0
    for i, s in enumerate(sites):
        site0 = wgs84.latlon(s.lat_deg, s.lon_deg)  # elevation 0, standard sunset
        start = datetime.combine(d, time(0, 0), tzinfo=WIB)
        f = almanac.sunrise_sunset(eph.eph, site0)
        times, events = almanac.find_discrete(
            eph.ts.from_datetime(start),
            eph.ts.from_datetime(start + timedelta(days=1)),
            f,
        )
        ss = next(t for t, ev in zip(times, events, strict=True) if not ev)

        site = wgs84.latlon(s.lat_deg, s.lon_deg, elevation_m=s.elev_m)
        m = (eph._earth + site).at(ss).observe(eph._moon).apparent()
        alt_geo = m.altaz()[0].degrees
        geo = eph._earth.at(ss)
        elong = geo.observe(eph._moon).apparent().separation_from(
            geo.observe(eph._sun).apparent()
        ).degrees

        worst_alt = max(worst_alt, abs(alt_geo + _refraction_deg(alt_geo) - r.sites[i].alt_refracted_deg))
        worst_elong = max(worst_elong, abs(elong - r.sites[i].elong_deg))

    assert worst_alt < 0.001
    assert worst_elong < 0.001
