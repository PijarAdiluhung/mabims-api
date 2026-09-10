from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.hilal import mapcard
from app.main import create_app

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "calendar_data.json"
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _tiny_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (720, 1280), (0, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def client(monkeypatch):
    app = create_app(
        settings=Settings(
            data_dir=DATA_PATH.parent,
            allowed_origins=["*"],
            rate_limit="10000/minute",
            enable_computed=False,
            enable_fallback=False,
        )
    )
    # The real render is ~20 s; the endpoint contract is what matters here.
    monkeypatch.setattr("app.main._map_png_cached", lambda *a, **k: _tiny_png())
    return TestClient(app)


def test_hilal_map_png(client):
    response = client.get("/api/v1/hilal/map?month=1&year=1448")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["Cache-Control"].startswith("public")
    assert response.content[:8] == PNG_SIG


def test_hilal_map_invalid_month(client):
    response = client.get("/api/v1/hilal/map?month=13&year=1448")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "out_of_coverage"


def test_hilal_map_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/hilal/map" in paths


def test_map_points_frozen():
    pts = mapcard._points()
    assert len(pts) == 95
    names = {p[0] for p in pts}
    for expected in ("Sabang (Weh Island)", "Jakarta", "Semarang", "Surabaya"):
        assert expected in names


def test_sign_and_header_formatting():
    from app.hilal.chart import _fmt_alt, _fmt_elong, _header_title

    assert _fmt_alt(4.0) == "+4.0\u00b0"
    assert _fmt_alt(-0.8) == "-0.8\u00b0"  # never "+-0.8°"
    assert _fmt_elong(5.2) == "5.2\u00b0"  # elongation is always positive
    assert _header_title("Jumadil Akhir") == "Visibilitas JUMADIL AKHIR"


def test_map_png_bytes_render_and_determinism():
    hero = ("Sabang / Weh Island", 5.8897, 95.3164, 4.0, 7.0)
    png = mapcard.map_png_bytes(
        evening=date(2026, 6, 15),
        vis_month="MUHARRAM",
        vis_year=1448,
        hijri_label="29 Dzulhijjah 1447 H",
        hero=hero,
        grid_deg=2.0,  # coarse grid keeps the test fast
    )
    assert png[:8] == PNG_SIG
    assert Image.open(io.BytesIO(png)).size == (720, 1280)
    again = mapcard.map_png_bytes(
        evening=date(2026, 6, 15),
        vis_month="MUHARRAM",
        vis_year=1448,
        hijri_label="29 Dzulhijjah 1447 H",
        hero=hero,
        grid_deg=2.0,
    )
    assert png == again
