---
title: "Deep Dive: Behind mabims-computed"
description: "A technical teardown of the MABIMS calendar fallback: hilal position, the 29 or 30 day decision, the seed table, and why the altitude is topocentric while the elongation stays geocentric."
date: 2026-09-09
tags:
  - MABIMS
  - Astronomy
  - Backend
  - Python
  - Deep Dive
excerpt: "If the date you request falls outside the Kemenag table, the MABIMS API doesn't guess. It recomputes the month length from the Neo MABIMS criteria. This post tears down the engine behind the mabims-computed source."
cover:
  image: ../../../../assets/kalkulator.jpg
  alt: Hilal computation and the MABIMS calendar
authors:
  - pijar
---

In this MABIMS API I've referred to `source: "mabims-computed"` as the fallback several times.

This post looks at how it actually works. `mabims-computed` is not just "if there's no data, use an estimate". Behind it there's a small engine that computes when a Hijri month starts, walks forward or backward from an anchor date, stores the results, and tells the client that what it received is not official Kemenag data.

So in this post I want to open up the parts that usually stay hidden: how a single month gets decided as 29 or 30 days, why the altitude is [topocentric](https://en.wikipedia.org/wiki/Horizontal_coordinate_system) while the elongation stays [geocentric](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy)), and why the criteria are evaluated at 25 coastal observation sites.

## Two kinds of data, one API

The MABIMS API has two main sources:

- `mabims` — dates from the public Kemenag RI calendar.
- `mabims-computed` — dates computed with the Neo MABIMS criteria when outside the table's coverage.

For example, a date that is still inside the table:

```json
{
  "output": {
    "date": "1447-09-01",
    "calendar": "hijri",
    "day": 1,
    "month": 9,
    "month_name": "Ramadhan",
    "year": 1447
  },
  "source": "mabims",
  "warnings": []
}
```

If the date is beyond the table, the response shape stays the same, but the source changes:

```json
{
  "output": {
    "date": "1450-01-01",
    "calendar": "hijri",
    "day": 1,
    "month": 1,
    "month_name": "Muharram",
    "year": 1450
  },
  "source": "mabims-computed",
  "warnings": [
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria (moon altitude >= 3 deg and elongation >= 6.4 deg at local sunset, seen anywhere across the coastal observation sites of Indonesia)."
  ]
}
```

I deliberately keep these two sources distinct. Computed results can be very useful for application calendars, but they must never be read as official announcements or a replacement for the isbat session.

## Neo MABIMS in two numbers

The short version of the [criteria](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia) is:

```text
hilal altitude  >= 3.0°
elongation      >= 6.4°
```

Both must pass at the same time, and passing at **any single site is enough**. Altitude passing but elongation falling short still means failure. The reverse is equally true. (See also [ANTARA English](https://en.antaranews.com/news/346717/indonesia-sets-march-1-as-first-day-of-ramadan) and [JAT journal](https://ejournal.um.edu.my/index.php/JAT/article/download/45242/17123/144190) on the history of these criteria.)

The criteria are evaluated at the **local sunset of each observation point** — currently **25 coastal sites** from Sabang to Rote (the list is open at [`api/data/hilal_sites.json`](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json)). The interesting pattern: for "comfortable" months, the westernmost site almost always decides — the further west, the later the sunset, the higher the hilal stands at dusk. But there are months with a southerly [lunar declination](https://en.wikipedia.org/wiki/Lunar_theory) where the southern arc wins (southern Java to the Lesser Sundas). That's why the southern points are on the list.

And there's no "Sabang rule" fetish here — this is exactly Kemenag's rukyah logic: if the hilal is seen anywhere in Indonesia, the month begins. The API even reports the site that decided via `deciding_site`.

## From hilal to month length

The calendar computation can actually be summarized as a tiny function:

```python
def month_length(month_start):
    result = criteria_on_day29(month_start)
    return 29 if result.visible else 30
```

`criteria_on_day29()` evaluates the sunset on the 29th night of the running month. If both criteria pass, the month ends after 29 days. If not, the month runs to 30 days.

In other words, to determine the start of Ramadan, what gets checked is not the first night of Ramadan. It's the 29th night of Sya'ban. If the hilal meets the criteria, the next day is 1 Ramadan. If not, Sya'ban completes to 30 days.

The simplified flow looks roughly like this:

```text
known Hijri month start
         ↓
evaluate sunset on the 29th night
         ↓
altitude >= 3° and elongation >= 6.4°?
      ↙                      ↘
    yes                      no
  29-day month            30-day month
      ↓                      ↓
next month start = start + month length
```

Because each subsequent month starts at the end of the previous one, this engine can build a calendar as a chain.

## Not your usual arithmetic conversion

[Tabular Hijri calendars](https://en.wikipedia.org/wiki/Tabular_Islamic_calendar) can usually be computed with an arithmetic pattern: months have a fixed length arrangement, and leap-year cycles determine where the 29s and 30s land.

`mabims-computed` doesn't work like that. Month lengths are decided one by one from the astronomical conditions on the 29th night. So this engine is more like a linked list than a one-line formula:

```text
1449-01-01
   └─ check hilal → 29 or 30 days
       └─ 1449-02-01
           └─ check hilal → 29 or 30 days
               └─ 1449-03-01
```

The consequence: we need one trusted starting point. In the app, that point comes from the boundary of the official Kemenag RI table. For dates after the table, the engine walks forward from that anchor.

## It can walk backward too

For dates before the official calendar, the API doesn't allow computation right away. The request must include `retro=true`.

The reason is simple: the Neo MABIMS criteria were only introduced in 2022. If we project those criteria onto 1990, the result is not official historical data. It is a reconstruction using today's rule.

That's why there's a third source:

```text
source: "mabims-retro"
```

This label means the result was computed backward using the same criteria, not taken from an official historical table. The API also emits a warning so this status difference doesn't get lost on the client side.

Internally, walking backward is a bit trickier than walking forward. If we know the 1st of the next month, we check the sunset at day −31 to determine whether the previous month is 29 or 30 days. After that, the previous month's start can be fixed.

## The part that forced me to re-investigate

At first I thought the question was simple: to compute the hilal criteria, should we use an observer's coordinates on the Earth's surface, or the position from the Earth's center?

The terms:

- **[Topocentric](https://en.wikipedia.org/wiki/Horizontal_coordinate_system)** — seen from the Earth's surface, accounting for the observer's position and lunar parallax.
- **[Geocentric](https://en.wikipedia.org/wiki/Barycentric_coordinates_(astronomy))** — seen from the Earth's center.

The topocentric intuition sounded more correct for hilal observation — humans observe from the Earth's surface. And after validating it end to end: the intuition was right. The engine above finally found its proper shape: hilal altitude is computed **topocentrically** ([atmospheric refraction](https://en.wikipedia.org/wiki/Atmospheric_refraction) applied) at **25 coastal observation sites** from Sabang to Rote, while elongation stays **geocentric** per the Indonesian hisab convention — and the criteria only need to be met at one site anywhere. The result is still 48/48 against the curated table: everything explained above about the 29/30-day decision is unchanged; what changed is "where" and "which reference frame".

## Borderline is real

Back to the topic. Passing the criteria doesn't mean the position is far above the threshold.

For example, the result could be:

```text
altitude  = 3.12°
elongation = 7.01°
```

Boolean-wise, this passes. But the nearest margin is only 0.12° from the altitude threshold. That's why the provider stores the smallest margin:

```python
margin = min(
    altitude - 3.0,
    elongation - 6.4,
)
```

If the margin is positive but under 0.25°, the month is flagged borderline. This information flows into `warnings[]` so applications don't treat a result hovering at the threshold as something certain.

An important note: borderline does not automatically mean the result is wrong. It only means that small changes in location, method, [ephemeris](https://ssd.jpl.nasa.gov/planets/eph_export.html) data, or criteria interpretation could affect the outcome.

## So when can `mabims-computed` be used?

In my opinion, it fits:

- application calendars that need longer multi-year coverage;
- previews of future observance dates;
- date conversion features without an official table;
- research, experiments, and hilal visualization;
- a technical fallback while official data is unavailable.

Don't treat it as:

- the official announcement of Ramadan or Eid al-Fitr's start;
- a replacement for the [isbat session](https://en.wikipedia.org/wiki/Moon_sighting);
- proof of hilal observation at a specific location;
- a single source for administrative or religious decisions.

On the client side, at minimum always check these two fields:

```js
if (data.source === "mabims-computed") {
  console.warn("This date is an algorithmic estimate, not official data.");
}

if (data.warnings?.length) {
  console.warn(data.warnings);
}
```

## The point

`mabims-computed` is a fairly self-aware compromise:

1. The official table is used when available.
2. Outside the table, month lengths are computed from the Neo MABIMS criteria.
3. The criteria are evaluated at each of 25 coastal sites' local sunsets; passing at any single site is enough.
4. Two thresholds, altitude 3° and elongation 6.4°, must pass together.
5. Altitude is topocentric (with refraction), elongation stays geocentric — the model is validated 48/48 against the curated table.
6. Results are labeled and warned so they aren't mistaken for official data.

If you only call `/today`, none of this complexity needs to be visible. But when you request a calendar for the year 2050, or ask why one month has 29 days and another 30, this is what happens behind the screen.

Try it yourself:

```bash
curl "https://api.mabims.dev/api/v1/events?year=2050&calendar=gregorian"
```

Notice the `source` and `warnings` fields in the response. Endpoint documentation and data coverage status are at [mabims.dev/data-sources](https://mabims.dev/en/data-sources).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Deep Dive: What Actually Happens Behind mabims-computed?",
  "description": "A technical teardown of the MABIMS calendar fallback: hilal position, the 29 or 30 day decision, the seed table, and why the altitude is topocentric while the elongation stays geocentric.",
  "datePublished": "2026-09-09",
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
    "@id": "https://mabims.dev/en/blog/deep-dive-mabims-computed"
  }
}
</script>
