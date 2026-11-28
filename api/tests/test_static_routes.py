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


def test_robots_txt_is_served(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert r.text.strip().splitlines() == ["User-agent: *", "Disallow: /api/"]


def test_robots_txt_leaves_playground_crawlable(client):
    r = client.get("/robots.txt")
    disallowed = [
        line.split(":", 1)[1].strip()
        for line in r.text.splitlines()
        if line.lower().startswith("disallow:")
    ]
    assert all(not "/playground".startswith(prefix) for prefix in disallowed)


def test_robots_txt_is_cacheable(client):
    r = client.get("/robots.txt")
    assert "max-age=86400" in r.headers["cache-control"]


def test_robots_txt_head_has_no_body(client):
    r = client.head("/robots.txt")
    assert r.status_code == 200
    assert r.content == b""


def test_root_redirects_to_playground(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/playground"


def test_root_head_redirects(client):
    r = client.head("/", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/playground"


def test_root_redirect_lands_on_a_200(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "scalar" in r.text.lower()


def test_new_routes_do_not_shadow_api(client):
    r = client.get("/api/v1/today")
    assert r.status_code == 200
    assert "output" in r.json()
