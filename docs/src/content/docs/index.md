---
title: MABIMS Date Converter API
description: Accurate Gregorian ⇄ Hijri conversion following the MABIMS standard.
template: splash
---

<div class="hero-badges">

`GET /api/v1/today` · `GET /api/v1/convert` · `GET /api/v1/range`

</div>

Accurate conversion between the **Gregorian** and **Hijri** calendars using the **MABIMS**
standard — the moon-sighting criteria adopted across **Singapore, Indonesia and Malaysia**.
Not an astronomical approximation: every date comes from a curated MABIMS lookup table.

## Try it

```bash
curl "https://api.example.com/api/v1/today"
```

Head to the [Playground](/playground) to test conversions against the live API.

## Why MABIMS?

Generic Hijri APIs (e.g. Umm al-Qura based) can differ from locally observed dates by ±1 day
around month boundaries. When your app displays prayer schedules or Islamic events for
Southeast Asian users, that one day matters. This API serves the table used by regional
religious authorities — and clearly marks any fallback data with its source.

## Get started

- [Quickstart](/quickstart) — make your first request in under a minute
- [API Reference](/endpoints/convert) — every endpoint, parameter and response shape
- [Data Coverage](/data-coverage) — what date range the table covers and how fallback works

:::note[Access]
Reads are fully public — no keys needed. See [Access & Rate Limits](/access) for details.
:::
