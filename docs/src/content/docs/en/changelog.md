---
title: Changelog
description: History of changes to the MABIMS API and documentation.
---

## 1.6.0 — 2026-09-10

### Added

- **`/hilal/map`** — a 720×1280 archipelago visibility-map card: the region where the Neo MABIMS criteria are met at local sunset, the altitude-3° / elongation-6.4° boundary lines, and **95 display points** (green = meets the criteria, gray = does not). The deciding point from the 25-site model is marked with a yellow ring. The card's table uses the **same deciding point as `/hilal/viz`**, plus `TITIK MEMENUHI` / `TITIK TIDAK MEMENUHI` counts. Rate limit 30/hour, immutable `Cache-Control`.
- **Hilal playground** now shows the map and the sky chart side by side, each with a PNG download link.

### Notes

- The 95 map points are a **display** set used to communicate coverage; the month verdict still comes from the 25-site model and is unchanged (0 month-length differences over 1970–2051).

---

## 1.5.0 — 2026-09-09

### Changed

- **Multi-site hilal criteria (`neo-mabims-multisite`)** — the hilal verdict now follows the Kemenag convention: **topocentric** moon altitude (refraction applied) ≥ 3.0° and **geocentric** elongation ≥ 6.4°, evaluated at each site's own local sunset on day 29 across **25 coastal observation sites** from Sabang to Rote (previously: geocentric altitude at Sabang only). Met at any single site → 29-day month. Validated 48/48 against the curated table.
- **Computed seed regenerated** with the new model — **10 month starts shifted ±1 day** (7 retro: 1393-02, 1395-03, 1396-03, 1398-02, 1410-03, 1428-11, 1436-10; 3 forward: 1452-05, 1466-07, 1467-11). The curated table is unchanged.
- **`/hilal/info` semantics** — `moon_alt_deg`, `elongation_deg`, `moon_az_deg`, `sun_alt_deg`, `sunset`, `moonset` now describe the **deciding site** (previously Sabang); times are shown in the site's own timezone (WIB/WITA). Response shape unchanged.
- **`/hilal/viz`** — sky scene, criteria table and times all at the deciding site; new **TITIK PENGAMAT** row; the header location line was replaced by that row.
- `/meta` — `method` is now `neo-mabims-multisite`.

### Added

- **`deciding_site`** on `/hilal/info` — `{ name, lat, lon, elev_m, tz }` object for the site the reported values describe: the decider when visible, the best-margin site otherwise.
- **`sites_checked`** on `/hilal/info` — number of observation points evaluated (25).
- **Site list as data** — [`api/data/hilal_sites.json`](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json): adding or moving sites is now a data PR, not a code change.

### Notes

- Response-shape changes are additive (minor), but several field **semantics** changed — clients relying on Sabang altitude/elongation values should read `deciding_site`.

---

## 1.4.0 — 2026-09-02

### Added

- **2023 curated data** — the official Kemenag RI table now starts 2023-01-23 (Rajab 1444 H), adding one year of official coverage.
- **`mabims-retro` tier** — dates below the curated table are now accessible with `retro=true` (down to 1945-01-01), computed by projecting the Neo MABIMS criteria backwards. The computed seed now extends back to 1970. New error: `invalid_retro`.

## 1.2.1 — 2026-08-29

### Fixed

- **CORS headers on cached responses** — `Access-Control-Allow-Origin` was only added when the request carried an `Origin` header. BunnyCDN cached the headerless variant and blocked cross-origin `fetch()` in browsers. All responses (OPTIONS, errors, and GET without Origin) now always include CORS headers.
- **README `/range` error table** — `range_too_large` incorrectly said "400 days"; fixed to 45.
- **404 page in sitemap** — `/en/404/` is no longer included in the sitemap.

### Changed

- **`calendar` defaults unified** — `/convert` and `/range` default to `gregorian` (matching their `YYYY-MM-DD` input format). `/month`, `/year`, `/events` default to `hijri` (matching the API's identity). Previously only `/year` defaulted to `hijri`.
- **Docs reorganized** — `/convert` & `/range` merged into one page (gregorian), `/month` & `/year` merged into one page (hijri), `/events` kept separate.

### Security

- **`X-Content-Type-Options: nosniff`** — added to all API responses.

---

## 1.2.0 — 2026-08-29

### Added

- **GET /year** — all days in a year (12 months in one call). `calendar` must be `hijri` or `gregorian`. Response contains a `months` object keyed 1–12, each holding an array of items identical to `/range`. Much simpler than calling `/month` 12 times.

### Changed

- **`/range` max 45 days** — the `/range` limit for `calendar=gregorian` is reduced from 400 days to 45 days. For longer spans, use `/month` or `/year`.

### Fixed

- **Hilal viz caching in docs** — documentation incorrectly stated `Cache-Control: private` for `/hilal/info` and `/hilal/viz`. The code actually sends `public, s-maxage=86400` (CDN-cached). Docs now reflect the actual behavior.

### Updated

- Calendar playground now uses `/year` (1 request) instead of 12 `/month` calls.
- Docs: `/range` limit updated across all pages (ID & EN), landing page, sidebar, README.

---

## 1.1.1 — 2026-08-29

### Fixed

- **Out-of-table Hijri months** — `/month` and `/range` with `calendar=hijri` are now served from the Neo MABIMS computed tier (previously only dates inside the official table were reachable through these two endpoints).
- **Hijri `/range` day-31 bug** — `/range?calendar=hijri` failed with `out_of_coverage` whenever the range crossed a month boundary (Hijri months have no day 31). It now walks Hijri months month-by-month.
- **24-question Safar day 30 rejected** — `YYYY-02-30` is a valid Hijri date (Safar can have 30 days) but was rejected as `invalid_date` because the Gregorian parser knows no Feb 30. The Hijri parser now separates syntax validation (days 1–30) from data existence; genuinely absent days (e.g. day 30 in a 29-day month) honestly return `404 date_not_found`.

---

## Documentation Updates — 2026-08-29

### Legal Compliance

- **Footer redesigned** — inline legal links (Terms · Privacy · Data Sources · Disclaimer), dropped inline disclaimer text.
- **New pages**: `/terms`, `/privacy`, `/data-sources`, `/disclaimer` (bilingual ID+EN), collapsed under "Legal" sidebar group.
- **Hilal viz labels updated** — verdict pill: "MEMENUHI KRITERIA" / "TIDAK MEMENUHI" / "MENDEKATI BATAS" / "DI BAWAH HORIZON". Chips: "MEMENUHI" / "TIDAK MEMENUHI".
- **Wording fixes** — "official/resmi" → "data publik" across README, landing page, footer, hilal docs, endpoint docs, playground, quickstart, FAQ, migration. Softened government affiliation language.
- **Schema descriptions** — `source`, `warnings`, `visible`, `alt_ok`, `elong_ok` fields now have OpenAPI descriptions.
- **Disclaimer section** added to README with non-affiliation clause.

### Updated

- New Calendar playground (`/playground/kalender`) — a full Hijri year, two columns, rendered live from `/month` and `/events`. Large number = Hijri date, small = Gregorian, Friday marked yellow, event badges, today marker.
- Calendar playground logic moved to a shared module (`src/lib/kalender.core.js`) so the ID & EN versions stay identical.
- `/range` & `/month` docs updated: `calendar=hijri` is now served from the computed tier beyond the public table.

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
