"""Generate the precomputed hilal history index (``api/data/hilal_index.json``).

The index is a compact per-month summary of the deciding evening — the same
numbers ``/api/v1/hilal/info`` returns — so ``GET /api/v1/hilal/history`` can
serve a whole range (the website's history list) as a lookup instead of
re-computing every month per request.

Usage:
    python -m scripts.generate_hilal_index --start 1444-08 --end 1475-12
    python -m scripts.generate_hilal_index                    # bundled default range

Regenerate after a criteria / site-list / ephemeris change or after extending
the curated table, then commit ``api/data/hilal_index.json`` (and ship it with
the image pack). The deciding evening for ``1444-08`` is the first that falls
inside the curated table, so the index floor is ``1444-08``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

DATA_DIR = API_DIR / "data"
DATA_PATH = DATA_DIR / "calendar_data.json"
INDEX_PATH = DATA_DIR / "hilal_index.json"

DEFAULT_FIRST = "1444-08"
DEFAULT_LAST = "1475-12"

_service = None
_provider = None


def _build():
    """CalendarService + computed provider wired like ``create_app``."""
    global _service, _provider
    if _service is not None:
        return _service, _provider

    from app.calendar import CalendarService
    from app.fallback import MemoryFallbackStore
    from app.mabims_computed import MabimsCalcProvider

    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    first_h = min(raw["hijri_to_gregorian"])
    anchor_hijri = (int(first_h[0:4]), int(first_h[5:7]))
    anchor_gregorian = date.fromisoformat(raw["hijri_to_gregorian"][first_h])

    provider = MabimsCalcProvider(anchor_hijri, anchor_gregorian)
    seed_path = DATA_DIR / "computed_seed.json"
    if seed_path.exists():
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        provider.seed_from_pairs(seed["hijri_to_gregorian"], margins=seed.get("margins"))

    _service = CalendarService(DATA_PATH, stores=[MemoryFallbackStore(DATA_DIR, provider)])
    _provider = provider
    return _service, provider


def _item(year: int, month: int) -> tuple[str, dict]:
    from app.hilal.service import resolve_sighting_evening
    from app.mabims_computed import COMPUTED_SOURCE
    from app.main import (
        BORDERLINE_WARNING_TEMPLATE,
        COMPUTED_WARNING,
        HILAL_ALT_MIN_DEG,
        HILAL_ELONG_MIN_DEG,
        observe_sighting_evening,
    )

    service, provider = _build()
    res = resolve_sighting_evening(service, year, month)
    sighting = observe_sighting_evening(res.evening_date)
    ms = sighting.multisite
    ms_site = ms.deciding_site or ms.best_site
    sky = ms.sky_for(ms_site.site)
    evening_g = res.evening_date.isoformat()

    source = service.lookup(evening_g, "gregorian").source
    warnings: list[str] = []
    if source == COMPUTED_SOURCE:
        warnings.append(COMPUTED_WARNING)
        ym = f"{res.prev_year:04d}-{res.prev_month:02d}"
        if ym in set(provider.borderline_months()):
            warnings.append(BORDERLINE_WARNING_TEMPLATE.format(ym=ym))

    item = {
        "month": {
            "name": res.target_name,
            "number": res.target_month,
            "year": res.target_year,
            "start": res.target_start.isoformat(),
        },
        "previous_month": {
            "name": res.prev_name,
            "number": res.prev_month,
            "year": res.prev_year,
            "length": res.prev_length,
        },
        "evening": {
            "hijri_date": res.evening_label,
            "hijri_day": res.evening_day,
            "gregorian_date": evening_g,
            "sunset": sighting.sunset_local,
            "moonset": sighting.moonset_local,
            "moon_alt_deg": round(ms_site.alt_refracted_deg, 2),
            "moon_az_deg": round(sky.moon_az_deg, 2),
            "sun_alt_deg": round(sky.sun_alt_deg, 2),
            "elongation_deg": round(ms_site.elong_deg, 2),
            "illumination_pct": round(sighting.illumination_pct, 2),
            "age_hours": round(sighting.age_hours, 1),
            "deciding_site": {
                "name": sighting.site.name,
                "lat": sighting.site.lat_deg,
                "lon": sighting.site.lon_deg,
                "elev_m": sighting.site.elev_m,
                "tz": sighting.site.tz,
            },
            "sites_checked": len(ms.sites),
            "alt_ok": ms_site.alt_refracted_deg >= HILAL_ALT_MIN_DEG,
            "elong_ok": ms_site.elong_deg >= HILAL_ELONG_MIN_DEG,
            "visible": ms.visible,
        },
        "source": source,
        "warnings": warnings,
    }
    return f"{year:04d}-{month:02d}", item


def _parse_ym(value: str) -> tuple[int, int]:
    try:
        year, month = value.split("-")
        y, m = int(year), int(month)
    except (ValueError, AttributeError):
        raise SystemExit(f"invalid Hijri YYYY-MM: {value!r}") from None
    if not 1 <= m <= 12:
        raise SystemExit(f"invalid month in {value!r}")
    return y, m


def _sequence(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    y, m = start
    while (y, m) <= end:
        out.append((y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the hilal history index")
    parser.add_argument("--start", default=DEFAULT_FIRST, help="first Hijri YYYY-MM (inclusive)")
    parser.add_argument("--end", default=DEFAULT_LAST, help="last Hijri YYYY-MM (inclusive)")
    parser.add_argument("--out", default=str(INDEX_PATH), help="output JSON path")
    args = parser.parse_args()

    start, end = _parse_ym(args.start), _parse_ym(args.end)
    if end < start:
        raise SystemExit("--end must be >= --start")
    months = _sequence(start, end)
    print(f"generating {len(months)} months -> {args.out}", flush=True)

    index: dict[str, dict] = {}
    started = time.time()
    for i, (year, month) in enumerate(months, 1):
        key, item = _item(year, month)
        index[key] = item
        if i % 25 == 0 or i == len(months):
            print(f"  {i}/{len(months)} ({key}) {time.time() - started:.0f}s", flush=True)

    payload = {
        "version": f"neo-mabims-multisite:{len(index)}",
        "range": {"first": args.start, "last": args.end},
        "count": len(index),
        "months": index,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=0, separators=(",", ":")), encoding="utf-8")
    print(f"done: {len(index)} months, {out.stat().st_size} bytes, {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
