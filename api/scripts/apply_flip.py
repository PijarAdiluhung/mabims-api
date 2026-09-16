"""Apply a Sidang Isbat correction (flip) to the curated table.

A flip = Kemenag's rukyat session decreed ONE month start (F) that differs
from the published calendar. One isbat night, one anchor line: the flip
edits only F's ``MONTH_STARTS`` anchor; every other anchor stays exactly as
published. The ±1 is absorbed by the two adjacent months (F−1 lengthens or
shortens 29↔30 — that is the isbat decision — and F's own length adjusts
the other way), which the table validator enforces. Later month starts
remain the published predictions until their own isbat nights decreed
them; if ever, each is its own flip entry.

The script:
  1. edits the anchor (validated: 29/30-day gaps, contiguity, no collisions)
  2. verifies the regenerated day-map diff touches only months F−1 and F
  3. regenerates ``api/data/calendar_data.json``
  4. appends an entry to ``api/data/divergences.json`` (append-only history)
  5. prints spot-check URLs; the CI deploy step purges the CDN zones

``--dry-run`` plans and prints without writing; ``--yes`` skips the
interactive confirmation.

Run:
  python api/scripts/apply_flip.py --hijri 1447-10 --new-start 2026-03-20 \\
      --reason "hilal tidak terlihat" --yes
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
API_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import scripts.build_calendar_data as bcd  # noqa: E402
from app.hilal.service import MONTH_NAMES_ID  # noqa: E402

DATA_DIR = API_DIR / "data"
CAL_PATH = DATA_DIR / "calendar_data.json"
DIV_PATH = DATA_DIR / "divergences.json"

TZ_WIB = timezone(timedelta(hours=7))


def plan_flip(
    month_starts: dict[str, tuple[int, int]], hy: int, hm: int, new_start: date
) -> tuple[dict[str, tuple[int, int]], date, int]:
    """Return (new anchors, published_start, delta) for flipping the start of
    hijri (hy, hm).

    Pure function — no I/O. One isbat decrees one month start, so only that
    anchor moves; the ±1 must be absorbable by both adjacent months:
    F−1's length shifts by +delta and F's own by −delta (each must stay
    29/30) — which also proves the delta direction is physically possible.
    """
    published_key = next((k for k, v in month_starts.items() if v == (hy, hm)), None)
    if published_key is None:
        raise ValueError(f"anchor {hy:04d}-{hm:02d} not found in MONTH_STARTS")
    published = date.fromisoformat(published_key)
    delta = (new_start - published).days
    if delta == 0:
        raise ValueError("new start equals the published start — nothing to flip")
    if abs(delta) > 1:
        raise ValueError(
            f"delta {delta:+d} day is outside ±1 — one isbat night decrees one "
            "month start by at most one day; use the MABIMS_ALLOW_FLIP=1 path "
            "with build_calendar_data.py for a wholesale revised calendar"
        )

    prev_key = next(
        (k for k, v in month_starts.items() if v == ((hy, hm - 1) if hm > 1 else (hy - 1, 12))),
        None,
    )
    if prev_key is None:
        raise ValueError("cannot flip the first anchor: the previous month is outside the curated table")
    prev_len = (published - date.fromisoformat(prev_key)).days
    next_key = next(
        (k for k, v in month_starts.items() if v == ((hy, hm + 1) if hm < 12 else (hy + 1, 1))),
        None,
    )
    current_len = (
        (date.fromisoformat(next_key) - published).days
        if next_key
        else (date(*bcd.LAST_GREGORIAN_DAY) - published).days + 1
    )
    bad = []
    if prev_len + delta not in (29, 30):
        bad.append(f"previous month becomes {prev_len + delta} days")
    if current_len - delta not in (29, 30):
        bad.append(f"the flipped month becomes {current_len - delta} days")
    if bad:
        raise ValueError(
            f"flipping 1 {MONTH_NAMES_ID.get(hm, hm)} {hy} H by {delta:+d} is not "
            "representable as a single-anchor flip — " + " and ".join(bad)
        )

    planned = dict(month_starts)
    del planned[published_key]
    planned[new_start.isoformat()] = (hy, hm)
    return dict(sorted(planned.items())), published, delta


def verify_diff(
    old: dict[str, str], new: dict[str, str], flip_month: str, delta: int, new_start: date
) -> None:
    """The diff must touch ONLY months F−1 and F: months before F−1 and from
    F+1 on are byte-identical (no cascade); F−1's day 30 appears or
    disappears; F's rows are rebuilt from its new start."""
    prev_y, prev_m = int(flip_month[0:4]), int(flip_month[5:7]) - 1
    if prev_m == 0:
        prev_y, prev_m = prev_y - 1, 12
    prev_label = f"{prev_y:04d}-{prev_m:02d}"
    ny, nm = (int(flip_month[0:4]), int(flip_month[5:7]) + 1) if int(flip_month[5:7]) < 12 else (
        int(flip_month[0:4]) + 1, 1,
    )
    next_g = next((g for g, h in old.items() if h == f"{ny:04d}-{nm:02d}-01"), None)
    prev_g = next((g for g, h in old.items() if h == prev_label + "-01"), None)
    if prev_g is None:
        raise AssertionError(f"curated table has no row for 1 {prev_label} — cannot verify the flip")
    expected: dict[str, str] = {}
    for g, h in old.items():
        if h.startswith(prev_label + "-") or h.startswith(flip_month + "-"):
            continue  # rebuilt below
        expected[g] = h
    last_g = date(*bcd.LAST_GREGORIAN_DAY)

    def add_month(label: str, start: date, length: int) -> None:
        for hd in range(1, length + 1):
            day = start + timedelta(days=hd - 1)
            if day > last_g:
                break  # the final month's tail is fixed at LAST_GREGORIAN_DAY
            expected[day.isoformat()] = f"{label}-{hd:02d}"

    add_month(prev_label, date.fromisoformat(prev_g), (new_start - date.fromisoformat(prev_g)).days)
    if next_g:
        add_month(flip_month, new_start, (date.fromisoformat(next_g) - new_start).days)
    else:
        add_month(flip_month, new_start, (date(*bcd.LAST_GREGORIAN_DAY) - new_start).days + 1)
    if new != expected:
        raise AssertionError(
            "regenerated table does not match the planned flip "
            f"(diff outside months {prev_label} and {flip_month})"
        )


