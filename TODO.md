# TODO

## Branding & domain
- [x] Pick domain + `api.` hostname (candidates: `hariini.app`, `tanggalan.id`, `mabims.dev`, `hijridate.dev`) choice: mabims.dev, during testing: mabims.pixostudio.id
- [x] Settle site title / tagline (current: "MABIMS Date Converter API") choice: mabims.dev - Integrasikan sistem kalender hijriah MABIMS dalam aplikasi / website Anda
- [x] Logo + favicon refresh (current favicons inherited from old project) + OG/social preview image — mabims.png in navbar + hero, Poppins font (#fecf46 yellow)
- [ ] Replace all placeholders once domain is live: `api.example.com` (docs content, `PUBLIC_API_BASE` default, playground fallback), `mabims.pixostudio.id` (`astro.config.mjs` site, `/meta` docs_url)

## Ship
- [ ] VPS: Dokploy compose service + domains → DEPLOY.md §2
- [ ] Bunny pull zones, *respect origin headers*, query strings in cache key → DEPLOY.md §3
- [ ] Smoke checklist incl. cache-hit verification (second request must not reach origin) → DEPLOY.md §4
- [ ] Uptime monitor on `/healthz` + alert if `fallback_active` stays true > a few days (healthchecks.io or similar)

## Data — hard deadline 2027-01-01
- [ ] 2027 MABIMS table: build the yearly ingest script (source: regional authority announcements), extend `api/data/`
- [ ] `/events` endpoint — curated Islamic observance dates (Ramadan start, Eid al-Fitr/Adha, 1 Muharram, Maulid) layered on the table; the differentiator vs Umm al-Qura APIs
- [ ] Decide long-term data format for yearly tables (versioned files + `/meta.data_version` bump)

## Product polish
- [ ] Homepage v2: hero with live "today in Hijri" widget, copy-paste quickstart, partner/social proof
- [ ] i18n docs (Bahasa Indonesia first, then Malay) — Starlight supports it natively
- [ ] Playground: shareable permalinks (`?date=…&calendar=…`), copy-as-curl button
- [ ] Response examples per endpoint auto-checked in CI against the live schema (docs drift guard)

## Cutover (M5)
- [ ] Repoint malangmengaji.com integrations to new hostnames
- [ ] One week parallel run (old Netlify stays live)
- [ ] Retire Netlify function + old domain redirects
- [ ] Push final state; tag `v1.0.0`
