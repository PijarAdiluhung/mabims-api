"""Kemenag sidang-isbat override registry.

Loads ``api/data/divergences.json`` — an append-only history of months
whose official start (Sidang Isbat decree) differs from the published
Kemenag calendar. Written by ``scripts/apply_flip.py``, read at app
startup, never edited by hand. Runtime behavior changes only through
the curated table itself; this registry exists to *explain* the table:
warnings on every response that touches an affected month, the
``/meta`` divergence list, and ack-aware criteria validation.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

OVERRIDE_PREFIX = "kemenag_override"
DIV_FILE = "divergences.json"


@dataclass(frozen=True)
class Divergence:
    hijri_month: str  # "1447-10" — the month whose start anchor was flipped
    published_start: str  # gregorian date per the published Kemenag calendar
    official_start: str  # gregorian date decreed at Sidang Isbat
    delta_days: int  # official - published (±1)
    reason: str  # e.g. "hilal tidak terlihat"
    recorded_at: str  # ISO-8601 with offset

    @property
    def year(self) -> int:
        return int(self.hijri_month[0:4])

    @property
    def month(self) -> int:
        return int(self.hijri_month[5:7])

    @property
    def prev_month_label(self) -> str:
        """Hijri YYYY-MM of the month whose length the flip changes."""
        y, m = self.year, self.month - 1
        if m == 0:
            return f"{y - 1:04d}-12"
        return f"{y:04d}-{m:02d}"

    @property
    def affected_months(self) -> frozenset[str]:
        """Hijri YYYY-MM labels whose rows this flip explains: the flipped
        month (its start moved) and the previous month (its length changed)."""
        return frozenset({self.hijri_month, self.prev_month_label})

    def warning(self, month_name: str) -> str:
        sign = "+" if self.delta_days > 0 else ""
        return (
            f"{OVERRIDE_PREFIX}: 1 {month_name} {self.year} H resmi {self.official_start} "
            f"(Sidang Isbat; kalender terbit Kemenag: {self.published_start}, "
            f"delta {sign}{self.delta_days} hari)."
        )


def load_divergences(data_dir: Path) -> dict[str, Divergence]:
    """Load the registry keyed by hijri YYYY-MM. Missing or invalid file → {}."""
    path = data_dir / DIV_FILE
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("divergences", raw) if isinstance(raw, dict) else raw
        known: dict[str, Divergence] = {}
        for e in entries:
            div = Divergence(
                hijri_month=str(e["hijri_month"]),
                published_start=str(e["published_start"]),
                official_start=str(e["official_start"]),
                delta_days=int(e["delta_days"]),
                reason=str(e.get("reason", "")),
                recorded_at=str(e.get("recorded_at", "")),
            )
            known[div.hijri_month] = div
        return known
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {}


def as_payload(divergences: dict[str, Divergence]) -> list[dict[str, str | int]]:
    """Slim form for /meta (month + delta is all a poller needs)."""
    items = sorted(divergences.values(), key=lambda d: d.recorded_at, reverse=True)
    return [
        {"hijri_month": d.hijri_month, "delta_days": d.delta_days}
        for d in items
    ]


def table_version(data_dir: Path, divergences: dict[str, Divergence]) -> str:
    """Client-facing flip version: file fingerprint + entry count."""
    path = data_dir / DIV_FILE
    if not divergences:
        return "none"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    return f"{len(divergences)}-{digest}"
