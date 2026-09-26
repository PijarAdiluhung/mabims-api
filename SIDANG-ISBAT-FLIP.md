# Sidang Isbat Flip — Runbook

What happens when Kemenag's Sidang Isbat decrees a month start that differs
from the **published** Kemenag calendar. The correction is a pure data event:
an edit to one anchor line, propagated through the curated table, and loudly
reported by the API. No runtime code changes, no schema changes.

> Background: the curated table always wins over the computed tier at
> request time. A flip edits the curated anchors; the computed seed stays as
> the criteria's own prediction, which is exactly what the divergence
> warnings compare against.

## The pieces

| Piece | Path | Role |
|---|---|---|
| Anchor source | `api/scripts/build_calendar_data.py` (`MONTH_STARTS`) | One line per Hijri month: `"2026-02-19": (1447, 9)`. The single point of edit. |
| Curated table | `api/data/calendar_data.json` | Generated from the anchors. Never hand-edited. |
| Flip history | `api/data/divergences.json` | Append-only registry of every override (published vs official, reason, timestamp). Written by the script, read by the app + CI. |
| Flip script | `api/scripts/apply_flip.py` | Edits one anchor (no cascade), regenerates + validates the table, appends history, prints spot-check URLs. |
| Validator | `api/scripts/validate_mabims.py` | Table-vs-criteria check in CI. Reported `OVERRIDDEN` (not failing) for acknowledged flips. |
| Seed regen | `api/scripts/generate_seed.py` | Yearly. Tolerates — but states — curated-vs-computed mismatches inside an acknowledged flip's cascade. Curated stays authoritative. |

## How a flip is represented

One isbat night decrees ONE month start — the flip moves that month's
anchor line only; **no cascade**: every other anchor stays byte-identical
to what Kemenag published. The ±1 must be absorbable by the two adjacent
months (each length must stay 29/30), which the script enforces and which
also proves the delta direction:

- `+1` flip: only when month F−1 is published with 29 days (→ 30; the isbat
  decision) and month F with 30 (→ 29)
- `−1` flip: the mirror — F−1 published 30 (→ 29), F published 29 (→ 30)

When the published neighbours don't allow it (a `(30, 30)` or `(29, 29)`
pair), the correction belongs to the *adjacent* anchor — flip that month's
start instead (the decree for the boundary that the observation actually
settled). Later month starts remain the published predictions until their
own isbat nights decree them; each such night is its own flip entry.
(Encyclopaedic note: in the last four years this has never happened —
`divergences.json` starts empty.)

```
--hijri 1447-10 --new-start 2026-03-20        (published said 2026-03-21)
  Ramadhan 1447: 30 -> 29 days (the isbat decision; its day 30 disappears)
  Syawal 1447:  re-anchored one day earlier, rows rebuilt inside the month
  Dzulqa'dah and everything else: byte-identical to the published table
```

## Step by step (announcement night)

```powershell
# 1. Plan first, look at it (writes nothing)
cd api
.venv\Scripts\python -m scripts.apply_flip --hijri 1447-10 --new-start 2026-03-22 `
    --reason "hilal tidak terlihat" --dry-run

# 2. Apply (regenerates calendar_data.json, appends divergences.json,
#    prints spot-check URLs, runs the internal validation)
.venv\Scripts\python -m scripts.apply_flip --hijri 1447-10 --new-start 2026-03-22 `
    --reason "hilal tidak terlihat" --yes

# 3. Local gates before pushing (pytest + ruff are deploy gates; mypy too)
.venv\Scripts\pytest -q
.venv\Scripts\ruff check .
.venv\Scripts\mypy

# 4. Commit exactly three files
git add scripts/build_calendar_data.py data/calendar_data.json data/divergences.json
git commit -m "flip: 1 Syawal 1447 -> 2026-03-22 (sidang isbat)"
git push
```

The push deploys by itself: the Dokploy image build runs the gates (the
flipped boundary reports `OVERRIDDEN`) → pytest / ruff → pipeline marks ❌
and the old build keeps serving when anything fails. After it goes live,
the GitHub `Prod monitor` workflow **purges both CDN zones** and verifies
the live endpoints, so propagation is minutes, not the 24h endpoint TTL.

## After-deploy verification (spot check)

```
curl https://api.mabims.dev/api/v1/meta            # table_version + divergences[] updated
curl "https://api.mabims.dev/api/v1/convert?date=2026-03-22&calendar=gregorian"
```

Expected on every response touching the flipped month (or the month before
it):

```json
"warnings": [
  "kemenag_override: 1 Syawal 1447 H resmi 2026-03-22 (Sidang Isbat; kalender terbit Kemenag: 2026-03-21, delta +1 hari)."
]
```

`source` stays `mabims` — curated data, it just changed. `/hilal/info` and
the history index report the same warning when the criteria verdict and the
official decision disagree.

## Client detection

Clients poll `/api/v1/meta` (5-min cache): `table_version` is `none` in an
override-free world and changes (count + fingerprint) with every flip;
`divergences[]` carries the full history newest-first.

## Follow-ups on announcement night

1. SDK: publish a `mabims-hijri` release so the bundled 2024–2026 table
   reflects the flip (its live-API fallback covers the gap meanwhile).
2. Hilal image pack: `render_version` derives from criteria + site lists —
   a flip alone does **not** invalidate it (cards are astronomically
   correct; the override is reported in warnings only).
3. Blog / FAQ update if the divergence is newsworthy (see docs plan below).

## Rollback

Append another entry with the published date restored (`--new-start` =
published start); never edit history entries in place. `recorded_at` keeps
the full story.

## Full revised calendar (rare)

If Kemenag publishes a wholesale revised calendar (multiple months move):
edit `MONTH_STARTS` wholesale, then:

```powershell
$env:MABIMS_ALLOW_FLIP="1"; .venv\Scripts\python scripts\build_calendar_data.py
```

…then record the revision in `divergences.json` by hand (one entry per
month that differs) and follow step 3 onward above.

## Docs page plan (mabims.dev)

New Starlight doc page, above **Data Coverage** in the sidebar:

- Sidebar entry (both locales), `docs/astro.config.mjs` after the
  JavaScript SDK group:
  `{ label: 'Sidang Isbat & Koreksi', link: '/isbat-koreksi', translations: { en: 'Sidang Isbat Corrections' } }`
- Files: `docs/src/content/docs/isbat-koreksi.md` + `docs/src/content/docs/en/isbat-koreksi.md`
- Content outline:
  1. **Why a flip can happen** — published calendar vs the rukyat session that actually decides; the API mirrors the *decision*, not the paper.
  2. **What you will see** — example `warnings[]` payload (`kemenag_override:`), `/meta` `divergences[]` + `table_version`, sourcing stays `mabims`.
  3. **What does NOT change** — computed criteria results; hilal cards remain astronomically correct and are annotated with the official outcome.
  4. **Client integration recipe** — poll `/meta.table_version`, on change re-fetch affected dates; parse the `kemenag_override` warning prefix.
  5. **History** — table of recorded flips (generated from `divergences.json`, starts empty: "no divergence has ever been recorded").
- Keep it imperative-free of repo internals on the public page (no script
  paths); the operational detail lives in this runbook.
