# MABIMS API

Gregorian ⇄ Hijri date conversion, Islamic events, and hilal visibility data, powered by the
official **MABIMS** moon-sighting tables from **Religious Ministry (Kemenag) of Indonesia**. Serves curated lookup data, and beyond table coverage it computes dates live with the Neo MABIMS criteria.

**Full docs, playground, API reference, FAQ, and blog → [mabims.dev](https://mabims.dev)**

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

For more examples (hilal data, date ranges, calendar grids), see the [live docs & playground](https://mabims.dev).

## Endpoints

Every endpoint supports `GET` and `HEAD`. All responses include a `source` field and `warnings[]` array.

The `source` field indicates where the data came from:

| `source` | Meaning |
|---|---|
| `mabims` | Official MABIMS table from Kemenag |
| `mabims-computed` | Computed with Neo MABIMS criteria (altitude ≥ 3°, elongation ≥ 6.4° at Sabang sunset) |
| `fallback:aladhan-ummalqura` | Emergency fallback (last resort) |

| Endpoint | Purpose | Rate Limit |
|---|---|---|
| `GET /api/v1/today?tz=` | Today's Hijri date, timezone-aware (default `Asia/Jakarta`). Accepts any IANA timezone (e.g. `Asia/Kuala_Lumpur`, `Asia/Singapore`). | 240/min |
| `GET /api/v1/today/{date}` | Same as above for a fixed `YYYY-MM-DD` date. Immutable, CDN-cacheable forever. | 240/min |
| `GET /api/v1/convert?date=&calendar=` | Single date conversion, either direction. `calendar` must be `hijri` or `gregorian`. | 240/min |
| `GET /api/v1/range?start=&end=&calendar=` | Bulk conversion (≤400 days). `calendar` must be `hijri` or `gregorian`. | 240/min |
| `GET /api/v1/month?year=&month=&calendar=` | All days in a month. `calendar` must be `hijri` or `gregorian`. | 240/min |
| `GET /api/v1/events?year=&calendar=` | Islamic observances. | 240/min |
| `GET /api/v1/hilal/info?month=&year=` | Hilal visibility data for the evening deciding a month start (geocentric hisab, Sabang). | 60/hour |
| `GET /api/v1/hilal/viz?month=&year=` | Hilal sky chart PNG (720×1280) with MABIMS criteria table. | 30/hour |

The hilal visibility criteria follow Neo MABIMS: **moon altitude ≥ 3.0°** and **elongation ≥ 6.4°** at sunset in Sabang (5°53′N 95°19′E), Indonesia's westernmost point. The `visible` field in `/hilal/info` is `true` when both conditions are met.
| `GET /api/v1/meta` | Coverage, data version, fallback status. | 240/min |
| `GET /healthz` | Liveness probe. | no limit |

## Parameters

| Parameter | Values | Notes |
|---|---|---|
| `calendar` | `hijri`, `gregorian` | Required on `/convert`, `/range`, `/month`, `/events`. |
| `date` | `YYYY-MM-DD` | ISO 8601 date format. |
| `tz` | IANA timezone or UTC offset | Default `Asia/Jakarta` (UTC+7). Examples: `Asia/Kuala_Lumpur`, `UTC+8`, `+08:00`. |
| `start`, `end` | `YYYY-MM-DD` | Used by `/range`. |
| `year` | Integer | Hijri or Gregorian year, depending on `calendar`. |
| `month` | Integer | Hijri or Gregorian month (1–12). |

## Events

| `event` slug | Name | Hijri date |
|---|---|---|
| `1_muharram` | Islamic New Year | 1 Muharram |
| `maulid_nabi` | Prophet Muhammad's Birthday | 12 Rabi' al-Awwal |
| `awal_ramadan` | Start of Ramadan | 1 Ramadan |
| `idul_fitri` | Eid al-Fitr | 1 Shawwal |
| `idul_adha` | Eid al-Adha | 10 Dhul Hijjah |

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
| 400 | `invalid_range` | `start` is after `end` |
| 400 | `invalid_month` | `month` is not between 1 and 12 |
| 400 | `invalid_year` | `year` is out of supported bounds |
| 400 | `out_of_coverage` | Date is outside available coverage |
| 400 | `date_out_of_supported_range` | Date exceeds supported range |
| 400 | `range_too_large` | Range exceeds 400 days |
| 404 | `date_not_found` | No calendar pair exists for this date |
| 500 | `render_failed` | Hilal chart rendering failed |
| 503 | `computation_unavailable` | Astronomical computation failed or is disabled |

## Caching

Every response includes an `ETag` header. Clients should send `If-None-Match` to avoid re-downloading unchanged data.

| Endpoint | `Cache-Control` | Notes |
|---|---|---|
| `/healthz` | `no-store` | Never cached |
| `/api/v1/meta` | `max-age=300` | 5 minutes |
| `/api/v1/today` | `max-age=60, s-maxage=<seconds to midnight>` | Dynamic — CDN caches until midnight in the requested timezone. A miss at 06:00 caches ~18h; a miss at 23:59 expires right after midnight so the date flips immediately. |
| `/api/v1/today/{date}` | `max-age=86400` | Immutable — cached forever |
| `/api/v1/convert` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/range` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/month` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/events` | `max-age=86400` | Immutable for fixed dates |
| `/api/v1/hilal/*` | `max-age=86400` | 24 hours |

Note: `/convert` does not depend on timezone by design — only `/today` accepts `tz`, because "today" depends on where you are. The immutable `/today/{date}` variant does not accept `tz` either.

## CORS

The API is fully open to all origins. Browser requests from any domain are allowed. Server-side clients (curl, backend, cron) are not affected by CORS.

Self-hosters can restrict access via the `ALLOWED_ORIGINS` environment variable (comma-separated origins, or `*` for public — the default). A suffix-based rule (`ALLOWED_ORIGIN_SUFFIXES`) also allows an apex domain plus all its subdomains.

## Versioning

The API follows [semver](https://semver.org/). The current version is returned by `/api/v1/meta` and `/healthz`. Breaking changes (field removal, type changes, new required parameters) will only ship in a new major version. Non-breaking additions (new endpoints, new optional fields) ship in minor versions.

## Rate limits

Default: **240 requests/minute** per IP. Hilal endpoints are stricter (60 or 30/hour) due to heavier computation.

## Authentication

No authentication required — all endpoints are public. Rate limits are applied per IP address.

## OpenAPI spec

The full OpenAPI 3.1 spec is available at `https://api.mabims.dev/openapi.json`. Use it with
[openapi-generator](https://openapi-generator.tech/) or [Swagger UI](https://petstore.swagger.io/?url=https://api.mabims.dev/openapi.json) to generate client libraries or explore the API interactively.

## Stack

| Layer | Tech |
|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com/) + [Pydantic v2](https://docs.pydantic.dev/), [slowapi](https://github.com/laurentS/slowapi) rate limit |
| Docs | [Astro](https://astro.build/) + [Starlight](https://starlight.astro.build/) with live playground, blog, and FAQ |
| Data | Precomputed MABIMS tables (`api/data/`) |
| Hosting | Docker Compose on VPS via Dokploy, Bunny CDN in front |
| CI | GitHub Actions — pytest, ruff, mypy, table-vs-criteria validation, yearly computed-table regen PR |

## Documentation site

The docs at [mabims.dev](https://mabims.dev) include:

- **Bilingual** — Indonesian (default) and English
- **Live playground** — try API calls directly from the browser
- **API Reference** — every endpoint with parameters, response shapes, and error codes
- **FAQ** — common questions about MABIMS, auth, timezone, and integration
- **Blog** — tutorials, integration guides, and the story behind the API
- **Data Coverage** — table dates, computed range, and fallback behavior

## Repository layout

```
api/       FastAPI app, calendar data, tests (pytest)
docs/      Astro/Starlight documentation site
docker-compose.yml        production services (internal-only ports)
docker-compose.dev.yml    local override publishing ports 8000/8080
DEPLOY.md                 Dokploy + Bunny CDN runbook
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

Follow [DEPLOY.md](DEPLOY.md): Dokploy compose service, two domains, Bunny pull zones with
*respect origin headers* (this powers the dynamic midnight-TTL caching on `/today`).

## Data & coverage

`api/data/calendar_data.json` is the authoritative MABIMS table (currently **Hijri 1445–1448**,
gregorian 2024 → 2026). Beyond it, `api/data/computed_seed.json` carries the same Neo MABIMS
criteria forward (**through Hijri 1473**, gregorian ~mid-2050), and dates past the seed are
still computed lazily on request. Both computed tiers flag borderline months (margin < 0.25°)
via warnings.

Regenerate the seed yearly with `api/scripts/generate_seed.py` (verifies curated-table overlap
before writing); `.github/workflows/regen-computed-table.yml` automates it every January and
opens a PR with the diff.

A Umm al-Qura tier remains wired as an emergency last resort; `/meta` exposes `method`,
`computed_active`, `computed_months`, `fallback_active` and `fallback_months`.

---

Built by [PIXO Studio](https://pixostudio.id) · contact: halo@pixostudio.id
