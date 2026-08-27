# Expansion Plan: FAQ + Blog

## Milestone 1 — FAQ Page

### Goals
- Add a bilingual FAQ page (`/faq/` + `/en/faq/`)
- Improve user self-service, reduce repeated questions
- Add FAQ schema markup for Google rich results

### Tasks

| # | Task | Details |
|---|---|---|
| 1.1 | Create `FaqAccordion.astro` component | Click-to-expand accordion. Pure CSS + minimal JS. Reusable for both languages. |
| 1.2 | Create `/faq.astro` (Indonesian) | Custom Astro page using FaqAccordion. Groups: Umum, Akses & Auth, Teknis, Konversi, Integrasi. |
| 1.3 | Create `/en/faq.astro` (English) | Same structure, translated content. |
| 1.4 | Add FAQ schema markup | `<script type="application/ld+json">` with `FAQPage` schema for SEO. |
| 1.5 | Add sidebar entry | Add FAQ to `astro.config.mjs` sidebar under a new "Resources" group or top-level. |
| 1.6 | Update topbar CTA | Add FAQ link to topbar nav in `index.astro`. |
| 1.7 | Update bottom CTA | Change bottom CTA secondary button from Playground → FAQ in `Cta.astro`. |

### Deliverable
- Working FAQ page live at `/faq/` and `/en/faq/`
- Accessible from topbar and bottom CTA
- Indexed by Google with rich result eligibility

---

## Milestone 2 — Blog

### Goals
- Add a blog section powered by Astro content collections (zero extra dependencies)
- Publish technical articles, tutorials, and updates
- Establish content pipeline for ongoing publishing

### Tasks

| # | Task | Details |
|---|---|---|
| 2.1 | Define `blog` collection in `content.config.ts` | Fields: title, description, pubDate, author, tags. Uses `glob` loader on `src/content/blog/`. |
| 2.2 | Create blog listing page `/blog/index.astro` | Card grid sorted by pubDate desc. Shows title, description, date, tags. |
| 2.3 | Create blog post page `/blog/[slug].astro` | Renders markdown. Shows title, date, author, tags. Prose styling. |
| 2.4 | Create English equivalents `/en/blog/` | Same pages, translated UI strings. |
| 2.5 | Seed 2-3 starter articles | Topics: "Why MABIMS over Umm al-Qura", "Integrating MABIMS in Android", "Understanding Hilal Data". |
| 2.6 | Add sidebar entry | Add Blog to `astro.config.mjs` sidebar. |
| 2.7 | Update topbar CTA | Add Blog link to topbar nav in `index.astro`. |
| 2.8 | Update hero CTA | Change hero secondary button from Docs → Blog in `Hero.astro`. |
| 2.9 | Add Open Graph meta tags | Per-post OG title, description, image for social sharing. |

### Deliverable
- Blog listing at `/blog/` and `/en/blog/`
- Individual posts at `/blog/[slug]/`
- 2-3 published articles
- Accessible from topbar and hero

---

## Milestone 3 — Polish

### Goals
- Refine UX, performance, and SEO across FAQ + Blog
- Ensure consistency with existing site design
- Add discoverability features

### Tasks

| # | Task | Details |
|---|---|---|
| 3.1 | FAQ search/filter | Add tag-based filtering or search to FAQ page for long-term maintainability. |
| 3.2 | RSS feed | Add `@astrojs/rss` endpoint for blog subscribers at `/rss.xml`. |
| 3.3 | Blog tag pages | Generate `/blog/tags/[tag]/` pages for tag-based browsing. |
| 3.4 | Related posts | Show 2-3 related articles at bottom of each blog post (by tag matching). |
| 3.5 | Sitemap update | Ensure `@astrojs/sitemap` (if added) includes `/faq/` and `/blog/` routes. |
| 3.6 | Social share buttons | Add Twitter/WhatsApp share buttons on blog posts. |
| 3.7 | Dark mode polish | Verify FAQ accordion and blog pages look correct in dark mode. |
| 3.8 | Mobile responsiveness audit | Test FAQ accordion expand/collapse and blog cards on mobile viewports. |
| 3.9 | Lighthouse audit | Run Lighthouse on FAQ + blog pages, fix any performance/accessibility issues. |

### Deliverable
- Polished FAQ + Blog experience
- RSS feed live
- Tag browsing for blog
- No regressions on mobile or dark mode

---

## Summary

| Milestone | Scope | Status |
|---|---|---|
| 1 — FAQ | Bilingual FAQ page, accordion component, SEO schema, CTA updates | ⬜ Not started |
| 2 — Blog | Content collection, listing + post pages, starter articles, CTA updates | ⬜ Not started |
| 3 — Polish | Search, RSS, tags, related posts, OG, mobile/SEO audit | ⬜ Not started |
