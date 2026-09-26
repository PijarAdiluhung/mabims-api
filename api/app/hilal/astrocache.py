"""SQLite-backed cache for hilal astronomy math (map card + site model).

Holds **facts keyed by evening date** — numpy blobs produced by the skyfield
passes — never design or verdicts. Mirror of the compute layer:

* ``mapcard._grid``              -> ``mapgrid025:alt`` / ``:elong``
* ``mapcard._compute`` (95 pts)  -> ``map_points:alt`` / ``:elong``
* ``mapcard._global_visibility`` -> ``world3:verdict``
* ``mabims_sites.sightings_on_dates`` -> ``sites25:*`` (alt, elong, moon_az,
  sun_alt, sun_az, sunset_jd)

Reads are always safe (missing file / missing row -> None -> recompute).
Writes are build-time only (``scripts/prime_astro_cache.py``), never the API
runtime, so the committed artifact stays deterministic under deploys. The one
exception is an opt-in re-fetch of the published artifact when the local copy
is stale (``MABIMS_ASTROCACHE_REFRESH=1``, see ``_refresh_if_stale``), which
lets a re-primed sqlite reach running containers without a volume reset.

The ephemeris tag is part of the key: swapping JPL files invalidates old
rows implicitly and old values can never mix with new-model values.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np

EPHEM_TAG = "de440s"
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "hilal_astro.sqlite"
DEFAULT_URL = "https://mabims-dev.b-cdn.net/hilal_astro.sqlite"
# How often a running process re-checks the published artifact (opt-in via
# MABIMS_ASTROCACHE_REFRESH). One cheap HEAD per interval per process.
REFRESH_INTERVAL_S = 6 * 3600

_SCHEMA = """
CREATE TABLE IF NOT EXISTS astro (
  evening TEXT NOT NULL,
  kind    TEXT NOT NULL,
  ephem   TEXT NOT NULL,
  dtype   TEXT NOT NULL,
  shape   TEXT NOT NULL,
  data    BLOB NOT NULL,
  PRIMARY KEY (evening, kind, ephem)
)
"""


def cache_path() -> Path:
    env = os.environ.get("MABIMS_ASTROCACHE")
    if env:
        return Path(env)
    return DEFAULT_PATH


def is_disabled() -> bool:
    return os.environ.get("MABIMS_DISABLE_ASTROCACHE", "") == "1"


def _download_once() -> bool:
    """First-boot fetch of the build artifact, mirroring the ephemeris pattern.

    Streaming to ``<path>.download`` then atomic rename: a failed or
    interrupted download never leaves a half-good sqlite at the live path.
    Silent failure by design — an unavailable URL just means the next
    caller computes live (slow renders, never broken endpoints).
    Returns True only when a new artifact was installed at the live path.
    """
    import urllib.error
    import urllib.request

    url = os.environ.get("MABIMS_ASTROCACHE_URL", DEFAULT_URL)
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".download")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "mabims-api"})
        with urllib.request.urlopen(request, timeout=120) as response, open(tmp, "wb") as fh:
            while chunk := response.read(1 << 22):
                fh.write(chunk)
        os.replace(tmp, path)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        tmp.unlink(missing_ok=True)
        return False


def refresh_enabled() -> bool:
    return os.environ.get("MABIMS_ASTROCACHE_REFRESH", "").lower() in {"1", "true", "yes", "on"}


def _remote_size(timeout: float = 10.0) -> int | None:
    """Published artifact size (Content-Length), or None if unknown/unreachable."""
    import urllib.error
    import urllib.request

    url = os.environ.get("MABIMS_ASTROCACHE_URL", DEFAULT_URL)
    try:
        request = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "mabims-api"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if (response.headers.get("Content-Encoding") or "").lower() not in ("", "identity"):
                return None  # compressed length would never match our raw file
            raw = response.headers.get("Content-Length")
            return int(raw) if raw else None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def _local_covers_sites(path: Path) -> bool:
    """True when the local artifact holds rows for the geometry we query next.

    A corrupt or zero-byte file counts as False, so the refresh below replaces
    an unreadable artifact instead of failing every read until a redeploy.
    """
    from app.mabims_sites import _sites_fingerprint

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5.0)
    except sqlite3.Error:
        return False
    try:
        row = conn.execute(
            "SELECT 1 FROM astro WHERE kind LIKE ? LIMIT 1",
            (f"sites25:{_sites_fingerprint()}:%",),
        ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()


_refresh_lock = threading.Lock()
_last_refresh_at = 0.0
_fp_refetch_exhausted = False
_size_refetch_exhausted = False


def _refresh_if_stale() -> None:
    """Swap in the published artifact when the local one is stale — no redeploy.

    Two independent staleness signals, rate-limited to one attempt per
    ``REFRESH_INTERVAL_S`` per process:

    * the local file carries no rows for the site geometry we are about to
      query (site list changed, file corrupt, artifact never primed), and
    * its size differs from the published artifact's ``Content-Length``
      (re-primed range or priming fix under an unchanged site geometry).

    Failures stay silent: an unreachable artifact means this process keeps
    using what it has and computes live for the rest, never a broken endpoint.
    """
    global _last_refresh_at, _fp_refetch_exhausted, _size_refetch_exhausted

    if not refresh_enabled():
        return
    path = cache_path()
    if not path.is_file():
        return
    now = time.monotonic()
    if now - _last_refresh_at < REFRESH_INTERVAL_S:
        return
    with _refresh_lock:
        if now - _last_refresh_at < REFRESH_INTERVAL_S:
            return
        _last_refresh_at = now
    covers = _local_covers_sites(path)
    remote = _remote_size()
    stale = (not covers and not _fp_refetch_exhausted) or (
        not _size_refetch_exhausted and remote is not None and remote != path.stat().st_size
    )
    if not stale:
        return
    if not _download_once():
        return
    _read_conn.cache_clear()
    _write_conn_cache.clear()
    if not covers and not _local_covers_sites(path):
        # The published artifact has no rows for our geometry either — retrying
        # would re-download the same useless file every interval. Stop; a
        # restart after the upload re-arms the check.
        _fp_refetch_exhausted = True
    if remote is not None and remote != path.stat().st_size:
        # Sizes still disagree after a successful fetch (edge cache serving a
        # different representation, say). Stop comparing sizes for this process
        # instead of re-downloading the artifact forever.
        _size_refetch_exhausted = True


def _ensure_file() -> None:
    if is_disabled():
        return
    if not cache_path().is_file():
        _download_once()
        return
    _refresh_if_stale()


@lru_cache(maxsize=1)
def _read_conn() -> sqlite3.Connection:
    path = cache_path()
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30.0)
    conn.execute("CREATE TABLE IF NOT EXISTS astro AS SELECT 1 WHERE 0")  # harmless if missing
    try:
        conn.execute(
            "SELECT 1 FROM astro LIMIT 1"
        )
    except sqlite3.OperationalError:
        conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _write_conn() -> sqlite3.Connection:
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


_read_lock = threading.Lock()
_write_lock = threading.Lock()
_write_conn_cache: list[sqlite3.Connection] = []


def load(evening: date, kind: str) -> np.ndarray | None:
    """Return the cached array for ``(evening, kind)``, or None on any miss."""
    if is_disabled():
        return None
    _ensure_file()
    if not cache_path().is_file():
        return None
    try:
        conn = _read_conn()
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            "SELECT dtype, shape, data FROM astro WHERE evening=? AND kind=? AND ephem=?",
            (evening.isoformat(), kind, EPHEM_TAG),
        ).fetchone()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return None
    if row is None:
        return None
    shape = tuple(int(x) for x in row[1].split(",")) if row[1].strip() else ()
    with _read_lock:
        return np.frombuffer(row[2], dtype=np.dtype(row[0])).reshape(shape).copy()


def store(evening: date, kind: str, arr: np.ndarray) -> None:
    """Build-time write of one array (prime script / tests)."""
    arr = np.ascontiguousarray(arr)
    if not _write_conn_cache:
        _write_conn_cache.append(_write_conn())
    conn = _write_conn_cache[0]
    with _write_lock:
        conn.execute(
            "INSERT OR REPLACE INTO astro (evening, kind, ephem, dtype, shape, data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                evening.isoformat(),
                kind,
                EPHEM_TAG,
                arr.dtype.str,
                ",".join(str(d) for d in arr.shape),
                arr.tobytes(),
            ),
        )
        conn.commit()


def has(evening: date, kinds: tuple[str, ...]) -> bool:
    return all(load(evening, k) is not None for k in kinds)


def kinds_for(evening: date) -> list[str]:
    """Introspection: kinds present for one evening."""
    _ensure_file()
    if not cache_path().is_file():
        return []
    try:
        conn = _read_conn()
        rows = conn.execute(
            "SELECT kind FROM astro WHERE evening=? AND ephem=?",
            (evening.isoformat(), EPHEM_TAG),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [r[0] for r in rows]
