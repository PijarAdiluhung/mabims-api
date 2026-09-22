from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _make_client(**settings_kwargs) -> TestClient:
    defaults = dict(
        allowed_origins=["*"],
        rate_limit="10000/minute",
        enable_fallback=False,
        enable_computed=False,
    )
    defaults.update(settings_kwargs)
    return TestClient(create_app(settings=Settings(**defaults)), raise_server_exceptions=False)


def test_wildcard_allows_any_origin():
    c = _make_client(allowed_origins=["*"])
    r = c.get("/api/v1/today", headers={"Origin": "https://evil.com"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


def test_rejected_origin_returns_403():
    c = _make_client(allowed_origins=["https://good.com"])
    r = c.get("/api/v1/today", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden_origin"


def test_origin_suffix_matches():
    c = _make_client(
        allowed_origins=[],
        origin_suffixes=["malangmengaji.com"],
    )
    r = c.get("/api/v1/today", headers={"Origin": "https://sub.malangmengaji.com"})
    assert r.status_code == 200


def test_origin_suffix_no_match():
    c = _make_client(
        allowed_origins=[],
        origin_suffixes=["malangmengaji.com"],
    )
    r = c.get("/api/v1/today", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403


def test_origin_exact_match():
    c = _make_client(allowed_origins=["https://exact.com"])
    r = c.get("/api/v1/today", headers={"Origin": "https://exact.com"})
    assert r.status_code == 200


def test_no_origin_header_passes():
    c = _make_client(allowed_origins=["https://only.com"])
    r = c.get("/api/v1/today")
    assert r.status_code == 200


def test_options_preflight_returns_204():
    c = _make_client(allowed_origins=["*"])
    r = c.options(
        "/api/v1/today",
        headers={
            "Origin": "https://any.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code == 204
    assert "access-control-allow-origin" in r.headers


def test_cors_headers_present_on_success():
    c = _make_client(allowed_origins=["*"])
    r = c.get("/api/v1/today")
    assert r.status_code == 200
    assert "access-control-allow-origin" in r.headers
    assert "access-control-allow-methods" in r.headers
    assert "access-control-allow-headers" in r.headers


def test_forbidden_origin_has_cors_headers():
    c = _make_client(allowed_origins=["https://good.com"])
    r = c.get("/api/v1/today", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403
    assert "access-control-allow-origin" in r.headers
