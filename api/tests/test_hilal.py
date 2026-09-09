from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.calendar import CalendarService
from app.config import Settings
from app.hilal.service import MonthNotResolvable, resolve_sighting_evening
from app.mabims_astro import observation_on_sunset
from app.mabims_sites import MultiSiteSighting, SiteSighting, SiteSky, load_sites
from app.main import SightingObservation, create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"


def _fake_multisite(
    visible: bool = True, alt: float = 8.8, elong: float = 11.1
) -> MultiSiteSighting:
    row = SiteSighting(
        site="Sabang / Weh Island",
        alt_deg=alt,
        alt_refracted_deg=alt,
        elong_deg=elong,
    )
    other = SiteSighting(
        site="Pangandaran Beach",
        alt_deg=alt,
        alt_refracted_deg=alt,
        elong_deg=elong,
    )
    sky = tuple(
        SiteSky(
            site=s.site,
            moon_az_deg=263.98,
            sun_alt_deg=-0.83,
            sun_az_deg=258.30,
            sunset_utc=datetime(2026, 2, 17, 11, 51, tzinfo=UTC),
        )
        for s in (row, other)
    )
    return MultiSiteSighting(evaluated_on=date(2026, 2, 17), sites=(row, other), sky=sky)


def _fake_sighting(**overrides) -> SightingObservation:
    kwargs = dict(
        multisite=_fake_multisite(),
        site=load_sites()[0],
        sunset_local="18:14",
        moonset_local="18:51",
        illumination_pct=1.07,
        age_hours=23.2,
    )
    return SightingObservation(**{**kwargs, **overrides})


@pytest.fixture()
def hilal_client(monkeypatch):
    app = create_app(
        settings=Settings(
            data_dir=DATA_PATH.parent,
            allowed_origins=["*"],
            rate_limit="10000/minute",
            enable_computed=False,
            enable_fallback=False,
        )
    )
    monkeypatch.setattr(
        "app.main.observe_sighting_evening", lambda *a, **k: _fake_sighting()
    )
    return TestClient(app)


def test_hilal_info_ok(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447")
    assert response.status_code == 200
    body = response.json()
    assert body["input"] == {"month": 9, "year": 1447}
    assert body["month"]["name"] == "Ramadhan"
    assert body["month"]["start"] == "2026-02-19"
    assert body["previous_month"]["name"] == "Sya'ban"
    assert body["previous_month"]["length"] == 30
    evening = body["evening"]
    assert evening["hijri_date"] == "29 Sya'ban 1447 H"
    assert evening["hijri_day"] == 29
    assert evening["gregorian_date"] == "2026-02-17"
    assert evening["sunset"] == "18:14"
    assert evening["moonset"] == "18:51"
    assert evening["visible"] is True
    assert evening["deciding_site"]["name"] == "Sabang / Weh Island"
    assert evening["deciding_site"]["tz"] == "Asia/Jakarta"
    assert evening["sites_checked"] == 2
    assert body["source"] == "mabims"
    assert response.headers["Cache-Control"].startswith("public")


def test_hilal_info_invisible(hilal_client, monkeypatch):
    monkeypatch.setattr(
        "app.main.observe_sighting_evening",
        lambda *a, **k: _fake_sighting(multisite=_fake_multisite(False, 1.5, 5.0)),
    )
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447")
    assert response.status_code == 200
    evening = response.json()["evening"]
    assert evening["alt_ok"] is False
    assert evening["elong_ok"] is False
    assert evening["visible"] is False
    # the reported values must still name the site they come from
    assert evening["deciding_site"]["name"] == "Sabang / Weh Island"


def test_hilal_info_invalid_month(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=13&year=1447")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_hilal_info_out_of_coverage_year(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1500")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_hilal_viz_png(hilal_client):
    response = hilal_client.get("/api/v1/hilal/viz?month=9&year=1447")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["Cache-Control"].startswith("public")
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(response.content) > 20_000


def test_hilal_viz_below_horizon(hilal_client, monkeypatch):
    monkeypatch.setattr(
        "app.main.observe_sighting_evening",
        lambda *a, **k: _fake_sighting(multisite=_fake_multisite(False, -2.0, 4.0)),
    )
    response = hilal_client.get("/api/v1/hilal/viz?month=9&year=1447")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


# ── geocentric criteria ⇔ curated table consistency ──


def test_curated_table_matches_geocentric_criteria():
    """Regression guard: the verdict served by /hilal must equal what the
    curated table says, for every month boundary in the table."""
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


# ── month resolution unit tests ──


@pytest.fixture()
def service():
    return CalendarService(DATA_PATH)


def test_resolve_evening_always_day29(service):
    """Evening is always the 29th; prev_length reports table month length."""
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
        resolve_sighting_evening(service, 1500, 9)
