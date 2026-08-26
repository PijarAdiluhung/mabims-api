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

## Beyond the table: forward computation only

Requests after the table end are answered by forward computation:

1. **`mabims-computed`** — the Neo MABIMS criteria evaluated live at Sabang
   (hilal altitude ≥ 3° and elongation ≥ 6.4° at sunset on day 29). This is the same
   rule the curated table follows, so it stays on-method into the future.
   Months decided by a margin under 0.25° carry a borderline warning.
2. **`fallback:aladhan-ummalqura`** — Umm al-Qura via Aladhan as a last resort,
   fetched lazily per month and cached at the origin.

:::caution[No backward walk]
The system **cannot** convert dates before 2024-01-13. The backward-walking algorithm is not available.
:::

## Hard limits

| Direction | Limit | Note |
|-----------|-------|------|
| Backward | 2024-01-13 | No conversion before this date |
| Forward | 2053-08-01 | No conversion after this date |

Dates outside these bounds are rejected with a `date_out_of_supported_range` error.

## Monitoring

[`GET /meta`](/endpoints/meta) exposes `computed_active`, `computed_months`,
`fallback_active` and `fallback_months`. The [live status](/playground) panel on the
Playground page reads it in real time.
