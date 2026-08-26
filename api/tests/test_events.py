from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.schemas import EventsResponse

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"


@pytest.fixture(scope="module")
def client():
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    return TestClient(create_app(settings=settings))


@pytest.fixture(scope="module")
def real_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _expected_events(real_data, year: int, calendar: str):
    h2g = real_data["hijri_to_gregorian"]
    prefix = f"{year:04d}-"
    event_days = {1: 1, 3: 12, 9: 1, 10: 1, 12: 10}
    rows = []
    for h_iso, g_iso in h2g.items():
        probe = h_iso if calendar == "hijri" else g_iso
        if probe.startswith(prefix) and int(h_iso[8:10]) == event_days.get(int(h_iso[5:7])):
            rows.append((g_iso, h_iso))
    return sorted(rows)


def test_events_by_hijri_year(client, real_data):
    response = client.get("/api/v1/events?year=1446&calendar=hijri")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 5
    actual = [(e["gregorian"], e["hijri"]) for e in body["events"]]
    assert actual == _expected_events(real_data, 1446, "hijri")


def test_events_known_dates(client):
    response = client.get("/api/v1/events?year=1446&calendar=hijri")
    body = response.json()
    by_slug = {event["event"]: event for event in body["events"]}
    assert by_slug["awal_ramadan"]["gregorian"] == "2025-03-01"
    assert by_slug["idul_adha"]["gregorian"] == "2025-06-06"
    assert all(event["source"] == "mabims" for event in body["events"])


def test_events_by_gregorian_year(client, real_data):
    response = client.get("/api/v1/events?year=2025&calendar=gregorian")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(_expected_events(real_data, 2025, "gregorian"))
    assert all(event["gregorian"].startswith("2025") for event in body["events"])


def test_events_outside_coverage_is_empty(client):
    response = client.get("/api/v1/events?year=2030&calendar=gregorian")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["events"] == []
    assert body["warnings"] == []


def test_events_matches_schema(client, real_data):
    response = client.get("/api/v1/events?year=1446&calendar=hijri")
    assert response.status_code == 200
    parsed = EventsResponse.model_validate(response.json())
    assert parsed.count == 5


def test_events_invalid_calendar(client):
    response = client.get("/api/v1/events?year=1446&calendar=julian")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_calendar"


def test_events_invalid_year(client):
    response = client.get("/api/v1/events?year=999&calendar=gregorian")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_year"


def test_events_missing_year(client):
    response = client.get("/api/v1/events")
    assert response.status_code == 422
