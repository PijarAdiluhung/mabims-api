from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"


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


def _tomorrow_in_curated(real_data) -> str | None:
    tomorrow = (datetime.now(ZoneInfo("Asia/Jakarta")).date() + timedelta(days=1)).isoformat()
    return tomorrow if tomorrow in real_data["gregorian_to_hijri"] else None


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


def test_today_next_returns_following_hijri_date(client, real_data):
    tomorrow = _tomorrow_in_curated(real_data)
    if tomorrow is None:
        pytest.skip("tomorrow is outside the curated table")
    r = client.get("/api/v1/today?next=true")
    assert r.status_code == 200
    body = r.json()
    assert body["next"]["date"] == real_data["gregorian_to_hijri"][tomorrow]
    assert body["next"]["calendar"] == "hijri"
    assert body["next"]["day"] >= 1
    assert body["next"]["month_name"]
    assert body["next"]["source"] == "mabims"


def test_today_next_matches_immutable_endpoint(client, real_data):
    tomorrow = _tomorrow_in_curated(real_data)
    if tomorrow is None:
        pytest.skip("tomorrow is outside the curated table")
    live = client.get("/api/v1/today?next=true").json()
    fixed = client.get(f"/api/v1/today/{tomorrow}").json()
    assert live["next"]["date"] == fixed["output"]["date"]


def test_today_next_absent_without_flag(client):
    body = client.get("/api/v1/today").json()
    assert "next" not in body


def test_today_next_false_absent(client):
    body = client.get("/api/v1/today?next=false").json()
    assert "next" not in body


def test_today_invalid_next(client):
    r = client.get("/api/v1/today?next=maybe")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_next"

