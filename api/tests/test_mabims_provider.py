from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.mabims_astro import criteria_on_day29
from app.mabims_computed import (
    BORDERLINE_MARGIN_DEG,
    COMPUTED_SOURCE,
    MabimsCalcProvider,
    next_hijri_month,
)
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

ANCHOR_HIJRI = (1445, 7)
ANCHOR_GREGORIAN = date(2024, 1, 13)


def prev_hijri_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


@pytest.fixture(scope="module")
def provider():
    return MabimsCalcProvider(ANCHOR_HIJRI, ANCHOR_GREGORIAN)


class TestHijriMonthArithmetic:
    def test_next_rollover(self):
        assert next_hijri_month(1446, 12) == (1447, 1)
        assert next_hijri_month(1446, 7) == (1446, 8)

    def test_prev_rollover(self):
        assert prev_hijri_month(1447, 1) == (1446, 12)
        assert prev_hijri_month(1446, 7) == (1446, 6)


class TestMabimsCalcProvider:
    def test_fetch_by_gregorian_matches_official_month_start(self, provider):
        pairs = provider.fetch_by_gregorian(2025, 3)
        assert pairs["2025-03-01"] == "1446-09-01"
        assert len(pairs) == 31

    def test_fetch_by_hijri_matches_official_month_start(self, provider):
        pairs = provider.fetch_by_hijri(1447, 9)
        assert pairs["1447-09-01"] == "2026-02-19"
        assert len(pairs) == 30

    def test_months_before_anchor_are_not_computed(self, provider):
        # Pre-anchor months come from the curated table; the provider only walks forward.
        assert provider.fetch_by_hijri(1445, 6) == {}

    def test_roundtrip_g2h_h2g_consistency(self, provider):
        g_pairs = provider.fetch_by_gregorian(2027, 1)
        for g, h in g_pairs.items():
            h_pairs = provider.fetch_by_hijri(int(h[:4]), int(h[5:7]))
            assert h_pairs[h] == g


class TestBorderlineClassification:
    def test_known_borderline_month_is_flagged(self):
        result = criteria_on_day29(date(2026, 11, 11))
        margin = min(result.alt_deg - 3.0, result.elong_deg - 6.4)
        assert margin < BORDERLINE_MARGIN_DEG
        assert result.visible is True

    def test_provider_reports_borderline_after_computation(self, provider):
        provider.fetch_by_hijri(1448, 6)
        assert "1448-06" in provider.borderline_months()


@pytest.fixture()
def computed_client(tmp_path):
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
        enable_aladhan=False,
    )
    return TestClient(create_app(settings=settings))


class TestComputedTierIntegration:
    def test_out_of_coverage_served_from_computed(self, computed_client):
        response = computed_client.get("/api/v1/convert?date=2027-03-10&calendar=gregorian")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == COMPUTED_SOURCE
        assert any("Neo MABIMS" in w for w in body["warnings"])

    def test_table_wins_over_computed(self, computed_client):
        response = computed_client.get("/api/v1/convert?date=2024-02-01&calendar=gregorian")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims"
        assert body["warnings"] == []

    def test_hijri_direction_beyond_coverage(self, computed_client):
        response = computed_client.get("/api/v1/convert?date=1449-01-01&calendar=hijri")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == COMPUTED_SOURCE
        assert body["output"]["calendar"] == "gregorian"

    def test_meta_exposes_method_and_tiers(self, computed_client):
        meta = computed_client.get("/api/v1/meta").json()
        assert meta["method"] == "neo-mabims-sabang"

        assert meta["computed_active"] is False


