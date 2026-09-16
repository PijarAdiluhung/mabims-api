from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import scripts.build_calendar_data as bcd
from app.config import Settings
from app.divergences import (
    Divergence,
    as_payload,
    load_divergences,
    table_version,
)
from app.main import create_app
from scripts.apply_flip import plan_flip, verify_diff

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"
SEED_PATH = API_DIR / "data" / "computed_seed.json"

# A real curated month to hang the synthetic override on:
# 1447-09 (Ramadhan) starts 2026-02-19 in the current table.
FLIP_YM = "1447-09"
FLIP_PUBLISHED = "2026-02-19"


@pytest.fixture()
def flipped_dir(tmp_path: Path) -> Path:
    out = tmp_path
    shutil.copy(DATA_PATH, out / "calendar_data.json")
    (out / "divergences.json").write_text(json.dumps({
        "divergences": [{
            "hijri_month": FLIP_YM,
            "published_start": "2026-02-18",
            "official_start": FLIP_PUBLISHED,
            "delta_days": 1,
            "reason": "hilal tidak terlihat",
            "recorded_at": "2026-02-17T19:41:00+07:00",
        }]
    }), encoding="utf-8")
    return out


@pytest.fixture()
def flipped_client(flipped_dir: Path) -> TestClient:
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    # Settings.data_dir is frozen; build a Settings-like namespace via create_app param.
    from dataclasses import replace

    return TestClient(create_app(settings=replace(settings, data_dir=flipped_dir)))


# ── registry loader ───────────────────────────────────────────────────────


def test_load_divergences_empty(tmp_path: Path):
    assert load_divergences(tmp_path) == {}
    assert table_version(tmp_path, {}) == "none"


def test_load_divergences_corrupt_is_silent(tmp_path: Path):
    (tmp_path / "divergences.json").write_text("{not json", encoding="utf-8")
    assert load_divergences(tmp_path) == {}


def test_affected_months_include_prev():
    d = Divergence(
        hijri_month="1447-01", published_start="2025-06-27",
        official_start="2025-06-28", delta_days=1, reason="x", recorded_at="t",
    )
    assert d.affected_months == frozenset({"1447-01", "1446-12"})


def test_warning_text_is_loud():
    d = Divergence(
        hijri_month="1447-09", published_start="2026-02-18",
        official_start="2026-02-19", delta_days=1, reason="hilal tidak terlihat",
        recorded_at="t",
    )
    w = d.warning("Ramadhan")
    assert w.startswith("kemenag_override:")
    assert "2026-02-19" in w and "2026-02-18" in w and "+1" in w


def test_as_payload_newest_first():
    d1 = Divergence("1445-01", "a", "b", 1, "", "2024-01-01T00:00:00+07:00")
    d2 = Divergence("1447-09", "c", "d", -1, "", "2026-02-17T19:41:00+07:00")
    payload = as_payload({"1445-01": d1, "1447-09": d2})
    assert [p["hijri_month"] for p in payload] == ["1447-09", "1445-01"]


# ── API surfacing ─────────────────────────────────────────────────────────


