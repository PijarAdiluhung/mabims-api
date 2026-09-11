"""Prime the hilal astronomy sqlite cache (api/data/hilal_astro.sqlite).

Computes, for the sighting evening of every Hijri month in the range:
  * ``sites25:*``      25-site model (alt, elong, az, sunset)
  * ``map_points:*``   95 display points (alt, elong)
  * ``mapgrid0.25:*``  archipelago grid (alt, elong)
  * ``world3:verdict`` world minimap verdicts

Design guarantees:
  * RESUMABLE — every row is committed immediately; rerun skips evenings
    whose kinds are already present, so a crash costs nothing.
  * VISIBLE progress — one line per evening with elapsed + ETA.
  * FAIL-SAFE stops — an unexpected error prints, notes the evening, and
    the script exits cleanly with partial data intact.

Usage:
    python scripts/prime_astro_cache.py --start-year 1444 --end-year 1475
    python scripts/prime_astro_cache.py --limit 3        # smoke test
    python scripts/prime_astro_cache.py --jobs 8         # parallel evenings
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

import numpy as np  # noqa: E402

from app.calendar import CalendarService  # noqa: E402
from app.fallback import MemoryFallbackStore  # noqa: E402
from app.hilal import astrocache  # noqa: E402
from app.hilal.mapcard import (  # noqa: E402
    CENTER_LAT,
    LON0,
    LON1,
    MAP_H,
    W,
    _compute,
    _global_visibility,
)
from app.hilal.service import resolve_sighting_evening  # noqa: E402
from app.mabims_computed import MabimsCalcProvider  # noqa: E402
from app.mabims_sites import _evaluate_batch, sites25_kinds  # noqa: E402

DATA_PATH = API_DIR / "data" / "calendar_data.json"

MAP_GRID_STEP = 0.25
_GRID_LAT_SPAN = (LON1 - LON0) * MAP_H / W
_GRID_LAT0 = CENTER_LAT - _GRID_LAT_SPAN / 2
_GRID_LAT1 = CENTER_LAT + _GRID_LAT_SPAN / 2
_GRID_KIND_BASE = (
    f"mapgrid{MAP_GRID_STEP:g}:{_GRID_LAT0:.3f}:{_GRID_LAT1:.3f}:{LON0:.3f}:{LON1:.3f}"
)

MAP_KINDS = ("map_points:alt", "map_points:elong", "world3:verdict",
             f"{_GRID_KIND_BASE}:alt", f"{_GRID_KIND_BASE}:elong")
ALL_KINDS = MAP_KINDS + sites25_kinds()


def _service() -> CalendarService:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    first_h = min(raw["hijri_to_gregorian"])
    provider = MabimsCalcProvider(
        (int(first_h[0:4]), int(first_h[5:7])),
        date.fromisoformat(raw["hijri_to_gregorian"][first_h]),
    )
    seed_path = DATA_PATH.parent / "computed_seed.json"
    if seed_path.exists():
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        provider.seed_from_pairs(seed["hijri_to_gregorian"], margins=seed.get("margins"))
    return CalendarService(DATA_PATH, stores=[MemoryFallbackStore(DATA_PATH.parent, provider)])


def _hijri_evenings(service: CalendarService, y0: int, y1: int) -> list[tuple[int, int, date]]:
    """Sighting evening (gregorian) per hijri month start; deduplicated."""
    out: list[tuple[int, int, date]] = []
    seen: set[date] = set()
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            res = resolve_sighting_evening(service, y, m)
            if res.evening_date not in seen:
                seen.add(res.evening_date)
                out.append((y, m, res.evening_date))
    return out


def _prime_sites25(evening: date) -> None:
    kinds = sites25_kinds()
    if astrocache.has(evening, kinds):
        return
    res = _evaluate_batch([evening])
    raw = ("alt", "elong", "moon_az", "sun_alt", "sun_az", "sunset_jd")
    for kind_key, kind in zip(kinds, raw, strict=True):
        astrocache.store(evening, kind_key, np.asarray(res[kind])[0])


def _prime_map(evening: date) -> None:
    pts = [(p["name"], float(p["lat"]), float(p["lon"])) for p in json.loads(
        (API_DIR / "data" / "map_points.json").read_text(encoding="utf-8")
    )["points"]]
    lat = np.array([p[1] for p in pts])
    lon = np.array([p[2] for p in pts])

    if not astrocache.has(evening, ("map_points:alt", "map_points:elong")):
        alt, elong = _compute(lat, lon, evening)
        astrocache.store(evening, "map_points:alt", alt)
        astrocache.store(evening, "map_points:elong", elong)

    gkinds = (f"{_GRID_KIND_BASE}:alt", f"{_GRID_KIND_BASE}:elong")
    if not astrocache.has(evening, gkinds):
        lats = np.linspace(_GRID_LAT0, _GRID_LAT1, int((_GRID_LAT1 - _GRID_LAT0) / MAP_GRID_STEP) + 1)
        lons = np.linspace(LON0, LON1, int((LON1 - LON0) / MAP_GRID_STEP) + 1)
        lo, la = np.meshgrid(lons, lats)
        alt, elong = _compute(la.ravel(), lo.ravel(), evening)
        astrocache.store(evening, f"{_GRID_KIND_BASE}:alt", alt.reshape(la.shape))
        astrocache.store(evening, f"{_GRID_KIND_BASE}:elong", elong.reshape(la.shape))

    if not astrocache.has(evening, ("world3:verdict",)):
        verdict = _global_visibility(evening)
        astrocache.store(evening, "world3:verdict", verdict)


def _prime_one(hy: int, hm: int, evening: date) -> str:
    """Prime a single evening (runs in a worker process). Returns status."""
    if astrocache.has(evening, ALL_KINDS):
        return "skipped"
    t0 = time.time()
    try:
        _prime_sites25(evening)
        _prime_map(evening)
    except KeyboardInterrupt:
        raise
    return f"ok in {time.time() - t0:.1f}s done=1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prime hilal astronomy sqlite cache")
    parser.add_argument("--start-year", type=int, default=1444)
    parser.add_argument("--end-year", type=int, default=1475)
    parser.add_argument("--limit", type=int, default=0, help="smoke test: first N evenings only")
    parser.add_argument("--jobs", type=int, default=1,
                        help="worker processes (evenings are independent; sqlite handles the writes)")
    args = parser.parse_args()

    print(f"cache file : {astrocache.cache_path()}", flush=True)
    print(f"ephem tag  : {astrocache.EPHEM_TAG}", flush=True)
    print(f"hijri range: {args.start_year} .. {args.end_year}", flush=True)

    service = _service()
    months = _hijri_evenings(service, args.start_year, args.end_year)
    if args.limit:
        months = months[: args.limit]
    total = len(months)
    print(f"{total} evenings to prime", flush=True)

    started = time.time()
    completed = 0
    failures: list[str] = []

    if args.jobs > 1:
        # NOTE: each worker writes its own rows via sqlite WAL+busy_timeout;
        # skipped-vs-completed distinction keeps the resume guarantee intact.
        print(f"parallel mode: {args.jobs} worker processes", flush=True)
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {
                pool.submit(_prime_one, hy, hm, evening): (hy, hm, evening)
                for (hy, hm, evening) in months
            }
            for future in as_completed(futures):
                hy, hm, evening = futures[future]
                completed += 1
                elapsed = time.time() - started
                eta = (elapsed / completed) * (total - completed)
                eta_m, eta_s = int(eta // 60), int(eta % 60)
                try:
                    status = future.result()
                    print(
                        f"[{completed:>{len(str(total))}}/{total}] {evening}  (H{hy}-{hm:02d})  "
                        f"{status}  elapsed {int(elapsed // 60)}:{int(elapsed % 60):02d}  "
                        f"eta ~{eta_m}:{eta_s:02d}",
                        flush=True,
                    )
                except KeyboardInterrupt:
                    raise
                except Exception:  # noqa: BLE001
                    failures.append(f"{evening} (H{hy}-{hm:02d})")
                    print(f"\nFAILED at {evening} (H{hy}-{hm:02d}):", flush=True)
                    traceback.print_exc()
        if failures:
            print(
                f"\npartial: {total - len(failures)}/{total} evenings committed; "
                f"rerun the same command to retry {len(failures)} failed evening(s)",
                flush=True,
            )
            return 1
        print(f"\nDONE: {total}/{total} evenings primed in {time.time() - started:.0f}s", flush=True)
        return 0

    done = 0
    stopped_at: str | None = None
    for idx, (hy, hm, evening) in enumerate(months, start=1):
        if astrocache.has(evening, ALL_KINDS):
            done += 1
            print(f"[{idx:>{len(str(total))}}/{total}] {evening}  (H{hy}-{hm:02d})  already cached, skipped",
                  flush=True)
            continue
        left = total - idx + 1
        elapsed = time.time() - started
        eta = (elapsed / done) * left if done > 0 else 0.0
        eta_m, eta_s = int(eta // 60), int(eta % 60)
        print(
            f"[{idx:>{len(str(total))}}/{total}] {evening}  (H{hy}-{hm:02d})  "
            f"elapsed {int(elapsed // 60)}:{int(elapsed % 60):02d}  eta ~{eta_m}:{eta_s:02d}",
            end=" ",
            flush=True,
        )
        try:
            t0 = time.time()
            _prime_sites25(evening)
            _prime_map(evening)
            print(f"ok in {time.time() - t0:.1f}s", flush=True)
            done += 1
        except KeyboardInterrupt:
            print(f"\ninterrupted — done {idx - 1}/{total}; rerun to continue", flush=True)
            return 130
        except Exception:  # noqa: BLE001
            stopped_at = f"{evening} (H{hy}-{hm:02d})"
            print(f"\nFAILED at {stopped_at}:", flush=True)
            traceback.print_exc()
            break

    if stopped_at is None:
        print(f"\nDONE: {total}/{total} evenings primed in {time.time() - started:.0f}s", flush=True)
        return 0
    print(
        f"\npartial: {idx - 1}/{total} evenings committed in {time.time() - started:.0f}s; "
        f"rerun the same command to resume after {stopped_at}",
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
