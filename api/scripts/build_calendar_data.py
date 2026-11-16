"""Rebuild ``data/calendar_data.json`` from the curated month starts.

The hand-edited source of truth is ``data/month_starts.json``:

    {
      "coverage_end": "2027-12-31",
      "months": {
        "1448-07": "2026-12-10",
        "1448-08": "2027-01-09",
        ...
      }
    }

One line per Hijri month: key = Hijri ``YYYY-MM``, value = Gregorian date of
day 1. Rows with a blank day (``"2027-01-__"``) are ignored, so future months
can sit in the file as placeholders that only need the day filled in. To add
a new published year, fill its rows and set ``coverage_end`` to that year's
last Gregorian day, then run:

    cd api
    python -m scripts.build_calendar_data

A Sidang Isbat flip edits one row via ``scripts/apply_flip.py`` (which writes
this file back), not by hand.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_PATH = DATA_DIR / "calendar_data.json"
MONTH_STARTS_PATH = DATA_DIR / "month_starts.json"

_HIJRI_KEY = re.compile(r"^(\d{4})-(\d{2})$")
_PENDING_VALUE = re.compile(r"^\d{4}-\d{2}-(?:__)?$")


def load_month_starts(
    path: Path = MONTH_STARTS_PATH,
) -> tuple[dict[str, tuple[int, int]], list[str], tuple[int, int, int]]:
    """Read the hand-edited JSON into ``(anchors, pending, coverage_end)``.

    ``anchors`` maps Gregorian ISO start -> (hijri year, month). ``pending``
    lists keys left blank (ignored until filled). Raises ``ValueError`` with
    a file-and-line-friendly message for malformed input.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    coverage_raw = raw.get("coverage_end")
    if not coverage_raw:
        raise ValueError(f"{path.name}: missing 'coverage_end'")
    try:
        coverage = date.fromisoformat(str(coverage_raw))
    except ValueError as exc:
        raise ValueError(f"{path.name}: invalid coverage_end {coverage_raw!r}") from exc

    months_raw = raw.get("months")
    if not isinstance(months_raw, dict) or not months_raw:
        raise ValueError(f"{path.name}: 'months' must be a non-empty object")

    anchors: dict[str, tuple[int, int]] = {}
    pending: list[str] = []
    seen_months: set[tuple[int, int]] = set()
    for label, value in months_raw.items():
        match = _HIJRI_KEY.match(str(label))
        if not match:
            raise ValueError(f"{path.name}: bad Hijri key {label!r} (want YYYY-MM)")
        hijri = (int(match.group(1)), int(match.group(2)))
        if not 1 <= hijri[1] <= 12:
            raise ValueError(f"{path.name}: bad Hijri month in {label!r}")
        if hijri in seen_months:
            raise ValueError(f"{path.name}: duplicate month {label}")
        seen_months.add(hijri)

        if value in (None, "") or _PENDING_VALUE.match(str(value)):
            pending.append(label)
            continue
        try:
            start = date.fromisoformat(str(value))
        except ValueError as exc:
            raise ValueError(f"{path.name}: {label}: invalid date {value!r}") from exc
        key = start.isoformat()
        if key in anchors:
            other = f"{anchors[key][0]:04d}-{anchors[key][1]:02d}"
            raise ValueError(f"{path.name}: {label} and {other} share start {key}")
        anchors[key] = hijri

    if not anchors:
        raise ValueError(f"{path.name}: no filled month starts")
    anchors = dict(sorted(anchors.items()))

    last_label = f"{max(anchors.values())[0]:04d}-{max(anchors.values())[1]:02d}"
    for label in pending:
        if label < last_label:
            raise ValueError(
                f"{path.name}: blank row {label} sits between filled months — "
                "fill it or remove it"
            )

    return anchors, sorted(pending), (coverage.year, coverage.month, coverage.day)


MONTH_STARTS, PENDING_MONTHS, LAST_GREGORIAN_DAY = load_month_starts()


def build() -> tuple[dict[str, str], dict[str, str]]:
    g2h: dict[str, str] = {}
    h2g: dict[str, str] = {}
    coverage_end = datetime(*LAST_GREGORIAN_DAY)
    dates = sorted(MONTH_STARTS)
    for i, start_iso in enumerate(dates):
        start = datetime.strptime(start_iso, "%Y-%m-%d")
        if start > coverage_end:
            break
        hy, hm = MONTH_STARTS[start_iso]
        hd = 1
        if i + 1 < len(dates):
            end = min(
                datetime.strptime(dates[i + 1], "%Y-%m-%d") - timedelta(days=1),
                coverage_end,
            )
        else:
            end = coverage_end
        while start <= end:
            g = start.strftime("%Y-%m-%d")
            h = f"{hy:04d}-{hm:02d}-{hd:02d}"
            if g in g2h or h in h2g:
                raise ValueError(f"collision at {g} / {h}")
            g2h[g] = h
            h2g[h] = g
            start += timedelta(days=1)
            hd += 1
    return g2h, h2g


