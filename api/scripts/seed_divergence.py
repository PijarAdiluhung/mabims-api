"""Divergence census: the current multi-site model vs computed_seed.json.

Runs the live model (topo alt + refraction, geocentric elongation, seen
at any of the coastal sites — see ``app.mabims_sites``) over EVERY month
boundary in ``api/data/computed_seed.json`` (retro + curated window +
forward) and compares the predicted month length to the seed's stored
length.

Use this before/after any change to the criteria, the site list, or the
ephemeris: it quantifies how many month starts a regeneration would
shift, without writing anything. Divergence is measured on the seed's
own dates — a real regen compounds (a changed length shifts all later
day-29 dates).

Run: python api/scripts/seed_divergence.py
Output: api/scripts/seed_divergence.json (gitignored artifact)
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

from app.mabims_sites import load_sites, sightings_on_dates  # noqa: E402

DATA_DIR = API_DIR / "data"
OUTPUT_PATH = API_DIR / "scripts" / "seed_divergence.json"


def month_starts(g2h: dict[str, str]) -> list[tuple[date, str]]:
    return [
        (date.fromisoformat(g), h) for g, h in sorted(g2h.items()) if h.endswith("-01")
    ]


def curated_bounds() -> tuple[date, date]:
    raw = json.loads((DATA_DIR / "calendar_data.json").read_text(encoding="utf-8"))
    starts = month_starts(raw["gregorian_to_hijri"])
    return starts[0][0], starts[-1][0]


def main() -> int:
    seed = json.loads((DATA_DIR / "computed_seed.json").read_text(encoding="utf-8"))
    seed_starts = month_starts(seed["gregorian_to_hijri"])
    cur_first, cur_last = curated_bounds()
    load_sites()  # validate the site list loads before the long sweep

    n = len(seed_starts) - 1
    starts = seed_starts[:n]
    actuals = [(seed_starts[i + 1][0] - seed_starts[i][0]).days for i in range(n)]
    day29 = [g + timedelta(days=28) for g, _ in starts]

    print(f"seed month boundaries: {n} ({starts[0][0]} -> {starts[-1][0]})")
    print("evaluating (one batched call)...")
    sightings = sightings_on_dates(day29)

    predicted = [s.month_length for s in sightings]
    best_margin = [s.best_site.margin_deg for s in sightings]

    regions = {
        "retro   (< curated)": [i for i in range(n) if starts[i][0] < cur_first],
        "curated window     ": [i for i in range(n) if cur_first <= starts[i][0] <= cur_last],
        "forward (> curated)": [i for i in range(n) if starts[i][0] > cur_last],
    }
    total_div = 0
    print(f"\n{'region':<21} {'months':>7} {'agree':>7} {'diverge':>8}")
    for label, idxs in regions.items():
        div = sum(predicted[i] != actuals[i] for i in idxs)
        total_div += div
        print(f"{label:<21} {len(idxs):>7} {len(idxs) - div:>7} {div:>8}")
    print(f"\ntotal divergent boundaries: {total_div}/{n} "
          "(a real regen may compound beyond this)")

    deciders: Counter[str] = Counter()
    for s in sightings:
        decider = s.deciding_site
        if decider is not None:
            deciders[decider.site] += 1
    print("\ndeciding sites across full seed range:")
    for name, cnt in deciders.most_common(8):
        print(f"  {cnt:>5}x  {name}")

    b29 = sum(0.0 <= m < 0.25 for m in best_margin)
    b30 = sum(-0.25 < m < 0.0 for m in best_margin)
    print(f"\nborderline months (|margin| < 0.25): {b29 + b30} "
          f"({b29} near-29, {b30} near-30)")
    close = sorted(
        (i for i in range(n) if abs(best_margin[i]) < 0.25),
        key=lambda i: abs(best_margin[i]),
    )
    print("closest 12 months by |margin|:")
    for i in close[:12]:
        print(f"  {starts[i][1]}  {starts[i][0]}  actual {actuals[i]} "
              f"pred {predicted[i]}  margin {best_margin[i]:+.3f}")

    os.makedirs(OUTPUT_PATH.parent, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "divergent_months": [
            {"hijri": starts[i][1], "greg_start": starts[i][0].isoformat(),
             "actual": actuals[i], "predicted": predicted[i],
             "margin": best_margin[i]}
            for i in range(n) if predicted[i] != actuals[i]
        ],
        "borderline_months": [
            {"hijri": starts[i][1], "greg_start": starts[i][0].isoformat(),
             "actual": actuals[i], "predicted": predicted[i],
             "margin": best_margin[i]}
            for i in close
        ],
    }, indent=1), encoding="utf-8")
    print(f"\ndetails written: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
