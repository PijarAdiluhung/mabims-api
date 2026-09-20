from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.events import EVENT_DEFINITIONS
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


def _expected_events_for_hijri_year(real_data, year: int):
    h2g = real_data["hijri_to_gregorian"]
    rows = []
    for h_iso, g_iso in h2g.items():
        hy, hm, hd = (int(x) for x in h_iso.split("-"))
        if hy == year:
            for defn in EVENT_DEFINITIONS:
                if hm == defn.month and hd == defn.day:
                    rows.append((g_iso, h_iso, defn.slug))
    return sorted(rows)


def test_events_by_hijri_year_count(client, real_data):
    r = client.get("/api/v1/events?year=1446&calendar=hijri")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5


def test_events_have_correct_hijri_dates(client, real_data):
    r = client.get("/api/v1/events?year=1446&calendar=hijri")
    body = r.json()
    by_slug = {e["event"]: e for e in body["events"]}
    for defn in EVENT_DEFINITIONS:
        assert defn.slug in by_slug, f"Missing event: {defn.slug}"
        hijri = by_slug[defn.slug]["hijri"]
        assert hijri == f"1446-{defn.month:02d}-{defn.day:02d}"


def test_events_match_table(client, real_data):
    expected = _expected_events_for_hijri_year(real_data, 1446)
    r = client.get("/api/v1/events?year=1446&calendar=hijri")
    body = r.json()
    actual = [(e["gregorian"], e["hijri"], e["event"]) for e in body["events"]]
    assert actual == [(g, h, s) for g, h, s in expected]


def test_events_by_gregorian_year_filters(client, real_data):
    r = client.get("/api/v1/events?year=2025&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    for e in body["events"]:
        assert e["gregorian"].startswith("2025")


def test_events_outside_coverage_empty(client):
    r = client.get("/api/v1/events?year=2030&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 0
    assert body["events"] == []
    assert body["warnings"] == []


def test_events_invalid_calendar(client):
    r = client.get("/api/v1/events?year=1446&calendar=julian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_calendar"


def test_events_invalid_year(client):
    r = client.get("/api/v1/events?year=999&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_year"


def test_events_missing_year(client):
    r = client.get("/api/v1/events")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"


def test_events_include_extra(client, real_data):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=extra")
    assert r.status_code == 200
    body = r.json()
    slugs = {e["event"] for e in body["events"]}
    assert slugs == {
        "1_muharram",
        "maulid_nabi",
        "awal_ramadan",
        "idul_fitri",
        "idul_adha",
        "isra_miraj",
        "nuzulul_quran",
        "arafah",
        "tasua",
        "asyura",
        "tasyrik",
    }


def test_events_include_invalid(client):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=bogus")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_include"


def test_events_include_cherry_pick_dedup(client):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=extra,asyura")
    assert r.status_code == 200
    slugs = [e["event"] for e in r.json()["events"]]
    assert slugs.count("asyura") == 1


def test_events_include_echo(client):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=asyura")
    assert r.status_code == 200
    assert set(r.json()["input"]["include"]) == {"asyura"}
    r2 = client.get("/api/v1/events?year=1446&calendar=hijri")
    assert r2.json()["input"]["include"] is None


def test_events_tasyrik_date_range(client, real_data):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=extra")
    assert r.status_code == 200
    tasyrik = next(e for e in r.json()["events"] if e["event"] == "tasyrik")
    assert tasyrik["hijri"] == "1446-12-11"
    dr = tasyrik["date_range"]
    assert dr["hijri_start"] == "1446-12-11"
    assert dr["hijri_end"] == "1446-12-13"
    h2g = real_data["hijri_to_gregorian"]
    assert dr["gregorian_start"] == h2g["1446-12-11"]
    assert dr["gregorian_end"] == h2g["1446-12-13"]
    single = next(e for e in r.json()["events"] if e["event"] == "arafah")
    assert single["date_range"] is None


def test_events_ayyamul_bidh(client, real_data):
    r = client.get("/api/v1/events?year=1446&calendar=hijri&include=ayyamul_bidh")
    assert r.status_code == 200
    body = r.json()
    bidh = [e for e in body["events"] if e["event"] == "ayyamul_bidh"]
    assert len(bidh) == 12
    months = sorted(e["hijri"][5:7] for e in bidh)
    assert months == [f"{m:02d}" for m in range(1, 13)]
    sample = bidh[0]
    assert sample["date_range"]["hijri_end"] == f"{sample['hijri'][:7]}-15"
    imp = client.get("/api/v1/events?year=1446&calendar=hijri")
    assert all(e["event"] != "ayyamul_bidh" for e in imp.json()["events"])


def test_events_ayyamul_bidh_gregorian(client, real_data):
    r = client.get("/api/v1/events?year=2025&calendar=gregorian&include=ayyamul_bidh")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    for e in body["events"]:
        assert e["gregorian"].startswith("2025")
