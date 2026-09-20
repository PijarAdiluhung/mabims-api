---
title: Changelog
description: History of changes to the MABIMS API and documentation.
---

---

## 1.10.0 — 2026-09-21

### Added

- **`weekday` field on all dates** — `/today`, `/today/{date}`, `/convert` (including `next`), `/range`, `/month`, and `/year` now carry the Indonesian weekday name for the same civil day: `"weekday": "Ahad"`, `"Selasa"`, ..., `"Sabtu"`. Sunday is written **Ahad** (the Kemenag convention), not "Minggu". The name is derived from the Gregorian date of the same physical day, so Hijri and Gregorian views of one date always agree.
- **OpenAPI description** for the new field via `schema.weekday` (bilingual).

### Notes

- Additive change (semver minor, non-breaking): the new field is always present on `output`/items; no field is removed or retyped. Clients that don't care about weekday names can ignore it.
- Documented samples on the endpoint pages, landing page, and README were updated alongside; the documentation site now uses `output.weekday` straight from the API with a local fallback for old snapshots.

---

## 1.9.0 — 2026-09-20

### Added

- **`include` parameter on `GET /api/v1/events`** — the 5 base events are returned by default (unchanged responses), and optional extras can now be requested: `include=extra` adds the tier-2 observances (Isra Mi'raj 27 Rajab, Nuzulul Quran 17 Ramadan, Arafah 9 Dhul Hijjah, Tasu'a 9 Muharram, Ashura 10 Muharram, Days of Tashriq 11–13 Dhul Hijjah), `include=ayyamul_bidh` adds the white days (13–15 of every Hijri month, 14–16 in Dhul Hijjah since the 13th is a Tashriq day, one ranged event per month, 12 per year), individual slugs can be cherry-picked, and `include=all` returns everything.
- **`date_range` field on event items** — multi-day events (`tasyrik`, `ayyamul_bidh`) carry `hijri_start`, `hijri_end`, `gregorian_start`, `gregorian_end`; single-day events have `date_range: null`. Optional field, non-breaking.
- **`input.include` echo** — the response echoes the requested include set (sorted, `null` when unset) so clients can verify what ran.
- **400 `invalid_include`** — unknown include tokens (e.g. `include=ayahsura`) are rejected with a message naming the invalid value.

### Notes

- For clients: existing calls keep returning `count: 5` with the same envelope; only opt-in requests change shape. All new dates are fixed Hijri mappings — within the curated table they are `source: mabims`; beyond it they follow the computed/retro tiers like the base events.
- The npm SDK `mabims-hijri@1.4.0` supports `events(year, calendar, { include })` with the same tokens, computing extras offline from the bundled table.

---

## 1.8.2 — 2026-09-19

### Added

- **ETag + 304 Not Modified on every 200** — every response now carries an **ETag** header; send `If-None-Match: <etag>` (weak comparison, or `*`) and the server answers a bare **304** with the same `Cache-Control` and ETag. Applies to all cacheable endpoints (`/today`, `today/{date}`, `convert`, `range`, `month`, `year`, `events`, `/hilal/*`).
- **`invalid_bare` and `invalid_download` error codes** — the `bare`/`download` params on `/hilal/viz` and `/hilal/map` are now strictly validated; non-boolean values are rejected with 400.
- **`GET /api/v1/months`** — new static endpoint returning the 12 Hijri month names with their numbers. No parameters required, cacheable (`max-age=86400`), rate-limit exempt. Useful for populating dropdowns or labels in UIs.

### Changed

- **Uniform error envelope `{"error":{"code","message"}}` on every error response** — including generic 404s on unknown paths (`not_found`) and the **429 rate limiter** (`rate_limit_exceeded`), which now sends a **`Retry-After`** header (integer seconds to wait).
- **No more raw FastAPI 422s** — malformed amounts return 400 (`invalid_year`/`invalid_month`/`missing_parameter`) and malformed booleans return 400 `invalid_<name>`; `retro`/`next`/`bare`/`download` accept `true`/`false` (case-insensitive) and `1`/`0`. Absent or empty = false.
- **The seed now covers the entire supported window** — approx. 1945-01-01 (Hijri months starting 1944-12-17) through 2100-01-01, so there is **no lazy computation at runtime at all**. Previously the seed only reached back to 1970 and forward to ~2050.
- **Borderline warning semantics tightened** — a Hijri month is flagged "close to the Neo MABIMS visibility threshold" **only when** its day-29 sighting evening **passed** both criteria (alt ≥ 3.0°, elong ≥ 6.4°) with a margin **< 0.25°**. Rejected months (no passing site) never get this warning; roughly 3% of computed months are borderline.
- **`/meta` now reports version 1.8.2**, and the OpenAPI spec documents `contact`/`license`/`externalDocs`, parameter examples, and the 304 response.
- **Reusable OpenAPI components** — the `retro`, `next`, `bare`, `download` parameters and error responses (404, 429, 400, 500, 503) are now defined once in `components/parameters` and `components/responses`, then referenced via `$ref` across all endpoints. The spec is shorter and descriptions can't drift between endpoints.

### Notes

- For clients: honor `Retry-After` on 429 and use `If-None-Match` to save bandwidth — a 304 fallback makes polling cheap.

---

## 1.8.1 — 2026-09-18

### Added

