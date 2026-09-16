---
title: Sidang Isbat Corrections
description: When a Sidang Isbat session decrees a month start that differs from the published Kemenag calendar — how the API surfaces it.
---

The published Kemenag calendar is produced from Neo MABIMS calculations, and for years its results have always been confirmed at the Sidang Isbat. In principle, though, the month start is **decided on the night of the Sidang Isbat** (the rukyat on day 29), not on the printed calendar. If that decision differs from the published one, the API follows the **official decision** — and says so, loudly.

## Why a difference can happen

The published calendar is a criteria prediction; the Sidang Isbat decision is what binds. The difference is at most ±1 day and it affects two months at once:

- the month whose start was published and overridden: its length changes 29↔30 days (the substance of the Isbat decision);
- the following months: their starts stay exactly as published until their own Sidang Isbat resolves them.

## What you will see

Every response touching the corrected month (or the month before it) carries a warning:

```json
{
  "warnings": [
    "kemenag_override: 1 Syawal 1447 H official 2026-03-20 (Sidang Isbat; published Kemenag calendar: 2026-03-21, delta -1 days)."
  ]
}
```

`source` remains `mabims` — the same data, just corrected.

`/meta` exposes the correction history, two slim fields per correction:

```json
{
  "table_version": "1-a41d3c9be021",
  "divergences": [
    { "hijri_month": "1447-10", "delta_days": -1 }
  ]
}
```

## What does NOT change

- The Neo MABIMS criteria results (`mabims-computed`, hilal cards) remain astronomically correct — the Isbat correction only reports the official decision in warnings, it does not alter the astronomy.
- Response shapes, error codes and endpoints are unchanged. Fields and warnings are additive.

## Client integration recipe

1. Poll `/meta` once a day (5-minute cache, cheap).
2. Compare `table_version` with the one you stored. `"none"` means no correction has ever been applied.
3. When it changes: read `divergences[]`, then re-fetch the dates falling in the corrected month and the month before it.
4. Alternatively: catch the `kemenag_override:` prefix on any response's `warnings[]` and surface it to your users.

## History

> So far **no correction has ever been applied** — `divergences[]` is empty and `table_version` is `"none"`. This page will be updated if a Sidang Isbat ever corrects the published calendar.

Implementation details live in `SIDANG-ISBAT-FLIP.md` in the repository.
