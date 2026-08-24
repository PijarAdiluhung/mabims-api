# MABIMS API — Rebuild Plan

Rewrite of the Netlify-function date converter into a single self-hosted stack: FastAPI backend + Astro/Starlight docs site, deployed as **one Docker Compose project on the VPS behind Dokploy**, fronted by **Cloudflare** for edge caching at scale.

## Decisions

| Topic | Decision |
|---|---|
| Backend | FastAPI (Python 3.12), clean break from old response shape |
| Frontend | Astro + Starlight docs site, vanilla-JS playground island (no Preline) |
| Hero endpoint | `/api/v1/today` — main consumer use case |
| Timezone | `tz` query param everywhere; **default `Asia/Jakarta` (UTC+7)** when unspecified |
| Scaling | Bunny CDN pull zone → Dokploy/Traefik → VPS; dynamic edge TTL via origin headers, origin sees ~0 traffic |
| Access | Public reads + CORS allowlist (`malangmengaji.com` + subdomains); rate limit only as origin abuse guard |
| Hosting | Single VPS, **Dokploy** manages deploy/TLS/domains (Traefik built in) |
| Deployment | One `docker-compose.yml`, two services |
| Data pipeline (2027+) | Deferred |
| Expiry fallback | Lazy per-month prefetch from Aladhan (Umm al-Qura), responses marked `source: fallback` — see below |

## Expiry fallback (Umm al-Qura bridge)

Safety net for forgotten yearly updates: never 404 just because the table ended.

- **Trigger**: lookup date falls outside `calendar_data.json` coverage.
- **Fill**: fetch `GET https://api.aladhan.com/v1/gToHCalendar/{month}/{year}` (and `hToGCalendar` for reverse lookups) → 12 calls max per year → build both maps → persist to `data/fallback_{year}.json` → load alongside main table.
- **Marking**: fallback responses carry `source: "fallback:aladhan-ummalqura"` + a `warnings[]` entry (±1 day drift vs MABIMS). Normal responses carry `source: "mabims"`.
- **Visibility**: `/meta` exposes `fallback_active`, covered fallback months; docs coverage page renders a loud banner from `/meta`.
- **Isolation**: provider client sits behind a tiny interface (`FallbackProvider`) so Aladhan is swappable without touching route logic.

## Repo layout

```
mabims-api/
├── api/                      # FastAPI app
│   ├── app/
│   │   ├── main.py           # routes, CORS, cache-header middleware
│   │   ├── calendar.py       # table loader, coverage checks
│   │   ├── timeutil.py       # tz resolution, midnight-TTL computation
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

## Request flow

```
Client → Bunny CDN edge (cache) → VPS/Dokploy Traefik (TLS) → api:8000 / docs:80
```

- No ports published to host. Dokploy/Traefik routes by domain:
  - `api.<domain>` → `api:8000`
  - `<domain>` or `docs.<domain>` → `docs:80`
- Deploy = push to git, redeploy stack from Dokploy UI (or webhook).

## Endpoints (v1)

All date-taking endpoints accept `tz` (IANA name or UTC offset). Default: `Asia/Jakarta` (UTC+7).

```
GET /api/v1/today?tz=Asia/Jakarta      # hero endpoint; gregorian today → hijri
GET /api/v1/today/{date}?tz=           # immutable variant, cacheable forever
GET /api/v1/convert?date=&calendar=&tz=
GET /api/v1/range?start=&end=&calendar=&step=day    # cap ~400d; month-view UIs
GET /api/v1/month?year=&month=&calendar=            # sugar over range; calendar grids
GET /api/v1/events?year=&calendar=hijri             # Ramadan start, Eid al-Fitr/Adha,
                                                    # 1 Muharram, Maulid… derived from
                                                    # MABIMS table (differentiator)
GET /api/v1/meta                       # coverage {first,last}, data_version,
                                       # fallback_active, docs_url
