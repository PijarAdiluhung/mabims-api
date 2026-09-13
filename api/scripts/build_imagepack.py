"""Build the CDN image pack (versioned tar + ``manifest.json``) for the hilal cards.

One pack, one manifest: the runtime keeps a single ``.version`` sidecar and a
single ``MABIMS_IMAGEPACK_URL``, so card and bare variants must travel together
in the same tar. Never publish a bare-only manifest over a card pack — a fresh
``/data`` volume would get the bare files without the cards.

Usage:
    # render the 1444–1450 core (card + bare) and package it
    python -m scripts.build_imagepack --start 1444 --end 1450 \
        --images ../mabims-assets/hilal_images --dist ../mabims-assets/hilal_images

    # package images that are already on disk (no re-render)
    python -m scripts.build_imagepack --skip-render \
        --images ../mabims-assets/hilal_images --dist ../mabims-assets/hilal_images

Then upload ``manifest.json`` and the ``.tar.gz`` it names to the CDN base
(``MABIMS_IMAGEPACK_URL``, default ``https://mabims-dev.b-cdn.net/hilal_images``).
``render_version`` is derived from the site list, display points and renderer
sources, so it changes whenever the images would; a new version is what makes
running containers re-download and merge the pack.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import tarfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

# Inputs that fully determine the rendered images. The renderers embed the
# criteria thresholds (alt >= 3.0, elongation >= 6.4), so hashing chart.py and
# mapcard.py covers criteria changes too.
VERSION_INPUTS = (
    "data/hilal_sites.json",
    "data/map_points.json",
    "app/hilal/chart.py",
    "app/hilal/mapcard.py",
)

KINDS = {
    "card": ("viz", "map"),
    "bare": ("viz-bare", "map-bare"),
    "both": ("viz", "map", "viz-bare", "map-bare"),
}


def render_version(variants: tuple[str, ...]) -> str:
    """Short hash of everything the pack depends on (+ format version)."""
    digest = hashlib.sha256()
    for rel in VERSION_INPUTS:
        digest.update((API_DIR / rel).read_bytes())
    digest.update(f"variants:{','.join(sorted(variants))};pack:v1".encode())
    return digest.hexdigest()[:12]


def _months(start: int, end: int) -> list[tuple[int, int]]:
    return [(y, m) for y in range(start, end + 1) for m in range(1, 13)]


def _render(images_dir: Path, kinds: tuple[str, ...], start: int, end: int, jobs: int, force: bool) -> None:
    from scripts.generate_hilal_images import _render_month

    jobs = jobs or (os.cpu_count() or 1)
    months = _months(start, end)
    print(
        f"rendering {len(months)} months x {len(kinds)} variant(s) -> {images_dir} ({jobs} jobs)",
        flush=True,
    )
    started = time.time()
    written = skipped = 0
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = {
            pool.submit(_render_month, y, m, str(images_dir), kinds, force): (y, m)
            for y, m in months
        }
        for future in as_completed(futures):
            year, month = futures[future]
            try:
                produced = future.result()
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {year}-{month:02d}: {exc.__class__.__name__}: {exc}", flush=True)
                continue
            if produced:
                written += 1
            else:
                skipped += 1
    print(f"render done: {written} written, {skipped} skipped, {time.time() - started:.0f}s", flush=True)


def _collect(images_dir: Path, kinds: tuple[str, ...], start: int, end: int) -> list[tuple[str, Path]]:
    members: list[tuple[str, Path]] = []
    for kind in kinds:
        kind_dir = images_dir / kind
        if not kind_dir.is_dir():
            raise SystemExit(f"missing render dir: {kind_dir} (run without --skip-render first)")
        for png in sorted(kind_dir.glob("*.png")):
            try:
                year = int(png.stem[:4])
            except ValueError:
                continue
            if start <= year <= end:
                members.append((f"{kind}/{png.name}", png))
    if not members:
        raise SystemExit(f"no PNGs for {kinds} in {images_dir} within {start}-{end}")
    return members


def _write_tar(members: list[tuple[str, Path]], tar_path: Path) -> None:
    # Deterministic: fixed gzip mtime + zeroed member mtimes, so identical
    # inputs produce identical bytes and a stable tar_sha256.
    with open(tar_path, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for arcname, png in members:
                info = tar.gettarinfo(str(png), arcname=arcname)
                info.mtime = 0
                with open(png, "rb") as handle:
                    tar.addfile(info, handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the hilal CDN image pack")
    parser.add_argument("--images", required=True, help="render directory (viz/, map/, viz-bare/, map-bare/)")
    parser.add_argument(
        "--dist",
        default=None,
        help="output directory for tar + manifest (default: --images)",
    )
    parser.add_argument("--start", type=int, default=1444, help="first Hijri year (inclusive)")
    parser.add_argument("--end", type=int, default=1450, help="last Hijri year (inclusive)")
    parser.add_argument("--variants", choices=["card", "bare", "both"], default="both")
    parser.add_argument("--jobs", type=int, default=0, help="render worker processes (0 = cpu count)")
    parser.add_argument("--force", action="store_true", help="re-render existing PNGs")
    parser.add_argument("--skip-render", action="store_true", help="package images already on disk")
    parser.add_argument("--name", default=None, help="tar filename (default hilal-images-<version>.tar.gz)")
    args = parser.parse_args()

    images_dir = Path(args.images)
    dist_dir = Path(args.dist) if args.dist else images_dir
    kinds = KINDS[args.variants]
    images_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_render:
        _render(images_dir, kinds, args.start, args.end, args.jobs, args.force)

    members = _collect(images_dir, kinds, args.start, args.end)
    version = render_version(tuple(args.variants))
    tar_path = dist_dir / (args.name or f"hilal-images-{version}.tar.gz")
    _write_tar(members, tar_path)

    digest = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    manifest = {
        "render_version": version,
        "path": tar_path.name,
        "tar_sha256": digest,
        "files": len(members),
        "range": [args.start, args.end],
        "variants": list(kinds),
    }
    manifest_path = dist_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\ntar:            {tar_path}  ({tar_path.stat().st_size / 1048576:.1f} MB)")
    print(f"manifest:       {manifest_path}")
    print(f"render_version: {version}")
    print(f"tar_sha256:     {digest}")
    print(f"files:          {len(members)}")
    print("\nupload both files to MABIMS_IMAGEPACK_URL (manifest must keep the name manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
