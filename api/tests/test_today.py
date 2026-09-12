from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

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


def test_today_returns_today_in_jakarta(client):
    jakarta = ZoneInfo("Asia/Jakarta")
    today = datetime.now(jakarta).date().isoformat()
    r = client.get("/api/v1/today")
    assert r.status_code == 200
    body = r.json()
    assert body["input"]["date"] == today
    assert body["input"]["tz"] == "Asia/Jakarta"


def test_today_utc_offset(client):
    r = client.get("/api/v1/today?tz=UTC+8")
    assert r.status_code == 200
    body = r.json()
    assert body["input"]["tz"].startswith(("UTC+08", "+08"))


def test_today_invalid_timezone(client):
    r = client.get("/api/v1/today?tz=Not/AZone")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_timezone"


def test_today_immutable_date_endpoint(client):
    r = client.get("/api/v1/today/2025-03-01")
    assert r.status_code == 200
    body = r.json()
    assert body["output"]["date"] == "1446-09-01"
    assert body["output"]["calendar"] == "hijri"


def test_today_immutable_cache_headers(client):
    r = client.get("/api/v1/today/2025-03-01")
    assert "max-age=86400" in r.headers["cache-control"]
    assert "s-maxage=86400" in r.headers["cache-control"]


def test_today_dynamic_cache_control(client):
    r = client.get("/api/v1/today")
    cc = r.headers["cache-control"]
    assert "max-age=60" in cc
    assert "s-maxage=" in cc
    s_maxage = int(cc.split("s-maxage=")[1].split(",")[0])
    assert 30 <= s_maxage <= 86400
