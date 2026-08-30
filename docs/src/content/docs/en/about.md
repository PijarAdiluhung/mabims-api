---
title: About MABIMS.dev
description: Free open-source API for the Indonesian Hijri calendar based on official MABIMS data from Kementerian Agama RI.
---

## What is MABIMS.dev?

MABIMS.dev is a free open-source API that provides an ecosystem for the Indonesian Hijri calendar. It uses official MABIMS data published by Indonesia's Ministry of Religious Affairs (Kementerian Agama RI), not Umm al-Qura (Saudi Arabia's standard).

## Who is it for?

- **Developers** building web or mobile apps with Hijri calendar features
- **Mosque and pesantren apps** that need to display fasting start, Eid al-Fitr, and Eid al-Adha dates matching Kemenag announcements
- **Islamic schools and universities** integrating Hijri dates into academic systems
- **Anyone** who needs accurate Indonesian Hijri dates

## Why MABIMS, Not Umm al-Qura?

Almost all Hijri calendar APIs and libraries default to Umm al-Qura. Umm al-Qura is Saudi Arabia's official calendar, designed for their needs — not Indonesia's.

Because the rukyah method and observation location differ, results can be ±1 day off from Kemenag's official decisions — especially for Ramadan start, Eid al-Fitr, and Eid al-Adha. MABIMS.dev uses public Kemenag RI table data and Neo MABIMS criteria (moon altitude ≥ 3°, elongation ≥ 6.4° at Sabang sunset) for dates beyond table coverage.

## What's Available?

| Endpoint | Function |
|---|---|
| `GET /today` | Today's Hijri date (timezone-aware) |
| `GET /convert` | Single date conversion (Gregorian ↔ Hijri) |
| `GET /range` | Bulk conversion up to 45 days |
| `GET /month` | All days in a month |
| `GET /year` | All days in a year (12 months) |
| `GET /events` | Islamic events (Ramadan, Eid al-Fitr, Eid al-Adha, 1 Muharram, Maulid Nabi) |
| `GET /hilal/info` | Hilal visibility data (JSON) |
| `GET /hilal/viz` | Hilal sky chart (PNG 720×1280) |

## How to Integrate a Hijri Calendar

MABIMS.dev is a standard REST API — works with JavaScript, PHP, Python, Dart, Swift, Kotlin, or any language that can make HTTP requests. No special libraries needed.

**Today's Hijri date:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/today");
const { day, month_name, year } = (await res.json()).output;
// "1448-03-14" → "14 Rabiul Akhir 1448 H"
```

**Convert a specific date:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/convert?date=2026-03-01&calendar=gregorian");
const { date } = (await res.json()).output;
// "1447-08-30"
```

**Full year calendar:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/year?year=1448&calendar=hijri");
const { months } = await res.json();
// 12 arrays, each containing all days in a Hijri month
```

See [Quickstart](/en/quickstart) for a full guide or try it in the [Playground](/en/playground/converter).

## Compared to Alternatives

For the Indonesian context, MABIMS.dev is more accurate than Umm al-Qura (Saudi standard, ±1 day off) and Aladhan API (which also defaults to Umm al-Qura). MABIMS.dev uses official Kemenag RI data, not data from another country's authority.

If you're currently using the Aladhan API, see the [Migration from Aladhan](/en/migration) guide for response format comparison and migration code examples.

## Specifications

| | |
|---|---|
| API | FastAPI + Pydantic v2 |
| Data | MABIMS tables (Hijri 1445–1448) + Neo MABIMS criteria (through ~2053) |
| Spec | OpenAPI 3.1 |
| License | MIT |
| Source | [github.com/PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api) |

## Get Started

```bash
curl "https://api.mabims.dev/api/v1/today"
```

See [Quickstart](/en/quickstart) or try it directly in the [Playground](/en/playground/converter).
