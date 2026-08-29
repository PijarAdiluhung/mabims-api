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
| **Table coverage** | 2024-01-13 → 2026-12-31 |

## Computed Tier

Beyond table coverage, the API computes dates using **Neo MABIMS** criteria:

| Parameter | Threshold |
|---|---|
| Moon altitude (refraction-corrected) | ≥ 3.0° |
| Elongation | ≥ 6.4° |
| Reference location | Sabang (5°53′N 95°19′E) |
| Reference time | At sunset |

## Licensing

Calendar data is sourced from Indonesian government publications for public use. API source code is licensed under the [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).
