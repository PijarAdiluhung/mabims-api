from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple

SOURCE_MABIMS = "mabims"


class CalendarDataError(RuntimeError):
    pass


class DateOutOfBounds(ValueError):
    pass


@dataclass(frozen=True)
class MonthKey:
    kind: str
    year: int
    month: int

    @property
    def label(self) -> str:
        return f"{self.kind}{self.year}-{self.month:02d}"


def month_key_for(date_iso: str, calendar: str) -> MonthKey:
    year = int(date_iso[0:4])
    month = int(date_iso[5:7])
    prefix = "G" if calendar == "gregorian" else "H"
    return MonthKey(kind=prefix, year=year, month=month)


class LookupResult(NamedTuple):
    value: str | None
    source: str


class CalendarService:
    def __init__(self, data_path: Path, fallback_store=None):
        try:
            raw = json.loads(data_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CalendarDataError(f"Could not load calendar data: {exc}") from exc
        self.g2h: dict[str, str] = raw["gregorian_to_hijri"]
        self.h2g: dict[str, str] = raw["hijri_to_gregorian"]
        self.coverage_first_g = min(self.g2h)
        self.coverage_last_g = max(self.g2h)
        self.coverage_first_h = min(self.h2g)
        self.coverage_last_h = max(self.h2g)
        self.fallback_store = fallback_store
        self._lock = threading.Lock()

    def covers(self, date_iso: str, calendar: str) -> bool:
        if calendar == "gregorian":
            first, last = self.coverage_first_g, self.coverage_last_g
        else:
            first, last = self.coverage_first_h, self.coverage_last_h
        return first <= date_iso <= last

    def lookup(self, date_iso: str, calendar: str) -> LookupResult:
        source_map = self.g2h if calendar == "gregorian" else self.h2g
        hit = source_map.get(date_iso)
        if hit is not None:
            return LookupResult(value=hit, source=SOURCE_MABIMS)
        if self.fallback_store is not None:
            hit = self.fallback_store.lookup(date_iso, calendar)
            if hit is not None:
                return LookupResult(value=hit, source=self.fallback_store.source_name)
        return LookupResult(value=None, source="not_found")

    def resolve(self, date_iso: str, calendar: str) -> LookupResult:
        result = self.lookup(date_iso, calendar)
        if result.value is not None:
            return result
        if self.fallback_store is None or self.covers(date_iso, calendar):
            return result
        with self._lock:
            key = month_key_for(date_iso, calendar)
            self.fallback_store.ensure_month(key)
        return self.lookup(date_iso, calendar)

    def ensure_hijri_month(self, year: int, month: int) -> None:
        if self.fallback_store is None:
            return
        with self._lock:
            self.fallback_store.ensure_month(MonthKey(kind="H", year=year, month=month))

    def ensure_range(self, start: str, end: str, calendar: str) -> None:
        if self.fallback_store is None:
            return
        keys: dict[str, MonthKey] = {}
        cursor = date.fromisoformat(start).replace(day=1)
        stop = date.fromisoformat(end)
        while cursor <= stop:
            iso = cursor.isoformat()
            key = month_key_for(iso, calendar)
            if key.label not in keys and not self.covers(iso, calendar):
                keys[key.label] = key
            cursor = (cursor + timedelta(days=32)).replace(day=1)
        with self._lock:
            for key in keys.values():
                self.fallback_store.ensure_month(key)

    def fallback_summary(self) -> tuple[bool, list[str]]:
        if self.fallback_store is None:
            return False, []
        return self.fallback_store.summary()
