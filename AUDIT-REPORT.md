# mabims.dev — Full Site Audit Report

**Date:** 2026-08-28
**Perspective:** Developer evaluating Hijri calendar API + Senior Marketing analysis

---

## What Already Works Well

### Landing Page

- Hero has live JSON response preview with latency badge (`200 OK · 183 ms`) — excellent, makes the API tangible immediately
- Comparison table (MABIMS vs Umm al-Qura vs Turki) is sharp and creates switching intent
- "418 days different" stat is a gut punch — makes devs rethink their current solution
- Feature section covers all the right points: auth-free, open source, timezone-aware, fallback
- Hilal viz endpoint (`/hilal/viz`) is a differentiator no other Hijri API has

### Documentation

- Quickstart is clean: base URL, working examples, timezone override, `source` field explained
- API reference has parameter tables, response examples, error codes (400, 404)
- Caching behavior is documented with real `Cache-Control` headers
- Access & Rate Limits page is transparent: 240/min, CDN caching, commercial contact for higher limits
- Data Coverage page is thorough: hard limits (2024–2053), fallback chain, `mabims-computed` vs `mabims` distinction

### Blog

- 3 posts (story, tutorial, behind-the-scenes) — good mix of content types
- RSS feed available
- Tutorial post covers JavaScript, Vue, React, mobile

### Playground

- Interactive converter + Hilal viz — rare for a free API, great for quick validation

---

## What Was Fixed (2026-08-28)

| # | Change | Status |
|---|--------|--------|
| 1 | Hero secondary CTA: "FAQ" → "Coba" (links to Playground) | ✅ Done |
| 2 | Bottom CTA: "FAQ" → "Coba" (links to Playground) | ✅ Done |
| 3 | Bottom CTA: added "Lihat tutorial integrasi →" link to blog tutorial | ✅ Done |
| 4 | Error response examples added to `/convert`, `/today`, `/range & /month`, `/events` (ID + EN) | ✅ Done |
| 5 | Migration guide created (`/migration`) with Aladhan → MABIMS side-by-side examples (ID + EN) | ✅ Done |
| 6 | Migration guide added to sidebar | ✅ Done |
| 7 | Sidebar FAQ renamed to "FAQ - Pertanyaan" | ✅ Done |
| 8 | Changelog page created (`/changelog`) with 1.0.0, 1.1.0, docs updates | ✅ Done |
| 9 | Changelog added to sidebar below FAQ | ✅ Done |
| 10 | Blog removed from sidebar (kept in top nav) | ✅ Done |

---

## What's Still Open

### Developer Experience

| Category | Issue | Priority |
|----------|-------|----------|
| **No SDK / npm package** | Only raw HTTP examples. No `npm install mabims`. | Medium |
| **No integration examples in API docs** | Blog tutorial exists but not inline in API reference pages. | Low |
| **No status page link** | No uptime monitoring or status page. | Medium |
| **No versioning strategy** | No mention of `/v2` or if `/v1` is frozen. | ✅ Done — SemVer adopted, documented in changelog |
| **No changelog** | Blog has 3 posts but no "what changed" log. | ✅ Done |
| **No community channel** | GitHub Issues only. No Discord/Telegram. | Low |

### Marketing & Conversion

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| **No social proof** | No GitHub stars badge, no "Used by X developers". | Deferred — site is fresh, revisit when traction grows. |
| **No "Who is this for" framing** | Devs don't see their use case (prayer apps? fintech? schools?). | Add a "Digunakan untuk" section. |
| **No newsletter / lead capture** | Losing visitors not ready to integrate yet. | Offer a "Hijri calendar cheat sheet" PDF. |
| **No performance / reliability proof** | Latency shown but no aggregate stats. | Add a small stats bar when uptime data is available. |

---

## Sidebar Structure (current)

```
Quickstart
Access & Rate Limits
API Reference
  GET /today
  GET /convert
  GET /range & /month
  GET /events
  GET /hilal
  GET /meta
Playground
  Konverter
  Hilal
Data Coverage
Migration dari Aladhan
FAQ - Pertanyaan
Changelog
```

Blog removed from sidebar — accessible via top nav and landing page CTA.

---

## Verdict

The product and docs are genuinely strong — above average for a free API. The changes made today (Coba CTA, error examples, migration guide, tutorial link, changelog, sidebar cleanup) directly address the "convinced → integrated" gap.

---

## Priority Remaining

1. Add social proof when traction grows (GitHub stars, community size)
2. Add status page / uptime monitoring
3. Add "Who is this for" use case section
4. Consider npm SDK for easier integration
