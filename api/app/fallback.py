from __future__ import annotations

import logging
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .calendar import MonthKey
from .schemas import Source

log = logging.getLogger(__name__)

_HIJRI_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})")


class FallbackError(RuntimeError):
    pass


class FallbackProvider(Protocol):
    source_name: Source

    def fetch_by_gregorian(self, year: int, month: int, *, retro: bool = False) -> dict[str, str]: ...

    def fetch_by_hijri(self, hijri_year: int, hijri_month: int, *, retro: bool = False) -> dict[str, str]: ...


def _invert(pairs: dict[str, str]) -> dict[str, str]:
    return {hijri: gregorian for gregorian, hijri in pairs.items()}


class FallbackStore:
    source_name: Source

    def __init__(self, data_dir: Path, provider: FallbackProvider):
        self.data_dir = data_dir
        self.provider = provider
        self._lock = threading.Lock()
        self.years: dict[int, dict] = {}

    def lookup(self, date_iso: str, calendar: str) -> str | None:
        if calendar == "gregorian":
            year = int(date_iso[0:4])
            data = self.years.get(year)
            if data is not None:
                hit = data["gregorian_to_hijri"].get(date_iso)
                if hit is not None:
                    return hit
            for other in self.years.values():
                hit = other["gregorian_to_hijri"].get(date_iso)
                if hit is not None:
                    return hit
            return None
        match = _HIJRI_MONTH_RE.match(date_iso)
        if not match:
            return None
        year = int(match.group(1))
        data = self.years.get(year)
        if data is not None:
            hit = data["hijri_to_gregorian"].get(date_iso)
            if hit is not None:
                return hit
        for other in self.years.values():
            hit = other["hijri_to_gregorian"].get(date_iso)
            if hit is not None:
                return hit
        return None

    def ensure_month(self, key: MonthKey, *, retro: bool = False) -> None:
        with self._lock:
            data = self.years.setdefault(
                key.year,
                {"year": key.year, "months": {}, "gregorian_to_hijri": {}, "hijri_to_gregorian": {}},
            )
            if key.label in data["months"]:
                return
            log.warning(
                "%s: fetching %s via HTTP (not preloaded)", self.source_name, key.label
            )
            if key.kind == "G":
                g2h = self.provider.fetch_by_gregorian(key.year, key.month, retro=retro)
                h2g = _invert(g2h)
            else:
                h2g = self.provider.fetch_by_hijri(key.year, key.month, retro=retro)
                g2h = _invert(h2g)
            data["months"][key.label] = {
                "fetched_at": datetime.now(UTC).isoformat(),
                "gregorian_to_hijri": g2h,
                "hijri_to_gregorian": h2g,
            }
            data["gregorian_to_hijri"].update(g2h)
            data["hijri_to_gregorian"].update(h2g)

    def summary(self) -> tuple[bool, list[str]]:
        labels: list[str] = []
        for data in self.years.values():
            labels.extend(sorted(data["months"].keys()))
        return bool(labels), sorted(labels)


class MemoryFallbackStore(FallbackStore):
    def __init__(self, data_dir: Path, provider: FallbackProvider):
        super().__init__(data_dir, provider)
        self.source_name = provider.source_name
