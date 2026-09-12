---
title: "Where Do You Look for the Hilal?"
description: "Technical deep-dive into the /hilal/viz endpoint. Neo MABIMS criteria at coastal observation points, the deciding site, and how the PNG chart is rendered from scratch."
date: 2026-08-29
tags:
  - Astronomy
  - Hilal
  - Visualization
  - MABIMS
excerpt: "One of my favorite endpoints on mabims.dev isn't /today or /convert, but /hilal/viz. This endpoint generates a 720×1280 PNG showing a complete evening sky visualization with moon position, MABIMS criteria pass/fail status, and a sky chart with stars. A deep dive behind the scenes."
cover:
  image: ../../../../assets/hilal.jpg
  alt: Hilal visualization from the /hilal/viz endpoint
authors:
  - pijar
---

One of my favorite endpoints on mabims.dev isn't `/today` or `/convert`, but `/hilal/viz`. This endpoint generates a 720×1280 PNG showing a complete evening sky visualization with moon position, MABIMS criteria pass/fail status, and a sky chart with stars.

No other Hijri calendar API (at least that I've found) has this feature. So this post discusses how it works, from [astronomy](https://en.wikipedia.org/wiki/Astronomy) to pixel rendering.

## Where Do You Look for the [Hilal](https://en.wikipedia.org/wiki/Hilal)?

The question used to be "why Sabang?". The better question now: **where?**

The [Neo MABIMS](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia) criteria (hilal altitude ≥ 3°, elongation ≥ 6.4°) are rukyah criteria — they must be evaluated **from a point on the Earth's surface**. And Indonesia is wide. So instead of picking a single point, the API now checks **25 coastal observation sites** from Sabang to Rote, and the criteria count as fulfilled if they pass at **any single site** — the same logic as Kemenag's rukyah: if the hilal is seen anywhere in Indonesia, the month begins. (See also [Jurnal Astroislamica](https://journal.uinsuna.ac.id/index.php/ASTROISLAMICA/article/view/2735) on the Maqāṣid al-Syarī'ah perspective of these criteria.)

The interesting pattern: for "comfortable" months, the westernmost site almost always decides. The further west, the later the sunset, so the higher the hilal stands above the horizon at dusk — Sabang and the west Aceh coast are both the *last chance* and the *first win*. But there are months with a southerly lunar declination where the southern arc wins (southern Java to the Lesser Sundas). Historical data from 1970–2050 shows Java sites (Ujung Kulon, Pangandaran) deciding dozens of months. That's why those southern points are on the list — they're not decoration.

When the criteria are met, the API reports the site that decided via the `deciding_site` field on `/hilal/info`, and the chart displays a **TITIK PENGAMAT** row.

## How It Works

A simplified version of the actual implementation:

```
FUNCTION hilal_viz(month, year):
  sighting = resolve_sighting_evening(year, month)
  ms = sighting_on_date(sighting.evening_date)     # 25 sites, one call
  chosen = ms.deciding_site or ms.best_site        # deciding site (or closest miss)
  alt_ok = chosen.alt_refracted >= 3.0°
  elong_ok = chosen.elongation >= 6.4°
  data = build_chart_data(..., decider=chosen)
  img = render_chart(data)
  return PNG
```

### 1. Resolve the sighting evening

If you request visibility for Ramadan, this endpoint doesn't calculate the 1st of Ramadan itself — it goes back to the **29th evening of Sya'ban**, because that's the actual evening observed to determine whether tomorrow marks the start of Ramadan. This is the fundamental logic of rukyah: you observe the hilal at the end of the current month, not at the start of the target month.

### 2. Calculate that evening's astronomy, at the deciding site

Two categories of data are computed:

- **Criteria** — `moon_alt` ([*topocentric*](https://en.wikipedia.org/wiki/Horizontal_coordinate_system) altitude, [refraction](https://en.wikipedia.org/wiki/Atmospheric_refraction) applied), `moon_az` (azimuth), `sun_alt`, and `elongation` (moon–sun angular distance, [*geocentric*](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy)) per the Indonesian hisab convention). These are the numbers directly compared against MABIMS thresholds — all of them belonging to **one single site**, so the sky scene, criteria table and verdict can never contradict each other.
- **Observer-clock times** — illumination, sunset time, and moonset time, all at the deciding site and displayed in that site's own timezone (WIB or WITA).

### 3. Check Neo MABIMS thresholds

```
alt_ok   = moon_alt_refracted >= 3.0°
elong_ok = elongation         >= 6.4°
```

Both conditions must be met together, at least at one site. If no site passes, the hilal is considered not to meet visibility criteria, even if the moon is above the horizon at several points.

## Example Result

<img src="/viz.png" alt="Hilal visualization from the /hilal/viz endpoint" style="max-width: min(420px, 100%); display: block;" />

The screenshot above shows visibility for 1 Dzulqa'dah 1447 H (evaluating the evening of 29 Syawal 1447 H, April 18 2026, observation point Sabang):

- Moon altitude +10.4° (passes, threshold ≥3.0°)
- Elongation 14.5° (passes, threshold ≥6.4°)
- Illumination 1.4% — still a slim crescent but clearly visible
- Sunset 18:46, moonset 19:31 — 45 minutes apart, a comfortable observation window

Status: **MEMENUHI KRITERIA** (criteria met), and this time the margin is far above the threshold. Compare that with borderline months (like 1446-08, which passed with a 0.006° margin) — in those charts the crescent is barely visible and the verdict reads "MENDEKATI BATAS" (close to the limit). The chart doesn't lie.

## Why Bother Building This?

Because raw numbers (`moon_alt: 10.4, elongation: 14.5`) aren't intuitive for most people, including myself. But once visualized — see the moon's position relative to the horizon, see the green/red pill, see the criteria table — it becomes much easier to digest. This endpoint isn't just for developers who need JSON, but for anyone curious about "how can the hilal be declared visible/not visible" without needing to understand astronomy.

Try it yourself on the [playground](/en/playground/hilal):

```
GET https://api.mabims.dev/api/v1/hilal/viz?month=1&year=1448
```

Change `month` and `year` to the Hijri month you want to check. Full parameter documentation at [mabims.dev/en/endpoints/hilal](https://mabims.dev/en/endpoints/hilal).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Where Do You Look for the Hilal?",
  "description": "Technical deep-dive into the /hilal/viz endpoint. Neo MABIMS criteria at coastal observation points, the deciding site, and how the PNG chart is rendered from scratch.",
  "datePublished": "2026-08-29",
  "author": {
    "@type": "Person",
    "name": "Pijar Adiluhung",
    "url": "https://pixostudio.id"
  },
  "publisher": {
    "@type": "Organization",
    "name": "mabims.dev",
    "logo": {
      "@type": "ImageObject",
      "url": "https://mabims.dev/mabims-long.png"
    }
  },
  "image": "https://mabims.dev/og-image.png",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://mabims.dev/en/blog/behind-hilal-viz"
  }
}
</script>
