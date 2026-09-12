from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.calendar import CalendarService
from app.config import Settings
from app.hilal.service import MonthNotResolvable, resolve_sighting_evening
from app.mabims_astro import observation_on_sunset
from app.mabims_sites import sighting_on_day29
from app.main import create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"


# ── Curated table vs criteria consistency ──────────────────────────────────


def test_curated_table_matches_geocentric_criteria():
    """Regression guard: the geocentric Sabang-only model must agree with
    the curated table for every month boundary."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    starts = sorted(
        (date.fromisoformat(g), h)
        for g, h in raw["gregorian_to_hijri"].items()
        if h.endswith("-01")
    )
    mismatches: list[str] = []
    for i in range(len(starts) - 1):
        g_start, hijri = starts[i]
        actual_len = (starts[i + 1][0] - g_start).days
        obs = observation_on_sunset(g_start + timedelta(days=28))
        predicted = 29 if obs.visible else 30
        if predicted != actual_len:
            mismatches.append(
                f"{hijri}: table={actual_len} geo-criteria={predicted} "
                f"(alt={obs.moon_alt_deg:.2f} elong={obs.elongation_deg:.2f})"
            )
    assert not mismatches, "geocentric criteria disagree with curated table:\n" + "\n".join(
        mismatches
    )


def test_curated_table_matches_multisite_criteria():
    """Regression guard: the multi-site production model must agree with
    the curated table for every month boundary."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    starts = sorted(
        (date.fromisoformat(g), h)
        for g, h in raw["gregorian_to_hijri"].items()
        if h.endswith("-01")
    )
    month_starts = [g for g, _ in starts]
    from app.mabims_sites import month_lengths

    predicted = month_lengths(month_starts[:-1])
    actual = [(starts[i + 1][0] - starts[i][0]).days for i in range(len(starts) - 1)]
    assert predicted == actual, "multi-site criteria disagree with curated table"


def test_refraction_matters_for_some_month():
    """Find a month where geometric altitude < 3° but refracted >= 3°.
    Without refraction the curated month length would be wrong."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    starts = sorted(
        (date.fromisoformat(g), h)
        for g, h in raw["gregorian_to_hijri"].items()
        if h.endswith("-01")
    )
    found = False
    for i in range(len(starts) - 1):
        g_start, hijri = starts[i]
        r = sighting_on_day29(g_start)
        best = r.best_site
        if best.alt_deg < 3.0 and best.alt_refracted_deg >= 3.0:
            found = True
            assert r.visible, f"{hijri}: refraction pushes alt above 3° but not visible"
            assert r.month_length == 29
            break
    assert found, "No month found where refraction changes the verdict (test may need update)"


def test_computed_pipeline_matches_curated():
    """Integration test: for dates in the curated table, the computed tier
    must produce the same result when asked."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    g2h = raw["gregorian_to_hijri"]
    sample = list(g2h.items())[::300]
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    c = TestClient(create_app(settings=settings))
    failures = []
    for g_iso, expected_h in sample:
        r = c.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        body = r.json()
        if body["source"] != "mabims":
            failures.append(f"{g_iso}: source={body['source']} instead of mabims")
        if body["output"]["date"] != expected_h:
            failures.append(f"{g_iso}: got {body['output']['date']}, expected {expected_h}")
    assert not failures, "Computed pipeline disagrees with curated:\n" + "\n".join(failures)


# ── Hilal info endpoint ───────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    return TestClient(create_app(settings=settings))


def test_hilal_info_invalid_month(client):
    r = client.get("/api/v1/hilal/info?month=13&year=1447")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "out_of_coverage"


def test_hilal_info_out_of_coverage_year(client):
    r = client.get("/api/v1/hilal/info?month=9&year=1517")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "out_of_coverage"


# ── Month resolution unit tests ───────────────────────────────────────────


@pytest.fixture()
def service():
    return CalendarService(DATA_PATH)


def test_resolve_evening_always_day29(service):
    res = resolve_sighting_evening(service, 1447, 9)
    assert res.target_name == "Ramadhan"
    assert res.prev_name == "Sya'ban"
    assert res.prev_length == 30
    assert res.evening_day == 29
    assert res.evening_date == date(2026, 2, 17)
    assert res.target_start == date(2026, 2, 19)
    assert res.evening_label == "29 Sya'ban 1447 H"


def test_resolve_evening_crosses_hijri_year(service):
    res = resolve_sighting_evening(service, 1448, 1)
    assert res.prev_name == "Dzulhijjah"
    assert res.prev_year == 1447
    assert res.prev_length == 29
    assert res.evening_day == 29
    assert res.evening_date == date(2026, 6, 15)


def test_resolve_evening_29_day_prev(service):
    res = resolve_sighting_evening(service, 1447, 12)
    assert res.prev_month == 11
    assert res.prev_length == 29
    assert res.evening_day == 29


def test_resolve_invalid_month(service):
    with pytest.raises(MonthNotResolvable):
        resolve_sighting_evening(service, 1447, 13)
    with pytest.raises(MonthNotResolvable):
        resolve_sighting_evening(service, 1447, 0)


def test_resolve_out_of_coverage(service):
    with pytest.raises(MonthNotResolvable):
        resolve_sighting_evening(service, 1517, 9)
