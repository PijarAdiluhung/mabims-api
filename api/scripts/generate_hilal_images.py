"""Pre-generate the hilal PNG cards (``viz`` + ``map``) for a Hijri year range.

Usage:
    python -m scripts.generate_hilal_images --start 1444 --end 1448 --out api/data/hilal_images
    python -m scripts.generate_hilal_images --start 1449 --end 1455 --out /data/hilal_images --force

Idempotent: existing files are skipped unless ``--force``. The API serves these
directly and lazily caches anything outside the generated range.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

DATA_PATH = API_DIR / "data" / "calendar_data.json"


def _build_service():
    """CalendarService wired with the computed tier (mirrors create_app)."""
    from app.calendar import CalendarService
    from app.fallback import MemoryFallbackStore
    from app.mabims_computed import MabimsCalcProvider

    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    first_h = min(raw["hijri_to_gregorian"])
    anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
    anchor_gregorian = date.fromisoformat(raw["hijri_to_gregorian"][first_h])

    provider = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
    seed_path = DATA_PATH.parent / "computed_seed.json"
    if seed_path.exists():
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        provider.seed_from_pairs(seed["hijri_to_gregorian"], margins=seed.get("margins"))
    return CalendarService(DATA_PATH, stores=[MemoryFallbackStore(DATA_PATH.parent, provider)])


def _render_month(year: int, month: int, out: str, kinds: tuple[str, ...], force: bool) -> list[str]:
    from app.hilal.service import resolve_sighting_evening
    from app.main import _render_map_png, _render_viz_png, observe_sighting_evening

    out_dir = Path(out)
    targets = {kind: out_dir / kind / f"{year:04d}-{month:02d}.png" for kind in kinds}
    if all(path.exists() for path in targets.values()) and not force:
        return []

    service = _build_service()
    res = resolve_sighting_evening(service, year, month)
    sighting = observe_sighting_evening(res.evening_date)
    ms_site = sighting.multisite.deciding_site or sighting.multisite.best_site
    alt_ok = ms_site.alt_refracted_deg >= 3.0
    elong_ok = ms_site.elong_deg >= 6.4

    written: list[str] = []
    for kind, target in targets.items():
        if target.exists() and not force:
            continue
        png = (
            _render_viz_png(res, sighting, ms_site, alt_ok, elong_ok)
            if kind == "viz"
            else _render_map_png(res, sighting, ms_site)
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(png)
        written.append(str(target))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate hilal PNG cards")
    parser.add_argument("--start", type=int, required=True, help="first Hijri year (inclusive)")
    parser.add_argument("--end", type=int, required=True, help="last Hijri year (inclusive)")
    parser.add_argument("--out", type=str, required=True, help="output directory")
    parser.add_argument("--kind", choices=["viz", "map", "both"], default="both")
    parser.add_argument("--jobs", type=int, default=0, help="worker processes (0 = cpu count)")
    parser.add_argument("--force", action="store_true", help="re-render existing files")
    args = parser.parse_args()

    kinds = ("viz", "map") if args.kind == "both" else (args.kind,)
    jobs = args.jobs or (os.cpu_count() or 1)
    months = [(y, m) for y in range(args.start, args.end + 1) for m in range(1, 13)]
    print(f"{len(months)} months x {len(kinds)} image(s) -> {args.out} ({jobs} jobs)", flush=True)

    started = time.time()
    written = skipped = 0
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        futures = {
            pool.submit(_render_month, y, m, args.out, kinds, args.force): (y, m)
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
                print(
                    f"  {year}-{month:02d} -> {len(produced)} file(s) "
                    f"({written}/{len(months)}, {time.time() - started:.0f}s)",
                    flush=True,
                )
            else:
                skipped += 1

    print(f"done: {written} months written, {skipped} skipped, {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
