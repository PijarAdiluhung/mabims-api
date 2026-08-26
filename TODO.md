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
- [x] `/events` endpoint — curated Islamic observance dates (Ramadan start, Eid al-Fitr/Adha, 1 Muharram, Maulid) layered on the table; the differentiator vs Umm al-Qura APIs
- [ ] Decide long-term data format for yearly tables (versioned files + `/meta.data_version` bump)

## Computed tier (precomputed_table)
- [ ] Yearly regeneration of `api/data/computed_table.json` → run `api/scripts/build_computed_table.py` from CI/cron each January and commit the diff (in-container schedulers don't survive restarts)
- [x] Seed `MabimsCalcProvider` blocks from the precomputed file at startup so out-of-range lazy walks start from the file edge instead of the 2024 anchor
- [ ] Revisit borderline warning noise: ~52% of computed months sit within the 0.25° margin band, making the warning fire on half of responses — consider raising the band, or only warning when `visible` is true

## Product polish
- [ ] Homepage v2: hero with live "today in Hijri" widget, copy-paste quickstart, partner/social proof
- [x] i18n docs (Bahasa Indonesia) — Starlight supports it natively
- [ ] Playground: shareable permalinks (`?date=…&calendar=…`), copy-as-curl button
- [ ] Response examples per endpoint auto-checked in CI against the live schema (docs drift guard)

## Cutover (M5)
- [ ] Repoint malangmengaji.com integrations to new hostnames
- [ ] One week parallel run (old Netlify stays live)
- [ ] Retire Netlify function + old domain redirects
- [ ] Push final state; tag `v1.0.0`
