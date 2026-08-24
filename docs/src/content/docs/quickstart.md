---
title: Quickstart
description: Make your first MABIMS conversion request in under a minute.
---

Base URL:

```
https://api.example.com/api/v1
```

## Today's Hijri date

The most common use case — what Hijri date is it right now?

```bash
curl "https://api.example.com/api/v1/today"
```

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

`today` defaults to **Asia/Jakarta (UTC+7)**. Override with any IANA zone or UTC offset:

```bash
curl "https://api.example.com/api/v1/today?tz=Asia/Kuala_Lumpur"
curl "https://api.example.com/api/v1/today?tz=UTC+8"
```

## Convert a specific date

```bash
curl "https://api.example.com/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl "https://api.example.com/api/v1/convert?date=1446-07-03&calendar=hijri"
```

## Always check `source`

Every response carries a `source` field:

- `mabims` — authoritative, from the curated table
- `fallback:aladhan-ummalqura` — approximate; may differ ±1 day from local observation

Treat `warnings` as user-facing notices when non-empty.

## Browser access

Requests from browsers must come from an allowlisted origin. Server-side calls are unrestricted.
See [Data Coverage](/data-coverage) for how the API behaves at the edge of the table.

## Next steps

- Full parameter reference: [API Reference](/endpoints/convert)
- Try it live: [Playground](/playground)
