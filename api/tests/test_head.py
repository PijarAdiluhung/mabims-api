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


def test_head_today(client):
    r = client.head("/api/v1/today")
    assert r.status_code == 200
    assert r.content == b""


def test_head_convert(client):
    r = client.head("/api/v1/convert?date=2025-01-01&calendar=gregorian")
    assert r.status_code == 200
    assert r.content == b""


def test_head_range(client):
    r = client.head("/api/v1/range?start=2025-01-01&end=2025-01-03&calendar=gregorian")
    assert r.status_code == 200
    assert r.content == b""


def test_head_month(client):
    r = client.head("/api/v1/month?year=1446&month=1&calendar=hijri")
    assert r.status_code == 200
    assert r.content == b""


def test_head_events(client):
    r = client.head("/api/v1/events?year=1446&calendar=hijri")
    assert r.status_code == 200
    assert r.content == b""


def test_head_meta(client):
    r = client.head("/api/v1/meta")
    assert r.status_code == 200
    assert r.content == b""


def test_head_months(client):
    r = client.head("/api/v1/months")
    assert r.status_code == 200
    assert r.content == b""


def test_head_hilal_info(client):
    r = client.head("/api/v1/hilal/info?month=9&year=1447")
    assert r.status_code == 200
    assert r.content == b""


def test_head_unknown_path(client):
    r = client.head("/api/v1/does-not-exist")
    assert r.status_code == 404
