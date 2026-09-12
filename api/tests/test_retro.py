"""Retro tier tests: computed dates below the curated table via ?retro=true."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"
TABLE_FIRST = min(json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"])


@pytest.fixture()
def retro_client(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    shrunk: dict[str, dict[str, str]] = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
    for key, value in list(raw["gregorian_to_hijri"].items())[:90]:
        shrunk["gregorian_to_hijri"][key] = value
        shrunk["hijri_to_gregorian"][value] = key
    (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")
    settings = Settings(
        data_dir=data_dir,
        allowed_origins=[],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    return TestClient(create_app(settings=settings))


class TestRetroGating:
    def test_below_curated_requires_retro(self, retro_client):
        below = (date.fromisoformat(TABLE_FIRST) - timedelta(days=10)).isoformat()
        r = retro_client.get(f"/api/v1/convert?date={below}&calendar=gregorian")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "date_out_of_supported_range"

    def test_retro_false_same_as_default(self, retro_client):
        inside = (date.fromisoformat(TABLE_FIRST) + timedelta(days=10)).isoformat()
        r = retro_client.get(f"/api/v1/convert?date={inside}&calendar=gregorian&retro=false")
        assert r.status_code == 200
        assert r.json()["source"] == "mabims"

    def test_invalid_retro_value(self, retro_client):
        r = retro_client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=1")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_retro"

    def test_retro_floor_rejects_1940(self, retro_client):
        r = retro_client.get("/api/v1/convert?date=1940-06-01&calendar=gregorian&retro=true")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "date_out_of_supported_range"


class TestRetroEndpoints:
    def test_retro_convert_gregorian(self, retro_client):
        below = (date.fromisoformat(TABLE_FIRST) - timedelta(days=10)).isoformat()
        r = retro_client.get(f"/api/v1/convert?date={below}&calendar=gregorian&retro=true")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-retro"
        assert any("backwards" in w for w in body["warnings"])

    def test_retro_convert_hijri(self, retro_client):
        r = retro_client.get("/api/v1/convert?date=1444-06-01&calendar=hijri&retro=true")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-retro"
        assert body["output"]["calendar"] == "gregorian"
        assert body["output"]["date"] < TABLE_FIRST

    def test_retro_month_gregorian(self, retro_client):
        first_of_curated_month = date.fromisoformat(TABLE_FIRST).replace(day=1)
        last_before = first_of_curated_month - timedelta(days=1)
        r = retro_client.get(
            f"/api/v1/month?year={last_before.year}&month={last_before.month}"
            "&calendar=gregorian&retro=true"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 28
        assert all(i["source"] == "mabims-retro" for i in body["items"])

    def test_straddling_month_mixes_tiers(self, retro_client):
        first = date.fromisoformat(TABLE_FIRST)
        r = retro_client.get(
            f"/api/v1/month?year={first.year}&month={first.month}"
            "&calendar=gregorian&retro=true"
        )
        assert r.status_code == 200
        body = r.json()
        sources = {i["source"] for i in body["items"]}
        assert sources == {"mabims", "mabims-retro"}

    def test_retro_events_hijri(self, retro_client):
        r = retro_client.get("/api/v1/events?year=1444&calendar=hijri&retro=true")
        assert r.status_code == 200
        assert r.json()["count"] == 5
