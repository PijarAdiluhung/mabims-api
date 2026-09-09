"""Validate curated table + retro seed against the multi-site model.

Model: "seen anywhere in Indonesia" — topocentric apparent moon altitude
(Bennett refraction) >= 3.0 deg and geocentric elongation >= 6.4 deg at
each site's local sunset on Hijri day 29; if ANY of the coastal sites in
api/data/hilal_sites.json sees the crescent, the month has 29 days.

Checks:
  1. every curated month boundary reproduces its table length
  2. the retro part of computed_seed.json is consistent with the FORWARD
     rule (the seed's retro region is generated with the backward rule)

Data: MABIMS_TEST_DATA env overrides the curated table path.
Exit 0 only if both checks pass.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

from app.mabims_sites import load_sites, sightings_on_dates  # noqa: E402

DATA_PATH = Path(os.environ.get("MABIMS_TEST_DATA", API_DIR / "data" / "calendar_data.json"))


def load_month_starts() -> list[tuple[date, tuple[int, int]]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    g2h = data["gregorian_to_hijri"]
    starts: list[tuple[date, tuple[int, int]]] = []
    for gd in sorted(g2h):
        hy, hm, hd = (int(x) for x in g2h[gd].split("-"))
        if hd == 1:
            starts.append((date.fromisoformat(gd), (hy, hm)))
    return starts


def validate_retro_seed(curated_first: date) -> int:
    """Independently verify the retro part of computed_seed.json.

    The seed's retro region was generated with the backward rule; here we
    re-check every retro month with the FORWARD rule (criteria at sunset of
    day 29, seen at any site) and require the predicted length to match
    the seed's actual month length. A mismatch means the backward chain is
    not consistent with the forward model.
    """
    seed_path = DATA_PATH.parent / "computed_seed.json"
    if not seed_path.exists():
        print("\nretro seed: computed_seed.json not found, skipped")
        return 0
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    g2h = seed.get("gregorian_to_hijri", {})
    retro = sorted(
        g for g, h in g2h.items()
        if h.endswith("-01") and date.fromisoformat(g) < curated_first
    )
    if len(retro) < 2:
        print("\nretro seed: no retro months below curated table, skipped")
        return 0

    print(f"\nretro seed check: {len(retro)} months below curated table")
    starts = [date.fromisoformat(g) for g in retro]
    sightings = sightings_on_dates([s + timedelta(days=28) for s in starts[:-1]])
    misses = 0
    for i, s in enumerate(sightings):
        actual = (starts[i + 1] - starts[i]).days
        if s.month_length != actual:
            misses += 1
            site = s.best_site
            print(
                f"  RETRO MISS {retro[i]}: len {actual}, "
                f"alt={site.alt_refracted_deg:.3f} elong={site.elong_deg:.3f} "
                f"({site.site})"
            )
    print(f"retro boundaries tested: {len(starts) - 1}, misses: {misses}")
    return 1 if misses else 0


def main() -> int:
    starts = load_month_starts()
    n = len(starts) - 1
    day29 = [starts[i][0] + timedelta(days=28) for i in range(n)]
    sightings = sightings_on_dates(day29)
    sites = load_sites()
    print(f"table: {DATA_PATH}")
    print(f"model: multi-site ({len(sites)} sites) | "
          f"thresholds: alt>=3.0 elong>=6.4 at local sunset (day 29)")
    print()
    hdr = f"{'hijri':>9} {'start':>10} {'len':>4} {'pred':>5} {'decider':<32} {'margin':>7} {'verdict':>9}"
    print(hdr)
    print("-" * len(hdr))

    misses = 0
    borderline: list[str] = []
    for i in range(n):
        g_start, (hy, hm) = starts[i]
        actual = (starts[i + 1][0] - g_start).days
        s = sightings[i]
        dec = s.deciding_site or s.best_site
        verdict = "OK" if s.month_length == actual else "MISS"
        if verdict == "MISS":
            misses += 1
        m = dec.margin_deg
        if m < 0.25:
            borderline.append(f"{hy}-{hm:02d} ({verdict}, margin {m:+.2f})")
        print(
            f"{hy:>6}-{hm:02d} {g_start.isoformat():>10} {actual:>4} "
            f"{s.month_length:>5} {dec.site:<32.32} {m:>7.3f} {verdict:>9}"
        )

    print()
    print(f"boundaries tested : {n}")
    print(f"multisite hits    : {n - misses}/{n}")
    if borderline:
        print("borderline months (margin < 0.25):")
        for b in borderline:
            print(f"  - {b}")
    if misses:
        return 1
    return validate_retro_seed(starts[0][0])


if __name__ == "__main__":
    sys.exit(main())
