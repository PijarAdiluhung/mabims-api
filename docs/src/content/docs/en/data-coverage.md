---
title: Data Coverage
description: How far the MABIMS table reaches, and what happens beyond it.
---

## Authoritative coverage

The curated MABIMS lookup table currently covers:

```{=html}
2025-01-01 → 2026-12-31
```

MABIMS month starts are set by local moon-sighting criteria, so the table is produced per
year by regional religious authorities. It does **not** extrapolate astronomically.

## Beyond the table: marked fallback

Requests outside coverage are still answered — from an **Umm al-Qura** source (Aladhan),
fetched lazily per Hijri/Gregorian month and cached at the origin.

These responses are never silent about it:

```json
{
  "source": "fallback:aladhan-ummalqura",
  "warnings": [
    "Date is outside MABIMS table coverage; served from the Umm al-Qura fallback and may differ from MABIMS by around one day."
  ]
}
```

:::caution[±1 day drift]
Umm al-Qura and MABIMS can disagree on month starts. For religious-critical dates during a
fallback period, verify against local announcements.
:::

## Monitoring

[`GET /meta`](/endpoints/meta) exposes `fallback_active` and `fallback_months`. The
[live status](/playground) panel on the Playground page reads it in real time.
