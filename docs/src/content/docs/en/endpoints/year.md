---
title: GET /year
description: All days in a year — 12 months in one call.
---

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

For `calendar=hijri`, months beyond the official table are still served from the Neo MABIMS computed tier while within the supported range.

## Errors

| `code` | HTTP | Cause |
|---|---|---|
| `invalid_year` | 400 | Year out of supported bounds |
| `invalid_calendar` | 400 | `calendar` param is not `hijri` or `gregorian` |
| `out_of_coverage` | 400 | Month outside table coverage |
| `date_out_of_supported_range` | 400 | Date exceeds supported range |
