from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.calendar import CalendarService
from app.config import Settings
from app.hilal.astro import Observation
from app.hilal.service import MonthNotResolvable, resolve_sighting_evening
from app.main import create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"


def _fake_obs(**overrides) -> Observation:
    obs = Observation(
        sunset_local="18:14",
        moonset_local="18:51",
        sun_alt=-0.83,
        sun_az=258.30,
        moon_alt=8.78,
        moon_az=263.98,
        elongation=11.07,
        illumination=0.0107,
        age_hours=23.2,
    )
    return replace(obs, **overrides) if overrides else obs


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
    monkeypatch.setattr("app.main.observe_at_sunset", lambda *a, **k: _fake_obs())
    return TestClient(app)


def test_hilal_info_ok(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447&location=jakarta")
    assert response.status_code == 200
    body = response.json()
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
    assert body["source"] == "mabims"
    assert response.headers["Cache-Control"].startswith("private")


def test_hilal_info_invisible(hilal_client, monkeypatch):
    monkeypatch.setattr(
        "app.main.observe_at_sunset",
        lambda *a, **k: _fake_obs(moon_alt=1.5, elongation=5.0, illumination=0.002),
    )
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447")
    assert response.status_code == 200
    evening = response.json()["evening"]
    assert evening["alt_ok"] is False
    assert evening["elong_ok"] is False
    assert evening["visible"] is False


def test_hilal_info_default_location(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447")
    assert response.status_code == 200
    assert response.json()["input"]["location"] == "jakarta"


def test_hilal_info_invalid_location(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1447&location=paris")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_location"


def test_hilal_info_invalid_month(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=13&year=1447")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_hilal_info_out_of_coverage_year(hilal_client):
    response = hilal_client.get("/api/v1/hilal/info?month=9&year=1500")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_hilal_viz_png(hilal_client):
    response = hilal_client.get("/api/v1/hilal/viz?month=9&year=1447&location=jakarta")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["Cache-Control"].startswith("private")
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(response.content) > 20_000


def test_hilal_viz_below_horizon(hilal_client, monkeypatch):
    monkeypatch.setattr(
        "app.main.observe_at_sunset",
        lambda *a, **k: _fake_obs(moon_alt=-2.0, elongation=4.0, illumination=0.001),
    )
    response = hilal_client.get("/api/v1/hilal/viz?month=9&year=1447")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


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
