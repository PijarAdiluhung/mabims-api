---
title: Data Coverage
description: How far the MABIMS table reaches, and what happens beyond it.
---

## Authoritative coverage

The curated MABIMS lookup table currently covers:

```{=html}
2024-01-13 → 2026-12-31
```

MABIMS month starts are set by local moon-sighting criteria, so the table is produced per
year by regional religious authorities. It does **not** extrapolate astronomically.

## Beyond the table: two computed tiers

Requests outside coverage are still answered, in this order:

1. **`mabims-computed`** — the Neo MABIMS criteria evaluated live at Sabang
   (hilal altitude ≥ 3° and elongation ≥ 6.4° at sunset on day 29). This is the same
   rule the curated table follows, so it stays on-method indefinitely into the future.
   Months decided by a margin under 0.25° carry a borderline warning.
2. **`fallback:aladhan-ummalqura`** — Umm al-Qura via Aladhan as a last resort,
   fetched lazily per month and cached at the origin.

These responses are never silent about it:

```json
{
  "source": "mabims-computed",
  "warnings": [
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria (hilal altitude >= 3 deg and elongation >= 6.4 deg at Sabang sunset)."
  ]
}
```

:::caution[±1 day drift]
Computed months near the visibility threshold can still shift once official
announcements land. For religious-critical dates outside table coverage, verify against
local announcements.
:::

## Monitoring

[`GET /meta`](/endpoints/meta) exposes `computed_active`, `computed_months`,
`fallback_active` and `fallback_months`. The [live status](/playground) panel on the
Playground page reads it in real time.
