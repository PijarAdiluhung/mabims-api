---
title: Changelog
description: History of changes to the MABIMS API and documentation.
---

## Documentation Updates — 2026-08-28

- Landing page with live JSON preview and latency badge
- Documentation site (Astro + Starlight)
- Blog (3 articles: story, tutorial, hilal behind-the-scenes)
- FAQ page (bilingual)
- Playground (converter + hilal visualization)
- Migration guide from Aladhan API
- Error response examples in all API reference pages
- Sidebar reorganized: "FAQ", Changelog

---

## 1.1.0 — 2026-08-28

### Added

- **GET /events** — Islamic observance dates (1 Muharram, Maulid Nabi, Ramadan start, Eid al-Fitr, Eid al-Adha) from the MABIMS table, extended with computed dates beyond table coverage.
- **GET /hilal/info** — hilal visibility data: Neo MABIMS criteria (hilal ≥ 3°, elongation ≥ 6.4°), moon position, TERLIHAT / TIDAK TERLIHAT verdict.
- **GET /hilal/viz** — PNG sky chart visualization 720×1280: moon position, crescent orientation, criteria table, computed at Sabang.

---

## 1.0.0 — 2026-08-28

### Added

- **GET /today** — Hijri date for "now", timezone-aware (default Asia/Jakarta). Dynamic edge-cache TTL.
- **GET /today/{date}** — immutable variant for specific dates, cache-forever.
- **GET /convert** — single date conversion between Gregorian and Hijri (bidirectional). `Cache-Control: max-age=86400`.
- **GET /range** — bulk conversion for date ranges (max 400 days). Each item carries its own `source`.
- **GET /month** — monthly calendar grid, 29–30 items per month.
- **Official MABIMS table** — data from Kemenag RI, coverage 2024-01-13 to 2026-12-31.
- **Fallback chain** — MABIMS table → Neo MABIMS computed (Sabang).
- **CDN caching** — Bunny CDN, dynamic TTL based on timezone, origin sees ~1 request per edge location per day.
- **CORS** — flexible, client-side apps on any domain can call directly.
- **Rate limiting** — 240 requests per minute per IP, 429 when exceeded.
- **GET /meta** — data coverage info, fallback status, data version.
- **GET /healthz** — liveness probe for uptime monitoring.
- **CI/CD** — GitHub Actions, ruff + mypy, schema contract tests, yearly table regen workflow.
