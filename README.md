# MABIMS Date Converter API

Gregorian ⇄ Hijri date conversion API following the **MABIMS** standard — the moon-sighting
criteria adopted across **Singapore, Indonesia and Malaysia**. Serves curated lookup tables
(not astronomical guesses), with a clearly-marked Umm al-Qura fallback beyond table coverage.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/today?tz=` | Hero endpoint — today's Hijri date, timezone-aware (default `Asia/Jakarta`) |
| `GET /api/v1/today/{date}` | Immutable variant, CDN-cacheable forever |
| `GET /api/v1/convert?date=&calendar=` | Single date, either direction |
| `GET /api/v1/range?start=&end=&calendar=` | Bulk conversion (≤400 days) |
| `GET /api/v1/month?year=&month=&calendar=` | Calendar-grid sugar over `/range` |
| `GET /api/v1/meta` | Coverage, data version, fallback status |
| `GET /healthz` | Liveness probe |

Every response carries `source` (`mabims` vs `fallback:aladhan-ummalqura`) and `warnings[]`.
Reads are public; see the docs' *Access & Rate Limits* page.

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI + Pydantic v2, slowapi rate limit |
| Docs | Astro + Starlight with live playground |
| Data | Precomputed MABIMS tables (`api/data/`) |
| Hosting | Docker Compose on VPS via Dokploy, Bunny CDN in front |

## Documentation site

The docs at [mabims.dev](https://mabims.dev) are built with Astro + Starlight:

- **Bilingual** — Indonesian (default) and English, toggled from the navbar
- **Splash landing page** — hero with terminal demo, feature cards, and quick-start links
- **Live playground** — try API calls directly from the browser
- **Sections** — Quickstart, Access & Rate Limits, API Reference (convert / today / range / meta), Playground, Data Coverage

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

Tests:

```powershell
cd api; .venv\Scripts\pytest
```

## Deployment

Follow [DEPLOY.md](DEPLOY.md): Dokploy compose service, two domains, Bunny pull zones with
*respect origin headers* (this powers the dynamic midnight-TTL caching on `/today`).

## Data & fallback

`api/data/calendar_data.json` is the authoritative MABIMS table (currently **2024 → 2026**).
Dates outside coverage fall through two tiers, both always marked in `source`/`warnings`:

1. **`mabims-computed`** — the Neo MABIMS criteria computed live at Sabang
   (hilal altitude ≥ 3°, elongation ≥ 6.4° at sunset on day 29); validated to reproduce
   every month boundary in the curated table. Borderline months (margin < 0.25°) carry a warning.
2. **`fallback:aladhan-ummalqura`** — Umm al-Qura via Aladhan as last resort,
   lazily fetched per month and persisted on disk.

`/meta` exposes `method`, `computed_active`, `computed_months`, `fallback_active` and
`fallback_months`. Tiers can be disabled with `MABIMS_DISABLE_COMPUTED=1` /
`MABIMS_DISABLE_ALADHAN=1`; the de421 ephemeris is baked into the Docker image.

---

Built by [PIXO Studio](https://pixostudio.id) · contact: halo@pixostudio.id
