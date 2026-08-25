---
title: Access & Rate Limits
description: Who can call the API, browser origin rules, and abuse protection.
---

## Reads are public

Every endpoint under `/api/v1/*` is **public** — no keys, no registration. Calendar dates
aren't secrets, and gating them would only push integrators to worse data sources.

## Browser vs server access

| Client | Behaviour |
|---|---|
| Server-side (curl, backend, cron) | Always allowed — CORS doesn't apply |
| Browser | Allowed from any origin |

Responses are served with permissive CORS headers, so client-side apps on any domain can
call the API directly.

:::note[Deploying your own restrictions?]
Self-hosters can re-enable an origin allowlist via the `ALLOWED_ORIGINS` environment
variable (comma-separated exact origins, or `*` for public — the default). A suffix-based
rule (`ALLOWED_ORIGIN_SUFFIXES`) also allows apex + all subdomains of a domain.
:::

## Rate limits & caching

- The **origin** applies a per-IP rate limit (default 240/min, `429` when exceeded) purely
  as abuse protection.
- In production the API sits behind a CDN: identical requests are answered at the edge and
  never reach the origin. At millions of requests/day the origin sees roughly one request
  per edge location per cached resource per day.
- [`/today`](/endpoints/today) responses carry a TTL that expires exactly at local midnight,
  so cached answers are never stale past date rollover.

## Higher limits / commercial use

Need a guaranteed rate, SLA, or want to support the project?
Contact [halo@pixostudio.id](mailto:halo@pixostudio.id).