def test_convert_in_flipped_month_warns(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/convert?date=2026-03-01&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "mabims"
    assert any(w.startswith("kemenag_override:") for w in body["warnings"])


def test_convert_in_prev_month_warns(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/convert?date=2026-02-17&calendar=gregorian")
    assert r.status_code == 200
    assert any(w.startswith("kemenag_override:") for w in r.json()["warnings"])


def test_convert_outside_flip_month_is_quiet(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/convert?date=2026-01-05&calendar=gregorian")
    assert r.status_code == 200
    assert not [w for w in r.json()["warnings"] if w.startswith("kemenag_override:")]


def test_hijri_input_also_warns(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/convert?date=1447-09-05&calendar=hijri")
    assert r.status_code == 200
    assert any(w.startswith("kemenag_override:") for w in r.json()["warnings"])


def test_month_endpoint_warns(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/month?year=1447&month=9&calendar=hijri")
    assert r.status_code == 200
    assert any(w.startswith("kemenag_override:") for w in r.json()["warnings"])


def test_meta_exposes_divergences(flipped_client: TestClient):
    r = flipped_client.get("/api/v1/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["table_version"] != "none" and body["table_version"]
    assert len(body["divergences"]) == 1
    assert body["divergences"][0]["hijri_month"] == FLIP_YM


def test_real_repo_has_no_divergences():
    assert load_divergences(API_DIR / "data") == {}


# ── flip planner (pure logic) ─────────────────────────────────────────────


def _starts_dict() -> dict[str, tuple[int, int]]:
    return {k: (y, m) for k, (y, m) in sorted(bcd.MONTH_STARTS.items())}


def test_plan_flip_changes_only_its_anchor():
    # +1 flip needs the sandwich (29, 30): 1444-08 is 29 days, 1444-09 is 30.
    starts = _starts_dict()
    planned, published, delta = plan_flip(starts, 1444, 9, date(2023, 3, 24))
    assert delta == 1 and published.isoformat() == "2023-03-23"
    assert planned["2023-03-24"] == (1444, 9)
    # every other anchor is byte-identical — no cascade
    expected_anchors = dict(starts)
    del expected_anchors["2023-03-23"]
    expected_anchors["2023-03-24"] = (1444, 9)
    assert planned == expected_anchors


def test_plan_flip_negative_delta():
    # -1 flip needs the mirrored sandwich: 1444-09 is 30, 1444-10 is 29.
    starts = _starts_dict()
    planned, published, delta = plan_flip(starts, 1444, 10, date(2023, 4, 21))
    assert delta == -1
    assert planned["2023-04-21"] == (1444, 10)
    expected_anchors = dict(starts)
    del expected_anchors["2023-04-22"]
    expected_anchors["2023-04-21"] = (1444, 10)
    assert planned == expected_anchors


def test_plan_flip_rejections():
    starts = _starts_dict()
    with pytest.raises(ValueError):
        plan_flip(starts, 1444, 9, date(2023, 3, 23))  # delta 0
    with pytest.raises(ValueError):
        plan_flip(starts, 1444, 9, date(2023, 3, 25))  # |delta| > 1
    with pytest.raises(ValueError):
        min_key = min(starts)
        plan_flip(starts, *starts[min_key], date.fromisoformat(min_key))  # first anchor
    with pytest.raises(ValueError):
        plan_flip(starts, 1400, 1, date(2023, 3, 24))  # no such anchor
    # unrepresentable direction: inside a (30, 30) pair (1447-08, 1447-09),
    # a +1 flip would make the previous month 31 days
    with pytest.raises(ValueError):
        plan_flip(starts, 1447, 9, date(2026, 2, 20))
    # same mirrored: (29, 29) pair — 1447-11 cannot take a -1 flip
    with pytest.raises(ValueError):
        plan_flip(starts, 1447, 11, date(2026, 4, 18))


def test_planned_table_builds_and_validates():
    starts = _starts_dict()
    planned, _, delta = plan_flip(starts, 1444, 9, date(2023, 3, 24))
    saved = dict(bcd.MONTH_STARTS)
    try:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(planned)
        g2h, h2g = bcd.build()
        bcd.validate(g2h, h2g)
        verify_diff(
            json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"],
            g2h,
            "1444-09",
            delta,
            date(2023, 3, 24),
        )
    finally:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(saved)


def test_verify_diff_rejects_unplanned_table():
    old = json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"]
    mangled = dict(old)
    mangled["2026-12-31"] = "1448-07-30"  # touch a row outside months F-1/F
    with pytest.raises(AssertionError):
        verify_diff(old, mangled, "1444-09", 1, date(2023, 3, 24))


def test_verify_diff_positive_delta_adds_prev_day30():
    starts = _starts_dict()
    planned, _, delta = plan_flip(starts, 1444, 9, date(2023, 3, 24))
    saved = dict(bcd.MONTH_STARTS)
    try:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(planned)
        g2h, _ = bcd.build()
        # the month before F swallows one day: its day 30 lands on the old F start
        assert g2h.get("2023-03-23") == "1444-08-30"
        verify_diff(
            json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"],
            g2h,
            "1444-09",
            delta,
            date(2023, 3, 24),
        )
    finally:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(saved)


def test_verify_diff_negative_delta_drops_prev_day30():
    starts = _starts_dict()
    planned, _, delta = plan_flip(starts, 1444, 10, date(2023, 4, 21))
    saved = dict(bcd.MONTH_STARTS)
    try:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(planned)
        g2h, _ = bcd.build()
        # the month before F (1444-09, 30 days) loses its day 30; F starts one
        # day earlier and its day 30 appears
        assert g2h.get("2023-04-21") == "1444-10-01"
        assert g2h.get("2023-04-20") == "1444-09-29"
        assert g2h.get("2023-05-20") == "1444-10-30"  # the extended F day 30
        verify_diff(
            json.loads(DATA_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"],
            g2h,
            "1444-10",
            delta,
            date(2023, 4, 21),
        )
    finally:
        bcd.MONTH_STARTS.clear()
        bcd.MONTH_STARTS.update(saved)


def test_seed_data_untouched_by_feature():
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    # sanity: the seed still predicts its own published sequence
    assert raw["gregorian_to_hijri"]
