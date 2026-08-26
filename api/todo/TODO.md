# Hilal Endpoints — Implementation Plan

Image-generation endpoints on mabims-api + docs playground.
`GET /api/v1/hilal/info` (JSON) · `GET /api/v1/hilal/viz` (PNG, day-29 evening).

## Milestones

- **M1 (now)**: endpoints PUBLIC (strict rate limit, no auth) + playground in docs —
  prove the system works end to end.
- **M2 (later)**: API-key gating (`X-API-Key`) on both endpoints + key docs.

## Decisions (locked)

- **Month boundaries**: MABIMS only — `service.h2g` lookup (curated → computed → lazy walk). No Aladhan.
- **Day-29 check**: `h2g["YYYY-MM-29"]` always exists; day 30 present = 30-day month.
- **Viz scope**: day-29 evening chart per request (single PNG).
- **Locations (M1 playground)**: Jakarta, Malang, Sabang, Makkah, Hawaii — these five only.
- **Language**: chart fully Indonesian (Sya'ban, Dzulqa'dah, Dzulhijjah, TERLIHAT/LOLOS, …).
- **Semantics**: month boundary authoritative from Sabang table; per-location math describes
  local sky only (`mabims_date` vs `local visibility` in response).
- **Sunset**: computed locally via Skyfield almanac per observer (no Aladhan, no hardcoded Maghrib).
- **Design (frozen)**: `DESIGN.md` + `mock_v2.py` — dusk vertical 720x1280, criteria table,
  visibility-factor moon, logo watermark. Blueprint outputs in `output/`.

## Done

- [x] Reference source in `api/todo/hilal-visualizer/`; offline smoke tests
- [x] Design mocks iterated → frozen (`mock_v2.py`, 4 verified cases incl. pill left-flip,
      below-horizon clamp, 0-opacity below threshold, logo watermark)

## M1 — playground + image generation

1. [ ] `pyproject.toml`: add `pillow` (only dep)
2. [ ] `app/hilal/locations.py` — the 5 locations w/ lat, lon, IANA tz
3. [ ] `app/hilal/astro.py` — per-observer sunset, topocentric alt/az, elong, illum, age, moonset
4. [ ] Month resolution via `ensure_hijri_month` + `h2g` (day-29/30, month length, target start)
5. [ ] `app/hilal/chart.py` — port `mock_v2.py` (TOKENS per DESIGN.md)
6. [ ] Endpoints in `main.py`: `/hilal/info` (JSON) · `/hilal/viz` (PNG, `@limiter.limit("30/hour")`,
       `Cache-Control: private`) — public in M1
7. [ ] Docs playground: month dropdown (12 Indonesian names) · year input · location dropdown (5) →
       shows PNG + data panel; calls the public endpoints (CORS already origin-gated)
8. [ ] Tests: info (mocked astro), viz smoke (small canvas), month-resolution edge cases
9. [ ] Gates: pytest · ruff · mypy green (add ruff per-file ignore for `api/todo/`)
10. [ ] Docs: API reference page for both endpoints

## M2 — API keys

1. [ ] `app/auth.py` + `api_keys` in `config.py` (`API_KEYS` csv env, `secrets.compare_digest`,
       401 house error shape)
2. [ ] Gate `/hilal/info` + `/hilal/viz` with `Depends(require_api_key)`
3. [ ] DECISION: how the public playground calls keyed endpoints (demo key / proxy / origin-trust)
4. [ ] Tests: auth 401/200
5. [ ] Docs: API-key access section; README endpoint rows

## Risks / notes

- ruff lints `api/todo/` legacy copies — per-file ignore needed before gates run.
- Ephemeris cached (`%TEMP%\mabims-ephemeris`, Docker via `MABIMS_EPHEMERIS_DIR`);
  skyfield downloads to cwd if run from repo root — always run from cache dir in dev.
- PNG deterministic per params (seeded starfield); `Cache-Control: private` (CDN later in M2 decision).
- Fonts: Segoe UI chain w/ DejaVu fallback for Docker.
