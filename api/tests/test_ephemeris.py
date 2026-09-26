from __future__ import annotations

import pytest

from app import ephemeris
from app.ephemeris import EPHEMERIS_FILE, EphemerisError, ephemeris_dir, load_spk

CORRUPT = ValueError("file starts with b'', not \"NAIF/DAF\" or \"DAF/\"")
_REAL_FETCH_FROM_CDN = ephemeris._fetch_from_cdn


@pytest.fixture(autouse=True)
def _fresh_repair_state(monkeypatch):
    monkeypatch.setattr(ephemeris, "_repaired", set())
    # Tests never fetch the real 31 MB kernel: refuse the CDN so the repair
    # path falls back to the loader (JPL) exactly as the stubs expect.
    def _no_cdn(target, *args, **kwargs):
        raise OSError("tests never fetch the ephemeris")

    monkeypatch.setattr(ephemeris, "_fetch_from_cdn", _no_cdn)


def test_ephemeris_dir_follows_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))
    assert ephemeris_dir() == tmp_path
    assert (tmp_path / EPHEMERIS_FILE).parent.is_dir()


def test_intact_kernel_is_loaded_without_touching_the_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))
    target = tmp_path / EPHEMERIS_FILE
    target.write_bytes(b"NAIF/DAF" + b"\0" * 64)
    calls: list[str] = []

    def loader(name: str) -> str:
        calls.append(name)
        return "kernel"

    assert load_spk(loader) == "kernel"
    assert calls == [EPHEMERIS_FILE]
    assert target.exists()


def test_zero_byte_kernel_is_deleted_and_refetched(tmp_path, monkeypatch):
    """Regression guard for the 2026-09 outage.

    Skyfield only downloads when the path is absent, so a zero-byte
    de440s.bsp raised ``ValueError`` on every load, taking down all three
    hilal endpoints while the rest of the API stayed up.
    """
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))
    target = tmp_path / EPHEMERIS_FILE
    target.write_bytes(b"")
    calls: list[str] = []

    def loader(name: str) -> str:
        calls.append(name)
        if target.exists():
            raise CORRUPT
        return "kernel"

    assert load_spk(loader) == "kernel"
    assert not target.exists()
    assert calls == [EPHEMERIS_FILE, EPHEMERIS_FILE]


def test_repair_is_attempted_once_per_process(tmp_path, monkeypatch):
    """A mirror that keeps serving a broken file must not loop deletes."""
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))
    target = tmp_path / EPHEMERIS_FILE
    calls: list[str] = []

    def loader(name: str) -> str:
        calls.append(name)
        target.write_bytes(b"")
        raise CORRUPT

    with pytest.raises(EphemerisError):
        load_spk(loader)
    first_round = len(calls)
    assert target.exists(), "the replacement file must stay on disk"

    with pytest.raises(EphemerisError):
        load_spk(loader)
    assert len(calls) == first_round + 1, "no second delete-and-refetch cycle"


def test_missing_kernel_download_failure_is_wrapped(tmp_path, monkeypatch):
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))

    def loader(name: str) -> str:
        raise OSError("cannot download de440s.bsp because HTTP Error 404")

    with pytest.raises(EphemerisError) as excinfo:
        load_spk(loader)
    assert isinstance(excinfo.value.__cause__, OSError)
    assert not (tmp_path / EPHEMERIS_FILE).exists()


# ── CDN refetch (MABIMS_EPHEMERIS_URL, served here over file://) ──────────


def test_fetch_from_cdn_stores_the_file_atomically(tmp_path, monkeypatch):
    origin = tmp_path / "origin"
    origin.mkdir()
    payload = b"NAIF/DAF" + b"\0" * 64
    (origin / EPHEMERIS_FILE).write_bytes(payload)
    monkeypatch.setenv("MABIMS_EPHEMERIS_URL", origin.as_uri())
    monkeypatch.setattr(ephemeris, "_fetch_from_cdn", _REAL_FETCH_FROM_CDN)
    target = tmp_path / "ephemeris" / EPHEMERIS_FILE

    ephemeris._fetch_from_cdn(target)

    assert target.read_bytes() == payload
    assert not target.with_suffix(target.suffix + ".part").exists()


def test_fetch_from_cdn_failure_leaves_nothing_behind(tmp_path, monkeypatch):
    monkeypatch.setenv("MABIMS_EPHEMERIS_URL", (tmp_path / "nope").as_uri())
    monkeypatch.setattr(ephemeris, "_fetch_from_cdn", _REAL_FETCH_FROM_CDN)
    target = tmp_path / EPHEMERIS_FILE

    with pytest.raises(OSError):
        ephemeris._fetch_from_cdn(target)

    assert not target.exists()
    assert not target.with_suffix(target.suffix + ".part").exists()


def test_repair_refetches_from_the_cdn_before_the_loader(tmp_path, monkeypatch):
    """A broken kernel is replaced from our CDN, not from JPL."""
    monkeypatch.setenv("MABIMS_EPHEMERIS_DIR", str(tmp_path))
    target = tmp_path / EPHEMERIS_FILE
    target.write_bytes(b"")
    fetched = []

    def fetch(path, *args, **kwargs):
        fetched.append(path)
        path.write_bytes(b"NAIF/DAF" + b"\0" * 64)

    monkeypatch.setattr(ephemeris, "_fetch_from_cdn", fetch)
    calls: list[str] = []

    def loader(name: str) -> str:
        calls.append(name)
        if target.stat().st_size < 16:
            raise CORRUPT
        return "kernel"

    assert load_spk(loader) == "kernel"
    assert fetched == [target]
    assert calls == [EPHEMERIS_FILE, EPHEMERIS_FILE]
