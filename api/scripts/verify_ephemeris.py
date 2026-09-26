"""Fail the image build when de440s.bsp is missing, truncated or unusable.

Skyfield *opens* a truncated SPK without complaint: the damage only shows up
mid-request inside jplephem as ``TypeError: buffer is too small for requested
array``, which prod served as ``computation_unavailable`` on /hilal/*. The
Docker build therefore has to prove the kernel computes before it ships.

Two modes:

``--no-download``
    Validate whatever is on disk, never touch the network. Used first so an
    existing bad kernel is detected, deleted and refetched by the caller.

default
    Refetches from our CDN first (``https://mabims-dev.b-cdn.net/de440s.bsp``,
    the same bytes as the tracked copy — JPL's server stalls builds for
    minutes), falling back to skyfield's built-in source if that fails, then
    validates.

Exit code 0 means "this kernel is safe to bake into the image".
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.ephemeris import EPHEMERIS_FILE, _fetch_from_cdn

# de440s.bsp is ~31 MiB; anything much smaller is a partial fetch.
MIN_BYTES = 30_000_000
DEFAULT_DIR = "/app/data/ephemeris"


def probe(directory: Path) -> None:
    """Open the kernel and force the coefficient segments to be read."""
    from skyfield import almanac
    from skyfield.api import Loader

    loader = Loader(str(directory))
    ephemeris = loader(EPHEMERIS_FILE)
    ts = loader.timescale(builtin=True)
    ephemeris["earth"].at(ts.utc(2020, 1, 1))
    almanac.moon_phase(ephemeris, ts.utc(2026, 9, 1))


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    no_download = "--no-download" in argv
    directory = Path(args[0]) if args else Path(DEFAULT_DIR)
    path = directory / EPHEMERIS_FILE

    if no_download and not path.is_file():
        print(f"FAIL: {path} is missing", file=sys.stderr)
        return 1
    if no_download and path.stat().st_size < MIN_BYTES:
        print(f"FAIL: {path} is only {path.stat().st_size} bytes", file=sys.stderr)
        return 1
    if not no_download:
        try:
            _fetch_from_cdn(path)
        except Exception as exc:  # noqa: BLE001 - report, then let probe try JPL
            print(
                f"CDN refetch failed ({type(exc).__name__}: {exc}); "
                "falling back to skyfield's source",
                file=sys.stderr,
            )
    try:
        probe(directory)
        size = path.stat().st_size
        if size < MIN_BYTES:
            raise OSError(f"only {size} bytes after load")
    except Exception as exc:  # noqa: BLE001 - every failure must fail the build
        print(f"FAIL: de440s.bsp unusable: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"de440s.bsp ok: {size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
