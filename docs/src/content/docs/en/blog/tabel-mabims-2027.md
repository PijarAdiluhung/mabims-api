---
title: "The 2027 MABIMS Table Is In, API Coverage Now Runs Through 2027"
description: "The official Kemenag calendar for 2027 is now part of the MABIMS API. Curated coverage reaches 31 December 2027 and every 2027 month start matches the Neo MABIMS computation."
date: 2026-11-16
tags:
  - MABIMS
  - Calendar
  - Kemenag
  - Data
excerpt: "The official Kemenag calendar for 2027 is now part of the MABIMS API. Curated coverage reaches 31 December 2027 and every 2027 month start matches the Neo MABIMS computation."
cover:
  image: ../../../../assets/kalender-2027.png
  alt: MABIMS calendar 2027
authors:
  - pijar
---

The MABIMS API now serves Hijri dates from the official calendar of Indonesia's Ministry of Religious Affairs through **31 December 2027**. The table previously stopped at 31 December 2026. This extension adds 13 month starts, from Sha'ban 1448 to Sha'ban 1449.

## The new coverage in numbers

| Item | Before | After |
|---|---|---|
| Coverage start | 23 January 2023 | 23 January 2023 |
| Coverage end | 31 December 2026 | 31 December 2027 |
| Days | 1,439 | 1,804 |

The change also shows up in `hilal_index.json`. Thirteen months that were previously served from computation now use calendar data, so `/hilal/history` responses for that range no longer carry the outside-table warning.

## No divergence from the Neo MABIMS computation

Before entering the table, those thirteen month starts were compared with the Neo MABIMS prediction the API already uses for dates outside the table. All of them matched exactly. The difference was zero days for every month.

Next, a validator checked each month length against the hilal criteria at 25 coastal observation sites. All 61 month boundaries passed. No month failed and no month had a thin margin, meaning below 0.25 degrees.

Because there was no difference, `divergences.json` stays empty. That file only records Sidang Isbat corrections, not differences between the calendar and the computation.

## What it means when you call the API

While a date is inside the table, the `source` field is `mabims`. Here is the start of Sha'ban 1448:

```bash
curl "https://api.mabims.dev/api/v1/convert?date=2027-01-09&calendar=gregorian"
```

```json
{
  "input": { "date": "2027-01-09", "calendar": "gregorian", "tz": null },
  "output": {
    "date": "1448-08-01",
    "calendar": "hijri",
    "day": 1,
    "month": 8,
    "month_name": "Sha'ban",
    "year": 1448,
    "weekday": "Sabtu"
  },
  "source": "mabims",
  "warnings": []
}
```

1 January 2028 is already outside the table. The API still answers, but `source` changes to `mabims-computed` and the response includes a warning. That means the date is calculated with the Neo MABIMS criteria, not taken from the official calendar.

| Date | Result | Source |
|---|---|---|
| 9 January 2027 | 1 Sha'ban 1448 | `mabims` |
| 29 December 2027 | 1 Sha'ban 1449 | `mabims` |
| 1 January 2028 | 4 Sha'ban 1449 | `mabims-computed` |

## How to update the table

With this update, `api/data/month_starts.json` is the single reference for the official calendar. It holds one line per Hijri month in the form `"YYYY-MM": "YYYY-MM-DD"`. To add a new year, fill in the month starts and adjust `coverage_end`.

Then run:

```bash
cd api
python -m scripts.build_calendar_data
```

The script rebuilds `calendar_data.json`, checks month lengths, and tells you if any row is still blank. `apply_flip.py` also writes Sidang Isbat corrections back to the same file, so there are no longer two sources that can drift apart.

## A note on the final month

Month 1449-08 currently has only three days in the table, namely 29 to 31 December 2027. Its length cannot be verified yet because the next month start, 1449-09, only arrives with the 2028 data. Until then, dates after 31 December 2027 are still served from computation.

## Closing

With this extension, API users get official Kemenag dates through the end of 2027. You can always check the coverage bounds at `GET /api/v1/meta` or on the [Data Coverage](/en/data-coverage/) page. If your app shows dates after 31 December 2027, keep checking the `source` field so users know the date is still a computed result.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "The 2027 MABIMS Table Is In, API Coverage Now Runs Through 2027",
  "description": "The official Kemenag calendar for 2027 is now part of the MABIMS API. Curated coverage reaches 31 December 2027 and every 2027 month start matches the Neo MABIMS computation.",
  "datePublished": "2026-11-16",
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
    "@id": "https://mabims.dev/en/blog/tabel-mabims-2027"
  }
}
</script>
