from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .calendar import MonthKey

FALLBACK_SOURCE = "fallback:aladhan-ummalqura"

_HIJRI_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})")


class FallbackError(RuntimeError):
    pass


class FallbackProvider(Protocol):
    def fetch_by_gregorian(self, year: int, month: int) -> dict[str, str]: ...

    def fetch_by_hijri(self, hijri_year: int, hijri_month: int) -> dict[str, str]: ...


class AladhanProvider:
    def __init__(self, base_url: str, client=None):
        self._base_url = base_url.rstrip("/")
        self._client = client

    def _http(self):
        if self._client is None:
            import httpx

            return httpx.Client(timeout=15.0)
        return self._client

    def _fetch_pairs(self, path: str) -> dict[str, str]:
        try:
            with self._http() as http:
                response = http.get(f"{self._base_url}{path}")
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise FallbackError(f"Aladhan request failed for {path}: {exc}") from exc
        if payload.get("code") != 200 or not isinstance(payload.get("data"), list):
            raise FallbackError(f"Unexpected Aladhan response for {path}")
        pairs: dict[str, str] = {}
        for entry in payload["data"]:
            gregorian = entry.get("gregorian", {})
            hijri = entry.get("hijri", {})
            try:
                g_iso = self._to_iso(gregorian)
                h_iso = self._to_iso(hijri)
            except (KeyError, TypeError, ValueError):
                continue
            pairs[g_iso] = h_iso
        if not pairs:
            raise FallbackError(f"Aladhan returned no usable days for {path}")
        return pairs

    @staticmethod
    def _to_iso(part: dict) -> str:
        day = int(part["day"])
        month = part["month"]
        month_number = int(month["number"] if isinstance(month, dict) else month)
        year = int(part["year"])
        return f"{year:04d}-{month_number:02d}-{day:02d}"

    def fetch_by_gregorian(self, year: int, month: int) -> dict[str, str]:
        return self._fetch_pairs(f"/gToHCalendar/{month}/{year}")

    def fetch_by_hijri(self, hijri_year: int, hijri_month: int) -> dict[str, str]:
        return self._fetch_pairs(f"/hToGCalendar/{hijri_month}/{hijri_year}")


def _invert(pairs: dict[str, str]) -> dict[str, str]:
    return {hijri: gregorian for gregorian, hijri in pairs.items()}


class FallbackStore:
    source_name = FALLBACK_SOURCE

    def __init__(self, data_dir: Path, provider: FallbackProvider):
        self.data_dir = data_dir
        self.provider = provider
        self._lock = threading.Lock()
        self.years: dict[int, dict] = {}

    def lookup(self, date_iso: str, calendar: str) -> str | None:
        if calendar == "gregorian":
            year = int(date_iso[0:4])
            data = self.years.get(year)
            if data is None:
                return None
            return data["gregorian_to_hijri"].get(date_iso)
        match = _HIJRI_MONTH_RE.match(date_iso)
        if not match:
            return None
        year = int(match.group(1))
        data = self.years.get(year)
        if data is None:
            return None
        return data["hijri_to_gregorian"].get(date_iso)

    def ensure_month(self, key: MonthKey) -> None:
        with self._lock:
            data = self.years.setdefault(
                key.year,
                {"year": key.year, "months": {}, "gregorian_to_hijri": {}, "hijri_to_gregorian": {}},
            )
            if key.label in data["months"]:
                return
            if key.kind == "G":
                g2h = self.provider.fetch_by_gregorian(key.year, key.month)
                h2g = _invert(g2h)
            else:
                h2g = self.provider.fetch_by_hijri(key.year, key.month)
                g2h = _invert(h2g)
            data["months"][key.label] = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "gregorian_to_hijri": g2h,
                "hijri_to_gregorian": h2g,
            }
            data["gregorian_to_hijri"].update(g2h)
            data["hijri_to_gregorian"].update(h2g)
            self._persist(data)

    def _persist(self, data: dict) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / f"fallback_{data['year']}.json"
        fd, tmp_path = tempfile.mkstemp(dir=str(self.data_dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, sort_keys=True)
            os.replace(tmp_path, path)
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def summary(self) -> tuple[bool, list[str]]:
        labels: list[str] = []
        for data in self.years.values():
            labels.extend(sorted(data["months"].keys()))
        return bool(labels), sorted(labels)

    def preload_year_file(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        year = int(data["year"])
        merged_g2h: dict[str, str] = {}
        merged_h2g: dict[str, str] = {}
        for month in data.get("months", {}).values():
            merged_g2h.update(month.get("gregorian_to_hijri", {}))
            merged_h2g.update(month.get("hijri_to_gregorian", {}))
        self.years[year] = {
            "year": year,
            "months": data.get("months", {}),
            "gregorian_to_hijri": merged_g2h,
            "hijri_to_gregorian": merged_h2g,
        }

    def load_existing(self) -> None:
        if not self.data_dir.exists():
            return
        for path in sorted(self.data_dir.glob("fallback_*.json")):
            try:
                self.preload_year_file(path)
            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                continue
