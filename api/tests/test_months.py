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


def test_months_returns_12(client):
    r = client.get("/api/v1/months")
    assert r.status_code == 200
    body = r.json()
    assert len(body["months"]) == 12
    numbers = [m["number"] for m in body["months"]]
    assert numbers == list(range(1, 13))


def test_months_names_are_indonesian(client):
    r = client.get("/api/v1/months")
    names = {m["number"]: m["name"] for m in r.json()["months"]}
    assert names[1] == "Muharram"
    assert names[9] == "Ramadhan"
    assert names[12] == "Dzulhijjah"


def test_months_is_rate_exempt():
    c = TestClient(
        create_app(settings=Settings(
            allowed_origins=["*"],
            rate_limit="1/minute",
            enable_fallback=False,
            enable_computed=False,
        )),
        raise_server_exceptions=False,
    )
    r1 = c.get("/api/v1/months")
    assert r1.status_code == 200
    r2 = c.get("/api/v1/months")
    assert r2.status_code == 200


def test_months_cache_immutable(client):
    r = client.get("/api/v1/months")
    cc = r.headers["cache-control"]
    assert "max-age=86400" in cc
    assert "s-maxage=86400" in cc
