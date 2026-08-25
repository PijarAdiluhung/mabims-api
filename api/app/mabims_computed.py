from __future__ import annotations

import threading
from datetime import date, timedelta
from typing import NamedTuple

from .fallback import FallbackError
from .mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG, criteria_on_day29

COMPUTED_SOURCE = "mabims-computed"
BORDERLINE_MARGIN_DEG = 0.25


def next_hijri_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def prev_hijri_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


class _Block(NamedTuple):
    hijri: tuple[int, int]
    start: date
    length: int
    margin: float


class MabimsCalcProvider:
    source_name = COMPUTED_SOURCE

    def __init__(self, anchor_hijri: tuple[int, int], anchor_gregorian: date):
        self.anchor_hijri = anchor_hijri
        self.anchor_gregorian = anchor_gregorian
        self._lock = threading.Lock()
        self._blocks: list[_Block] = []
        self._g2h: dict[str, str] = {}
        self._h2g: dict[str, str] = {}

    @property
    def _first_start(self) -> date | None:
        return self._blocks[0].start if self._blocks else None

    @property
    def _last_end(self) -> date | None:
        if not self._blocks:
            return None
        last = self._blocks[-1]
        return last.start + timedelta(days=last.length - 1)

    def _decide(self, hijri: tuple[int, int], start: date) -> _Block:
        result = criteria_on_day29(start)
        length = 29 if result.visible else 30
        margin = min(result.alt_deg - ALT_MIN_DEG, result.elong_deg - ELONG_MIN_DEG)
        return _Block(hijri=hijri, start=start, length=length, margin=margin)

    def _fill(self, block: _Block) -> None:
        y, m = block.hijri
        cursor = block.start
        for d in range(1, block.length + 1):
            g = cursor.isoformat()
            h = f"{y:04d}-{m:02d}-{d:02d}"
            self._g2h[g] = h
            self._h2g[h] = g
            cursor += timedelta(days=1)

    def _extend_forward_to(self, target: date) -> None:
        while self._last_end is None or self._last_end < target:
            if not self._blocks:
                block = self._decide(self.anchor_hijri, self.anchor_gregorian)
            else:
                last = self._blocks[-1]
                block = self._decide(
                    next_hijri_month(*last.hijri),
                    last.start + timedelta(days=last.length),
                )
            self._fill(block)
            self._blocks.append(block)

    def _extend_backward_to(self, target: date) -> None:
        while self._first_start is None or self._first_start > target:
            if not self._blocks:
                raise FallbackError("cannot extend backward without anchor block")
            first = self._blocks[0]
            candidate = first.start - timedelta(days=29)
            result = criteria_on_day29(candidate)
            if result.visible:
                block = _Block(prev_hijri_month(*first.hijri), candidate, 29,
                               min(result.alt_deg - ALT_MIN_DEG, result.elong_deg - ELONG_MIN_DEG))
            else:
                block = _Block(prev_hijri_month(*first.hijri), first.start - timedelta(days=30), 30,
                               min(result.alt_deg - ALT_MIN_DEG, result.elong_deg - ELONG_MIN_DEG))
            self._fill(block)
            self._blocks.insert(0, block)

    def _gregorian_month_end(self, year: int, month: int) -> date:
        if not 1 <= month <= 12:
            raise FallbackError(f"invalid gregorian month {year}-{month:02d}")
        lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if month == 2 and is_leap(year):
            lengths[1] = 29
        return date(year, month, lengths[month - 1])

    def fetch_by_gregorian(self, year: int, month: int) -> dict[str, str]:
        try:
            month_start = date(year, month, 1)
        except ValueError as exc:
            raise FallbackError(f"invalid gregorian month {year}-{month:02d}") from exc
        month_end = self._gregorian_month_end(year, month)
        with self._lock:
            if self._last_end is None or self._last_end < month_end:
                self._extend_forward_to(month_end)
            if self._blocks and self._first_start > month_start:
                self._extend_backward_to(month_start)
            prefix = f"{year:04d}-{month:02d}-"
            return {k: v for k, v in sorted(self._g2h.items()) if k.startswith(prefix)}

    def fetch_by_hijri(self, hijri_year: int, hijri_month: int) -> dict[str, str]:
        target = (hijri_year, hijri_month)
        with self._lock:
            while self._blocks and self._blocks[0].hijri > target:
                self._extend_backward_to(
                    self._blocks[0].start - timedelta(days=60)
                )
            while not self._blocks or self._blocks[-1].hijri < target:
                anchor_point = (
                    self._blocks[-1].start + timedelta(days=self._blocks[-1].length + 5)
                    if self._blocks
                    else self.anchor_gregorian
                )
                self._extend_forward_to(anchor_point)
            prefix = f"{hijri_year:04d}-{hijri_month:02d}-"
            return {k: v for k, v in sorted(self._h2g.items()) if k.startswith(prefix)}

    def borderline_months(self) -> list[str]:
        return sorted(
            f"{b.hijri[0]:04d}-{b.hijri[1]:02d}"
            for b in self._blocks
            if b.margin < BORDERLINE_MARGIN_DEG
        )

    def snapshot(self) -> tuple[dict[str, str], dict[str, str]]:
        return dict(self._g2h), dict(self._h2g)

    def seed_from_pairs(self, h2g: dict[str, str]) -> None:
        with self._lock:
            if self._blocks:
                return
            months: dict[tuple[int, int], list[str]] = {}
            for h_iso, g_iso in h2g.items():
                months.setdefault((int(h_iso[0:4]), int(h_iso[5:7])), []).append(g_iso)

            blocks: list[_Block] = []
            for (hy, hm), g_dates in sorted(months.items()):
                g_dates.sort()
                blocks.append(
                    _Block(
                        hijri=(hy, hm),
                        start=date.fromisoformat(g_dates[0]),
                        length=len(g_dates),
                        margin=float("inf"),
                    )
                )
            for prev, curr in zip(blocks, blocks[1:]):
                expected = prev.start + timedelta(days=prev.length)
                if curr.start != expected:
                    raise ValueError(
                        f"non-contiguous seed data: {prev.hijri} ends {expected}, "
                        f"{curr.hijri} starts {curr.start}"
                    )
            self._blocks = blocks
            for block in blocks:
                self._fill(block)

    def margin_for(self, hijri_year: int, hijri_month: int) -> float | None:
        for b in self._blocks:
            if b.hijri == (hijri_year, hijri_month):
                return b.margin
        return None
