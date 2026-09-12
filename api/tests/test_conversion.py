from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"


@pytest.fixture(scope="module")
def real_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


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
def computed_client():
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    return TestClient(create_app(settings=settings))


# ── Curated table: Gregorian → Hijri ──────────────────────────────────────


def test_gregorian_to_hijri_every_date_in_table(client, real_data):
    g2h = real_data["gregorian_to_hijri"]
    failures = []
    for g_iso, expected_h in g2h.items():
        r = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        if r.status_code != 200:
            failures.append(f"{g_iso}: HTTP {r.status_code}")
            continue
        actual_h = r.json()["output"]["date"]
        if actual_h != expected_h:
            failures.append(f"{g_iso}: expected {expected_h}, got {actual_h}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:20])


def test_gregorian_to_hijri_source_is_mabims(client, real_data):
    g2h = real_data["gregorian_to_hijri"]
    sample = list(g2h.items())[::100]
    for g_iso, _ in sample:
        r = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        body = r.json()
        assert body["source"] == "mabims", f"{g_iso}: source={body['source']}"
        assert body["warnings"] == [], f"{g_iso}: warnings={body['warnings']}"


def test_convert_output_contains_day_month_year(client):
    r = client.get("/api/v1/convert?date=2025-03-01&calendar=gregorian")
    assert r.status_code == 200
    out = r.json()["output"]
    assert out["date"] == "1446-09-01"
    assert out["calendar"] == "hijri"
    assert out["day"] == 1
    assert out["month"] == 9
    assert out["year"] == 1446


# ── Curated table: Hijri → Gregorian ──────────────────────────────────────


def test_hijri_to_gregorian_every_date_in_table(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    failures = []
    for h_iso, expected_g in h2g.items():
        r = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
        if r.status_code != 200:
            failures.append(f"{h_iso}: HTTP {r.status_code}")
            continue
        actual_g = r.json()["output"]["date"]
        if actual_g != expected_g:
            failures.append(f"{h_iso}: expected {expected_g}, got {actual_g}")
    assert not failures, f"{len(failures)} mismatches:\n" + "\n".join(failures[:20])


def test_hijri_to_gregorian_source_is_mabims(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    sample = list(h2g.items())[::100]
    for h_iso, _ in sample:
        r = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
        body = r.json()
        assert body["source"] == "mabims", f"{h_iso}: source={body['source']}"
        assert body["warnings"] == [], f"{h_iso}: warnings={body['warnings']}"


# ── Roundtrips ────────────────────────────────────────────────────────────


def test_roundtrip_gregorian_hijri_gregorian(client, real_data):
    g2h = real_data["gregorian_to_hijri"]
    sample = list(g2h.items())[::200]
    failures = []
    for g_iso, _ in sample:
        r1 = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        h_iso = r1.json()["output"]["date"]
        r2 = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
        back = r2.json()["output"]["date"]
        if back != g_iso:
            failures.append(f"{g_iso} → {h_iso} → {back}")
    assert not failures, "Roundtrip failures:\n" + "\n".join(failures)


def test_roundtrip_hijri_gregorian_hijri(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    sample = list(h2g.items())[::200]
    failures = []
    for h_iso, _ in sample:
        r1 = client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
        g_iso = r1.json()["output"]["date"]
        r2 = client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        back = r2.json()["output"]["date"]
        if back != h_iso:
            failures.append(f"{h_iso} → {g_iso} → {back}")
    assert not failures, "Roundtrip failures:\n" + "\n".join(failures)


# ── Computed tier ─────────────────────────────────────────────────────────


def test_computed_serves_outside_table(computed_client, real_data):
    last_g = max(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    beyond = (date.fromisoformat(last_g) + timedelta(days=30)).isoformat()
    r = computed_client.get(f"/api/v1/convert?date={beyond}&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "mabims-computed"
    assert any("Neo MABIMS" in w for w in body["warnings"])


def test_computed_matches_curated_in_overlap(computed_client, real_data):
    g2h = real_data["gregorian_to_hijri"]
    sample = list(g2h.items())[::300]
    failures = []
    for g_iso, expected_h in sample:
        r = computed_client.get(f"/api/v1/convert?date={g_iso}&calendar=gregorian")
        body = r.json()
        if body["source"] != "mabims":
            failures.append(f"{g_iso}: source={body['source']} instead of mabims")
        if body["output"]["date"] != expected_h:
            failures.append(f"{g_iso}: {body['output']['date']} != {expected_h}")
    assert not failures, "Computed disagree with curated:\n" + "\n".join(failures)


def test_computed_disabled_returns_error(real_data):
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    c = TestClient(create_app(settings=settings))
    last_g = max(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    beyond = (date.fromisoformat(last_g) + timedelta(days=30)).isoformat()
    r = c.get(f"/api/v1/convert?date={beyond}&calendar=gregorian")
    assert r.status_code in (400, 404)
    assert r.json()["error"]["code"] in ("out_of_coverage", "date_not_found")


def test_computed_both_directions(computed_client, real_data):
    last_g = max(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    beyond_g = (date.fromisoformat(last_g) + timedelta(days=60)).isoformat()
    r = computed_client.get(f"/api/v1/convert?date={beyond_g}&calendar=gregorian")
    assert r.status_code == 200
    h_iso = r.json()["output"]["date"]

    r2 = computed_client.get(f"/api/v1/convert?date={h_iso}&calendar=hijri")
    assert r2.status_code == 200
    assert r2.json()["output"]["date"] == beyond_g


# ── Retro tier ────────────────────────────────────────────────────────────


def test_retro_true_unlocks_below_table(real_data):
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    c = TestClient(create_app(settings=settings))
    first_g = min(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    below = (date.fromisoformat(first_g) - timedelta(days=10)).isoformat()
    r = c.get(f"/api/v1/convert?date={below}&calendar=gregorian&retro=true")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "mabims-retro"
    assert any("backwards" in w.lower() or "retro" in w.lower() for w in body["warnings"])


def test_retro_false_same_as_default(real_data):
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    c = TestClient(create_app(settings=settings))
    first_g = min(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    inside = (date.fromisoformat(first_g) + timedelta(days=10)).isoformat()
    r_default = c.get(f"/api/v1/convert?date={inside}&calendar=gregorian")
    r_false = c.get(f"/api/v1/convert?date={inside}&calendar=gregorian&retro=false")
    assert r_default.json()["output"]["date"] == r_false.json()["output"]["date"]
    assert r_default.json()["source"] == r_false.json()["source"]


def test_retro_floor_rejects_1940(real_data):
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    c = TestClient(create_app(settings=settings))
    r = c.get("/api/v1/convert?date=1940-06-01&calendar=gregorian&retro=true")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "date_out_of_supported_range"


def test_retro_hijri_direction(real_data):
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=True,
        enable_computed=True,
    )
    c = TestClient(create_app(settings=settings))
    first_g = min(real_data["gregorian_to_hijri"])
    from datetime import date, timedelta

    below = (date.fromisoformat(first_g) - timedelta(days=30)).isoformat()
    r = c.get(f"/api/v1/convert?date={below}&calendar=gregorian&retro=true")
    assert r.status_code == 200
    h_iso = r.json()["output"]["date"]

    r2 = c.get(f"/api/v1/convert?date={h_iso}&calendar=hijri&retro=true")
    assert r2.status_code == 200
    assert r2.json()["output"]["date"] == below
