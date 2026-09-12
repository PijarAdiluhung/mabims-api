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


# ── Month grids ───────────────────────────────────────────────────────────


def test_curated_month_length_matches_table(client, real_data):
    g2h = real_data["gregorian_to_hijri"]
    month_starts = sorted(
        (g, h) for g, h in g2h.items() if h.endswith("-01")
    )
    failures = []
    for i in range(len(month_starts) - 1):
        g_start, h_start = month_starts[i]
        g_next, h_next = month_starts[i + 1]
        expected_days = (date_fromiso(g_next) - date_fromiso(g_start)).days
        year, month = int(h_start[:4]), int(h_start[5:7])
        r = client.get(
            f"/api/v1/month?year={year}&month={month}&calendar=hijri"
        )
        if r.status_code != 200:
            failures.append(f"{h_start}: HTTP {r.status_code}")
            continue
        actual = r.json()["count"]
        if actual != expected_days:
            failures.append(f"{h_start}: expected {expected_days}, got {actual}")
    assert not failures, "Month length mismatches:\n" + "\n".join(failures)


def test_gregorian_month_has_all_days(client):
    r = client.get("/api/v1/month?year=2025&month=2&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 28
    days = [item["gregorian"] for item in body["items"]]
    assert days == sorted(days)
    for day in range(1, 29):
        expected = f"2025-02-{day:02d}"
        assert expected in days, f"Missing {expected}"


def test_gregorian_month_31_days(client):
    r = client.get("/api/v1/month?year=2025&month=1&calendar=gregorian")
    assert r.status_code == 200
    assert r.json()["count"] == 31


def test_hijri_month_days_are_sorted(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    sample_h = sorted(h2g.keys())[500]
    year, month = int(sample_h[:4]), int(sample_h[5:7])
    r = client.get(f"/api/v1/month?year={year}&month={month}&calendar=hijri")
    assert r.status_code == 200
    gregorians = [item["gregorian"] for item in r.json()["items"]]
    assert gregorians == sorted(gregorians)


def test_hijri_month_source_consistency(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    sample_h = sorted(h2g.keys())[500]
    year, month = int(sample_h[:4]), int(sample_h[5:7])
    r = client.get(f"/api/v1/month?year={year}&month={month}&calendar=hijri")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["source"] == "mabims"


def test_month_invalid_month(client):
    r = client.get("/api/v1/month?year=2025&month=13&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_month"


def test_month_zero_month(client):
    r = client.get("/api/v1/month?year=2025&month=0&calendar=gregorian")
    assert r.status_code == 400


def test_month_invalid_year(client):
    r = client.get("/api/v1/month?year=0&month=1&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_year"


# ── Year grids ────────────────────────────────────────────────────────────


def test_gregorian_year_365_days(client):
    r = client.get("/api/v1/year?year=2025&calendar=gregorian")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 365
    assert len(body["months"]) == 12


def test_gregorian_year_leap_366_days(client):
    r = client.get("/api/v1/year?year=2024&calendar=gregorian")
    assert r.status_code == 200
    assert r.json()["count"] == 366


def test_year_matches_12_month_calls(client):
    r_year = client.get("/api/v1/year?year=2025&calendar=gregorian")
    assert r_year.status_code == 200
    year_body = r_year.json()
    for m in range(1, 13):
        r_month = client.get(f"/api/v1/month?year=2025&month={m}&calendar=gregorian")
        assert r_month.status_code == 200
        assert r_month.json()["items"] == year_body["months"][str(m)]


def test_hijri_year_has_12_months(client):
    r = client.get("/api/v1/year?year=1446&calendar=hijri")
    assert r.status_code == 200
    body = r.json()
    assert len(body["months"]) == 12
    for m in range(1, 13):
        assert str(m) in body["months"]
        assert len(body["months"][str(m)]) > 0


def test_year_all_months_present(client):
    r = client.get("/api/v1/year?year=2025&calendar=gregorian")
    assert r.status_code == 200
    months = r.json()["months"]
    for m in range(1, 13):
        assert str(m) in months
        assert len(months[str(m)]) > 0


# ── Ranges ────────────────────────────────────────────────────────────────


def test_range_returns_exact_day_count(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-01-31&calendar=gregorian")
    assert r.status_code == 200
    assert r.json()["count"] == 31
    assert len(r.json()["items"]) == 31


def test_range_dates_are_consecutive(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-01-10&calendar=gregorian")
    assert r.status_code == 200
    dates = [item["gregorian"] for item in r.json()["items"]]
    for i in range(1, len(dates)):
        from datetime import date

        d1 = date.fromisoformat(dates[i - 1])
        d2 = date.fromisoformat(dates[i])
        assert (d2 - d1).days == 1, f"{dates[i-1]} to {dates[i]} not consecutive"


def test_range_too_large(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-03-01&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "range_too_large"


def test_range_start_after_end(client):
    r = client.get("/api/v1/range?start=2025-01-31&end=2025-01-01&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_range"


def test_hijri_range_works(client, real_data):
    h2g = real_data["hijri_to_gregorian"]
    first_h = min(h2g.keys())
    year, month = int(first_h[:4]), int(first_h[5:7])
    r = client.get(
        f"/api/v1/month?year={year}&month={month}&calendar=hijri"
    )
    assert r.status_code == 200
    items = r.json()["items"]
    if len(items) >= 2:
        start = items[0]["hijri"]
        end = items[-1]["hijri"]
        r2 = client.get(
            f"/api/v1/range?start={start}&end={end}&calendar=hijri"
        )
        assert r2.status_code == 200
        assert r2.json()["count"] == len(items)


# ── Helpers ───────────────────────────────────────────────────────────────


def date_fromiso(s: str):
    from datetime import date

    return date.fromisoformat(s)
