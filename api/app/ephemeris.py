"""JPL de440s SPK loading, with repair of an unusable on-disk kernel.

Skyfield only downloads when the path is *absent* (``Loader._assure``).
A zero-byte or truncated ``de440s.bsp`` left behind by a failed fetch
keeps raising ``ValueError: file starts with b'', not "NAIF/DAF" ...`` on
every single load, which took down ``/hilal/info``, ``/hilal/viz`` and
``/hilal/map`` while the rest of the API stayed healthy. Parse failures
therefore delete the file once per process, so the next attempt fetches a
fresh copy instead of parsing the same broken bytes forever.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

log = logging.getLogger("mabims.ephemeris")

EPHEMERIS_FILE = "de440s.bsp"
# The same bytes are published next to the astro cache; JPL's own server is
# slow enough to stall a container build for minutes.
DEFAULT_CDN = "https://mabims-dev.b-cdn.net"

# Pathnames already deleted and retried by this process: a kernel that
# comes back corrupt from the mirror must not trigger a re-download loop
# on every request.
_repaired: set[str] = set()


def _fetch_from_cdn(target: Path, timeout: float = 120.0) -> None:
    """Fetch ``de440s.bsp`` from our CDN, atomically, into ``target``.

    Raises on any failure; callers decide whether to fall back to skyfield's
    built-in source (JPL). Overridable with ``MABIMS_EPHEMERIS_URL``.
    """
    import urllib.request

    base = os.environ.get("MABIMS_EPHEMERIS_URL", DEFAULT_CDN)
    url = f"{base.rstrip('/')}/{EPHEMERIS_FILE}"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "mabims-api"})
        with urllib.request.urlopen(request, timeout=timeout) as response, open(tmp, "wb") as fh:
            while chunk := response.read(1 << 22):
                fh.write(chunk)
        os.replace(tmp, target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


class EphemerisError(RuntimeError):
    """The JPL ephemeris kernel could not be loaded (missing or corrupt)."""


def ephemeris_dir() -> Path:
    """Directory holding ``de440s.bsp`` (``MABIMS_EPHEMERIS_DIR`` or a temp dir)."""
    directory = os.environ.get("MABIMS_EPHEMERIS_DIR")
    path = Path(directory) if directory else Path(tempfile.gettempdir()) / "mabims-ephemeris"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_spk(loader, filename: str = EPHEMERIS_FILE):
    """Open an SPK kernel through ``loader``, repairing a broken file once.

    ``loader`` is a ``skyfield.api.Loader`` instance (or any callable
    mapping a filename to a parsed kernel — tests pass a fake).
    """
    path = ephemeris_dir() / filename
    try:
        return loader(filename)
    except Exception as exc:
        key = str(path)
        if path.is_file() and key not in _repaired:
            _repaired.add(key)
            log.warning("removing unusable ephemeris %s (%s: %s)", path, type(exc).__name__, exc)
            try:
                path.unlink()
            except OSError as unlink_exc:
                raise EphemerisError(
                    f"ephemeris {path} is unusable and could not be replaced: {unlink_exc}"
                ) from exc
            try:
                _fetch_from_cdn(path)
            except Exception as fetch_exc:  # noqa: BLE001 - fall back to JPL below
                log.warning(
                    "CDN refetch of %s failed (%s: %s); falling back to skyfield's source",
                    EPHEMERIS_FILE,
                    type(fetch_exc).__name__,
                    fetch_exc,
                )
            try:
                return loader(filename)
            except Exception as retry_exc:
                raise EphemerisError(
                    f"ephemeris {path} could not be reloaded after repair: {retry_exc}"
                ) from retry_exc
        raise EphemerisError(f"ephemeris {path} could not be loaded: {exc}") from exc
