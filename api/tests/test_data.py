from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"
SITES_PATH = API_DIR / "data" / "hilal_sites.json"
SEED_PATH = API_DIR / "data" / "computed_seed.json"


@pytest.fixture(scope="module")
def real_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


# ── Curated table integrity ───────────────────────────────────────────────


def test_curated_table_has_no_gaps(real_data):
    g2h = real_data["gregorian_to_hijri"]
    dates = sorted(date.fromisoformat(g) for g in g2h)
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        assert gap == 1, f"Gap of {gap} days between {dates[i-1]} and {dates[i]}"


def test_curated_reverse_mapping_is_consistent(real_data):
    g2h = real_data["gregorian_to_hijri"]
    h2g = real_data["hijri_to_gregorian"]
    failures = []
    for g, h in g2h.items():
        if h2g.get(h) != g:
            failures.append(f"G→H: {g} → {h}, but H→G: {h} → {h2g.get(h)}")
    for h, g in h2g.items():
        if g2h.get(g) != h:
            failures.append(f"H→G: {h} → {g}, but G→H: {g} → {g2h.get(g)}")
    assert not failures, "Inconsistent mappings:\n" + "\n".join(failures[:20])


def test_all_hijri_months_are_29_or_30_days(real_data):
    g2h = real_data["gregorian_to_hijri"]
    month_starts = sorted(
        (date.fromisoformat(g), h) for g, h in g2h.items() if h.endswith("-01")
    )
    bad = []
    for i in range(len(month_starts) - 1):
        days = (month_starts[i + 1][0] - month_starts[i][0]).days
        if days not in (29, 30):
            bad.append(f"{month_starts[i][1]}: {days} days")
    assert not bad, "Invalid month lengths:\n" + "\n".join(bad)


# ── Hilal sites ───────────────────────────────────────────────────────────


def test_hilal_sites_count_and_bounds():
    raw = json.loads(SITES_PATH.read_text(encoding="utf-8"))
    sites = raw["sites"]
    assert len(sites) >= 20, f"Only {len(sites)} sites"
    for s in sites:
        assert -11.5 <= s["lat"] <= 6.5, f"{s['name']}: lat={s['lat']}"
        assert 94.0 <= s["lon"] <= 125.0, f"{s['name']}: lon={s['lon']}"
        assert s.get("elev_m", 0) >= 0


def test_hilal_sites_have_valid_timezone():
    raw = json.loads(SITES_PATH.read_text(encoding="utf-8"))
    sites = raw["sites"]
    valid_tz = {"Asia/Jakarta", "Asia/Makassar"}
    bad = [s["name"] for s in sites if s.get("tz") not in valid_tz]
    assert not bad, f"Sites with invalid timezone: {bad}"


def test_hilal_sites_names_are_unique():
    raw = json.loads(SITES_PATH.read_text(encoding="utf-8"))
    sites = raw["sites"]
    names = [s["name"] for s in sites]
    assert len(names) == len(set(names)), "Duplicate site names"


# ── Computed seed ─────────────────────────────────────────────────────────


def test_computed_seed_is_contiguous():
    if not SEED_PATH.exists():
        pytest.skip("No seed file")
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    g2h = seed.get("g2h", {})
    if not g2h:
        pytest.skip("Empty seed")
    dates = sorted(date.fromisoformat(g) for g in g2h)
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        assert gap == 1, f"Seed gap of {gap} days between {dates[i-1]} and {dates[i]}"