- **Per-endpoint OpenAPI responses** — every endpoint now declares its own `responses` blocks (400/404/429, etc.) with error body examples, so API clients (Scalar, Swagger UI, generators) render realistic failure scenarios instead of generic ones. See `openapi.json` or the [Scalar playground](https://api.mabims.dev/playground).
- **`servers` declared in the OpenAPI spec** — the spec pins `https://api.mabims.dev`, so generated/interactive clients always resolve the live origin with no extra configuration.
- **Embedded API client on every endpoint doc** — a *Test Request* button opens the Scalar API client preloaded with the live spec; the full playground remains as a fallback.

### Changed

- **OpenAPI descriptions rewritten and localized** — endpoint summaries/descriptions were rewritten for clarity and translated to Indonesian.
- **Endpoint pages restructured** — each endpoint now has a Scalar-style request card (`GET /…` + *Test Request* button), with parameters, examples and errors grouped per endpoint, and request lines that now include optional params (`next`, `retro`).

### Notes

- Docs/spec only — no runtime behaviour or response-contract changes.

---

## 1.8.0 — 2026-09-16

### Added

- **`?next=true` on `GET /today`** — also returns the Hijri date that begins at this evening's maghrib (the next civil day's mapping) as a `next` object with its own `source`. The API does not compute sunset — clients gate the flip on their own maghrib time. Supports all timezones like `/today`.
- **Sidang Isbat corrections** — the published calendar now has an official correction path when a Sidang Isbat session decrees a month start that differs from the published Kemenag calendar: `/meta` exposes **`divergences[]`** (the correction history, newest first) and **`table_version`** (a version token for that history; `"none"` when there are no corrections, changes whenever one is applied).
- **`kemenag_override:` warning** — responses touching a corrected month (and the month before it, whose length changes) now carry a warning naming the official date (Sidang Isbat) vs the published calendar plus the day delta. Automatic across convert, month/year, events and `/hilal/info`; `source` stays `mabims`.

### Notes

- No behaviour change while no correction is on record: `divergences[]` is empty and `table_version` is `"none"`. Fields and warnings are additive, no breaking change.
- Client integration details: the [Sidang Isbat Corrections](/en/isbat-koreksi) page.

---

## 1.7.0 — 2026-09-13

### Added

- **Bare cards (/hilal/viz + /hilal/map `?bare=true`)** — drops the criteria panel and returns a high-resolution **1440×1520** card (header + graphic + callout/verdict + logo) for use as a web hero image. The full 720×1280 card is unchanged. Bare variants are pre-rendered into the CDN image pack (one tar with `viz/` + `map/` + `viz-bare/` + `map-bare/`).
- **`download=true` (/hilal/viz + /hilal/map)** — sends `Content-Disposition: attachment` so download links work cross-origin (the HTML `download` attribute is ignored for cross-origin URLs).
- **`GET /api/v1/hilal/history?from=&to=`** — per-month summaries for a whole Hijri range (default **1444-08 → 1475-12**) from the precomputed `api/data/hilal_index.json` (`scripts/generate_hilal_index.py`), so the history list needs a single request. Rate limit 240/min.
- **`scripts/build_imagepack.py`** — one-command image-pack builder: render (or `--skip-render`), then write a deterministic tar + `manifest.json` whose `render_version` derives from the site lists + display points + renderer sources.
- **Public `/hilal` page** — today's Hijri date, countdown to the next deciding evening, zoomable bare map + sky chart, and a history list with inline info panels. The site now shares `LandingLayout.astro` between the landing page and `/hilal`.

---

## 1.6.1 — 2026-09-11

### Changed

- **Hilal cards ~10x faster** — the map/chart cards now read their astronomy from a **SQLite cache of astronomy facts** (0.25° grid, 95 display points, 25-site model, world minimap), keyed by sighting evening + ephemeris tag + site-list fingerprint. The runtime only reads; writes come from the build script (`scripts/prime_astro_cache.py`, resumable + parallel). The cache auto-downloads on first boot into the `/data` volume (`MABIMS_ASTROCACHE_URL`), same pattern as the ephemeris file.
- **Ephemeris de421 → de440s** (JPL coverage 1849–2150) and **forward cap 2053-08-01 → 2100-01-01**. The computed seed now runs through 2099-12-31.
- **PNG card render cap: Hijri 1444–1475** — `hilal_image_range` on `/meta` is now a hard cap for `/hilal/viz` + `/hilal/map`; outside it the endpoints refuse with `out_of_coverage` (the date data cap stays `coverage.forward_ceil` = 2100). 1444–1450 ship pre-rendered; other months inside the cap render on demand in seconds from the astronomy cache.
- **Map card: criteria table → min-max gauges** — the `ALT. BULAN`/`ELONGASI` rows on `/hilal/map` now show the **min–max range across all 95 display points** as a bar: red = points below the MABIMS minimum, green = points that pass, tick + `min. MABIMS` label at the 3.0°/6.4° threshold. The scale is adaptive per month (the bar fills for comfortable months, tightens for borderline ones). LOLOS/GAGAL chips and the MIN./STATUS columns are gone.
- **Hilal card font: DejaVu → Selawik** — all viz + map text now renders in **Selawik** (SIL OFL, metric-compatible with Segoe UI), bundled in `api/app/hilal/assets/` so Windows and Linux server output are identical.
- **Pre-rendered cards now CDN-hosted (image pack)** — the 1444–1450 set (viz+map, 168 PNGs) is no longer committed to the repo; it ships as a versioned tar + `manifest.json` on the CDN (`MABIMS_IMAGEPACK_URL`, default `mabims-dev.b-cdn.net/hilal_images`). At runtime the manifest is probed, the tar downloaded, sha256-verified, and extracted per-file into the `/data` volume (`app/hilal/imagepack.py`) — lazily rendered out-of-range cards survive installs. Failures log under `mabims.imagepack` and endpoints fall back to on-demand rendering. Set `MABIMS_DISABLE_IMAGEPACK=1` to opt out.

### Notes

- The sunset Newton solve went from 8 to 3 iterations: measured zero result difference (max 0.00015°). No values or verdicts changed — speed only.

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
