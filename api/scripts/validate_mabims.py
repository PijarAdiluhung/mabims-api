from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path

from skyfield import almanac
from skyfield.api import Loader, wgs84

REPO = Path(__file__).resolve().parents[2]
DATA_PATH = Path(os.environ.get("MABIMS_TEST_DATA", REPO / "api" / "data" / "calendar_data.json"))

LAT_DEG = 5.0 + 53.0 / 60.0
LON_DEG = 95.0 + 19.0 / 60.0
ALT_MIN = 3.0
ELONG_MIN = 6.4
WIB = timezone(timedelta(hours=7))

DEFAULT_EPHEM_DIR = Path(tempfile.gettempdir()) / "mabims-ephemeris"
EPHEM_DIR = Path(os.environ.get("MABIMS_EPHEMERIS_DIR") or DEFAULT_EPHEM_DIR)
EPHEM_DIR.mkdir(parents=True, exist_ok=True)

_loader = Loader(str(EPHEM_DIR))
ts = _loader.timescale(builtin=True)
eph = _loader("de421.bsp")
earth = eph["earth"]
moon = eph["moon"]
sun = eph["sun"]
sabang_pos = wgs84.latlon(LAT_DEG, LON_DEG)
sabang = earth + sabang_pos


def load_month_starts() -> list[tuple[date, tuple[int, int]]]:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    g2h = data["gregorian_to_hijri"]
    starts: list[tuple[date, tuple[int, int]]] = []
    for gd in sorted(g2h):
        hy, hm, hd = (int(x) for x in g2h[gd].split("-"))
        if hd == 1:
            starts.append((date.fromisoformat(gd), (hy, hm)))
    return starts


def sunset_on(d: date) -> datetime:
    start = datetime.combine(d, time(0, 0), tzinfo=WIB)
    end = start + timedelta(days=1)
    f = almanac.sunrise_sunset(eph, sabang_pos)
    times, events = almanac.find_discrete(ts.from_datetime(start), ts.from_datetime(end), f)
    for t, ev in zip(times, events, strict=True):
        dt = t.utc_datetime()
        if not ev:
            return dt
    raise RuntimeError(f"no sunset found for {d}")


def metrics_at(dt: datetime) -> dict[str, float]:
    t = ts.from_datetime(dt.replace(tzinfo=UTC))
    geo = earth.at(t)
    m = geo.observe(moon).apparent()
    s = geo.observe(sun).apparent()
    elong = m.separation_from(s).degrees

    alt_topo = (
        sabang.at(t)
        .observe(moon)
        .apparent()
        .altaz()[0]
        .degrees
    )

    ra, dec_ang, _dist = m.radec(epoch=t)
    lat = math.radians(LAT_DEG)
    dec = math.radians(dec_ang.degrees)
    lst_deg = (t.gast * 15.0 + LON_DEG) % 360.0
    ha_deg = ((lst_deg - ra.hours * 15.0 + 180.0) % 360.0) - 180.0
    ha = math.radians(ha_deg)
    sin_alt = math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt_geo = math.degrees(math.asin(sin_alt))
    h = max(alt_geo, -1.0)
    refr_arcmin = 1.02 / math.tan(math.radians(h + 10.3 / (h + 5.11)))
    alt_geo_r = alt_geo + refr_arcmin / 60.0

    return {"alt_topo": alt_topo, "alt_geo": alt_geo, "alt_geo_r": alt_geo_r, "elong": elong}


def predict_len(mx: dict[str, float], mode: str) -> int:
    alt = mx[mode]
    ok = alt >= ALT_MIN and mx["elong"] >= ELONG_MIN
    return 29 if ok else 30


