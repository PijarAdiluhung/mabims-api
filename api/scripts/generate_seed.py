"""Generate a forward-only seed file for the computed provider (2024-2050).

Run once: python api/scripts/generate_seed.py
Outputs: api/data/computed_seed.json
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

from app.mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG
from app.mabims_computed import MabimsCalcProvider

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
    print("computing...")

    provider = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
    provider.fetch_by_gregorian(TARGET_END.year, TARGET_END.month)

    g2h, h2g = provider.snapshot()
    borderline = provider.borderline_months()

    first_g = min(g2h)
    last_g = max(g2h)
    print(f"coverage: {first_g} -> {last_g} ({len(g2h)} days)")
    print(f"borderline months: {len(borderline)}")

    payload = {
        "meta": {
            "back": first_g,
            "forward": last_g,
            "days": len(g2h),
            "criteria": {"alt_min_deg": ALT_MIN_DEG, "elong_min_deg": ELONG_MIN_DEG},
            "borderline_months": borderline,
        },
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
