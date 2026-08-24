from __future__ import annotations

import calendar as pycalendar
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

ALLOWED = ["https://partner.example"]


def make_settings(data_dir: Path | None = None, **overrides) -> Settings:
    kwargs = {
        "data_dir": data_dir or DATA_PATH.parent,
        "allowed_origins": ALLOWED,
        "rate_limit": "10000/minute",
        **overrides,
    }
    return Settings(**kwargs)


@pytest.fixture(scope="session")
def real_data():
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return raw


@pytest.fixture()
def client(real_data):
    app = create_app(settings=make_settings(enable_fallback=False))
    return TestClient(app)


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


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
    utc_now = datetime.now(timezone.utc).date().isoformat()
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


def test_origin_allowlist(client):
    ok = client.get("/api/v1/today", headers={"Origin": "https://partner.example"})
    subdomain = client.get("/api/v1/today", headers={"Origin": "https://app.malangmengaji.com"})
    bad = client.get("/api/v1/today", headers={"Origin": "https://evil.example"})
    none = client.get("/api/v1/today")
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "https://partner.example"
    assert subdomain.status_code == 200
    assert bad.status_code == 403
    assert bad.json()["error"]["code"] == "forbidden_origin"
    assert none.status_code == 200


def test_preflight_options(client):
    response = client.options(
        "/api/v1/convert",
        headers={"Origin": "https://partner.example", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 204
    assert response.headers["access-control-allow-origin"] == "https://partner.example"


class TestFallbackBridge:
    @pytest.fixture()
    def fallback_env(self, tmp_path, real_data):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        shrunk = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
        for key, value in list(real_data["gregorian_to_hijri"].items())[:90]:
            shrunk["gregorian_to_hijri"][key] = value
            shrunk["hijri_to_gregorian"][value] = key
        (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")

        class FakeAladhan:
            def __init__(self):
                self.g_calls = 0
                self.h_calls = 0

            def fetch_by_gregorian(self, year, month):
                self.g_calls += 1
                pairs = {}
                for day in range(1, pycalendar.monthrange(year, month)[1] + 1):
                    pairs[f"{year:04d}-{month:02d}-{day:02d}"] = f"1449-{month:02d}-{day:02d}"
                return pairs

            def fetch_by_hijri(self, hy, hm):
                self.h_calls += 1
                pairs = {}
                for day in range(1, 30 + 1):
                    pairs[f"{hy:04d}-{hm:02d}-{day:02d}"] = f"2027-{hm:02d}-{min(day, 28):02d}"
                return pairs

        fake = FakeAladhan()
        settings = make_settings(
            data_dir=data_dir,
            enable_fallback=True,
            allowed_origins=[],
        )
        app = create_app(settings=settings, fallback_provider=fake)
        return TestClient(app), fake, data_dir

    def test_fallback_serves_marks_and_persists_once(self, fallback_env):
        client_, fake, data_dir = fallback_env
        first = client_.get("/api/v1/convert?date=2026-06-15&calendar=gregorian")
        assert first.status_code == 200
        body = first.json()
        assert body["output"]["date"] == "1449-06-15"
        assert body["source"] == "fallback:aladhan-ummalqura"
        assert any("Umm al-Qura" in warning for warning in body["warnings"])
        assert fake.g_calls == 1
        assert (data_dir / "fallback_2026.json").exists()

        second = client_.get("/api/v1/convert?date=2026-06-16&calendar=gregorian")
        assert second.status_code == 200
        assert fake.g_calls == 1

        meta = client_.get("/api/v1/meta").json()
        assert meta["fallback_active"] is True
        assert meta["fallback_months"] == ["G2026-06"]

    def test_fallback_hijri_direction(self, fallback_env):
        client_, fake, _ = fallback_env
        response = client_.get("/api/v1/convert?date=1449-06-15&calendar=hijri")
        assert response.status_code == 200
        assert response.json()["output"]["date"] == "2027-06-15"
        assert fake.h_calls == 1

    def test_preloaded_year_file_avoids_refetch(self, fallback_env):
        client_, fake, data_dir = fallback_env
        client_.get("/api/v1/convert?date=2026-06-15&calendar=gregorian")

        from app.fallback import FallbackStore

        store = FallbackStore(data_dir, fake)
        store.load_existing()
        assert store.lookup("2026-06-15", "gregorian") == "1449-06-15"
