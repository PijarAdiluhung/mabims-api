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

- **CDN edge** (Bunny CDN): 4 requests/second sustained per IP, burst of 24. This is the
  primary rate limit — most requests never reach the origin.
- **Origin** (FastAPI): 240/min per IP as a fallback if the CDN is bypassed. Hilal endpoints
  (`/hilal/info`, `/hilal/viz`) are stricter at the origin (60 or 30/hour) due to heavy
  computation, but CDN-level per-endpoint limits are not yet configured.
- Identical requests are served from CDN cache and never reach the origin. At millions of
  requests/day the origin sees roughly one request per edge location per cached resource per day.
- [`/today`](/endpoints/today) responses carry a TTL that expires exactly at local midnight,
  so cached answers are never stale past date rollover.

## Higher limits / commercial use

Need a guaranteed rate, SLA, or want to support the project?
Contact [halo@pixostudio.id](mailto:halo@pixostudio.id).
