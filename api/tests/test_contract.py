"""Contract tests: real endpoint responses must keep matching the Pydantic schemas.

These tests parse each response into its declared model so any shape change fails
loudly here instead of silently breaking API consumers or going stale versus the docs.
"""

from __future__ import annotations

import calendar as pycalendar
import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.schemas import (
    ConvertResponse,
    ErrorResponse,
    EventsResponse,
    HealthResponse,
    MetaResponse,
    MonthResponse,
    RangeResponse,
)

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

DOCUMENTED_ENDPOINTS = [
    "/healthz",
    "/api/v1/meta",
    "/api/v1/today",
    "/api/v1/today/{target_date}",
    "/api/v1/convert",
    "/api/v1/range",
    "/api/v1/month",
    "/api/v1/events",
]


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


def _parse(body, model):
    return model.model_validate(body)


def test_documented_endpoints_exist_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in DOCUMENTED_ENDPOINTS:
        assert path in paths, f"{path} is documented but missing from the OpenAPI schema"


def test_healthz_matches_schema(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    _parse(response.json(), HealthResponse)


def test_meta_matches_schema(client):
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    _parse(response.json(), MetaResponse)


def test_convert_gregorian_matches_schema(client, real_data):
    g_iso = min(real_data["gregorian_to_hijri"])
    response = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
    assert response.status_code == 200
    _parse(response.json(), ConvertResponse)


def test_convert_hijri_matches_schema(client, real_data):
    h_iso = max(real_data["hijri_to_gregorian"])
    response = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
    assert response.status_code == 200
    _parse(response.json(), ConvertResponse)


def test_today_immutable_matches_schema(client, real_data):
    g_iso = min(real_data["gregorian_to_hijri"])
    response = client.get(f"/api/v1/today/{g_iso}")
    assert response.status_code == 200
    _parse(response.json(), ConvertResponse)


def test_range_matches_schema(client, real_data):
    first = date.fromisoformat(min(real_data["gregorian_to_hijri"]))
    last = date.fromisoformat(max(real_data["gregorian_to_hijri"]))
    end = min(date.fromordinal(first.toordinal() + 9), last)
    response = client.get(f"/api/v1/range?start={first}&end={end}&calendar=gregorian")
    assert response.status_code == 200
    body = _parse(response.json(), RangeResponse)
    assert body.count == (end - first).days + 1


def test_month_matches_schema(client, real_data):
    g_first = date.fromisoformat(min(real_data["gregorian_to_hijri"]))
    g_last = date.fromisoformat(max(real_data["gregorian_to_hijri"]))
    year, month = g_last.year, g_last.month
    response = client.get(f"/api/v1/month?year={year}&month={month}&calendar=gregorian")
    assert response.status_code == 200
    body = _parse(response.json(), MonthResponse)
    month_start = max(date(year, month, 1), g_first)
    month_end = date(year, month, pycalendar.monthrange(year, month)[1])
    expected_end = min(month_end, g_last)
    assert body.count == (expected_end - month_start).days + 1


def test_events_matches_schema(client, real_data):
    h_iso = max(real_data["hijri_to_gregorian"])
    response = client.get(f"/api/v1/events?year={int(h_iso[0:4])}&calendar=hijri")
    assert response.status_code == 200
    _parse(response.json(), EventsResponse)


def test_error_shape_matches_schema(client):
    response = client.get("/api/v1/convert?date=2025-13-99&calendar=gregorian")
    assert response.status_code == 400
    _parse(response.json(), ErrorResponse)


def test_missing_parameter_error_shape(client):
    response = client.get("/api/v1/convert")
    assert response.status_code == 400
    _parse(response.json(), ErrorResponse)
