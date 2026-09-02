"""Generate the seed file for the computed provider.

Forward: curated anchor -> 2050-12-31 (Neo MABIMS forward computation).
Backward (retro): curated anchor -> RETRO_SEED_BACK (1970-01-01), using the
validated backward rule. Dates below the seed are computed lazily at request
time down to RETRO_FLOOR (1945-01-01).

Run once: python api/scripts/generate_seed.py
Outputs: api/data/computed_seed.json
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

from app.coverage import RETRO_SEED_BACK  # noqa: E402
from app.mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG  # noqa: E402
from app.mabims_computed import MabimsCalcProvider  # noqa: E402

DATA_PATH = API_DIR / "data" / "calendar_data.json"
OUTPUT_PATH = API_DIR / "data" / "computed_seed.json"
TARGET_END = date(2050, 12, 31)


def main() -> int:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    first_h = min(raw["hijri_to_gregorian"])
    anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
    anchor_gregorian = date.fromisoformat(raw["hijri_to_gregorian"][first_h])

    print(f"anchor: {anchor_hijri} = {anchor_gregorian}")
    print(f"target end: {TARGET_END}")
    print(f"target retro back: {RETRO_SEED_BACK}")
    print("computing...")

    provider = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
    provider.fetch_by_gregorian(TARGET_END.year, TARGET_END.month)
    provider._ensure_anchor_block()

    started = time.time()
    print("walking backwards (10-year chunks)...", flush=True)
    while provider._blocks[0].start > RETRO_SEED_BACK:
        chunk_target = max(
            provider._blocks[0].start - timedelta(days=3650), RETRO_SEED_BACK
        )
        provider._extend_backward_to(chunk_target)
        print(
            f"  retro back to {provider._blocks[0].start} "
            f"({len(provider._blocks)} blocks, {time.time() - started:.0f}s)",
            flush=True,
        )

    g2h, h2g = provider.snapshot()

    curated = raw["hijri_to_gregorian"]
    mismatches = [(h, g, curated[h]) for h, g in h2g.items() if h in curated and curated[h] != g]
    if mismatches:
        for h, computed_g, official_g in mismatches[:10]:
            print(f"MISMATCH {h}: computed={computed_g} official={official_g}")
        print(f"total mismatches vs curated table: {len(mismatches)}")
        return 1
    print(f"curated overlap verified: {len(curated)} months agree byte-for-byte")
    borderline = provider.borderline_months()

    first_g = min(g2h)
    last_g = max(g2h)
    print(f"coverage: {first_g} -> {last_g} ({len(g2h)} days)")
    print(f"borderline months: {len(borderline)}")

    margins = {
        f"{block.hijri[0]:04d}-{block.hijri[1]:02d}": block.margin
        for block in provider._blocks
    }

    payload = {
        "meta": {
            "back": first_g,
            "forward": last_g,
            "days": len(g2h),
            "criteria": {"alt_min_deg": ALT_MIN_DEG, "elong_min_deg": ELONG_MIN_DEG},
            "borderline_months": borderline,
        },
        "margins": {k: margins[k] for k in sorted(margins)},
        "gregorian_to_hijri": dict(sorted(g2h.items())),
        "hijri_to_gregorian": dict(sorted(h2g.items())),
    }

    fd, tmp_name = tempfile.mkstemp(dir=str(OUTPUT_PATH.parent), suffix=".tmp")
    tmp = Path(tmp_name)
    with open(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp.replace(OUTPUT_PATH)

    print(f"wrote {len(g2h)} days to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
