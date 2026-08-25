from __future__ import annotations

from datetime import date, timedelta

from .mabims_astro import month_length


def next_hijri_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def predict_month_starts(
    anchor_hijri: tuple[int, int],
    anchor_gregorian: date,
    months: int,
) -> dict[tuple[int, int], date]:
    starts: dict[tuple[int, int], date] = {}
    year, month = anchor_hijri
    current = anchor_gregorian
    for _ in range(months):
        starts[(year, month)] = current
        current += timedelta(days=month_length(current))
        year, month = next_hijri_month(year, month)
    return starts