GET /healthz                           # liveness for Dokploy healthchecks
```

Every response includes `source: "mabims" | "fallback:aladhan-ummalqura"` and optional `warnings[]` so consumers can always tell which calendar authority produced the date.

Response shape is new (v1) — no compatibility with the old Netlify payload.

## Caching & scaling

Principle: every response is keyed by its inputs, so identical requests are pure cache hits at the edge.

- **Immutable endpoints** (`/today/{date}`, `/convert`, `/range`, `/month`, `/events`): long static TTL (`max-age=86400`).
- **`/today`: dynamic TTL until local midnight** in the request's resolved tz:
  ```python
  ttl = seconds_until_midnight(tz)     # miss at 06:00 → ~64800s
  Cache-Control: public, max-age=60, s-maxage={ttl}
  ```
  - Miss at 06:00 → cached all day, zero origin hits.
  - Miss at 23:59 → short TTL; entry expires right after midnight and the next request refetches — never serves yesterday past midnight.
- Bunny CDN zone: caching set to respect origin `Cache-Control` headers (no override), query strings included in cache key (default). Note: Bunny has no `stale-while-revalidate`; the midnight rollover is handled purely by the computed TTL expiring exactly at local midnight.
- Origin load at millions req/day ≈ one request per edge PoP per key per day.

## Cross-cutting

- **CORS**: explicit allowlist origins (`https://malangmengaji.com`, `*.malangmengaji.com`); no wildcard.
- **Rate limiting**: slowapi per-IP on origin only as abuse guard (CDN absorbs legitimate traffic).
- **No auth**: reads are harmless lookups; drop the old origin-whitelist theater entirely.
- **Docs site**: Starlight sections = Home hero, Quickstart, Endpoint reference pages, Playground island hitting live `/api/v1/*`, Data coverage page (live from `/meta`), Contact.

## Milestones

| # | Milestone | Scope | Done when |
|---|---|---|---|
| **M0** | **Scrap & clean slate** | Delete `netlify/`, `netlify.toml`, `index_local.js`, `index.html`, `converter.html`, `script.js`, `style.css`, `test_data_path.js`, `package.json`, `package-lock.json`, `node_modules/`. Update `.gitignore` (Python + `.env`). Keep only `data/`, `favicons/`, `PLAN.md`; README rewritten | Repo contains nothing outside the new architecture |
| **M1** | **API core** | Scaffold `api/` (`pyproject.toml`, `app/{main,calendar,timeutil,schemas,config}.py`). Move `data/` → `api/data/`. Endpoints: `/convert`, `/today`, `/today/{date}`, `/range`, `/month`, `/meta`, `/healthz`. TZ resolution (default UTC+7) + midnight-TTL headers. Rate limit + CORS allowlist. pytest suite from real pairs | `pytest` green; curl smoke tests pass locally |
| **M2** | **Fallback bridge** | `FallbackProvider` interface, Aladhan lazy per-month fetch → `data/fallback_{year}.json`, `source`/`warnings` marking, `/meta.fallback_active`. Fixture test with shrunk coverage | Simulated expired table → fallback serves + marks correctly; no repeat live calls after first fill |
| **M3** | **Compose + Dokploy ship** | Both Dockerfiles, one `docker-compose.yml`, Dokploy stack, domains, Bunny pull zone (respect origin headers). Smoke incl. cache-hit verification | Live HTTPS on both domains; repeat requests don't reach origin (verified via logs) |
| **M4** | **Docs site** | Starlight: home, quickstart, endpoint reference, playground island, coverage/fallback banner from `/meta`. Favicons move into `docs/` | Docs deployed; playground converts real dates against live API |
| **M5** | **Cutover** | Partners repointed; Netlify kept until confirmed; archive | Old deployment retired |

Deferred out of all milestones: `/events` endpoint (blocked on curated observance-dates list), 2027+ generator script, expiry monitoring alert, i18n.

## Open items

- [ ] Pick domain + hostnames (`api.<domain>`, docs apex)
- [ ] Curated Islamic observance dates source for `/events` (needs a hand-maintained list layered on the conversion table)
- [ ] Confirm rate-limit thresholds
- [ ] Source/format for future yearly calendar tables (2027+)
