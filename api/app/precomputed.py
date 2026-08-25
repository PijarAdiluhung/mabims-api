from __future__ import annotations

import json
from pathlib import Path

from .calendar import MonthKey
from .mabims_computed import COMPUTED_SOURCE

PRECOMPUTED_FILENAME = "computed_table.json"


class PrecomputedDataError(RuntimeError):
    pass


class PrecomputedStore:
    source_name = COMPUTED_SOURCE

    def __init__(self, data_path: Path):
        try:
            raw = json.loads(data_path.read_text(encoding="utf-8"))
            self.g2h: dict[str, str] = raw["gregorian_to_hijri"]
            self.h2g: dict[str, str] = raw["hijri_to_gregorian"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise PrecomputedDataError(f"Could not load {data_path.name}: {exc}") from exc
        meta = raw.get("meta", {})
        self.borderline: frozenset[str] = frozenset(meta.get("borderline_months", []))
        self.generated_at: str | None = meta.get("generated_at")
        self.first_g = min(self.g2h)
        self.last_g = max(self.g2h)
        self.first_h = min(self.h2g)
        self.last_h = max(self.h2g)

    @property
    def label(self) -> str:
        return f"{self.first_g}..{self.last_g}"

    def covers(self, date_iso: str, calendar: str) -> bool:
        first, last = (self.first_g, self.last_g) if calendar == "gregorian" else (self.first_h, self.last_h)
        return first <= date_iso <= last

    def lookup(self, date_iso: str, calendar: str) -> str | None:
        if calendar == "gregorian":
            return self.g2h.get(date_iso)
        return self.h2g.get(date_iso)

    def ensure_month(self, key: MonthKey) -> None:
        return None

    def summary(self) -> tuple[bool, list[str]]:
        return True, [f"precomputed:{self.label}"]
