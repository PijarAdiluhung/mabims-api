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

- Full parameter reference: [API Reference](/endpoints/convert-range)
- Try it live: [Playground](/playground)
- OpenAPI spec: [api.mabims.dev/openapi.json](https://api.mabims.dev/openapi.json)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebAPI",
  "name": "MABIMS API",
  "description": "Free Hijri-Gregorian date conversion API based on Indonesia's official MABIMS criteria (Kementerian Agama RI). No API key required.",
  "url": "https://api.mabims.dev",
  "documentation": "https://mabims.dev/en/quickstart",
  "openAPISpec": "https://api.mabims.dev/openapi.json",
  "provider": {
    "@type": "Organization",
    "name": "mabims.dev",
    "url": "https://mabims.dev"
  },
  "potentialAction": [
    {
      "@type": "InvokeAction",
      "name": "Get today's Hijri date",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/today?tz={timezone}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Convert Gregorian to Hijri",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/convert?date={date}&calendar=gregorian",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Convert Hijri to Gregorian",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/convert?date={date}&calendar=hijri",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get Islamic events",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/events?year={year}&calendar={calendar}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get month calendar",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/month?year={year}&month={month}&calendar={calendar}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get hilal visibility",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/hilal/info?month={month}&year={year}",
        "contentType": "application/json"
      }
    }
  ]
}
</script>
