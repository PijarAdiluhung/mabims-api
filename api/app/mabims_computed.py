from __future__ import annotations

import threading
from datetime import date, timedelta
from typing import NamedTuple

from .coverage import FORWARD_CEIL, RETRO_FLOOR
from .fallback import FallbackError
from .mabims_astro import ALT_MIN_DEG, ELONG_MIN_DEG, criteria_on_day29, criteria_on_sunset
from .schemas import Source

COMPUTED_SOURCE: Source = "mabims-computed"
BORDERLINE_MARGIN_DEG = 0.25

HARD_CAP_END = FORWARD_CEIL


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

    def _decide_backward(self, next_start: date) -> _Block:
        """Previous month, from a known 1st at ``next_start``.

        Validated backward rule (48/48 vs curated 1444-1448): the month
        before a known 1st is 30 days iff the criteria are met at Sabang
        sunset on ``next_start - 31`` — the evening before the candidate
        30-day start. If visible, that evening started the 30-day month;
        if not, the 1st sits at ``next_start - 29``.

        The recorded margin comes from the block's own day-29 evening — the
        same evening a forward decision uses — so borderline flags stay
        consistent across tiers.
        """
        result = criteria_on_sunset(next_start - timedelta(days=31))
        length = 30 if result.visible else 29
        block_start = next_start - timedelta(days=length)
        forward = criteria_on_day29(block_start)
        margin = min(forward.alt_deg - ALT_MIN_DEG, forward.elong_deg - ELONG_MIN_DEG)
        first = self._blocks[0]
        return _Block(
            hijri=prev_hijri_month(*first.hijri),
            start=block_start,
            length=length,
            margin=margin,
        )

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
        if target > HARD_CAP_END:
            raise FallbackError(
                f"computed table cannot extend past {HARD_CAP_END.isoformat()}"
            )
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
        """Prepend months until the earliest block starts at or before ``target``."""
        if target < RETRO_FLOOR:
            raise FallbackError(
                f"retro computation cannot reach before {RETRO_FLOOR.isoformat()}"
            )
        while self._blocks[0].start > target:
            block = self._decide_backward(self._blocks[0].start)
            if block.start < RETRO_FLOOR:
                raise FallbackError(
                    f"retro computation cannot reach before {RETRO_FLOOR.isoformat()}"
                )
            self._blocks.insert(0, block)
            self._fill(block)

    def _extend_backward_to_hijri(self, target: tuple[int, int]) -> None:
        """Prepend months until the earliest block is at or before ``target``."""
        while self._blocks[0].hijri > target:
            if self._blocks[0].start - timedelta(days=30) < RETRO_FLOOR:
                raise FallbackError(
                    f"retro computation cannot reach before {RETRO_FLOOR.isoformat()}"
                )
            block = self._decide_backward(self._blocks[0].start)
            self._blocks.insert(0, block)
            self._fill(block)

    def _ensure_anchor_block(self) -> None:
        if not self._blocks:
            block = self._decide(self.anchor_hijri, self.anchor_gregorian)
            self._fill(block)
            self._blocks.append(block)

    def _gregorian_month_end(self, year: int, month: int) -> date:
        if not 1 <= month <= 12:
            raise FallbackError(f"invalid gregorian month {year}-{month:02d}")
        lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if month == 2 and is_leap(year):
            lengths[1] = 29
        return date(year, month, lengths[month - 1])

    def fetch_by_gregorian(self, year: int, month: int, *, retro: bool = False) -> dict[str, str]:
        try:
            month_start = date(year, month, 1)
        except ValueError as exc:
            raise FallbackError(f"invalid gregorian month {year}-{month:02d}") from exc
        month_end = self._gregorian_month_end(year, month)
        if month_end > HARD_CAP_END:
            raise FallbackError(
                f"date {month_end.isoformat()} is beyond the computed table limit "
                f"({HARD_CAP_END.isoformat()})"
            )
        prefix = f"{year:04d}-{month:02d}-"
        if month_start < self.anchor_gregorian:
            # Pre-curated territory: only reachable with the retro flag.
            if not retro:
                raise FallbackError(
                    f"date {month_start.isoformat()} is before the curated table start "
                    f"({self.anchor_gregorian.isoformat()}); requires retro=true"
                )
            with self._lock:
                self._ensure_anchor_block()
                self._extend_backward_to(month_start)
                return {k: v for k, v in sorted(self._g2h.items()) if k.startswith(prefix)}
        with self._lock:
            if self._last_end is None or self._last_end < month_end:
                self._extend_forward_to(month_end)
            return {k: v for k, v in sorted(self._g2h.items()) if k.startswith(prefix)}

    def fetch_by_hijri(self, hijri_year: int, hijri_month: int, *, retro: bool = False) -> dict[str, str]:
        target = (hijri_year, hijri_month)
        with self._lock:
            earliest = self._blocks[0].hijri if self._blocks else self.anchor_hijri
            if target < earliest:
                if not retro:
                    raise FallbackError(
                        f"hijri month {target[0]:04d}-{target[1]:02d} is before the "
                        f"curated table; requires retro=true"
                    )
                self._ensure_anchor_block()
                self._extend_backward_to_hijri(target)
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

    def seed_from_pairs(
        self,
        h2g: dict[str, str],
        margins: dict[str, float] | None = None,
    ) -> None:
        with self._lock:
            if self._blocks:
                return
            margins = margins or {}
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
                        margin=margins.get(f"{hy:04d}-{hm:02d}", float("inf")),
                    )
                )
            for prev, curr in zip(blocks, blocks[1:], strict=False):
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
