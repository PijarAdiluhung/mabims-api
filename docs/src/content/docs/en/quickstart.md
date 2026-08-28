---
title: Quickstart
description: Make your first MABIMS conversion request in under a minute.
---

Base URL:

```
https://api.mabims.dev/api/v1
```

## Today's Hijri date

The most common use case — what Hijri date is it right now?

```bash
curl "https://api.mabims.dev/api/v1/today"
```

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448 },
  "source": "mabims",
  "warnings": []
}
```

`today` defaults to **Asia/Jakarta (UTC+7)**. Override with any IANA zone or UTC offset:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Kuala_Lumpur"
curl "https://api.mabims.dev/api/v1/today?tz=UTC+8"
```

## Convert a specific date

```bash
curl "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl "https://api.mabims.dev/api/v1/convert?date=1446-07-03&calendar=hijri"
```

## Always check `source`

Every response carries a `source` field:

- `mabims` — authoritative, from the curated table (2024-01-13 to 2026-12-31)
- `mabims-computed` — computed with Neo MABIMS criteria (after 2026-12-31, up to 2053)

Treat `warnings` as user-facing notices when non-empty.

## Browser access

The API is public and CORS-permissive — client-side apps on any domain can call it directly.
Server-side calls are equally unrestricted. See [Access & Rate Limits](/access) for the
full policy and abuse protection details.

## Next steps

- Full parameter reference: [API Reference](/endpoints/convert)
- Try it live: [Playground](/playground)