def _shrunk_curated_months() -> tuple[list[str], dict[str, str]]:
    """First two fully/partially covered Hijri months of the shrunk table."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    g2h = dict(sorted(raw["gregorian_to_hijri"].items())[:90])
    h2g = {v: k for k, v in g2h.items()}
    months = sorted({h[:7] for h in h2g})
    return months, h2g


class TestComputedTierHijriEndpoints:
    def test_hijri_month_computed(self, computed_client):
        r = computed_client.get("/api/v1/month?year=1449&month=1&calendar=hijri")
        assert r.status_code == 200
        body = r.json()
        assert 29 <= body["count"] <= 30
        assert all(i["source"] == COMPUTED_SOURCE for i in body["items"])
        gregorians = [i["gregorian"] for i in body["items"]]
        assert gregorians == sorted(gregorians)
        assert body["items"][0]["hijri"] == "1449-01-01"

    def test_hijri_month_curated_not_extended_by_computed(self, computed_client):
        # A fully-curated month keeps its authoritative length (29 or 30),
        # even if the computed provider would differ.
        months, h2g = _shrunk_curated_months()
        m1_days = sorted(h for h in h2g if h[:7] == months[0])
        curated_len = len(m1_days)
        assert curated_len in (29, 30)
        r = computed_client.get(
            f"/api/v1/month?year={months[0][:4]}&month={int(months[0][5:7])}&calendar=hijri"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == curated_len
        assert all(i["source"] == "mabims" for i in body["items"])

    def test_hijri_range_crosses_curated_month_boundary(self, computed_client):
        months, h2g = _shrunk_curated_months()
        m1_days = sorted(h for h in h2g if h[:7] == months[0])
        m2_days = sorted(h for h in h2g if h[:7] == months[1])
        start, end = m1_days[-1], m2_days[0]
        r = computed_client.get(f"/api/v1/range?start={start}&end={end}&calendar=hijri")
        assert r.status_code == 200
        items = r.json()["items"]
        assert [i["hijri"] for i in items] == [start, end]
        assert all(i["source"] == "mabims" for i in items)

    def test_hijri_range_rejects_phantom_day30(self, computed_client):
        # Rabiul Akhir 1448 is 29 days, so 1448-04-30 is gregorian-valid but
        # has no Hijri pair. It must 404, not silently clip the range.
        r = computed_client.get(
            "/api/v1/range?start=1448-04-30&end=1448-05-02&calendar=hijri"
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "date_not_found"

    def test_hijri_safar30_is_accepted(self, computed_client):
        # Some Hijri years (e.g. 1450) have a 30-day Safar, so 1450-02-30 is a
        # legitimate date even though it is invalid in the Gregorian calendar.
        r = computed_client.get("/api/v1/convert?date=1450-02-30&calendar=hijri")
        assert r.status_code == 200
        body = r.json()
        assert body["output"]["calendar"] == "gregorian"

        # The range endpoint must accept it too.
        r2 = computed_client.get(
            "/api/v1/range?start=1450-02-30&end=1450-02-30&calendar=hijri"
        )
        assert r2.status_code == 200
        assert r2.json()["count"] == 1
        assert r2.json()["items"][0]["hijri"] == "1450-02-30"

    def test_hijri_safar30_in_29day_month_is_not_found(self, computed_client):
        # Guard: a 30 Safar request for a year where Safar has 29 days must 404.
        assert computed_client.get(
            "/api/v1/month?year=1449&month=2&calendar=hijri"
        ).json()["count"] == 29
        r = computed_client.get("/api/v1/convert?date=1449-02-30&calendar=hijri")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "date_not_found"

    def test_hijri_range_full_year_computed(self, computed_client):
        # End on the real last day of Dzulhijjah (may be 29 or 30).
        last = computed_client.get(
            "/api/v1/month?year=1449&month=12&calendar=hijri"
        ).json()["items"][-1]["hijri"]
        r = computed_client.get(
            f"/api/v1/range?start=1449-01-01&end={last}&calendar=hijri"
        )
        assert r.status_code == 200
        body = r.json()
        assert 350 <= body["count"] <= 355
        hijris = [i["hijri"] for i in body["items"]]
        assert hijris == sorted(hijris)
        assert len(hijris) == len(set(hijris))
        assert all(i["source"] == COMPUTED_SOURCE for i in body["items"])
        assert any("Neo MABIMS" in w for w in body["warnings"])
