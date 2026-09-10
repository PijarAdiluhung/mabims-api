"""PNG store for the hilal cards (`/hilal/viz` + `/hilal/map`).

Lookup order:
  1. bundled ``api/data/hilal_images`` (pre-generated, shipped in the image)
  2. writable cache dir — ``MABIMS_IMAGES_DIR`` (default ``/data/hilal_images``
     when the container volume is present, else a temp dir)

Misses are rendered by the caller and written back to the cache dir so a cold
month is only ever rendered once per deployment.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

BUNDLED_DIR = Path(__file__).resolve().parents[2] / "data" / "hilal_images"


def cache_dir() -> Path:
    env = os.environ.get("MABIMS_IMAGES_DIR")
    if env:
        return Path(env)
    volume = Path("/data")
    if volume.is_dir() and os.access(volume, os.W_OK):
        return volume / "hilal_images"
    return Path(tempfile.gettempdir()) / "mabims-images"


def image_path(kind: str, year: int, month: int) -> Path | None:
    """Return an existing PNG for the Hijri ``(year, month)``, or None."""
    name = f"{year:04d}-{month:02d}.png"
    for base in (BUNDLED_DIR, cache_dir()):
        candidate = base / kind / name
        if candidate.is_file():
            return candidate
    return None


def store(kind: str, year: int, month: int, data: bytes) -> None:
    """Best-effort atomic write of a rendered PNG into the cache dir."""
    target = cache_dir() / kind / f"{year:04d}-{month:02d}.png"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, target)
    except OSError:
        pass
