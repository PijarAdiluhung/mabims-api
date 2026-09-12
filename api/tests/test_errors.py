from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    return TestClient(create_app(settings=settings))


def test_invalid_date_format(client):
    r = client.get("/api/v1/convert?date=not-a-date&calendar=gregorian")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "invalid_date"
    assert "message" in body["error"]


def test_invalid_calendar_value(client):
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=lunar")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_calendar"


def test_missing_date_param(client):
    r = client.get("/api/v1/convert")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"


def test_invalid_timezone(client):
    r = client.get("/api/v1/today?tz=Not/AZone")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_timezone"


def test_invalid_retro_value(client):
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=1")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_retro"


def test_invalid_step_value(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-01-10&step=week")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_step"


def test_date_out_of_supported_range_before(client):
    r = client.get("/api/v1/convert?date=1900-01-01&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "date_out_of_supported_range"


def test_error_shape_is_consistent(client):
    r = client.get("/api/v1/convert?date=bad&calendar=gregorian")
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert isinstance(body["error"], dict)
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert isinstance(body["error"]["code"], str)
    assert isinstance(body["error"]["message"], str)


def test_events_invalid_calendar(client):
    r = client.get("/api/v1/events?year=1446&calendar=julian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_calendar"


def test_events_invalid_year(client):
    r = client.get("/api/v1/events?year=999&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_year"
