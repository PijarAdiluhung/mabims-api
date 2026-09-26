from __future__ import annotations

import shutil
import sqlite3
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from app.hilal import astrocache
from app.mabims_sites import sites25_kinds

EVENING = date(2026, 2, 17)
STALE_FP_KIND = "sites25:deadbeef00:alt"  # a fingerprint we no longer query


@pytest.fixture(autouse=True)
def _fresh_refresh_state(monkeypatch):
    monkeypatch.setattr(astrocache, "_last_refresh_at", 0.0)
    monkeypatch.setattr(astrocache, "_fp_refetch_exhausted", False)
    monkeypatch.setattr(astrocache, "_size_refetch_exhausted", False)
    astrocache._read_conn.cache_clear()
    astrocache._write_conn_cache.clear()


def _write_artifact(path: Path, kinds, width: int = 25) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE astro ("
        " evening TEXT NOT NULL, kind TEXT NOT NULL, ephem TEXT NOT NULL,"
        " dtype TEXT NOT NULL, shape TEXT NOT NULL, data BLOB NOT NULL,"
        " PRIMARY KEY (evening, kind, ephem))"
    )
    for i, kind in enumerate(kinds):
        payload = np.full(width, i + 1.0, dtype=np.float64)
        conn.execute(
            "INSERT INTO astro VALUES (?,?,?,?,?,?)",
            (
                EVENING.isoformat(),
                kind,
                astrocache.EPHEM_TAG,
                payload.dtype.str,
                str(width),
                payload.tobytes(),
            ),
        )
    conn.commit()
    conn.close()


def _point_at_stale_local(tmp_path, monkeypatch) -> tuple[Path, Path]:
    """Local artifact keyed by an old fingerprint, published one keyed by ours."""
    local = tmp_path / "astro.sqlite"
    published = tmp_path / "published.sqlite"
    _write_artifact(local, [STALE_FP_KIND])
    _write_artifact(published, sites25_kinds())
    monkeypatch.setenv("MABIMS_ASTROCACHE", str(local))
    monkeypatch.setenv("MABIMS_ASTROCACHE_REFRESH", "1")
    return local, published


def _install_published_copy(monkeypatch, local: Path, published: Path) -> list[Path]:
    downloads: list[Path] = []

    def fake_download() -> bool:
        downloads.append(local)
        shutil.copyfile(published, local)
        return True

    monkeypatch.setattr(astrocache, "_download_once", fake_download)
    return downloads


def test_stale_site_geometry_is_refetched_without_a_redeploy(tmp_path, monkeypatch):
    """A site-list rename must not strand running containers on dead rows."""
    local, published = _point_at_stale_local(tmp_path, monkeypatch)
    downloads = _install_published_copy(monkeypatch, local, published)
    monkeypatch.setattr(astrocache, "_remote_size", lambda *a, **k: published.stat().st_size)

    assert not astrocache._local_covers_sites(local)
    astrocache._refresh_if_stale()
    assert downloads == [local]
    assert astrocache._local_covers_sites(local)


def test_load_serves_the_downloaded_artifact(tmp_path, monkeypatch):
    """End to end: the next read uses the published rows, no volume reset."""
    local, published = _point_at_stale_local(tmp_path, monkeypatch)
    downloads = _install_published_copy(monkeypatch, local, published)
    monkeypatch.setattr(astrocache, "_remote_size", lambda *a, **k: published.stat().st_size)

    arr = astrocache.load(EVENING, sites25_kinds()[0])
    assert downloads == [local], "the stale local file must be replaced first"
    assert arr is not None
    assert arr[0] == 1.0


def test_current_artifact_is_left_alone(tmp_path, monkeypatch):
    local = tmp_path / "astro.sqlite"
    _write_artifact(local, sites25_kinds())
    monkeypatch.setenv("MABIMS_ASTROCACHE", str(local))
    monkeypatch.setenv("MABIMS_ASTROCACHE_REFRESH", "1")
    sizes: list[int] = []
    downloads: list[Path] = []

    def fake_download() -> bool:
        downloads.append(local)
        return True

    def fake_size(*_args, **_kwargs) -> int:
        sizes.append(local.stat().st_size)
        return local.stat().st_size

    monkeypatch.setattr(astrocache, "_download_once", fake_download)
    monkeypatch.setattr(astrocache, "_remote_size", fake_size)

    astrocache._refresh_if_stale()
    assert sizes and downloads == [], "matching size and geometry must not re-download"


def test_size_change_alone_triggers_a_refresh(tmp_path, monkeypatch):
    """Re-priming under an unchanged site list is picked up too."""
    local = tmp_path / "astro.sqlite"
    published = tmp_path / "published.sqlite"
    _write_artifact(local, sites25_kinds())
    _write_artifact(published, [*sites25_kinds(), "map_points:alt"], width=2000)
    monkeypatch.setenv("MABIMS_ASTROCACHE", str(local))
    monkeypatch.setenv("MABIMS_ASTROCACHE_REFRESH", "1")
    downloads = _install_published_copy(monkeypatch, local, published)
    monkeypatch.setattr(astrocache, "_remote_size", lambda *a, **k: published.stat().st_size)

    astrocache._refresh_if_stale()
    assert downloads == [local]
    assert local.stat().st_size == published.stat().st_size


def test_zero_byte_artifact_is_replaced(tmp_path, monkeypatch):
    local = tmp_path / "astro.sqlite"
    published = tmp_path / "published.sqlite"
    local.write_bytes(b"")
    _write_artifact(published, sites25_kinds())
    monkeypatch.setenv("MABIMS_ASTROCACHE", str(local))
    monkeypatch.setenv("MABIMS_ASTROCACHE_REFRESH", "1")
    downloads = _install_published_copy(monkeypatch, local, published)
    monkeypatch.setattr(astrocache, "_remote_size", lambda *a, **k: published.stat().st_size)

    astrocache._refresh_if_stale()
    assert downloads == [local]
    assert astrocache._local_covers_sites(local)


def test_unreachable_cdn_keeps_the_local_file(tmp_path, monkeypatch):
    local, _published = _point_at_stale_local(tmp_path, monkeypatch)
    before = local.read_bytes()
    monkeypatch.setattr(astrocache, "_remote_size", lambda *a, **k: None)

    def fail_download() -> bool:
        return False

    monkeypatch.setattr(astrocache, "_download_once", fail_download)

    astrocache._refresh_if_stale()  # silent by design
    assert local.read_bytes() == before
    assert not astrocache._fp_refetch_exhausted, "a failed fetch may be retried later"


def test_refresh_attempts_are_rate_limited(tmp_path, monkeypatch):
    local, published = _point_at_stale_local(tmp_path, monkeypatch)
    downloads = _install_published_copy(monkeypatch, local, published)
    sizes: list[int] = []

    def fake_size(*_args, **_kwargs) -> int:
        sizes.append(0)
        return published.stat().st_size

    monkeypatch.setattr(astrocache, "_remote_size", fake_size)

    astrocache._refresh_if_stale()
    astrocache._refresh_if_stale()
    assert len(sizes) == 1
    assert downloads == [local]


def test_refresh_is_off_by_default(tmp_path, monkeypatch):
    """CI and the prime script must never reach for the network."""
    local, _published = _point_at_stale_local(tmp_path, monkeypatch)
    monkeypatch.delenv("MABIMS_ASTROCACHE_REFRESH")

    def boom(*_args, **_kwargs) -> int:
        raise AssertionError("refresh must be opt-in")

    monkeypatch.setattr(astrocache, "_remote_size", boom)
    astrocache._refresh_if_stale()
    assert not astrocache._local_covers_sites(local)
