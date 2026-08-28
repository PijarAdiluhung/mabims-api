---
title: GET /today
description: The hero endpoint — today's Hijri date, timezone aware.
---

Returns the Hijri date for "now" in the requested timezone. This is the endpoint most consumer
apps poll, and it is tuned for it: responses carry **dynamic edge-cache TTLs** so a CDN serves
nearly all traffic.

```
GET /api/v1/today?tz={timezone}
```

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `tz` | string | no (default `Asia/Jakarta`, UTC+7) | IANA zone name (`Asia/Kuala_Lumpur`) or UTC offset (`UTC+7`, `+08:00`) |

## Response

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448 },
  "source": "mabims",
  "warnings": []
}
```

The `input.tz` field echoes the *resolved* timezone so clients can confirm what was used.

## Immutable variant

```{=html}
GET /api/v1/today/{YYYY-MM-DD}
```

Same conversion for any given Gregorian date — useful as a stable, cache-forever resource and
for replaying historical days:

```bash
curl "https://api.mabims.dev/api/v1/today/2025-01-03"
```

## Caching behaviour

- `Cache-Control: public, max-age=60, s-maxage=<seconds until local midnight>`
- A cache miss at 06:00 is cached at the edge for ~18 hours; a miss at 23:59 expires right
  after midnight so the date rolls over immediately.
- At millions of requests/day the origin sees roughly one request per edge location per day.
