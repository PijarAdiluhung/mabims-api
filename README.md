# MABIMS API


MABIMS.dev is an unofficial, free, open-source API that provides an ecosystem for the Indonesian Hijri calendar following the official Menteri Agama Brunei, Indonesia, Malaysia, Singapura criteria. Get today's Hijri date, date conversion tools, monthly and yearly calendars, hilal visibility data, and Islamic event dates. All based on MABIMS criteria from **Kementerian Agama Republik Indonesia** — the standard behind the [kalender Hijriah MABIMS](https://mabims.dev/kalender-hijriah/).

**[Landing page](https://mabims.dev)** · [Quickstart](https://mabims.dev/quickstart) — make your first request · [Playground](https://api.mabims.dev/playground) — test endpoints in-browser · [FAQ](https://mabims.dev/faq) · [Blog](https://mabims.dev/blog)

## Quick start

```bash
curl "https://api.mabims.dev/api/v1/today"
```
```json
{
  "input": { "date": "2026-08-27", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-14", "calendar": "hijri", "day": 14, "month": 3, "month_name": "Rabiul Akhir", "year": 1448 },
  "source": "mabims",
  "warnings": []
}
```

```bash
curl "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"
```
```json
{
  "input": { "date": "2025-01-03", "calendar": "gregorian", "tz": null },
  "output": { "date": "1446-07-03", "calendar": "hijri", "day": 3, "month": 7, "month_name": "Rajab", "year": 1446 },
  "source": "mabims",
  "warnings": []
}
```

```bash
curl "https://api.mabims.dev/api/v1/events?year=2025&calendar=gregorian"
```
```json
{
  "input": { "year": 2025, "calendar": "gregorian" },
  "count": 5,
  "events": [
    { "event": "awal_ramadan", "name": "Awal Ramadan", "hijri": "1446-09-01", "gregorian": "2025-03-01", "source": "mabims" },
    { "event": "idul_fitri", "name": "Idul Fitri", "hijri": "1446-10-01", "gregorian": "2025-03-31", "source": "mabims" },
    { "event": "idul_adha", "name": "Idul Adha", "hijri": "1446-12-10", "gregorian": "2025-06-06", "source": "mabims" },
    { "event": "1_muharram", "name": "Tahun Baru Islam", "hijri": "1447-01-01", "gregorian": "2025-06-27", "source": "mabims" },
    { "event": "maulid_nabi", "name": "Maulid Nabi Muhammad Shallallahu Alaihi Wasallam", "hijri": "1447-03-12", "gregorian": "2025-09-05", "source": "mabims" }
  ],
  "warnings": []
}
```

For more examples (hilal data, date ranges, calendar grids), see the [live docs, demo & API client](https://mabims.dev).

## Endpoints

Every endpoint supports `GET` and `HEAD`. All responses include a `source` field and `warnings[]` array.

The `source` field indicates where the data came from:

| `source` | Meaning |
|---|---|
| `mabims` | Curated from data publik yang dikeluarkan resmi oleh Kementerian Agama RI |
| `mabims-computed` | Computed with the Neo MABIMS multi-site criteria (moon altitude ≥ 3°, elongation ≥ 6.4° at local sunset, seen at any of 25 coastal sites) — algorithmic estimates, not official data |
| `mabims-retro` | Below the curated table (pre-2023): the same Neo MABIMS criteria projected backwards. Requires `retro=true`. The criteria did not exist before 2022, so treat these as historical estimates only |

| Endpoint | Purpose | Rate Limit |
|---|---|---|
| `GET /api/v1/today?tz=&next=` | Today's Hijri date, timezone-aware (default `Asia/Jakarta`). Add `next=true` for the Hijri date that begins after this evening's maghrib. Accepts any IANA timezone (e.g. `Asia/Kuala_Lumpur`, `Asia/Singapore`). | 240/min |
| `GET /api/v1/today/{date}` | Same as above for a fixed `YYYY-MM-DD` date. Immutable, CDN-cacheable forever. | 240/min |
| `GET /api/v1/convert?date=&calendar=` | Single date conversion, either direction. `calendar` must be `hijri` or `gregorian`. | 240/min |
| `GET /api/v1/range?start=&end=&calendar=` | Bulk conversion (≤45 days). `calendar` must be `hijri` or `gregorian`. Beyond table coverage, hijri ranges are served from the computed tier. | 240/min |
| `GET /api/v1/month?year=&month=&calendar=` | All days in a month. `calendar` must be `hijri` or `gregorian`. Hijri months beyond the table are served from the computed tier. | 240/min |
| `GET /api/v1/year?year=&calendar=` | All days in a year (12 months). `calendar` must be `hijri` or `gregorian`. | 240/min |
| `GET /api/v1/events?year=&calendar=&include=` | Islamic observances. Base 5 events by default; `include=extra` adds tier-2 observances (Isra Mi'raj, Nuzulul Quran, Arafah, Tasu'a, Asyura, Tasyrik), `include=ayyamul_bidh` adds the white days (13–15 every Hijri month), or cherry-pick slugs / `all`. | 240/min |
| `GET /api/v1/hilal/info?month=&year=` | Hilal visibility data for the evening deciding a month start (topocentric altitude + geocentric elongation at the deciding site). | 60/hour |
| `GET /api/v1/hilal/viz?month=&year=` | Hilal sky chart PNG (720×1280) with the criteria table — scene, values and times at the deciding site. Add `bare=true` for the panel-less high-resolution (1440×1520) web card, or `download=true` to send it as an attachment. | 30/hour |
| `GET /api/v1/hilal/map?month=&year=` | Hilal visibility map PNG (720×1280): the archipelago visible region, 95 display points and the all-indonesia min–max gauges. Add `bare=true` for the panel-less high-resolution (1440×1520) web card, or `download=true` to send it as an attachment. Available for Hijri 1444–1475 (pre-rendered for 1444–1450 via the CDN image pack, cached renders beyond); outside that range the endpoint refuses. | 30/hour |
| `GET /api/v1/hilal/history?from=&to=` | Per-month hilal summary for a Hijri range (`YYYY-MM`), from the precomputed index (1444-08 → 1475-12 by default). A single cheap lookup that powers the website's history list. | 240/min |

The hilal visibility criteria follow Neo MABIMS: **moon altitude ≥ 3.0°** (topocentric, refraction applied) and **elongation ≥ 6.4°** (geocentric), evaluated at each site's local sunset on day 29 across **25 coastal observation sites** around Indonesia (Aceh to Rote — see `api/data/hilal_sites.json`). The month has 29 days when the criteria are met at **any** site; the site that passed is reported as `deciding_site` by `/hilal/info`, which also carries `sites_checked`. `/meta` reports `method: neo-mabims-multisite`.

`/hilal/viz` draws the sky scene at the deciding site; `/hilal/map` draws the same criteria as an archipelago map — the visible region, the altitude-3°/elongation-6.4° isolines and **95 display points** (green = meets the criteria, gray = does not), with the deciding site ringed. Both cards share the same deciding point. The PNG endpoints are hard-capped at **Hijri 1444–1475** (`hilal_image_range` on `/meta` — a render cap, not the data cap); 1444–1450 come from the CDN image pack, the rest render on demand in seconds from the astronomy cache. Pass `bare=true` on either endpoint to drop the criteria panel and return a 1440×1520 card (header, graphic, logo) for use as a web hero image.

`/hilal/history` serves the whole per-month history from the precomputed `api/data/hilal_index.json` (generated by `api/scripts/generate_hilal_index.py`), so a client can render the full timeline with one request instead of one `/hilal/info` call per month. Regenerate the index whenever the criteria, site list or ephemeris change, or after extending the curated table.
| `GET /api/v1/meta` | Coverage, data version, fallback status. | 240/min |
| `GET /healthz` | Liveness probe. | no limit |

## Parameters

| Parameter | Values | Notes |
|---|---|---|
| `calendar` | `hijri`, `gregorian` | Default `gregorian` on `/convert`, `/range`. Default `hijri` on `/month`, `/year`, `/events`. |
| `date` | `YYYY-MM-DD` | ISO 8601 date format. |
| `tz` | IANA timezone or UTC offset | Default `Asia/Jakarta` (UTC+7). Examples: `Asia/Kuala_Lumpur`, `UTC+8`, `+08:00`. |
| `start`, `end` | `YYYY-MM-DD` | Used by `/range`. |
| `year` | Integer | Hijri or Gregorian year, depending on `calendar`. |
| `retro` | `true`, `false` | Default `false`. Unlocks computed retro dates below the curated table (down to 1945-01-01), tagged `mabims-retro`. Boolean flags accept `true`/`false` (case-insensitive) or `1`/`0`. |
| `next` | `true`, `false` | Default `false`. On `/today`, also returns the Hijri date that begins after this evening's maghrib (the next civil day's mapping) as `next`, with its own `source`. The API does not compute sunset — the client gates the flip on its own maghrib time. Same boolean acceptance as `retro`. |
| `month` | 1–12 | Hijri or Gregorian month. |
| `bare`, `download` | `true`, `false` | Default `false`. Hilal PNG endpoints only. Boolean flags accept `true`/`false` (case-insensitive) or `1`/`0`; anything else is rejected with 400 `invalid_bare` / `invalid_download`. `download` adds `Content-Disposition: attachment`. |
| `include` | CSV | `/events` only. Comma separated `extra`, `ayyamul_bidh`, `all`, or individual slugs (`isra_miraj`, `nuzulul_quran`, `arafah`, `tasua`, `asyura`, `tasyrik`). Invalid values → 400 `invalid_include`. |

Integer parameters (`year`, `month`) must be plain digits. Malformed integers
return 400 `invalid_year` / `invalid_month` (never FastAPI's 422 shape).

## Events

Default (`no include`) — the base 5, unchanged from v1:

| `event` slug | Name | Hijri date |
|---|---|---|
| `1_muharram` | Islamic New Year | 1 Muharram |
| `maulid_nabi` | Prophet Muhammad's Birthday | 12 Rabi' al-Awwal |
| `awal_ramadan` | Start of Ramadan | 1 Ramadan |
| `idul_fitri` | Eid al-Fitr | 1 Shawwal |
| `idul_adha` | Eid al-Adha | 10 Dhul Hijjah |

`include=extra` → tier-2 observances (not national holidays):

| `event` slug | Name | Hijri date |
|---|---|---|
| `isra_miraj` | Isra Mi'raj | 27 Rajab |
| `nuzulul_quran` | Nuzulul Quran | 17 Ramadan |
| `arafah` | Arafah fasting (Wukuf) | 9 Dhul Hijjah |
| `tasua` | Tasu'a fasting | 9 Muharram |
| `asyura` | Ashura fasting | 10 Muharram |
| `tasyrik` | Days of Tashriq | 11–13 Dhul Hijjah |

`include=ayyamul_bidh` → one ranged event per Hijri month (`date_range` field with the
13–15 span), 12 events per Hijri year. `include=all` → everything. Individual slugs
from tier 2 may also be cherry-picked, comma separated; `input.include` echoes what
was requested. Multi-day events (`tasyrik`, `ayyamul_bidh`) carry a `date_range` field;
single-day events have `date_range: null`.

## Error responses

All errors follow a consistent JSON shape:

```json
{
  "error": {
    "code": "invalid_date",
    "message": "'xyz' is not a valid ISO date (YYYY-MM-DD)."
  }
}
```

| HTTP Status | `error.code` | When |
|---|---|---|
| 400 | `invalid_date` | Malformed date string |
| 400 | `invalid_calendar` | `calendar` param is not `hijri` or `gregorian` |
| 400 | `invalid_timezone` | Unknown timezone string |
| 400 | `missing_parameter` | Required query param not provided |
| 400 | `invalid_step` | `step` param is not `day` |
| 400 | `invalid_retro` | `retro` param is not a boolean (`true`/`false`, `1`/`0`) |
| 400 | `invalid_next` | `next` param is not a boolean |
| 400 | `invalid_bare` | `bare` param is not a boolean |
| 400 | `invalid_download` | `download` param is not a boolean |
| 400 | `invalid_include` | `/events` `include` param has unknown values |
| 400 | `invalid_range` | `start` is after `end` |
| 400 | `invalid_month` | `month` is not an integer or is not between 1 and 12 |
| 400 | `invalid_year` | `year` is not an integer or is out of supported bounds |
| 400 | `out_of_coverage` | Date is outside available coverage |
| 400 | `date_out_of_supported_range` | Date exceeds supported range |
| 400 | `range_too_large` | Range exceeds 45 days |
| 404 | `date_not_found` | No calendar pair exists for this date |
| 404 | `not_found` | Unknown path (also returned in the JSON envelope) |
| 429 | `rate_limit_exceeded` | Rate limit exceeded — includes a `Retry-After` header |
| 500 | `render_failed` | Hilal chart rendering failed |
| 503 | `computation_unavailable` | Astronomical computation failed or is disabled |

Every error above uses the same JSON envelope, including 404s from unknown
paths and 429s from the rate limiter. Integer and boolean parameters are
validated manually, so FastAPI's raw 422 `{"detail": [...]}` shape never
appears.

## Caching

Every response includes an `ETag` header. Send `If-None-Match: <etag>` (weak
comparison, or `*`) and the origin answers a bare **304 Not Modified** when the
data is unchanged, with the same `Cache-Control` and `ETag` headers — cheap
revalidation on top of the CDN cache.

| Endpoint | `Cache-Control` | Notes |
|---|---|---|
| `/healthz` | `no-store` | Never cached |
| `/api/v1/meta` | `max-age=300` | 5 minutes |
| `/api/v1/today` | `max-age=60, s-maxage=<seconds to midnight>` | Dynamic — CDN caches until midnight in the requested timezone. A miss at 06:00 caches ~18h; a miss at 23:59 expires right after midnight so the date flips immediately. |
| `/api/v1/today/{date}` | `max-age=86400` | Immutable — cached forever |
| `/api/v1/convert` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/range` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/month` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/year` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/events` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/hilal/*` | `public, max-age=86400, s-maxage=86400` | CDN-cached — one render per edge location per day |

Note: `/convert` does not depend on timezone by design — only `/today` accepts `tz`, because "today" depends on where you are. The immutable `/today/{date}` variant does not accept `tz` either.

## CORS

The API is fully open to all origins. Browser requests from any domain are allowed. Server-side clients (curl, backend, cron) are not affected by CORS.

Self-hosters can restrict access via the `ALLOWED_ORIGINS` environment variable (comma-separated origins, or `*` for public — the default). A suffix-based rule (`ALLOWED_ORIGIN_SUFFIXES`) also allows an apex domain plus all its subdomains.

## Versioning

The API follows [semver](https://semver.org/). The current version is returned by `/api/v1/meta` and `/healthz`. Breaking changes (field removal, type changes, new required parameters) will only ship in a new major version. Non-breaking additions (new endpoints, new optional fields) ship in minor versions.

## Rate limits

Default: **240 requests/minute** (4/s sustained, burst 24) per IP via Bunny CDN. The origin
also applies a per-IP limit (240/min) as a fallback. Hilal endpoints are stricter (60 or 30/hour)
due to heavier computation. When limited, the response is 429 `rate_limit_exceeded` in the same
error envelope above, with a `Retry-After` header carrying the wait in seconds.

## Authentication

No authentication required — all endpoints are public. Rate limits are applied per IP address.

## JavaScript SDK

**[mabims-hijri](https://www.npmjs.com/package/mabims-hijri)** is an offline-first npm package that bundles MABIMS 2024–2026 data directly in the package.

### Why use the SDK over the API directly?

| | REST API | SDK |
|---|---|---|
| Network | Required on every call | **Offline** — works without internet |
| Rate limits | 240 req/min | **None** — data lives in your app |
| Latency | CDN round-trip | **Instant** — local lookup |
| Data freshness | Always live | Bundled + auto-syncs when online |
| Scope | Full API (hilal charts, meta) | `today`, `convert`, `range`, `month`, `year`, `events`, `hilal.info` |
| Setup | Base URL + headers | `npm install` |

Use the **API** when you need hilal sky charts, the full date range beyond 2024–2026, or server-side webhook verification. Use the **SDK** when you want fast, offline, zero-config Hijri dates in a JS/TS app.

```bash
npm install mabims-hijri
```

```typescript
import { today, convert } from 'mabims-hijri';

const date = await today();
console.log(`${date.output.day} ${date.output.month_name} ${date.output.year} H`);

const ramadhan = await convert('2026-02-19');
console.log(ramadhan.output.month_name); // 'Ramadhan'
```

Works in Node.js (v18+), browsers, Edge Runtime, and React Native. Falls back to the live API when data is outside the bundled range.

GitHub: [PijarAdiluhung/mabims-hijri](https://github.com/PijarAdiluhung/mabims-hijri) · [npm](https://www.npmjs.com/package/mabims-hijri) · [Full docs](https://mabims.dev/en/sdk/)

## OpenAPI spec

The full OpenAPI 3.1 spec is available at `https://api.mabims.dev/openapi.json` (it declares `https://api.mabims.dev` as its server, so API clients resolve the live origin). Interactive usage:
- **Scalar reference** — [api.mabims.dev/playground](https://api.mabims.dev/playground), the API client is also embedded directly on every endpoint doc
- [openapi-generator](https://openapi-generator.tech/) to generate client libraries
- [Swagger UI](https://petstore.swagger.io/?url=https://api.mabims.dev/openapi.json) as a classic alternative

## Stack

| Layer | Tech |
|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com/) + [Pydantic v2](https://docs.pydantic.dev/), [slowapi](https://github.com/laurentS/slowapi) rate limit |
| Docs | [Astro](https://astro.build/) + [Starlight](https://starlight.astro.build/) with demo pages, embedded Scalar API client, blog, and FAQ |
| Data | Precomputed MABIMS tables (`api/data/`) |
| Rendering | [Skyfield](https://rhodesmill.org/skyfield/) + [Matplotlib](https://matplotlib.org/) + [Pillow](https://python-pillow.org/) + [Shapely](https://shapely.readthedocs.io/) |
| Hosting | Docker Compose on VPS via Dokploy, Bunny CDN in front |
| CI | GitHub Actions — pytest, ruff, mypy, table-vs-criteria validation, deploy health-check + CDN purge |

## Documentation site

The docs at [mabims.dev](https://mabims.dev) include:

- **Bilingual** — Indonesian (default) and English
- **Demo** — sample implementations: date converter, full-year calendar, hilal cards (src/pages/demo/)
- **API client** — "Coba sendiri"/try-it buttons on every endpoint doc open a Scalar client modal (new tab fallback: full reference at [api.mabims.dev/playground](https://api.mabims.dev/playground))
- **API Reference** — every endpoint with parameters, response shapes, and error codes
- **FAQ** — common questions about MABIMS, auth, timezone, and integration
- **Blog** — tutorials, integration guides, and the story behind the API
- **Data Coverage** — table dates and computed range

## Repository layout

```
.github/        CI/CD workflows
api/             FastAPI app, calendar data, tests (pytest)
docs/            Astro/Starlight documentation site
docker-compose.yml        production services (internal-only ports)
docker-compose.dev.yml    local override publishing ports 8000/8080
LICENSE                   MIT license
mabims-assets/            image pack build artifacts
TODO.md                   open work items
```

## Local development

```powershell
# full stack in containers
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
# API  → http://localhost:8000/docs   (Swagger UI)
# Docs → http://localhost:8080

# or hot-reload
cd api; .venv\Scripts\uvicorn app.main:app --reload --port 8000
cd docs; npm run dev
```

Tests, lint and type checks (same gates as CI):

```powershell
cd api
.venv\Scripts\pytest
.venv\Scripts\ruff check .
.venv\Scripts\mypy
```

## Deployment

Shipped on a VPS via Dokploy (compose service) with Bunny CDN pull zones running
*respect origin headers* — that powers the dynamic midnight-TTL caching on `/today`.

## Data & coverage

`api/data/calendar_data.json` is the authoritative MABIMS table (currently **Hijri 1444-07 → 1448-07**,
gregorian 2023-01-23 → 2026-12-31). Beyond it, `api/data/computed_seed.json` carries the same multi-site
Neo MABIMS criteria across the full supported window — **1945-01-01 → 2100-01-01** (JPL de440s),
precomputed and shipped, so no lazy computation happens at request time. Both computed tiers flag
**genuine borderline months** via warnings: only months whose day-29 sighting evening *passed* with
less than 0.25° of margin above the criteria thresholds (a passed month that was days away from
rejection). Rejected months — where a clear 29-day verdict is certain — never warn.

Dates **below the curated table** are gated behind `retro=true` and tagged `mabims-retro`:
Neo MABIMS was introduced in 2022, so pre-2023 results are a retrospective projection, not
data the criteria ever produced officially. Supported floor: **1945-01-01** (earlier dates
return `date_out_of_supported_range` even with `retro=true`).

Regenerate the seed on demand with `api/scripts/generate_seed.py` (verifies curated-table overlap
before writing). The seed is static across the whole window, so no periodic regen is needed —
rerun manually after criteria, site-list or ephemeris changes.

Hilal cards read their astronomy from a SQLite cache of precomputed facts
(`api/data/hilal_astro.sqlite`, keyed by sighting evening + ephemeris tag + site-list
fingerprint). It is never written at runtime: prime it with
`api/scripts/prime_astro_cache.py` (`--jobs` for parallel, resumable) and host the file
on any CDN — in containers it auto-downloads to the `/data` volume on first boot
(`MABIMS_ASTROCACHE_URL`), the same pattern as the JPL ephemeris.

The pre-rendered PNG cards (Hijri 1444–1450, `viz` + `map`) and their panel-less
`viz-bare` + `map-bare` web variants are served from the CDN as a single **image
pack** instead of living in the repo. Build it with one command:

```powershell
python -m scripts.build_imagepack --start 1444 --end 1450 --variants both `
    --images ..\mabims-assets\hilal_images --dist ..\mabims-assets\hilal_images
```

That renders the range (add `--skip-render` to package images already on disk),
then writes a **versioned tar plus `manifest.json`**; `render_version` is derived
from the site lists + display points + renderer sources (criteria included), and
the tar is built deterministically so an unchanged pack keeps its sha. Upload both
files to the CDN base (`MABIMS_IMAGEPACK_URL`). Card and bare variants must ship in
the **same tar** — the runtime keeps one `.version` sidecar, so a bare-only manifest
would leave a fresh `/data` volume without the cards.

At runtime the manifest is probed (`MABIMS_DISABLE_IMAGEPACK=1` to opt out); a
changed version triggers a hash-verified download that is extracted into the
`/data` volume per-file and **merged** (never wiped), so lazily rendered
out-of-range cards survive a pack install. Failures log under `mabims.imagepack`
and the endpoints fall back to lazy rendering.

`/meta` exposes `method`, `computed_active`, `computed_months`, and `retro`.

If a Sidang Isbat session ever decrees a month start that differs from the published
Kemenag calendar, apply the correction with `api/scripts/apply_flip.py` (see
`SIDANG-ISBAT-FLIP.md`): one anchor edit (no cascade — later starts wait for their own
isbat nights) regenerates the curated table, the override is recorded in
`api/data/divergences.json`, every response touching that month gains a
`kemenag_override` warning, and `/meta` exposes `divergences[]` plus a `table_version`
clients can poll.

## Disclaimer

MABIMS API is an independent open-source project and is **not affiliated with, sponsored by, endorsed by, or officially authorized by** Kementerian Agama Republik Indonesia or MABIMS. Data sourced from publicly available MABIMS tables. Computed results (`mabims-computed`) are algorithmic estimates using Neo MABIMS criteria and do not represent official observations or announcements.

---

Built by [PIXO Studio](https://pixostudio.id) · contact: halo@pixostudio.id
