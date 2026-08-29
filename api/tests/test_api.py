from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import APP_VERSION, Settings
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

ALLOWED = ["https://partner.example"]


def make_settings(data_dir: Path | None = None, **overrides) -> Settings:
    kwargs = {
        "data_dir": data_dir or DATA_PATH.parent,
        "allowed_origins": ALLOWED,
        "rate_limit": "10000/minute",
        "enable_computed": False,
        **overrides,
    }
    return Settings(**kwargs)


@pytest.fixture(scope="session")
def real_data():
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return raw


@pytest.fixture()
def client(real_data):
    app = create_app(settings=make_settings(enable_fallback=False, allowed_origins=["*"]))
    return TestClient(app)


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": APP_VERSION}


def test_convert_gregorian_known_pair(client, real_data):
    g_iso = min(real_data["gregorian_to_hijri"])
    expected_h = real_data["gregorian_to_hijri"][g_iso]
    response = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
    assert response.status_code == 200
    body = response.json()
    assert body["output"]["date"] == expected_h
    assert body["output"]["calendar"] == "hijri"
    assert body["source"] == "mabims"
    assert body["warnings"] == []


def test_convert_hijri_known_pair(client, real_data):
    h_iso = max(real_data["hijri_to_gregorian"])
    expected_g = real_data["hijri_to_gregorian"][h_iso]
    response = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
    assert response.status_code == 200
    body = response.json()
    assert body["output"]["date"] == expected_g
    assert body["output"]["calendar"] == "gregorian"


def test_convert_invalid_date(client):
    response = client.get("/api/v1/convert?date=2025-13-99&calendar=gregorian")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_date"


def test_convert_missing_params(client):
    response = client.get("/api/v1/convert")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_parameter"


def test_convert_invalid_calendar(client):
    response = client.get("/api/v1/convert?date=2025-01-01&calendar=lunar")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_calendar"


def test_today_matches_table_and_dynamic_ttl(client, real_data):
    jakarta = ZoneInfo("Asia/Jakarta")
    today_iso = datetime.now(jakarta).date().isoformat()
    response = client.get("/api/v1/today")
    assert response.status_code == 200
    body = response.json()
    if today_iso in real_data["gregorian_to_hijri"]:
        assert body["input"]["date"] == today_iso
        assert body["output"]["date"] == real_data["gregorian_to_hijri"][today_iso]
        assert body["warnings"] == []
    cache_control = response.headers["cache-control"]
    assert "max-age=60" in cache_control
    s_maxage = int(cache_control.split("s-maxage=")[1])
    assert 30 <= s_maxage <= 86_400


def test_today_tz_offset_default_is_jakarta(client):
    jakarta_now = datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    utc_now = datetime.now(UTC).date().isoformat()
    default_body = client.get("/api/v1/today").json()
    offset_body = client.get("/api/v1/today", params={"tz": "UTC+7"}).json()
    assert default_body["input"]["tz"] == "Asia/Jakarta"
    assert offset_body["input"]["tz"].startswith(("UTC+07", "+07"))
    if jakarta_now != utc_now:
        assert default_body["input"]["date"] == jakarta_now


def test_today_invalid_timezone(client):
    response = client.get("/api/v1/today?tz=Not/AZone")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_timezone"


def test_today_on_immutable_cache(client, real_data):
    g_iso = min(real_data["gregorian_to_hijri"])
    response = client.get(f"/api/v1/today/{g_iso}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert response.json()["output"]["date"] == real_data["gregorian_to_hijri"][g_iso]


def test_meta_coverage_and_version(client, real_data):
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    body = response.json()
    g_keys = sorted(real_data["gregorian_to_hijri"])
    assert body["coverage"]["first"] == g_keys[0]
    assert body["coverage"]["last"] == g_keys[-1]
    assert body["fallback_active"] is False
    assert len(body["data_version"]) == 12


def test_range_month_grid(client, real_data):
    response = client.get("/api/v1/range?start=2025-01-01&end=2025-01-31&calendar=gregorian")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 31
    for item in body["items"]:
        assert real_data["gregorian_to_hijri"][item["gregorian"]] == item["hijri"]
    month_response = client.get("/api/v1/month?year=2025&month=1&calendar=gregorian")
    assert month_response.status_code == 200
    assert month_response.json()["items"] == body["items"]


def test_hijri_month_returns_sorted_pairs(client, real_data):
    sample_h = sorted(real_data["hijri_to_gregorian"])[100]
    year, month = int(sample_h[0:4]), int(sample_h[5:7])
    response = client.get(f"/api/v1/month?year={year}&month={month}&calendar=hijri")
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["hijri"].startswith(sample_h[:7]) for item in items)
    gregorians = [item["gregorian"] for item in items]
    assert gregorians == sorted(gregorians)


def test_range_too_large(client):
    response = client.get("/api/v1/range?start=2025-01-01&end=2026-06-01&calendar=gregorian")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "range_too_large"


def test_range_out_of_coverage_without_fallback(client, real_data):
    last = max(real_data["gregorian_to_hijri"])
    beyond = (date.fromisoformat(last) + timedelta(days=10)).isoformat()
    response = client.get(f"/api/v1/range?start={beyond}&end={beyond}&calendar=gregorian")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_origin_public_by_default(client):
    any_origin = client.get("/api/v1/today", headers={"Origin": "https://random-site.example"})
    none = client.get("/api/v1/today")
    assert any_origin.status_code == 200
    assert any_origin.headers["access-control-allow-origin"] == "*"
    assert none.status_code == 200


def test_origin_allowlist_still_available_when_configured(real_data):
    restrictive = make_settings(allowed_origins=["https://partner.example"], origin_suffixes=[])
    app = create_app(settings=restrictive)
    client = TestClient(app)
    ok = client.get("/api/v1/today", headers={"Origin": "https://partner.example"})
    bad = client.get("/api/v1/today", headers={"Origin": "https://evil.example"})
    assert ok.status_code == 200
    assert bad.status_code == 403


def test_preflight_options(client):
    response = client.options(
        "/api/v1/convert",
        headers={"Origin": "https://partner.example", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "*"


class TestComputedFallback:
    @pytest.fixture()
    def computed_env(self, tmp_path, real_data):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        shrunk: dict[str, dict[str, str]] = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
        for key, value in list(real_data["gregorian_to_hijri"].items())[:90]:
            shrunk["gregorian_to_hijri"][key] = value
            shrunk["hijri_to_gregorian"][value] = key
        (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")

        settings = make_settings(
            data_dir=data_dir,
            enable_fallback=True,
            enable_computed=True,
            enable_aladhan=False,
            allowed_origins=[],
        )
        app = create_app(settings=settings)
        return TestClient(app)

    def test_computed_fallback_serves_outside_table(self, computed_env):
        response = computed_env.get("/api/v1/convert?date=2035-06-15&calendar=gregorian")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims-computed"
        assert any("Neo MABIMS" in w for w in body["warnings"])

    def test_computed_fallback_hijri_direction(self, computed_env):
        response = computed_env.get("/api/v1/convert?date=1460-01-01&calendar=hijri")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims-computed"
        assert any("Neo MABIMS" in w for w in body["warnings"])

    def test_curated_dates_still_use_mabims_source(self, computed_env, real_data):
        g_iso = min(real_data["gregorian_to_hijri"])
        response = computed_env.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims"
        assert body["warnings"] == []
