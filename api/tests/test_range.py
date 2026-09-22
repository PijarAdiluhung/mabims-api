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


def test_range_basic_gregorian(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-01-05&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5
    assert len(body["items"]) == 5
    assert body["input"]["start"] == "2025-01-01"
    assert body["input"]["end"] == "2025-01-05"
    assert body["input"]["calendar"] == "gregorian"


def test_range_max_45_days(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-02-15&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "range_too_large"


def test_range_hijri_to_hijri(client):
    r = client.get("/api/v1/range?start=1446-01-01&end=1446-01-05&calendar=hijri")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5
    assert body["input"]["calendar"] == "hijri"
    for item in body["items"]:
        assert item["hijri"].startswith("1446-01-")


def test_range_start_after_end(client):
    r = client.get("/api/v1/range?start=2025-01-10&end=2025-01-01&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_range"


def test_range_missing_params(client):
    r = client.get("/api/v1/range")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"

    r = client.get("/api/v1/range?start=2025-01-01")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"


def test_range_step_not_day(client):
    r = client.get(
        "/api/v1/range?start=2025-01-01&end=2025-01-05&step=week"
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_step"


def test_range_head_matches_get(client):
    r_head = client.head("/api/v1/range?start=2025-01-01&end=2025-01-03&calendar=gregorian")
    r_get = client.get("/api/v1/range?start=2025-01-01&end=2025-01-03&calendar=gregorian")
    assert r_head.status_code == r_get.status_code
    assert r_head.content == b""
