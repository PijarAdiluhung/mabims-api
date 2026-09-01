---
title: "Introducing mabims-hijri: Hijri Dates, Now Offline"
description: "Why I built an offline-first JavaScript SDK for MABIMS, and when to use it versus the REST API."
date: 2026-08-31
tags:
  - SDK
  - JavaScript
  - TypeScript
  - Hijri
  - Offline
excerpt: "If you just need today's Hijri date on your website, the REST API is great. But what if your app needs to work offline, or you're tired of managing rate limits? Meet mabims-hijri."
cover:
  image: ../../../../assets/app.jpg
  alt: mabims-hijri SDK
authors:
  - pijar
---

If you just need today's Hijri date on your website, the [REST API](https://mabims.dev/en/blog/cara-pakai-mabims-api) is great. One `fetch` call, parse the JSON, done.

But after building a few apps with it, I kept running into the same friction:

- **Every page load hits the API.** Even though the Hijri date doesn't change every few seconds.
- **Rate limits are fine, but they're still limits.** If your site gets traffic spikes, or you have multiple components all fetching the same date...
- **Offline doesn't exist.** Build a PWA or a mobile app? No Hijri date without a network connection.
- **Caching is your problem.** You have to build your own caching layer, handle stale data, and decide TTLs.

So I built **[mabims-hijri](https://www.npmjs.com/package/mabims-hijri)**, an offline-first npm package that bundles MABIMS 2024-2026 data directly in the package.

## What it does

```
Bundled MABIMS (2024-2026)  -->  Local cache  -->  Live API (fallback)
     ~70KB, built-in              TTL 24h          only when out of range
```

1. MABIMS 2024-2026 data is bundled inside the package (~70KB)
2. When online, the SDK checks `/meta` for newer data and auto-syncs
3. If the date is outside the bundle range, it falls back to the live API
4. All `today()`, `convert()`, and `range()` operations work without internet

No API key. No registration. Just `npm install`.

## Quick start

```bash
npm install mabims-hijri
```

```typescript
import { today, convert } from 'mabims-hijri';

// Today's Hijri date, works offline
const date = await today();
console.log(`${date.output.day} ${date.output.month_name} ${date.output.year} H`);

// Convert a specific date
const ramadhan = await convert('2026-02-19');
console.log(ramadhan.output.month_name); // 'Ramadhan'
```

That's it. No base URL, no headers, no fetch wrappers. The data is already in your app.

## SDK vs REST API: When to use which?

I still think the REST API is the right choice for many cases. Here's how I think about it:

**Use the REST API when:**
- You need hilal sky charts (`/hilal/viz`)
- You need data beyond 2024-2026 and don't want to bundle it
- You're building a server-side integration where you control caching
- You want the full OpenAPI spec and code generation

**Use the SDK when:**
- You just need today's date, conversion, or events in a JS/TS app
- You want offline support (PWAs, mobile apps, unreliable networks)
- You want zero-config, no fetch wrappers, no caching logic
- You're tired of managing rate limits for the same data

For example, in a React app:

```tsx
import { useState, useEffect } from 'react';
import { today, type HijriDate } from 'mabims-hijri';

function HijriDate() {
  const [date, setDate] = useState<HijriDate | null>(null);

  useEffect(() => {
    today().then((res) => setDate(res.output));
  }, []);

  if (!date) return <span>Loading...</span>;
  return <span>{date.day} {date.month_name} {date.year} H</span>;
}
```

No API URL to manage. No loading state to debug. Just import and use.

## What's inside the SDK

| Function | What it does |
|----------|--------------|
| `today()` | Today's Hijri date, timezone-aware |
| `convert(date)` | Single date conversion, either direction |
| `range(start, end)` | Bulk conversion (max 45 days) |
| `month(year, month)` | All days in a month |
| `year(year)` | All days in a year (12 months) |
| `events(year)` | Islamic observances (Ramadan, Eid, etc.) |
| `hilal.info(month, year)` | Hilal visibility data |

All of these work offline as long as the date is within the bundled range.

## React Native note

If you're building a React Native app, you'll need to set a storage adapter for persistent caching:

```typescript
import { setStorageAdapter } from 'mabims-hijri';
import AsyncStorage from '@react-native-async-storage/async-storage';

class RNStorage implements StorageAdapter {
  private prefix = 'mabims_';
  async get(key: string) { return AsyncStorage.getItem(this.prefix + key); }
  async set(key: string, value: string) { await AsyncStorage.setItem(this.prefix + key, value); }
  async has(key: string) { return (await AsyncStorage.getItem(this.prefix + key)) !== null; }
}

setStorageAdapter(new RNStorage());
```

Without this, the cache resets every time the app restarts.

## The bottom line

If your app's only Hijri-related need is "show today's date in the header," don't build a caching layer, don't write a fetch wrapper, and don't worry about rate limits.

```bash
npm install mabims-hijri
```

One import, one function call, done, online or offline.

Full documentation at [mabims.dev/en/sdk](https://mabims.dev/en/sdk/). Source on GitHub: [PijarAdiluhung/mabims-hijri](https://github.com/PijarAdiluhung/mabims-hijri).

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Introducing mabims-hijri: Hijri Dates, Now Offline",
  "description": "Why I built an offline-first JavaScript SDK for MABIMS, and when to use it versus the REST API.",
  "datePublished": "2026-08-31",
  "author": {
    "@type": "Person",
    "name": "Pijar Adiluhung",
    "url": "https://pixostudio.id"
  },
  "publisher": {
    "@type": "Organization",
    "name": "mabims.dev",
    "logo": {
      "@type": "ImageObject",
      "url": "https://mabims.dev/mabims-long.png"
    }
  },
  "image": "https://mabims.dev/og-image.png",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://mabims.dev/en/blog/introducing-mabims-hijri-sdk"
  }
}
</script>