def affected_urls(base_url: str, changed_g: list[str], changed_h: list[str], limit: int = 8) -> list[str]:
    urls = [f"{base_url}/api/v1/meta"]
    for g in sorted(changed_g)[: limit - 1]:
        urls.append(f"{base_url}/api/v1/today/{g}")
        urls.append(f"{base_url}/api/v1/convert?date={g}&calendar=gregorian")
    urls.append(f"{base_url}/api/v1/convert?date={sorted(changed_h)[0]}&calendar=hijri" if changed_h else "")
    return [u for u in urls if u]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Apply a sidang-isbat flip to the curated table")
    ap.add_argument("--hijri", required=True, metavar="YYYY-MM",
                    help="flipped hijri month, e.g. 1447-10")
    ap.add_argument("--new-start", required=True, metavar="YYYY-MM-DD",
                    help="official gregorian month start")
    ap.add_argument("--reason", required=True, help="short reason, e.g. 'hilal tidak terlihat'")
    ap.add_argument("--base-url", default="https://api.mabims.dev", help="origin for spot-check URLs")
    ap.add_argument("--dry-run", action="store_true", help="plan and print, write nothing")
    ap.add_argument("--yes", action="store_true", help="skip the interactive confirmation")
    args = ap.parse_args(argv)

    try:
        hy, hm = (int(x) for x in args.hijri.split("-"))
        if not 1 <= hm <= 12:
            raise ValueError
        new_start = date.fromisoformat(args.new_start)
    except ValueError:
        ap.error("--hijri must be 'YYYY-MM' (hijri) and --new-start 'YYYY-MM-DD'")
        return 2

    month_name = MONTH_NAMES_ID.get(hm, str(hm))
    try:
        planned, published, delta = plan_flip(bcd.MONTH_STARTS, hy, hm, new_start)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    bcd.MONTH_STARTS.clear()
    bcd.MONTH_STARTS.update(planned)
    try:
        g2h, h2g = bcd.build()
        bcd.validate(g2h, h2g)
    except AssertionError as exc:
        print(f"error: planned flip produces an invalid table: {exc}")
        return 2

    old = json.loads(CAL_PATH.read_text(encoding="utf-8"))["gregorian_to_hijri"]
    verify_diff(old, g2h, f"{hy:04d}-{hm:02d}", delta, new_start)

    changed_g = [g for g in old if g not in g2h or g2h.get(g) != old[g]]
    changed_g += [g for g in g2h if g not in old]
    changed_h = [h for g, h in old.items() if g in changed_g]

    print(f"flip : 1 {month_name} {hy} H  {published.isoformat()} -> "
          f"{new_start.isoformat()} ({delta:+d} day)")
    print(f"day mappings changed: {len(changed_g)}")
    print(f"hijri dates touched : {len(changed_h)}")
    print(f"coverage            : {min(h2g)} -> {max(h2g)}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    if not args.yes:
        answer = input(f"Apply and write {CAL_PATH.name} + divergences.json? [y/N] ").strip().lower()
        if answer != "y":
            print("aborted — nothing written")
            return 1

    payload = {
        "gregorian_to_hijri": dict(sorted(g2h.items())),
        "hijri_to_gregorian": dict(sorted(h2g.items())),
    }
    tmp = CAL_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(CAL_PATH)

    raw = json.loads(DIV_PATH.read_text(encoding="utf-8")) if DIV_PATH.exists() else {"divergences": []}
    entries = raw.get("divergences", []) if isinstance(raw, dict) else raw
    entries.append({
        "hijri_month": f"{hy:04d}-{hm:02d}",
        "published_start": published.isoformat(),
        "official_start": new_start.isoformat(),
        "delta_days": delta,
        "reason": args.reason,
        "recorded_at": datetime.now(TZ_WIB).isoformat(),
    })
    out = {"divergences": entries}
    dtmp = DIV_PATH.with_suffix(".json.tmp")
    dtmp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    dtmp.replace(DIV_PATH)

    print(f"wrote {CAL_PATH.name} ({len(g2h)} entries)")
    print(f"appended divergence entry -> {DIV_PATH.name}")
    print("\ncache: CI purges the CDN zones on push to main. Spot-check URLs after deploy:")
    for u in affected_urls(args.base_url, changed_g, changed_h):
        print(f"  {u}")
    print("\nnext steps:")
    print("  1. cd api && .venv\\Scripts\\pytest && .venv\\Scripts\\ruff check .")
    print("  2. commit build_calendar_data.py + data/calendar_data.json + data/divergences.json")
    print("  3. push -> CI validates, deploys and purges the CDN")
    print("  4. publish the mabims-hijri SDK release (bundled table refresh)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
