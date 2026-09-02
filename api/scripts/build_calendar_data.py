from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "calendar_data.json"
LAST_GREGORIAN_DAY = (2026, 12, 31)

MONTH_STARTS = {
    "2023-01-23": (1444, 7),
    "2023-02-22": (1444, 8),
    "2023-03-23": (1444, 9),
    "2023-04-22": (1444, 10),
    "2023-05-21": (1444, 11),
    "2023-06-20": (1444, 12),
    "2023-07-19": (1445, 1),
    "2023-08-18": (1445, 2),
    "2023-09-17": (1445, 3),
    "2023-10-16": (1445, 4),
    "2023-11-15": (1445, 5),
    "2023-12-14": (1445, 6),
    "2024-01-13": (1445, 7),
    "2024-02-11": (1445, 8),
    "2024-03-12": (1445, 9),
    "2024-04-10": (1445, 10),
    "2024-05-10": (1445, 11),
    "2024-06-08": (1445, 12),
    "2024-07-07": (1446, 1),
    "2024-08-06": (1446, 2),
    "2024-09-05": (1446, 3),
    "2024-10-04": (1446, 4),
    "2024-11-03": (1446, 5),
    "2024-12-03": (1446, 6),
    "2025-01-01": (1446, 7),
    "2025-01-31": (1446, 8),
    "2025-03-01": (1446, 9),
    "2025-03-31": (1446, 10),
    "2025-04-29": (1446, 11),
    "2025-05-28": (1446, 12),
    "2025-06-27": (1447, 1),
    "2025-07-26": (1447, 2),
    "2025-08-25": (1447, 3),
    "2025-09-23": (1447, 4),
    "2025-10-23": (1447, 5),
    "2025-11-22": (1447, 6),
    "2025-12-21": (1447, 7),
    "2026-01-20": (1447, 8),
    "2026-02-19": (1447, 9),
    "2026-03-21": (1447, 10),
    "2026-04-19": (1447, 11),
    "2026-05-18": (1447, 12),
    "2026-06-16": (1448, 1),
    "2026-07-16": (1448, 2),
    "2026-08-14": (1448, 3),
    "2026-09-13": (1448, 4),
    "2026-10-12": (1448, 5),
    "2026-11-11": (1448, 6),
    "2026-12-10": (1448, 7),
}


def build() -> tuple[dict[str, str], dict[str, str]]:
    g2h: dict[str, str] = {}
    h2g: dict[str, str] = {}
    dates = sorted(MONTH_STARTS)
    for i, start_iso in enumerate(dates):
        start = datetime.strptime(start_iso, "%Y-%m-%d")
        hy, hm = MONTH_STARTS[start_iso]
        hd = 1
        if i + 1 < len(dates):
            end = datetime.strptime(dates[i + 1], "%Y-%m-%d") - timedelta(days=1)
        else:
            end = datetime(*LAST_GREGORIAN_DAY)
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

    for g, h in g2h.items():
        assert h2g.get(h) == g, f"hijri_to_gregorian mismatch for {g}->{h}"
    assert len(g2h) == len(h2g), "maps are not the same size"


def main() -> int:
    g2h, h2g = build()
    validate(g2h, h2g)

    if DATA_PATH.exists():
        old = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        for g, h in old["gregorian_to_hijri"].items():
            new_h = g2h.get(g)
            assert new_h == h, f"regression: {g} was {h}, now {new_h}"
        print(f"preserved {len(old['gregorian_to_hijri'])} existing entries")

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
