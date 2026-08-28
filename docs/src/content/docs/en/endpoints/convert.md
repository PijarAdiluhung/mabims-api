---
title: GET /convert
description: Convert a single date between Gregorian and Hijri calendars.
---

Converts one date in the direction implied by `calendar`.

```
GET /api/v1/convert?date={YYYY-MM-DD}&calendar={gregorian|hijri}
```

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `date` | string | yes | ISO date (`YYYY-MM-DD`) |
| `calendar` | string | no (default `gregorian`) | Calendar of the input date |

## Responses

**200 OK**

```json
{
  "input": { "date": "2025-01-03", "calendar": "gregorian" },
  "output": { "date": "1446-07-03", "calendar": "hijri", "day": 3, "month": 7, "month_name": "Rajab", "year": 1446 },
  "source": "mabims",
  "warnings": []
}
```

**400** — invalid date format or unknown calendar

```json
{
  "error": {
    "code": "invalid_date",
    "message": "'not-a-date' is not a valid ISO date (YYYY-MM-DD)."
  }
}
```

| `code` | Cause |
|---|---|
| `invalid_date` | Date is not in `YYYY-MM-DD` format |
| `invalid_calendar` | `calendar` parameter is not `gregorian` or `hijri` |
| `missing_parameter` | `date` query parameter is missing |
| `out_of_coverage` | Date is outside table coverage; see [/meta](/endpoints/meta) |

**404** — `date_not_found`: no pair exists for that date

```json
{
  "error": {
    "code": "date_not_found",
    "message": "No calendar pair exists for 2023-01-01 (gregorian). See /api/v1/meta for coverage."
  }
}
```

## Caching

Responses are immutable per input and sent with `Cache-Control: max-age=86400` — safe to cache
at any layer for a full day.

:::note
`/convert` is timezone-independent by design. Only [`/today`](/endpoints/today) takes a `tz`
parameter, because "today" depends on where you ask from.
:::
