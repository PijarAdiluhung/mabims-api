# TODO

## Branding & domain
- [x] Pick domain + `api.` hostname (candidates: `hariini.app`, `tanggalan.id`, `mabims.dev`, `hijridate.dev`) choice: mabims.dev
- [x] Settle site title / tagline (current: "MABIMS Date Converter API") choice: mabims.dev - Integrasikan sistem kalender hijriah MABIMS dalam aplikasi / website Anda
- [x] Logo + favicon refresh (current favicons inherited from old project) + OG/social preview image — mabims.png in navbar + hero, Poppins font (#fecf46 yellow)
- [x] Replace all placeholders once domain is live (bought mabims.dev): docs content + `PUBLIC_API_BASE` → `api.mabims.dev`; astro site + `/meta` docs_url → `https://mabims.dev`

## Ship
- [x] VPS: Dokploy compose service + domains
- [x] Bunny pull zones, *respect origin headers*, query strings in cache key
- [x] Smoke checklist incl. cache-hit verification (second request must not reach origin)
- [x] Uptime monitor on `/healthz` + alert (Instatus)

## Data — curated table ends 2026-12-31
- [ ] 2027 MABIMS table: Kemenag usually publishes the new-year table mid-October or later (sometimes later still) — watch for the announcement, then run the yearly ingest and extend `api/data/`. Until then the API serves the computed tier past the table edge, so nothing breaks — coverage just reports `mabims-computed` instead of `mabims` for dates past 2026-12-31
- [x] `/events` endpoint — Islamic observance dates (Ramadan start, Eid al-Fitr/Adha, 1 Muharram, Maulid) from the curated table, extended with computed dates beyond table coverage using Neo MABIMS criteria
- [ ] Decide long-term data format for yearly tables (versioned files + `/meta.data_version` bump) — do this before the 2027 ingest, since the ingest script's shape depends on it
- [ ] When the table nears exhaustion with no 2027 update published, surface it via `/meta` so consumers aren't surprised by the `mabims` → `mabims-computed` shift

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
- [x] **Hilal map — stage 1: expand to ~100 sites.** More granular coastal points (site-list data PR, `api/data/hilal_sites.json` + `seed_divergence.py` census before/after). Evidence that densification matters: 1428-10 (2007-11-10 evening) was a 4-site Java-only rescue, and single-site topocentric loses 4 months that multi-site rescues. Verdicts are robust — 28 narrow months in 80 years, seen-count histogram in `temp/narrow_months.txt` — so additions mainly sharpen `deciding_site` reporting and cover future decades.
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

## Hilal Explorer — `/hilal` page
- [ ] **Backend: `/api/v1/hilal/map-data` endpoint** — returns contour polylines + display points as JSON (~15KB)
- [ ] **Backend: `/api/v1/hilal/minimap` endpoint** — returns small world minimap PNG (~400×200 @2x, ~20KB)
- [ ] **Frontend: `/hilal` page** — standalone Astro page with Canvas-rendered map + sky scene
- [ ] **Bundle static GeoJSON** — indonesia_boundary, indonesia_provinces, world countries into `docs/public/geo/`

### `/hilal` page — design

```
┌──────────────────────────────────────────────────────────────┐
│  ◀  Ramadhan 1447 H  ▶           [Peta] [Langit]            │  ← floating top bar
├──────────────────────────────────────────────────────────────┤
│                                                              │
│              FULLSCREEN CANVAS                               │
│              (map or sky, fills viewport)                    │
│                                                              │
│  ┌─────────────────────────────────────┐                     │
│  │  🌙 MEMENUHI KRITERIA               │  ← floating card   │
│  │  Alt bulan:    +4.8°  ✅           │    bottom-left      │
│  │  Elongasi:      8.1°  ✅           │    backdrop-blur    │
│  │  Titik: Sabang                      │                     │
│  │  ▾ Detail                           │                     │
│  └─────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

- One month at a time, prev/next arrows, URL params `?month=X&year=Y`
- Default to next upcoming month (from `/api/v1/today`)
- Map: Canvas with Indonesia outline + visibility polygon + isolines + dots + minimap PNG
- Viz: Canvas with gradient sky + stars + sun/moon + crescent + horizon + verdict pill
- Toggle switches between map and viz
- Info card: full details from `/hilal/info` (verdict, alt, elong, site, sunset, moonset, illumination, age, sites checked)

### `/hilal` — implementation order

#### Phase 1: Backend endpoints

1. **`api/app/hilal/mapcard.py`** — add `map_data_json()`:
   - Reuse `_grid()` for 2D alt/elong arrays
   - Extract contour paths via `ax.contour()` on temp figure
   - Simplify with shapely `simplify(tolerance=0.1)`
   - Convert to JSON `[[[lon, lat], ...], ...]`
   - Return dict with `evening`, `month`, `hero`, `points`, `contours`

2. **`api/app/hilal/mapcard.py`** — add `minimap_png_bytes()`:
   - Reuse `_global_visibility()` (3° step, cached)
   - Render at 800×400 (2x current inset)
   - Return PNG bytes

3. **`api/app/main.py`** — wire up endpoints:
   - `GET /api/v1/hilal/map-data?month=&year=` → JSON (60/hour)
   - `GET /api/v1/hilal/minimap?month=&year=` → PNG (60/hour)
   - Reuse `_hilal_context()` for sighting evening + multi-site result

4. **Test**: `curl /api/v1/hilal/map-data?month=9&year=1447` → verify shape

#### Phase 2: Static assets

5. **Bundle GeoJSON** into `docs/public/geo/`:
   - `indonesia_boundary.geojson` (~346KB)
   - `indonesia_provinces_raw.geojson` (~335KB)
   - `ne_110m_admin_0_countries.geojson` (~819KB)
   - `map_points.json` (~4KB)
   - `hilal_sites.json` (~3KB)

#### Phase 3: Frontend page

6. **`docs/src/pages/hilal.astro`** — page skeleton:
   - Standalone HTML (no StarlightPage)
   - Floating header bar (month title, nav arrows, map/viz toggle)
   - Fullscreen canvas element
   - Floating info card (bottom-left, backdrop-blur)
   - Loading skeleton
   - Brand CSS (Poppins, #fecf46 accent, dark bg)

7. **Sky scene renderer** (`<script>` or inline):
   - Fetch `/api/v1/hilal/info?month=X&year=Y`
   - Canvas: gradient sky, starfield, sun/moon positions, crescent, horizon, verdict pill
   - ~150 lines JS, no dependencies

8. **Map renderer**:
   - Fetch `/api/v1/hilal/map-data?month=X&year=Y`
   - Fetch static GeoJSON files
   - Canvas: ocean fill → world land → Indonesia land → province lines → visibility polygon → isolines → dots → hero marker → minimap PNG
   - Simple Mercator projection
   - GeoJSON → Canvas path conversion

9. **Navigation + toggle**:
   - Read `?month=&year=` from URL
   - Prev/next arrows: increment/decrement month (wrap at 12→1)
   - `history.replaceState` on navigation
   - Toggle swaps canvas renderer
   - Auto-default to next month via `/api/v1/today`

10. **Info card**:
    - Populate from `/api/v1/hilal/info` response
    - Verdict badge (green/red)
    - Grid: moon alt, elongation, deciding site, sunset, moonset, illumination, age, sites checked
    - Expandable raw JSON (`<details>`)

11. **Responsive**:
    - Desktop: canvas fills viewport, info card bottom-left
    - Mobile (≤768px): info card bottom sheet, larger touch targets

#### Phase 4: Polish

12. **SEO**: `<title>`, `<meta description>`, canonical URL, JSON-LD
13. **Loading states**: skeleton while fetching JSON, spinner while rendering canvas
14. **Error handling**: invalid month/year, API errors, empty contours
15. **Canvas resize**: debounced redraw on window resize

### `/hilal` — data flow

```
Page load
  │
  ├─ Read ?month=&year= from URL (or fetch /api/v1/today → next month)
  │
  ├─ Fetch /api/v1/hilal/info?month=X&year=Y  ──→ populate info card
  │
  ├─ Fetch /api/v1/hilal/map-data?month=X&year=Y  ──→ map contours + points
  │
  ├─ Fetch /api/v1/hilal/minimap?month=X&year=Y  ──→ minimap PNG
  │
  ├─ Load /geo/indonesia_boundary.geojson  ──→ Indonesia outline
  │   (cached after first load)
  │
  └─ Render canvas (map or sky based on toggle)
```

### `/hilal` — key technical details

**Map projection** (simple Mercator for Indonesia):
```js
function project(lon, lat) {
  const x = ((lon - LON0) / (LON1 - LON0)) * canvas.width;
  const y = ((LAT1 - lat) / (LAT1 - LAT0)) * canvas.height;
  return [x, y];
}
```

**Crescent moon** (Canvas arc):
```js
ctx.beginPath();
ctx.arc(cx, cy, r, 0, Math.PI * 2);           // full disc
ctx.arc(cx + offset, cy, r, 0, Math.PI * 2, true); // shadow punch
ctx.fill();
```

**Dashed isolines** (Canvas dash):
```js
ctx.setLineDash([8, 4]);
ctx.strokeStyle = '#ff9f43'; // orange for alt
ctx.stroke();
```

**GeoJSON → Canvas**:
```js
function drawGeoPolygon(ctx, coords, project) {
  ctx.beginPath();
  coords.forEach((ring, i) => {
    ring.forEach(([lon, lat], j) => {
      const [x, y] = project(lon, lat);
      i === 0 && j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
  });
  ctx.closePath();
}
```

### `/hilal` — file changes

| File | Action | Est. lines |
|---|---|---|
| `api/app/hilal/mapcard.py` | Add `map_data_json()` + `minimap_png_bytes()` | ~60 |
| `api/app/main.py` | Add `/hilal/map-data` + `/hilal/minimap` endpoints | ~40 |
| `docs/src/pages/hilal.astro` | **New**: standalone page | ~500 |
| `docs/public/geo/*.json` | Bundle static geographic data | 5 files |

### `/hilal` — estimated payload sizes

| Resource | Size | Cached |
|---|---|---|
| `/hilal/info` | ~2KB | CDN 24h |
| `/hilal/map-data` | ~15KB | CDN 24h |
| `/hilal/minimap` | ~20KB | CDN 24h |
| GeoJSON (once) | ~1.5MB (~300KB gzip) | Browser cache |
| **Total per visit** | ~37KB (+ 300KB first visit) | |

## Cutover (M5)
- [x] Repoint malangmengaji.com integrations to new hostnames
- [x] One week parallel run (old Netlify stays live)
- [x] Retire Netlify function + old domain redirects
- [x] Push final state; tag `v1.0.0`