def validate(g2h: dict[str, str], h2g: dict[str, str]) -> None:
    dates = sorted(g2h)
    first = datetime.strptime(dates[0], "%Y-%m-%d")
    last = datetime.strptime(dates[-1], "%Y-%m-%d")
    assert last == datetime(*LAST_GREGORIAN_DAY), f"coverage ends {last}, expected {LAST_GREGORIAN_DAY}"
    cursor = first
    while cursor < last:
        cursor += timedelta(days=1)
        assert cursor.strftime("%Y-%m-%d") in g2h, f"gap at {cursor:%Y-%m-%d}"

    starts = [(datetime.strptime(k, "%Y-%m-%d"), v) for k, v in MONTH_STARTS.items()]
    for i in range(len(starts) - 1):
        gap = (starts[i + 1][0] - starts[i][0]).days
        assert gap in (29, 30), f"month {starts[i][1]} length {gap} invalid"

        hy, hm = starts[i][1]
        expected = (hy + 1, 1) if hm == 12 else (hy, hm + 1)
        assert starts[i + 1][1] == expected, (
            f"{starts[i][1]} is followed by {starts[i + 1][1]}, expected {expected}"
        )

    assert starts[-1][0] <= datetime(*LAST_GREGORIAN_DAY), (
        f"last filled month {starts[-1][1]} starts {starts[-1][0]:%Y-%m-%d}, after "
        f"coverage_end {datetime(*LAST_GREGORIAN_DAY):%Y-%m-%d} — bump coverage_end "
        "to cover the new year"
    )

    tail = (datetime(*LAST_GREGORIAN_DAY) - starts[-1][0]).days
    assert 0 <= tail <= 30, (
        f"coverage_end {datetime(*LAST_GREGORIAN_DAY):%Y-%m-%d} is {tail} days after "
        f"the last filled month ({starts[-1][1]} at {starts[-1][0]:%Y-%m-%d}); "
        f"fill the blank rows ({', '.join(PENDING_MONTHS)}) or move coverage_end back"
    )

    for g, h in g2h.items():
        assert h2g.get(h) == g, f"hijri_to_gregorian mismatch for {g}->{h}"
    assert len(g2h) == len(h2g), "maps are not the same size"


def save_month_starts(
    month_starts: dict[str, tuple[int, int]], path: Path = MONTH_STARTS_PATH
) -> None:
    """Write ``month_starts`` back to the hand-edited JSON, preserving blank
    placeholder rows and the ``_readme`` / ``coverage_end`` fields."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    previous = raw.get("months", {})
    months: dict[str, str] = {}
    for start_iso, (hy, hm) in sorted(month_starts.items()):
        months[f"{hy:04d}-{hm:02d}"] = start_iso
    for label, value in previous.items():
        months.setdefault(label, value)
    raw["months"] = months
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    if PENDING_MONTHS:
        print(
            f"note: {len(PENDING_MONTHS)} blank month start(s) ignored: "
            + ", ".join(PENDING_MONTHS)
        )

    g2h, h2g = build()
    validate(g2h, h2g)

    skip_regression = os.environ.get("MABIMS_ALLOW_FLIP") == "1"
    if DATA_PATH.exists() and not skip_regression:
        old = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        for g, h in old["gregorian_to_hijri"].items():
            new_h = g2h.get(g)
            assert new_h == h, f"regression: {g} was {h}, now {new_h}"
        print(f"preserved {len(old['gregorian_to_hijri'])} existing entries")
    elif skip_regression:
        print("regression check skipped (MABIMS_ALLOW_FLIP=1 — sidang isbat flip)")

    payload = {
        "gregorian_to_hijri": dict(sorted(g2h.items())),
        "hijri_to_gregorian": dict(sorted(h2g.items())),
    }
    tmp = DATA_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(DATA_PATH)
    print(f"wrote {len(g2h)} entries to {DATA_PATH}")
    print(f"coverage: {min(g2h)} -> {max(g2h)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
