"""Single source of truth for calendar coverage bounds.

Only the POLICY constants below are hand-edited. Data-derived bounds are
resolved from the data files per app instance, so extending the curated
table (e.g. when the 2027 Kemenag calendar ships) is a data change, not a
code hunt: append the month starts to ``scripts/build_calendar_data.py``,
rebuild, and every consumer derives the rest.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .schemas import Source

RETRO_SOURCE: Source = "mabims-retro"

# --- policy (hand-edited) --------------------------------------------------
RETRO_FLOOR = date(1945, 1, 1)      # absolute supported floor (requires retro=true)
RETRO_SEED_BACK = date(1970, 1, 1)  # precomputed retro seed reaches back to here
FORWARD_CEIL = date(2053, 8, 1)     # absolute supported ceiling
# ----------------------------------------------------------------------------

RETRO_WARNING = (
    "Date is below the curated MABIMS table and predates the Neo MABIMS "
    "criteria (introduced 2022); computed by projecting the same criteria "
    "(hilal altitude >= 3 deg, elongation >= 6.4 deg at Sabang sunset) "
    "backwards. Treat as an estimate, not an official date."
)


@dataclass(frozen=True)
class Coverage:
    """Resolved bounds for one app instance (from its own data dir)."""

    curated_first: str
    curated_last: str
    seed_first: str = ""
    seed_last: str = ""
    retro_floor: str = RETRO_FLOOR.isoformat()
    forward_ceil: str = FORWARD_CEIL.isoformat()

    def lower_bound(self, retro: bool) -> str:
        """Lowest supported gregorian ISO date for the given retro mode."""
        return self.retro_floor if retro else self.curated_first


def load_coverage(data_dir: Path) -> Coverage:
    """Derive coverage bounds from the data files in ``data_dir``."""
    g2h = json.loads((data_dir / "calendar_data.json").read_text(encoding="utf-8"))[
        "gregorian_to_hijri"
    ]
    seed_first = seed_last = ""
    seed_path = data_dir / "computed_seed.json"
    if seed_path.exists():
        try:
            meta = json.loads(seed_path.read_text(encoding="utf-8")).get("meta", {})
            seed_first = str(meta.get("back", ""))
            seed_last = str(meta.get("forward", ""))
        except (OSError, json.JSONDecodeError):
            pass
    return Coverage(
        curated_first=min(g2h),
        curated_last=max(g2h),
        seed_first=seed_first,
        seed_last=seed_last,
    )
