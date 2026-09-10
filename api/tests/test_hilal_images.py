from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.hilal import images
from app.main import create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("MABIMS_IMAGES_DIR", str(tmp_path))
    app = create_app(
        settings=Settings(
            data_dir=DATA_PATH.parent,
            allowed_origins=["*"],
            rate_limit="10000/minute",
            enable_computed=False,
            enable_fallback=False,
        )
    )
    return TestClient(app)


def test_store_and_lookup(tmp_path, monkeypatch):
    monkeypatch.setenv("MABIMS_IMAGES_DIR", str(tmp_path))
    assert images.image_path("map", 1460, 1) is None  # outside the bundled core
    images.store("map", 1460, 1, _png())
    found = images.image_path("map", 1460, 1)
    assert found is not None
    assert found.read_bytes()[:8] == PNG_SIG


def test_map_served_from_bundle_without_render(client, monkeypatch):
    monkeypatch.setattr(
        "app.main._map_png_cached", lambda *a, **k: pytest.fail("cache hit should not render")
    )
    response = client.get("/api/v1/hilal/map?month=1&year=1445")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["Cache-Control"].startswith("public")
    assert response.content[:8] == PNG_SIG


def test_viz_served_from_bundle_without_render(client, monkeypatch):
    monkeypatch.setattr(
        "app.main._render_viz_png", lambda *a, **k: pytest.fail("cache hit should not render")
    )
    response = client.get("/api/v1/hilal/viz?month=1&year=1445")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == PNG_SIG


def test_meta_exposes_image_range(client):
    body = client.get("/api/v1/meta").json()
    assert body["hilal_image_range"] == [1445, 1455]
