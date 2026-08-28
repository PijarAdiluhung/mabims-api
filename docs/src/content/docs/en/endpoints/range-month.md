---
title: GET /range & /month
description: Bulk conversion for date ranges and calendar grids.
---

## GET /range

Converts every day in an inclusive range.

```
GET /api/v1/range?start={YYYY-MM-DD}&end={YYYY-MM-DD}&calendar={gregorian|hijri}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `start` / `end` | string | yes | ISO dates; `start ≤ end`; max span 400 days |
| `calendar` | string | no (default `gregorian`) | Calendar of the input bounds |

```json
{
  "input": { "start": "2025-01-01", "end": "2025-01-03", "calendar": "gregorian" },
  "count": 3,
  "items": [
    { "gregorian": "2025-01-01", "hijri": "1446-07-01", "source": "mabims" },
    { "gregorian": "2025-01-02", "hijri": "1446-07-02", "source": "mabims" },
    { "gregorian": "2025-01-03", "hijri": "1446-07-03", "source": "mabims" }
  ],
  "warnings": []
}
```

Each item carries its own `source` — ranges crossing the table boundary can mix
authoritative and fallback data.

## GET /month

Convenience wrapper that resolves a whole month grid.

```
GET /api/v1/month?year={Y}&month={M}&calendar={gregorian|hijri}
```

For `calendar=hijri` the response contains every Gregorian date onto which that Hijri month
maps — exactly what a Hijri month-view needs (29–30 items). Same item shape as `/range`.

## Errors

All errors return a standard JSON envelope:

```json
{
  "error": {
    "code": "range_too_large",
    "message": "Range is limited to 400 days."
  }
}
```

| `code` | HTTP | Cause |
|---|---|---|
| `invalid_step` | 400 | Step is not `day` |
| `range_too_large` | 400 | Range exceeds 400 days |
| `out_of_coverage` | 400 | Date outside table coverage |
| `invalid_month` | 400 | Month is not 1–12 |
| `invalid_year` | 400 | Year out of supported bounds |
