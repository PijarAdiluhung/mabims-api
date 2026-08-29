---
title: Privacy Policy
description: How the MABIMS API handles your data — no tracking, no cookies.
---

## No Tracking

This API uses **no** cookies, fingerprinting, analytics, or user tracking of any kind. There are no user accounts, no data actively collected.

## Server Logs

Like any web service, standard access logs are recorded by the server (VPS and CDN):

| Data | Purpose | Storage |
|---|---|---|
| IP address | Rate limiting and debugging identification | Auto-rotated, deleted within days |
| Timestamp | Debugging and audit | Auto-rotated |
| User-Agent | Client identification (optional) | Auto-rotated |

These logs are **not used** for tracking, user profiling, or any purpose beyond technical operations.

## Rate Limiting

Rate limits are applied per IP address (240 requests/minute). IPs are used only for abuse prevention and are not stored permanently.

## CDN

Bunny CDN is used for caching. CDN edge nodes may process your IP address per [Bunny CDN's privacy policy](https://bunny.net/privacy-policy/). Caches are public — all clients receive the same response for the same parameters.

## No Data Storage

The API is stateless:
- No request bodies are stored
- No sessions are tracked
- No user data is recorded

## Contact

For privacy-related questions, contact [halo@pixostudio.id](mailto:halo@pixostudio.id).