def validate_retro_seed(curated_first: str) -> int:
    """Independently verify the retro part of computed_seed.json.

    The seed's retro region was generated with the backward rule; here we
    re-check every retro month with the FORWARD rule (criteria at sunset of
    day 29) and require the predicted length to match the seed's actual
    month length. A mismatch means the backward chain is not consistent
    with the forward model.
    """
    seed_path = DATA_PATH.parent / "computed_seed.json"
    if not seed_path.exists():
        print("\nretro seed: computed_seed.json not found, skipped")
        return 0
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    g2h = seed.get("gregorian_to_hijri", {})
    starts = sorted(
        g for g, h in g2h.items() if h.endswith("-01") and g < curated_first
    )
    if not starts:
        print("\nretro seed: no retro months below curated table, skipped")
        return 0

    print(f"\nretro seed check: {len(starts)} months below curated table")
    misses = 0
    for i in range(len(starts) - 1):
        start = date.fromisoformat(starts[i])
        actual = (date.fromisoformat(starts[i + 1]) - start).days
        ss = sunset_on(start + timedelta(days=28))
        mx = metrics_at(ss)
        if predict_len(mx, "alt_geo_r") != actual:
            misses += 1
            print(
                f"  RETRO MISS {starts[i]}: len {actual}, "
                f"alt={mx['alt_geo_r']:.3f} elong={mx['elong']:.3f}"
            )
    print(f"retro boundaries tested: {len(starts) - 1}, misses: {misses}")
    return 1 if misses else 0


def main() -> int:
    global LAT_DEG, LON_DEG
    site = "Sabang"
    if len(sys.argv) == 3:
        LAT_DEG, LON_DEG = float(sys.argv[1]), float(sys.argv[2])
        site = f"{LAT_DEG:.4f}N {LON_DEG:.4f}E"
    starts = load_month_starts()
    print(f"table: {DATA_PATH}")
    print(
        f"anchor: {starts[0][1][0]}-{starts[0][1][1]:02d}-01 = {starts[0][0]}"
        f"  ({len(starts)} month starts)"
    )
    print(f"site: {site} | thresholds: alt>={ALT_MIN} elong>={ELONG_MIN} (sunset, day 29)")
    print()
    hdr = (
        f"{'hijri':>9} {'start':>10} {'len':>4} "
        f"{'altGeo':>8} {'predG':>5} {'altG+R':>8} {'predR':>5} {'elong':>7} {'verdict':>9}"
    )
    print(hdr)
    print("-" * len(hdr))

    hit_t = hit_g = hit_r = total = 0
    borderline: list[str] = []
    rows: list[str] = []

    for i in range(len(starts) - 1):
        g_start, (hy, hm) = starts[i]
        g_next, nxt = starts[i + 1]
        actual_len = (g_next - g_start).days
        day29 = g_start + timedelta(days=28)
        ss = sunset_on(day29)
        mx = metrics_at(ss)
        pred_t = predict_len(mx, "alt_topo")
        pred_g = predict_len(mx, "alt_geo")
        pred_r = predict_len(mx, "alt_geo_r")

        ok_t = pred_t == actual_len
        ok_g = pred_g == actual_len
        ok_r = pred_r == actual_len
        hit_t += ok_t
        hit_g += ok_g
        hit_r += ok_r
        total += 1

        m_r = min(mx["alt_geo_r"] - ALT_MIN, mx["elong"] - ELONG_MIN)
        verdict = "OK" if (ok_t and ok_g and ok_r) else ("geoR-only" if ok_r else "MISS")
        if m_r < 0.25:
            borderline.append(f"{hy}-{hm:02d} ({verdict}, margin {m_r:+.2f})")

        row = (
            f"{hy:>6}-{hm:02d} {g_start.isoformat():>10} {actual_len:>4} "
            f"{mx['alt_geo']:>8.3f} {pred_g:>5} {mx['alt_geo_r']:>8.3f} {pred_r:>5} "
            f"{mx['elong']:>7.3f} {verdict:>9}"
        )
        print(row)
        rows.append(row)

    print()
    print(f"boundaries tested : {total}")
    print(f"topocentric hits  : {hit_t}/{total}")
    print(f"geocentric  hits  : {hit_g}/{total}")
    print(f"geo + refr. hits  : {hit_r}/{total}")
    if borderline:
        print("borderline months (margin < 0.25):")
        for b in borderline:
            print(f"  - {b}")
    if hit_r != total:
        return 1
    retro_status = validate_retro_seed(starts[0][0].isoformat())
    return 0 if retro_status == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
