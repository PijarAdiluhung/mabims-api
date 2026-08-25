from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.mabims_computed import MabimsCalcProvider
from app.precomputed import PrecomputedStore

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"

FAKE_EPOCH = date(622, 7, 16)


def fake_hijri(gregorian: date) -> str:
    index = (gregorian - FAKE_EPOCH).days // 30
    day = (gregorian - FAKE_EPOCH).days % 30 + 1
    return f"{index // 12:04d}-{index % 12 + 1:02d}-{day:02d}"


def write_table(path: Path, back: date, forward: date, borderline: list[str]) -> str:
    g2h: dict[str, str] = {}
    h2g: dict[str, str] = {}
    cursor = back
    while cursor <= forward:
        hijri = fake_hijri(cursor)
        g2h[cursor.isoformat()] = hijri
        h2g[hijri] = cursor.isoformat()
        cursor = date.fromordinal(cursor.toordinal() + 1)
    payload = {
        "meta": {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "back": back.isoformat(),
            "forward": forward.isoformat(),
            "days": len(g2h),
            "borderline_months": borderline,
        },
        "gregorian_to_hijri": dict(sorted(g2h.items())),
        "hijri_to_gregorian": dict(sorted(h2g.items())),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture()
def table_path(tmp_path: Path) -> Path:
    return write_table(
        tmp_path / "computed_table.json",
        date(2023, 1, 1),
        date(2027, 12, 31),
        borderline=["1448-06"],
    )


class TestPrecomputedStore:
    def test_lookup_both_directions(self, table_path):
        store = PrecomputedStore(table_path)
        g_iso = "2025-06-15"
        h_iso = store.lookup(g_iso, "gregorian")
        assert h_iso == fake_hijri(date(2025, 6, 15))
        assert store.lookup(h_iso, "hijri") == g_iso

    def test_misses_outside_range(self, table_path):
        store = PrecomputedStore(table_path)
        assert store.lookup("1975-04-01", "gregorian") is None
        assert store.covers("1975-04-01", "gregorian") is False
        assert store.covers("2025-06-15", "gregorian") is True

    def test_ensure_month_is_noop(self, table_path):
        from app.calendar import MonthKey

        store = PrecomputedStore(table_path)
        assert store.ensure_month(MonthKey("G", 1999, 1)) is None

    def test_summary_reports_span(self, table_path):
        store = PrecomputedStore(table_path)
        active, labels = store.summary()
        assert active is True
        assert labels == ["precomputed:2023-01-01..2027-12-31"]

    def test_borderline_months_loaded(self, table_path):
        store = PrecomputedStore(table_path)
        assert "1448-06" in store.borderline


@pytest.fixture()
def computed_client(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    shrunk = {"gregorian_to_hijri": {}, "hijri_to_gregorian": {}}
    for key, value in list(raw["gregorian_to_hijri"].items())[:90]:
        shrunk["gregorian_to_hijri"][key] = value
        shrunk["hijri_to_gregorian"][value] = key
    (data_dir / "calendar_data.json").write_text(json.dumps(shrunk), encoding="utf-8")

    borderline_month = fake_hijri(date(2026, 8, 10))[0:7]
    write_table(
        data_dir / "computed_table.json",
        date(2023, 1, 1),
        date(2027, 12, 31),
        borderline=[borderline_month],
    )

    settings = Settings(
        data_dir=data_dir,
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
        enable_aladhan=False,
    )
    return TestClient(create_app(settings=settings)), borderline_month


class TestComputedTierIntegration:
    def test_precomputed_serves_without_skyfield(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=2026-08-10&calendar=gregorian")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims-computed"
        assert any("Neo MABIMS" in w for w in body["warnings"])

    def test_curated_table_still_wins(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=2024-02-01&calendar=gregorian")
        assert response.status_code == 200
        assert response.json()["source"] == "mabims"

    def test_hijri_direction_from_precomputed(self, computed_client):
        client, _ = computed_client
        expected_g = date(2027, 5, 5)
        h_iso = fake_hijri(expected_g)
        response = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "mabims-computed"
        assert body["output"]["calendar"] == "gregorian"
        assert body["output"]["date"] == expected_g.isoformat()

    def test_borderline_warning_from_file_meta(self, computed_client):
        client, borderline_month = computed_client
        response = client.get("/api/v1/convert?date=2026-08-10&calendar=gregorian")
        assert response.status_code == 200
        warnings = response.json()["warnings"]
        assert any(borderline_month in w and "threshold" in w for w in warnings)

    def test_meta_merges_precomputed_labels(self, computed_client):
        client, _ = computed_client
        meta = client.get("/api/v1/meta").json()
        assert meta["method"] == "neo-mabims-sabang"
        assert meta["computed_active"] is True
        assert any(label.startswith("precomputed:") for label in meta["computed_months"])


def _synthetic_month_pairs() -> dict[str, str]:
    h2g: dict[str, str] = {}
    starts_lengths = [
        ((1441, 5), date(2020, 1, 1), 30),
        ((1441, 6), date(2020, 1, 31), 29),
        ((1441, 7), date(2020, 2, 29), 30),
    ]
    for (hy, hm), start, length in starts_lengths:
        for day in range(length):
            g_iso = date.fromordinal(start.toordinal() + day).isoformat()
            h2g[f"{hy:04d}-{hm:02d}-{day + 1:02d}"] = g_iso
    return h2g


class TestSeededLazyWalk:
    def test_seed_walks_from_file_edge_not_anchor(self):
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        h2g = _synthetic_month_pairs()

        provider.seed_from_pairs(h2g)
        pairs = provider.fetch_by_gregorian(2019, 12)

        assert max(pairs) == "2019-12-31"
        last_h = pairs["2019-12-31"]
        assert last_h.startswith("1441-04-")
        assert h2g["1441-05-01"] == "2020-01-01"
        month_days = sum(1 for h in set(pairs.values()) if h[0:7] == "1441-04")
        assert int(last_h[-2:]) == month_days

    def test_seed_is_idempotent(self):
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        h2g = _synthetic_month_pairs()
        provider.seed_from_pairs(h2g)
        snapshot_before = len(provider._g2h)
        provider.seed_from_pairs(h2g)
        assert len(provider._g2h) == snapshot_before

    def test_non_contiguous_seed_rejected(self):
        provider = MabimsCalcProvider((1445, 7), date(2024, 1, 13))
        h2g = _synthetic_month_pairs()
        del h2g["1441-06-15"]
        with pytest.raises(ValueError):
            provider.seed_from_pairs(h2g)


class TestSupportedRangeCap:
    def test_gregorian_below_floor_rejected(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=1944-12-31&calendar=gregorian")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"

    def test_gregorian_above_ceiling_rejected(self, computed_client):
        client, _ = computed_client
        ceiling = (date.today().year + 31, 1, 1)
        response = client.get(f"/api/v1/convert?date={ceiling[0]}-{ceiling[1]:02d}-01&calendar=gregorian")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"

    def test_gregorian_inside_range_accepted(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=1997-01-20&calendar=gregorian")
        assert response.status_code == 200

    def test_hijri_far_future_rejected(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=1700-01-01&calendar=hijri")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"

    def test_hijri_far_past_rejected(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/convert?date=1000-01-01&calendar=hijri")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"

    def test_range_endpoint_capped(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/range?start=1940-01-01&end=1940-01-05&calendar=gregorian")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"

    def test_month_endpoint_capped(self, computed_client):
        client, _ = computed_client
        response = client.get("/api/v1/month?year=1940&month=5&calendar=gregorian")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "date_out_of_supported_range"
