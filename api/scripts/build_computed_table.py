from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG  # noqa: E402
from app.mabims_computed import MabimsCalcProvider  # noqa: E402
from app.precomputed import PRECOMPUTED_FILENAME  # noqa: E402

DATA_PATH = API_DIR / "data" / "calendar_data.json"
OUTPUT_PATH = API_DIR / "data" / PRECOMPUTED_FILENAME
DEFAULT_BACK_YEAR = 1970
DEFAULT_FORWARD_YEARS = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Precompute the Neo MABIMS lookup table.")
    parser.add_argument("--back-year", type=int, default=DEFAULT_BACK_YEAR)
    parser.add_argument("--forward-end-year", type=int, default=None)
    return parser.parse_args()


def build(back_year: int, forward_end_year: int) -> tuple[dict[str, str], dict[str, str], list[str]]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    first_h = min(raw["hijri_to_gregorian"])
    anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
    anchor_gregorian = date.fromisoformat(raw["hijri_to_gregorian"][first_h])

    provider = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
    provider.fetch_by_gregorian(back_year, 1)
    provider.fetch_by_gregorian(forward_end_year, 12)

    g2h, h2g = provider.snapshot()
    borderline = provider.borderline_months()
    return dict(sorted(g2h.items())), dict(sorted(h2g.items())), borderline


def validate(
    g2h: dict[str, str],
    h2g: dict[str, str],
    curated_g2h: dict[str, str],
    back_iso: str,
    forward_iso: str,
) -> None:
    cursor = date.fromisoformat(back_iso)
    limit = date.fromisoformat(forward_iso)
    while cursor <= limit:
        iso = cursor.isoformat()
        assert iso in g2h, f"gap at {iso}"
        cursor = date.fromordinal(cursor.toordinal() + 1)

    for g, h in g2h.items():
        assert h2g.get(h) == g, f"roundtrip mismatch for {g}->{h}"
    assert len(g2h) == len(h2g), "maps are not the same size"

    overlaps = [item for item in curated_g2h.items() if back_iso <= item[0] <= forward_iso]
    assert overlaps, "no overlap with curated table; bounds are wrong"
    for g, h in overlaps:
        assert g2h.get(g) == h, f"overlap mismatch at {g}: computed {g2h.get(g)} != curated {h}"


def main() -> int:
    args = parse_args()
    back_year = args.back_year
    forward_end_year = args.forward_end_year or (date.today().year + DEFAULT_FORWARD_YEARS)

    started = datetime.now(UTC)
    print(f"computing {back_year}-01-01 .. {forward_end_year}-12-31 ...")
    g2h, h2g, borderline = build(back_year, forward_end_year)
    elapsed = (datetime.now(UTC) - started).total_seconds()

    back_iso = min(g2h)
    forward_iso = max(g2h)
    curated = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    validate(g2h, h2g, curated["gregorian_to_hijri"], back_iso, forward_iso)

    payload = {
        "meta": {
            "generated_at": started.isoformat(timespec="seconds"),
            "back": back_iso,
            "forward": forward_iso,
            "days": len(g2h),
            "criteria": {"alt_min_deg": ALT_MIN_DEG, "elong_min_deg": ELONG_MIN_DEG},
            "borderline_months": borderline,
        },
        "gregorian_to_hijri": g2h,
        "hijri_to_gregorian": h2g,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(OUTPUT_PATH.parent), suffix=".tmp")
    tmp = Path(tmp_name)
    with open(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp.replace(OUTPUT_PATH)

    print(f"wrote {len(g2h)} days to {OUTPUT_PATH}")
    print(f"coverage: {back_iso} -> {forward_iso} ({len(borderline)} borderline months)")
    print(f"overlap with curated table verified ({elapsed:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
