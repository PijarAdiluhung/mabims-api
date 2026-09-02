"""Retro tier tests: computed dates below the curated table via ?retro=true."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.mabims_computed as mc
from app.config import Settings
from app.fallback import FallbackError
from app.mabims_computed import MabimsCalcProvider
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
        enable_aladhan=False,
    )
    return TestClient(create_app(settings=settings))


class TestRetroGating:
    def test_below_curated_requires_retro(self, retro_client):
        below = (date.fromisoformat(TABLE_FIRST) - timedelta(days=10)).isoformat()
        r = retro_client.get(f"/api/v1/convert?date={below}&calendar=gregorian")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "date_out_of_supported_range"

    def test_retro_false_behaves_like_default(self, retro_client):
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
        # The whole month before the month containing the curated start is
        # fully retro (the curated-start month itself legitimately mixes tiers).
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
        assert any("backwards" in w for w in body["warnings"])

    def test_straddling_month_mixes_tiers(self, retro_client):
        # The curated-start month mixes curated and retro days.
        first = date.fromisoformat(TABLE_FIRST)
        r = retro_client.get(
            f"/api/v1/month?year={first.year}&month={first.month}&calendar=gregorian&retro=true"
        )
        assert r.status_code == 200
        body = r.json()
        sources = {i["source"] for i in body["items"]}
        assert sources == {"mabims", "mabims-retro"}
        assert body["warnings"]  # aggregate flags the retro portion

    def test_retro_hilal_info(self, retro_client):
        r = retro_client.get("/api/v1/hilal/info?month=6&year=1444&retro=true")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "mabims-retro"
        assert body["month"]["year"] == 1444

    def test_retro_events_hijri(self, retro_client):
        r = retro_client.get("/api/v1/events?year=1444&calendar=hijri&retro=true")
        assert r.status_code == 200
        assert r.json()["count"] == 5

    def test_retro_meta_block(self, retro_client):
        meta = retro_client.get("/api/v1/meta").json()
        assert meta["retro"] is not None
        assert meta["retro"]["floor"] == "1945-01-01"
        assert meta["retro"]["requires_param"] is True


class TestBackwardProvider:
    @staticmethod
    def _stub_pattern(monkeypatch, pattern: list[bool]) -> None:
        calls = {"n": 0}

        class FakeResult:
            def __init__(self, visible: bool):
                self.alt_deg = 5.0 if visible else 1.0
                self.elong_deg = 8.0 if visible else 4.0

            @property
            def visible(self) -> bool:
                return self.alt_deg >= 3.0 and self.elong_deg >= 6.4

        def fake_criteria(d):
            result = FakeResult(pattern[calls["n"] % len(pattern)])
            calls["n"] += 1
            return result

        monkeypatch.setattr(mc, "criteria_on_sunset", fake_criteria)

    def test_backward_extension_matches_pattern(self, monkeypatch):
        # Deciding evenings: 30-day, 29-day, 30-day, 29-day ...
        self._stub_pattern(monkeypatch, [True, False, True, False])
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        provider.fetch_by_gregorian(2023, 11, retro=True)

        blocks = provider._blocks
        assert [b.hijri for b in blocks] == [
            (1445, 4), (1445, 5), (1445, 6), (1445, 7),
        ]
        # Pattern drives prepended lengths; the anchor block is decided forward.
        assert [b.length for b in blocks] == [30, 29, 30, blocks[-1].length]
        for prev, curr in zip(blocks, blocks[1:], strict=False):
            assert prev.start + timedelta(days=prev.length) == curr.start

    def test_backward_respects_retro_floor(self, monkeypatch):
        self._stub_pattern(monkeypatch, [True, False])
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        with pytest.raises(FallbackError):
            provider.fetch_by_gregorian(1940, 6, retro=True)

    def test_backward_real_dates_match_curated(self):
        # One real (unstubbed) backward step from the curated anchor must
        # reproduce the curated Jumadil Akhir 1445 start (2023-12-14).
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        pairs = provider.fetch_by_hijri(1445, 6, retro=True)
        assert pairs["1445-06-01"] == "2023-12-14"
        assert len(pairs) == 30
