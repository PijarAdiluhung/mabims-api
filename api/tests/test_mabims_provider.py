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
    prev_hijri_month,
)
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

ANCHOR_HIJRI = (1445, 7)
ANCHOR_GREGORIAN = date(2024, 1, 13)


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

    def test_backward_extension_from_anchor(self, provider):
        pairs = provider.fetch_by_hijri(1445, 6)
        assert "1445-06-01" in pairs
        values = sorted(pairs.values())
        assert values[-1] == "2024-01-12"
        assert len(pairs) in (29, 30)

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
        assert meta["fallback_active"] is False
        assert meta["computed_active"] is False
