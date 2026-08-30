---
title: GET /meta
description: Table coverage, data version and fallback status.
---

Machine-readable truth about the dataset backing every other endpoint.

```
GET /api/v1/meta
```

```json
{
  "version": "1.0.0",
  "data_version": "9f2c41aa7b03",
  "coverage": { "first": "2024-01-13", "last": "2026-12-31" },
  "computed_active": false,
  "computed_months": [],
  "method": "neo-mabims-sabang",
  "docs_url": "https://mabims.dev"
}
```

| Field | Description |
|---|---|
| `data_version` | Short hash of the MABIMS table — changes when the table is updated |
| `coverage` | Gregorian range covered by the authoritative table |
| `computed_active` | `true` once any request has been served from the computed Neo MABIMS calendar |
| `computed_months` | Which months have been computed via the Neo MABIMS criteria so far |
| `method` | Out-of-table computation method (`neo-mabims-sabang`) |

## Recommended client behaviour

1. Poll `/meta` daily (it is cheap and cacheable for 5 minutes).
2. If `computed_active` is true, show a subtle notice in your UI —
   dates may drift ±1 day from official announcements.

## GET /healthz

Liveness probe for uptime monitors. Returns `{"status": "ok", "version": "..."}` with
`Cache-Control: no-store`.
