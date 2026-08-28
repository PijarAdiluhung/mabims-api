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

**400** — invalid date format or unknown calendar (`invalid_date`, `invalid_calendar`, `missing_parameter`)
**404** — `date_not_found`: no pair exists for that date; check [/meta](/endpoints/meta)

## Caching

Responses are immutable per input and sent with `Cache-Control: max-age=86400` — safe to cache
at any layer for a full day.

:::note
`/convert` is timezone-independent by design. Only [`/today`](/endpoints/today) takes a `tz`
parameter, because "today" depends on where you ask from.
:::
