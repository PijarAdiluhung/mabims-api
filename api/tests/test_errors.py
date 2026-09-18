from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    settings = Settings(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    return TestClient(create_app(settings=settings))


def test_invalid_date_format(client):
    r = client.get("/api/v1/convert?date=not-a-date&calendar=gregorian")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "invalid_date"
    assert "message" in body["error"]


def test_invalid_calendar_value(client):
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=lunar")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_calendar"


def test_missing_date_param(client):
    r = client.get("/api/v1/convert")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"


def test_invalid_timezone(client):
    r = client.get("/api/v1/today?tz=Not/AZone")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_timezone"


def test_retro_aliases_accepted(client):
    # Decision: boolean flags accept true/false (any case) and 1/0.
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=1")
    assert r.status_code == 200
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=0")
    assert r.status_code == 200
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=TRUE")
    assert r.status_code == 200


def test_invalid_retro_value(client):
    r = client.get("/api/v1/convert?date=2025-01-01&calendar=gregorian&retro=maybe")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "invalid_retro"
    assert body["error"]["message"] == "'retro' must be 'true' or 'false'."


def test_invalid_step_value(client):
    r = client.get("/api/v1/range?start=2025-01-01&end=2025-01-10&step=week")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_step"


def test_date_out_of_supported_range_before(client):
    r = client.get("/api/v1/convert?date=1900-01-01&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "date_out_of_supported_range"


def test_error_shape_is_consistent(client):
    r = client.get("/api/v1/convert?date=bad&calendar=gregorian")
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert isinstance(body["error"], dict)
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert isinstance(body["error"]["code"], str)
    assert isinstance(body["error"]["message"], str)


def test_events_invalid_calendar(client):
    r = client.get("/api/v1/events?year=1446&calendar=julian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_calendar"


def test_events_invalid_year(client):
    r = client.get("/api/v1/events?year=999&calendar=gregorian")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_year"


def test_int_params_not_leaking_422(client):
    r = client.get("/api/v1/month?year=1446&month=abc")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_month"

    r = client.get("/api/v1/month?year=abc&month=3")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_year"


def test_missing_required_params_envelope(client):
    r = client.get("/api/v1/month")
    assert r.status_code == 400
    body = r.json()
    assert body["error"]["code"] == "missing_parameter"
    assert "year" in body["error"]["message"]

    r = client.get("/api/v1/events")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "missing_parameter"


def test_unknown_path_envelope(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert "message" in body["error"]


def test_invalid_bare_flag_envelope(client):
    r = client.get("/api/v1/hilal/viz?month=8&year=1446&bare=maybe")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_bare"


def test_date_whitespace_strict(client):
    r = client.get("/api/v1/convert", params={"date": " 2025-01-03"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_date"

    r = client.get(
        "/api/v1/convert", params={"date": " 2025-01-03", "calendar": "hijri"}
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "invalid_date"


def test_etag_conditional_304(client):
    r1 = client.get("/api/v1/convert?date=2025-01-03")
    assert r1.status_code == 200
    etag = r1.headers["etag"]
    r2 = client.get("/api/v1/convert?date=2025-01-03", headers={"if-none-match": etag})
    assert r2.status_code == 304
    assert r2.content == b""
    assert r2.headers.get("etag") == etag
    assert "cache-control" in r2.headers


def test_etag_mismatch_returns_200(client):
    r = client.get("/api/v1/convert?date=2025-01-03", headers={"if-none-match": '"nope"'})
    assert r.status_code == 200


def test_star_notation_hits_304(client):
    r = client.get("/api/v1/meta", headers={"if-none-match": "*"})
    assert r.status_code == 304


def test_rate_limit_uses_error_envelope():
    settings = Settings(
        rate_limit="1/minute",
        allowed_origins=["*"],
        enable_fallback=False,
        enable_computed=False,
    )
    c = TestClient(create_app(settings=settings), raise_server_exceptions=False)
    first = c.get("/api/v1/convert?date=2025-01-03")
    assert first.status_code == 200
    limited = c.get("/api/v1/convert?date=2025-01-03")
    assert limited.status_code == 429
    body = limited.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
    retry = limited.headers.get("retry-after")
    assert retry is not None
    assert int(retry) >= 1
