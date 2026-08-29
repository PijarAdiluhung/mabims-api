---
title: GET /month & /year
description: Monthly and yearly calendar grids.
---

## GET /month

Convenience wrapper that resolves a whole month grid.

```
GET /api/v1/month?year={Y}&month={M}&calendar={hijri|gregorian}
```

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `year` | int | yes | Hijri or Gregorian year |
| `month` | int | yes | Month 1–12 |
| `calendar` | string | no (default `hijri`) | Calendar of the `year` input |

For `calendar=hijri` the response contains every Gregorian date onto which that Hijri month
maps — exactly what a Hijri month-view needs (29–30 items). Hijri months beyond the public
table (e.g. next year) are still resolved from the Neo MABIMS computed tier while within
the supported range. Same item shape as `/range`.

## GET /year

Returns every day across all 12 months of a year. Much simpler than calling `/month` 12 times.

```
GET /api/v1/year?year={Y}&calendar={hijri|gregorian}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `year` | int | yes | Hijri or Gregorian year |
| `calendar` | string | no (default `hijri`) | Calendar of the `year` input |

```json
{
  "input": { "year": 1447, "calendar": "hijri" },
  "count": 354,
  "months": {
    "1": [
      { "gregorian": "2025-06-27", "hijri": "1447-01-01", "source": "mabims" },
      { "gregorian": "2025-06-28", "hijri": "1447-01-02", "source": "mabims" }
    ],
    "2": [ "..." ],
    "3": [ "..." ],
    "4": [ "..." ],
    "5": [ "..." ],
    "6": [ "..." ],
    "7": [ "..." ],
    "8": [ "..." ],
    "9": [ "..." ],
    "10": [ "..." ],
    "11": [ "..." ],
    "12": [ "..." ]
  },
  "warnings": []
}
```

Each month key contains an array of items with the same shape as `/range`. The total `count` is the number of days across the entire year.

For `calendar=hijri`, months beyond the public table are still served from the Neo MABIMS computed tier while within the supported range.

## Errors

| `code` | HTTP | Cause |
|---|---|---|
| `invalid_month` | 400 | Month is not 1–12 |
| `invalid_year` | 400 | Year out of supported bounds |
| `invalid_calendar` | 400 | `calendar` param is not `hijri` or `gregorian` |
| `out_of_coverage` | 400 | Month outside table coverage |
| `date_out_of_supported_range` | 400 | Date exceeds supported range |
