# TODO

## Branding & domain
- [x] Pick domain + `api.` hostname (candidates: `hariini.app`, `tanggalan.id`, `mabims.dev`, `hijridate.dev`) choice: mabims.dev, during testing: mabims.pixostudio.id
- [x] Settle site title / tagline (current: "MABIMS Date Converter API") choice: mabims.dev - Integrasikan sistem kalender hijriah MABIMS dalam aplikasi / website Anda
- [x] Logo + favicon refresh (current favicons inherited from old project) + OG/social preview image — mabims.png in navbar + hero, Poppins font (#fecf46 yellow)
- [x] Replace all placeholders once domain is live (bought mabims.dev): docs content + `PUBLIC_API_BASE` → `api.mabims.dev`; astro site + `/meta` docs_url → `https://mabims.dev`

## Ship
- [x] VPS: Dokploy compose service + domains → DEPLOY.md §2
- [x] Bunny pull zones, *respect origin headers*, query strings in cache key → DEPLOY.md §3
- [x] Smoke checklist incl. cache-hit verification (second request must not reach origin) → DEPLOY.md §4
- [ ] Uptime monitor on `/healthz` + alert if `fallback_active` stays true > a few days (healthchecks.io or similar)

## Data — hard deadline 2027-01-01
- [ ] 2027 MABIMS table: build the yearly ingest script (source: regional authority announcements), extend `api/data/`
- [x] `/events` endpoint — Islamic observance dates (Ramadan start, Eid al-Fitr/Adha, 1 Muharram, Maulid) from the curated table, extended with computed dates beyond table coverage using Neo MABIMS criteria
- [ ] Decide long-term data format for yearly tables (versioned files + `/meta.data_version` bump)

## Computed tier (precomputed_table)
- [x] Computed-seed regeneration on demand → `.github/workflows/regen-computed-table.yml` (`workflow_dispatch`): rebuilds `computed_seed.json`, verifies curated overlap byte-for-byte, opens a PR with the diff. Seed is static through Hijri 1473, so no yearly cron needed; rerun manually after criteria/ephemeris changes
- [x] Seed `MabimsCalcProvider` blocks from the precomputed file at startup so out-of-range lazy walks start from the file edge instead of the 2024 anchor
- [ ] Revisit borderline warning noise: ~52% of computed months sit within the 0.25° margin band, making the warning fire on half of responses — consider raising the band, or only warning when `visible` is true

## Product polish
- [ ] Homepage v2: hero with live "today in Hijri" widget, copy-paste quickstart, partner/social proof
- [x] i18n docs (Bahasa Indonesia) — Starlight supports it natively
- [ ] Playground: shareable permalinks (`?date=…&calendar=…`), copy-as-curl button
- [x] Response examples per endpoint auto-checked in CI against the live schema — `api/tests/test_contract.py` parses every real response into its Pydantic model and asserts documented paths exist in `/openapi.json`
- [ ] Docs-site example JSON blocks: verify the payloads printed in `docs/src/content/docs/endpoints/*.md` still match live responses (contract tests cover schema shapes, not the markdown snippets)
## Hilal endpoints
- [x] `/hilal/info` + `/hilal/viz` shipped, Sabang-only geocentric hisab (design tokens in `app/hilal/chart.py`, spec in git history `api/todo/DESIGN.md`)
- [x] No API keys (dropped M2) — outputs are deterministic per `(month, year)`; CDN caches them via `Cache-Control: public, max-age=86400`, purge-on-push keeps edge fresh
- [ ] viz precompute 1446–1466 (252 PNGs, build script + immutable cache) only if origin render traffic ever matters

## Cutover (M5)
- [x] Repoint malangmengaji.com integrations to new hostnames
- [x] One week parallel run (old Netlify stays live)
- [x] Retire Netlify function + old domain redirects
- [x] Push final state; tag `v1.0.0`
