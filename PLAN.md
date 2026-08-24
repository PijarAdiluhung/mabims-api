# MABIMS API — Rebuild Plan

Rewrite of the Netlify-function date converter into a single self-hosted stack: FastAPI backend + Astro/Starlight docs site, deployed as **one Docker Compose project on the VPS behind Dokploy**.

## Decisions

| Topic | Decision |
|---|---|
| Backend | FastAPI (Python 3.12), clean break from old response shape |
| Frontend | Astro + Starlight docs site, vanilla-JS playground island (no Preline) |
| Access | Public reads + CORS allowlist (`malangmengaji.com` + subdomains) + rate limiting |
| Hosting | Single VPS, **Dokploy** manages deploy/TLS/domains (Traefik built in) |
| Deployment | One `docker-compose.yml`, two services |
| Data pipeline (2027+) | Deferred — see "Deferred" |

## Repo layout

```
mabims-api/
├── api/                      # FastAPI app
│   ├── app/
│   │   ├── main.py           # routes, CORS, rate-limit middleware
│   │   ├── calendar.py       # table loader, coverage checks
│   │   └── schemas.py        # Pydantic models
│   ├── data/calendar_data.json   # existing lookup table, moved as-is
│   ├── tests/                # pytest; pairs sampled from real data
│   ├── Dockerfile
│   └── pyproject.toml
├── docs/                     # Astro + Starlight
│   ├── src/content/docs/     # home, quickstart, API reference, playground page
│   ├── Dockerfile            # multi-stage: astro build → nginx:alpine
│   └── ...
├── docker-compose.yml        # single compose, both services
└── PLAN.md
```

## Compose topology

```yaml
services:
  api:
    # build ./api, exposes 8000 (internal only)
    # data/ mounted read-only into container
  docs:
    # build ./docs, serves static Astro output on 80 (internal only)
```

- No ports published to host. Dokploy/Traefik terminates TLS and routes by domain:
  - `api.<domain>` → `api:8000`
  - `<domain>` or `docs.<domain>` → `docs:80`
- Deploy = push to git, redeploy stack from Dokploy UI (or webhook).

## Endpoints (v1)

```
GET /api/v1/convert?date=YYYY-MM-DD&calendar=gregorian|hijri
    - strict date validation via Pydantic
    - 404 when outside table coverage (with link to /meta)
GET /api/v1/today
    - gregorian today → hijri
    - adds warnings[] when within N days of table end
GET /api/v1/meta
    - { coverage: {first, last}, data_version, docs_url }
    - safety net for the hard 2026-12-31 expiry of current data
GET /healthz
    - liveness for Dokploy healthchecks / uptime monitors
```

Response shape is new (v1) — no compatibility with the old Netlify payload.

## Cross-cutting

- **CORS**: explicit allowlist origins (`https://malangmengaji.com`, `https://*.malangmengaji.com` handled at app level); no wildcard.
- **Rate limiting**: slowapi per-IP, generous default (e.g. 60/min), 429 responses documented.
- **No auth**: reads are harmless lookups; drop the old origin-whitelist theater entirely.
- **Docs site**: Starlight sections = Home hero, Quickstart, Endpoint reference (3 pages), Playground island hitting live `/api/v1/*`, Data coverage page (shows `/meta` live), Contact.

## Milestones

1. **API core** (~½ day) — scaffold `api/`, port lookup logic, pytest against known pairs from existing JSON, `/meta` coverage logic.
2. **Compose + Dokploy ship** (~½ day) — both Dockerfiles, single compose, create stack in Dokploy, assign domains, TLS, smoke tests.
3. **Docs site** (~1 day) — Starlight scaffold, content pages, playground island wired to live API.
4. **Cutover** — point partner sites to new URL, keep old Netlify untouched until confirmed, then archive.
5. **Deferred** — 2027+ calendar generator script, expiry monitoring alert, i18n (id/ms).

## Open items

- [ ] Pick hostnames (`api.<domain>`, docs domain)
- [ ] Confirm rate-limit thresholds
- [ ] Source/format for future yearly calendar tables (2027+)
