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
