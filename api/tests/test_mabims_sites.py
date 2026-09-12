"""Golden tests for multi-site hilal criteria."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.mabims_sites import load_sites, sighting_on_day29

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "calendar_data.json"


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


def test_golden_1446_08_tightest_month():
    r = sighting_on_day29(date(2025, 1, 31))
    assert r.month_length == 29
    assert r.deciding_site is not None
    assert r.deciding_site.site == "Lhoknga / Tgk. Chiek Kuta Karang"
    assert 0.0 < r.deciding_site.margin_deg < 0.02
    assert r.deciding_site.elong_deg == pytest.approx(6.4055, abs=0.01)
