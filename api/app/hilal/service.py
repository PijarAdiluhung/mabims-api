"""Resolve a MABIMS hijri month to its sighting evening (last evening of the
previous month) using the calendar service tables (curated → computed)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

MONTH_NAMES_ID = {
    1: "Muharram",
    2: "Safar",
    3: "Rabiul Awal",
    4: "Rabiul Akhir",
    5: "Jumadil Awal",
    6: "Jumadil Akhir",
    7: "Rajab",
    8: "Sya'ban",
    9: "Ramadhan",
    10: "Syawal",
    11: "Dzulqa'dah",
    12: "Dzulhijjah",
}

MIN_HIJRI_YEAR = 1446
MAX_HIJRI_YEAR = 1486


class MonthNotResolvable(ValueError):
    pass


def _hijri_date(service, year: int, month: int, day: int) -> str | None:
    """Lookup via the full store chain (curated → computed), not just curated h2g."""
    iso = f"{year:04d}-{month:02d}-{day:02d}"
    return service.lookup(iso, "hijri").value


@dataclass(frozen=True)
class SightingEvening:
    target_year: int
    target_month: int
    target_name: str
    target_start: date
    prev_year: int
    prev_month: int
    prev_name: str
    prev_length: int  # 29 or 30 (from the table)
    evening_date: date
    evening_day: int  # always 29 — the sighting night
    evening_label: str  # e.g. "29 Sya'ban 1447 H"


def resolve_sighting_evening(service, year: int, month: int) -> SightingEvening:
    """Resolve target hijri (year, month) to its sighting evening.

    The sighting evening is always the **29th** of the previous month — the
    night people actually go looking. ``prev_length`` reports whether the
    month ultimately had 29 or 30 days (from the MABIMS table).
    """
    if not 1 <= month <= 12:
        raise MonthNotResolvable(f"bulan harus 1..12, dapat {month}")
    if not MIN_HIJRI_YEAR <= year <= MAX_HIJRI_YEAR:
        raise MonthNotResolvable(f"tahun hijriah {year} di luar cakupan")
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)

    service.ensure_hijri_month(year, month)
    service.ensure_hijri_month(prev_year, prev_month)

    d29 = _hijri_date(service, prev_year, prev_month, 29)
    if d29 is None:
        raise MonthNotResolvable(
            f"Bulan {MONTH_NAMES_ID[prev_month]} {prev_year} H di luar cakupan data."
        )
    d30 = _hijri_date(service, prev_year, prev_month, 30)
    start = _hijri_date(service, year, month, 1)
    if start is None:
        raise MonthNotResolvable(
            f"Bulan {MONTH_NAMES_ID[month]} {year} H di luar cakupan data."
        )

    return SightingEvening(
        target_year=year,
        target_month=month,
        target_name=MONTH_NAMES_ID[month],
        target_start=date.fromisoformat(start),
        prev_year=prev_year,
        prev_month=prev_month,
        prev_name=MONTH_NAMES_ID[prev_month],
        prev_length=30 if d30 is not None else 29,
        evening_date=date.fromisoformat(d29),
        evening_day=29,
        evening_label=f"29 {MONTH_NAMES_ID[prev_month]} {prev_year} H",
    )
