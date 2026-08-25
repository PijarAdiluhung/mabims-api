# MABIMS Date Converter API

Gregorian ⇄ Hijri date conversion API following the **MABIMS** standard — the moon-sighting
criteria adopted across **Singapore, Indonesia and Malaysia**. Serves curated lookup tables
(not astronomical guesses), and beyond table coverage it stays on-method by computing
dates live with the Neo MABIMS criteria.

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

Every response carries `source` (`mabims` vs `mabims-computed`) and `warnings[]`.
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

## Data & coverage

`api/data/calendar_data.json` is the authoritative MABIMS table (currently **2024 → 2026**).
`api/data/computed_table.json` extends fast lookups to **1970 → current year + 5** using the same
Neo MABIMS criteria — regenerate it yearly with `api/scripts/build_computed_table.py`, which
verifies the curated-table overlap byte-for-byte before writing (automation: see TODO.md).
Dates outside that span are still computed lazily on request. Both computed tiers flag
borderline months (margin < 0.25°) via warnings.
A Umm al-Qura tier remains wired as an emergency last resort; `/meta` exposes `method`,
`computed_active`, `computed_months`, `fallback_active` and `fallback_months`.

---

Built by [PIXO Studio](https://pixostudio.id) · contact: halo@pixostudio.id
