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

# Pathnames already deleted and retried by this process: a kernel that
# comes back corrupt from the mirror must not trigger a re-download loop
# on every request.
_repaired: set[str] = set()


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
                return loader(filename)
            except Exception as retry_exc:
                raise EphemerisError(
                    f"ephemeris {path} could not be reloaded after repair: {retry_exc}"
                ) from retry_exc
        raise EphemerisError(f"ephemeris {path} could not be loaded: {exc}") from exc
