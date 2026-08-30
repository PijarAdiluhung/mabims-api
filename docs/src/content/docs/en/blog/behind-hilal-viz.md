---
title: "Why Search for Hilal in Sabang?"
description: "Technical deep-dive into the /hilal/viz endpoint. Geocentric astronomy, Neo MABIMS criteria, and how the PNG chart is rendered from scratch."
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

No other Hijri calendar API (at least that I've found) has this feature. So this post discusses how it works, from astronomy to pixel rendering.

## Why Sabang?

This is the question I get most often. The answer is simple: **Sabang is Indonesia's westernmost point.**

For moon sighting (rukyah), geographic position matters — the further west, the later sunset occurs. This means if the hilal doesn't meet criteria elsewhere, its *last chance* will be in Sabang.

This isn't an official MABIMS rule about "must use Sabang," but it's a practical reference point that makes sense for representing Indonesia-wide hilal visibility in a single coordinate.

## How It Works

A simplified version of the actual implementation:

```
FUNCTION hilal_viz(month, year):
  sighting = resolve_sighting_evening(year, month)
  observation = observe_sighting_evening(sighting.evening_date)
  alt_ok = observation.moon_alt >= 3.0°
  elong_ok = observation.elongation >= 6.4°
  data = build_chart_data(...)
  img = render_chart(data)
  return PNG
```

### 1. Resolve the sighting evening

If you request visibility for Ramadan, this endpoint doesn't calculate the 1st of Ramadan itself — it goes back to the **29th evening of Sya'ban**, because that's the actual evening observed to determine whether tomorrow marks the start of Ramadan. This is the fundamental logic of rukyah: you observe the hilal at the end of the current month, not at the start of the target month.

### 2. Calculate that evening's astronomy, from Sabang

Two categories of data are computed:

- **Geocentric criteria** — `moon_alt` (altitude), `moon_az` (azimuth), `sun_alt`, and `elongation` (angular distance between moon and sun). These are the numbers directly compared against MABIMS thresholds.
- **Observer-clock times** — illumination, local sunset time, and moonset time. This is what's displayed as additional info on the bottom card.

### 3. Check Neo MABIMS thresholds

```
alt_ok  = moon_alt   >= 3.0°
elong_ok = elongation >= 6.4°
```

Both conditions must be met simultaneously. If either fails, the hilal is considered not to meet visibility criteria, even if the moon is above the horizon.

## Example Result

<img src="/viz.png" alt="Hilal visualization from the /hilal/viz endpoint" style="max-width: min(420px, 100%); display: block;" />

The screenshot above shows visibility for 1 Muharram 1448 H (evaluating the evening of 29 Dzulhijjah 1447 H, June 15 2026, from Sabang):

- Moon altitude +5.0° (passes, threshold ≥3.0°)
- Elongation 7.0° (passes, threshold ≥6.4°)
- Illumination 0.2% — very thin, the hilal is extremely young
- Sunset 18:53, moonset 19:11, only 18 minutes apart

Status: **VISIBLE**, though with not much margin.

## Why Bother Building This?

Because raw numbers (`moon_alt: 5.2, elongation: 8.7`) aren't intuitive for most people, including myself. But once visualized — see the moon's position relative to the horizon, see the green/red pill, see the criteria table — it becomes much easier to digest. This endpoint isn't just for developers who need JSON, but for anyone curious about "how can the hilal be declared visible/not visible" without needing to understand astronomy.

Try it yourself on the [playground](/en/playground/hilal):

```
GET https://api.mabims.dev/api/v1/hilal/viz?month=1&year=1448
```

Change `month` and `year` to the Hijri month you want to check. Full parameter documentation at [mabims.dev/en/endpoints/hilal](https://mabims.dev/en/endpoints/hilal).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Why Search for the Hilal in Sabang?",
  "description": "Technical deep-dive into the /hilal/viz endpoint. Geocentric astronomy, Neo MABIMS criteria, and how the PNG chart is rendered from scratch.",
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
