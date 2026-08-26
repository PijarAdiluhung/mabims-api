---
title: GET /events
description: Islamic observance dates (1 Muharram, Maulid, Ramadan start, Eid al-Fitr, Eid al-Adha) straight from the official MABIMS table.
---

Returns the **Islamic observance dates** for one calendar year — not astronomical guesses,
but the same curated MABIMS table that powers `/convert`. This is what sets this API apart
from Umm al-Qura calendars: dates that match the official announcements used across
Indonesia, Malaysia and Singapore.

```
GET /api/v1/events?year={Y}&calendar={gregorian|hijri}
```

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `year` | integer | yes | Year in the requested `calendar` (Hijri: `1446`, Gregorian: `2025`) |
| `calendar` | string | no (default `gregorian`) | `gregorian` or `hijri` |

## Response

```json
{
  "input": { "year": 1446, "calendar": "hijri" },
  "count": 5,
  "events": [
    { "event": "1_muharram",   "name": "Tahun Baru Islam",         "hijri": "1446-01-01", "gregorian": "2024-07-07", "source": "mabims" },
    { "event": "maulid_nabi",  "name": "Maulid Nabi Muhammad SAW", "hijri": "1446-03-12", "gregorian": "2024-09-16", "source": "mabims" },
    { "event": "awal_ramadan", "name": "Awal Ramadan",             "hijri": "1446-09-01", "gregorian": "2025-03-01", "source": "mabims" },
    { "event": "idul_fitri",   "name": "Idul Fitri",               "hijri": "1446-10-01", "gregorian": "2025-03-31", "source": "mabims" },
    { "event": "idul_adha",    "name": "Idul Adha",                "hijri": "1446-12-10", "gregorian": "2025-06-06", "source": "mabims" }
  ],
  "warnings": []
}
```

Items are sorted by Gregorian date.

## Available events

| `event` | Name | Hijri month | Day |
|---|---|---|---|
| `1_muharram` | Islamic New Year | 1 (Muharram) | 1 |
| `maulid_nabi` | Prophet's Birthday | 3 (Rabi' al-awwal) | 12 |
| `awal_ramadan` | First day of Ramadan | 9 (Ramadan) | 1 |
| `idul_fitri` | Eid al-Fitr | 10 (Shawwal) | 1 |
| `idul_adha` | Eid al-Adha | 12 (Dhu al-Hijjah) | 10 |

## Notes

- Data comes **only from the curated MABIMS table** (`source` is always `mabims`) — no
  computed-tier warnings on this endpoint.
- Outside table coverage the response is still `200` with `"count": 0` and an empty list.
  Check [/meta](/endpoints/meta) for the current coverage span.
- Like `/convert`, responses are cached immutably at the CDN — observance dates never
  change once published.
