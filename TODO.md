# TODO

## Branding & domain
- [x] Pick domain + `api.` hostname (candidates: `hariini.app`, `tanggalan.id`, `mabims.dev`, `hijridate.dev`) choice: mabims.dev
- [x] Settle site title / tagline (current: "MABIMS Date Converter API") choice: mabims.dev - Integrasikan sistem kalender hijriah MABIMS dalam aplikasi / website Anda
- [x] Logo + favicon refresh (current favicons inherited from old project) + OG/social preview image — mabims.png in navbar + hero, Poppins font (#fecf46 yellow)
- [x] Replace all placeholders once domain is live (bought mabims.dev): docs content + `PUBLIC_API_BASE` → `api.mabims.dev`; astro site + `/meta` docs_url → `https://mabims.dev`

## Ship
- [x] VPS: Dokploy compose service + domains → DEPLOY.md §2
- [x] Bunny pull zones, *respect origin headers*, query strings in cache key → DEPLOY.md §3
- [x] Smoke checklist incl. cache-hit verification (second request must not reach origin) → DEPLOY.md §4
- [x] Uptime monitor on `/healthz` + alert (Instatus)

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
- [x] Multi-site criteria overhaul (v1.5.0): topo alt + geo elong at 25 coastal sites, decider-driven `/hilal/*`, regenerated seed (10 boundaries ±1d), 48/48 vs curated
- [ ] **Hilal map — stage 1: expand to ~100 sites.** More granular coastal points (site-list data PR, `api/data/hilal_sites.json` + `seed_divergence.py` census before/after). Evidence that densification matters: 1428-10 (2007-11-10 evening) was a 4-site Java-only rescue, and single-site topocentric loses 4 months that multi-site rescues. Verdicts are robust — 28 narrow months in 80 years, seen-count histogram in `temp/narrow_months.txt` — so additions mainly sharpen `deciding_site` reporting and cover future decades.
- [x] **Hilal map — stage 2: continuous grid.** Shipped as `/hilal/map` (v1.6.0): 720×1280 card with the visible region, alt-3°/elong-6.4° isolines, 95 display points and the 25-site decider ringed. `/meta.hilal_image_range` + pre-generated image set.
- [x] Rewrite blog `deep-dive-mabims-computed.md` — multi-site rationale + new EN version
- [x] Rewrite blog `behind-hilal-viz.md` (id+en) as "Di Mana Cari Hilal?" — multi-site edition
- [x] Sync `mabims-hijri` SDK (v1.2.0): additive `deciding_site`/`sites_checked` types, multi-site docs, pushed (npm publish after v1.5 deploy ✓ API is live)
- [x] No API keys (dropped M2) — outputs are deterministic per `(month, year)`; CDN caches them via `Cache-Control: public, max-age=86400`, purge-on-push keeps edge fresh
- [x] Pre-generated hilal image set (`api/scripts/generate_hilal_images.py`): pre-rendered 1444–1450 now served from the CDN **image pack** (versioned tar + `manifest.json`, `MABIMS_IMAGEPACK_URL`, hash-verified merge install into the `/data` volume — `app/hilal/imagepack.py`); PNGs no longer committed, lazy disk cache renders to the `/data` volume for the rest, `/meta.hilal_image_range = 1444–1475`

### Hilal map card — polish
- [x] Fix alt/elong contour-line artefact on the map card (stray `alt 3°` label — was clabel text left behind by the clip; isolines no longer clipped)
- [x] Extend the alt/elong lines outside the Indonesia buffer (to the map edge) so they read as continuous isolines
- [x] Fix the `+`/`-` sign formatting bug on the criteria values (tooltip hardcoded `+`, produced `+-0.8°`; now shared `_fmt_alt`/`_fmt_elong`)
- [x] Add a world minimap for geographic context (low-res real-sunset alt-3/elong-6.4 region, ~1s/month, cached + pre-generated)
- [x] Fix hilal-viz text (title was dropping the year for two-word months; header now uniform with the map: month caps, no year)
- [x] Hilal map header too long (uniform title fits; safety shrink if a month ever overflows)

## Cutover (M5)
- [x] Repoint malangmengaji.com integrations to new hostnames
- [x] One week parallel run (old Netlify stays live)
- [x] Retire Netlify function + old domain redirects
- [x] Push final state; tag `v1.0.0`
