---
title: Data Sources
description: Where MABIMS data comes from and its licensing status.
---

## Primary Source

Calendar data is sourced from **data published publicly by the Ministry of Religious Affairs of the Republic of Indonesia** (Kemenag RI) — the MABIMS calendar tables issued annually.

| Property | Value |
|---|---|
| **Source** | Ministry of Religious Affairs of the Republic of Indonesia — Hijri Calendar |
| **Original format** | PDF |
| **Table coverage** | 2023-01-23 → 2026-12-31 |

## Computed Tier

Beyond table coverage, the API computes dates using **Neo MABIMS** criteria:

| Parameter | Threshold |
|---|---|
| Moon altitude (topocentric, refraction-corrected) | ≥ 3.0° |
| Elongation (geocentric) | ≥ 6.4° |
| Observation points | 25 coastal sites across Indonesia — fulfilled at **any single point** → 29-day month ([site list](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json)) |
| Reference time | At each site's local sunset (day 29) |

## Map data

The map card (`/hilal/map`) uses the following geographic data:

| Layer | Source | License |
|---|---|---|
| Indonesian landmass + province borders | [superpikar/indonesia-geojson](https://github.com/superpikar/indonesia-geojson) | per source repo |
| Surrounding countries | [Natural Earth](https://www.naturalearthdata.com/) 1:110m admin-0 | Public domain |
| Display points (95) | derived from a 126-city list + the 25 MABIMS observation sites | — |

## Retro (below the curated table)

Dates before 2023-01-23 were never produced under the Neo MABIMS criteria (introduced in 2022). Passing `retro=true` unlocks computed dates below the curated table down to 1945-01-01, tagged `source: "mabims-retro"` with a warning that these are a retrospective projection — not official data.

## Licensing

Calendar data is sourced from Indonesian government publications for public use. API source code is licensed under the [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).
