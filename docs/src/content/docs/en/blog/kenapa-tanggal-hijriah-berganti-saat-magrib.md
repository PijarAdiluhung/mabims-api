---
title: "Why the Hijri Date Changes at Maghrib (and How to Handle It)"
description: "At 6:30 PM the Gregorian date is still the same day, but the Hijri date has already jumped to tomorrow. Here's why Hijri days begin at maghrib, and how to use the next=true parameter on GET /today so your app shows the right date."
date: 2026-09-19
tags:
  - Tutorial
  - Hijri
  - MABIMS
  - JavaScript
  - maghrib
excerpt: "At 6:30 PM the Gregorian date is still the same day, but the Hijri date has already jumped to tomorrow. Here's why Hijri days begin at maghrib, and how to use the next=true parameter on GET /today so your app shows the right date."
cover:
  image: ../../../../assets/maghrib.jpg
  alt: Evening sky at maghrib
authors:
  - pijar
---

This is the part that often slips past developers building Hijri date features. We're used to the "day changes at midnight" pattern, so our reflex is to grab today's date, display it, done. But for the Hijri calendar, that's only half correct.

In this post we cover two things: why Hijri days begin at maghrib, and how the `next=true` parameter on [GET /today](https://mabims.dev/en/endpoints/today) helps you handle it without headaches.

## Why do Hijri days begin at maghrib?

The Gregorian calendar counts days from one midnight to the next — pure convention. A worldwide agreement among nations, essentially.

The Hijri calendar is different. It's a lunar calendar, and each month starts with the **sighting of the hilal** — the first thin crescent visible after the new moon. The hilal can only be observed (or its criteria evaluated) **at sunset**, on the western horizon, just after maghrib.

So the logic goes:

```text
sunset (maghrib)
        ↓
hilal observed / criteria checked
        ↓
if criteria met, new month begins
        ↓
first day of new month starts NOW, not at midnight
```

Because the new-month determination happens at maghrib, it makes sense that the day boundary follows. Hijri days run from maghrib to maghrib.

If you've read the [deep dive on mabims-computed](/en/blog/deep-dive-mabims-computed), this connects directly. The Neo MABIMS criteria (moon altitude ≥ 3°, elongation ≥ 6.4°) are evaluated **at sunset**. That same moment is the day boundary.

## The simplest example: the first night of Ramadan

This is something every Indonesian has experienced.

Suppose 1 Ramadan falls on a Wednesday in the Gregorian calendar. When is the first tarawih prayer? **Tuesday night.**

Why? Because after maghrib on Tuesday, the Hijri date has already entered 1 Ramadan. The evening is already a Ramadan evening, so tarawih and sahur follow. The next day, Wednesday, is the first day of fasting (this is also why Saturday night is called "Sunday eve" in Indonesian culture).

So at 7 PM on Tuesday, the Gregorian calendar says "Tuesday" but the Hijri calendar already says "1 Ramadan." Both are correct — they just have different day boundaries.

The same applies to Jumu'ah night, the night of 1 Muharram, the night of Eid al-Fitr (takbiran night), and so on. All those "nights" actually belong to the following day.

## The problem for developers

Now imagine you're building a Hijri date widget for a mosque website. You call `/today` as usual:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
```

The response:

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "weekday": "Senin" },
  "source": "mabims",
  "warnings": []
}
```

This is correct during the day. But at 6:30 PM WIB, congregants visiting the website have already entered 12 Rabiul Akhir in Islamic terms, while your widget still shows 11. It only "catches up" at midnight.

That 5–6 hour gap seems small, but for a mosque website, pesantren app, or fasting reminder (Ayyamul Bidh, Monday-Thursday fasting, Ashura, etc.), the wrong date can cause confusion — especially when the night in question actually matters.

## The solution: `next=true`

That's why `/today` has a `next` parameter. Usage:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
```

The response now includes an additional object called `next`:

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "weekday": "Senin" },
  "next": { "date": "1448-03-12", "calendar": "hijri", "day": 12, "month": 3, "month_name": "Rabiul Akhir", "year": 1448, "weekday": "Selasa", "source": "mabims" },
  "source": "mabims",
  "warnings": []
}
```

This means:

- `output` = the Hijri date **right now** (before maghrib).
- `next` = the Hijri date that takes effect **after maghrib tonight**.

One request gives you both. Just pick which one to display based on whether maghrib has passed.

Without `next=true`, the `next` field doesn't appear at all and the response is identical to before. Your existing code is safe — nothing breaks.

## One important thing: the API does not calculate maghrib time

Read this carefully.

**The API doesn't know what time maghrib is in your location.** It only provides two candidate dates — `output` and `next`. When to switch from the first to the second is a client-side concern.

This makes sense when you think about it: maghrib time depends on a specific location (city, even coordinates) and changes every day. Maghrib in Jakarta, Malang, Makassar, and Jayapura are all different. So the API stays focused on what it does well — Hijri dates — and you source maghrib time from whatever prayer-schedule provider fits your users.

Any source works: a prayer-time library, a prayer-time API, or schedule data you already have in your app (if your app displays prayer times, just use the same maghrib time).

## JavaScript implementation example

```js
async function getHijriDate(maghribTime) {
  const res = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
  );
  const data = await res.json();

  // maghribTime is a Date object for today's maghrib at the user's location
  const isAfterMaghrib = new Date() >= maghribTime;

  return isAfterMaghrib ? data.next : data.output;
}
```

Then display it as usual:

```js
const maghribTime = getTodayMaghrib(); // from your prayer-schedule source
const date = await getHijriDate(maghribTime);

const { day, month_name, year } = date;
document.querySelector("#hijri-date").textContent =
  `${day} ${month_name} ${year} H`;
```

Before maghrib it shows `11 Rabiul Akhir 1448 H`; after maghrib it automatically becomes `12 Rabiul Akhir 1448 H`.

The upside is you don't need to re-fetch when maghrib arrives. Both `output` and `next` are available from the start, so one fetch is enough — just compare against the current time (using `setInterval` or checking whenever the component renders).

## What happens after midnight?

After 00:00, the Gregorian date rolls over and `/today` automatically returns an `output` containing the new Hijri date. Its value matches the `next` you fetched the previous evening.

So `next=true` is relevant in the **maghrib-to-midnight** window. Outside that window, `output` alone is sufficient. It's fine to always send `next=true` — the results stay consistent.

## Timezone and maghrib go hand in hand

If you've read the [integration tutorial](/en/blog/cara-pakai-mabims-api), I already covered the `tz` parameter. Here it becomes even more important.

`next=true` is always calculated relative to "today" in the timezone you send. If your user is in Makassar, send `tz=Asia/Makassar`. In Jayapura, send `tz=Asia/Jayapura`. If omitted, it defaults to `Asia/Jakarta`.

The `input.tz` field in the response shows which timezone was used, so you can verify the API calculated in the correct zone.

## Don't forget to check `next.source`

The `next` object has its own `source` field, separate from the main `source`. Why?

Because tomorrow's date might fall outside the official Kemenag table even if today's date is still inside it. For example, if today is the last day covered by the table, the main `source` is `mabims` but `next.source` could be `mabims-computed`.

```js
if (data.next?.source === "mabims-computed") {
  console.warn("Post-maghrib date computed using Neo MABIMS criteria, not the official table.");
}
```

This follows the same principle across the API: computed results never silently masquerade as official data. If you want to know more about the difference, see the [deep dive on mabims-computed](/en/blog/deep-dive-mabims-computed).

## Caching considerations

`/today` is edge-cached until local midnight. This is safe for `next=true` because both `output` and `next` are valid for the entire day. The switch from `output` to `next` happens on the client side, not the server, so caching won't cause the date to "stick."

But there's one gotcha if you build your own server-side cache (e.g. in WordPress or PHP like in the [previous tutorial](/en/blog/cara-tampilkan-tanggal-hijriah)):

> **Don't cache the final selected value.** Cache the raw response (`output` and `next`), then decide which to display each time the page renders.

If you cache the string `"11 Rabiul Akhir 1448 H"` for 1 hour, your widget could keep showing the old date for up to 1 hour after maghrib. If you cache the JSON response and make the `output` vs `next` choice at render time, the date stays current.

## Possible errors

The `next` parameter accepts `true`/`false` (case-insensitive) and `1`/`0`. If you send any other value, e.g. `next=yes`, the API responds:

```json
{
  "error": {
    "code": "invalid_next",
    "message": "..."
  }
}
```

with HTTP status `400`. So if your widget suddenly goes blank after adding this parameter, check the value first.

## Summary

1. Hijri days begin at **maghrib**, not midnight, because the new month is determined by the hilal evaluated at sunset.
2. As a result, from maghrib to midnight the Hijri date is already "tomorrow" while the Gregorian date is still the same day.
3. Use `?next=true` on `GET /today` to get the `next` object — the Hijri date that takes effect after maghrib tonight.
4. **The API does not calculate maghrib time.** You decide when to switch from `output` to `next`, using the maghrib time for your user's location.
5. Send the correct `tz`, check `next.source`, and if you build your own cache, store the raw response, not the selected result.

Try it now:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta&next=true"
```

Full endpoint documentation is at [mabims.dev/endpoints/today](https://mabims.dev/en/endpoints/today). If there's a case not covered or you spot a date that looks off, please open an issue on [GitHub](https://github.com/PijarAdiluhung/mabims-api).

Hopefully your Hijri date widget will never be a day late again :)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Why the Hijri Date Changes at Maghrib (and How to Handle It with next=true)",
  "description": "At 6:30 PM the Gregorian date is still the same day, but the Hijri date has already jumped to tomorrow. This isn't a bug. Here's why Hijri days begin at maghrib, and how to use the next=true parameter on GET /today so your app shows the right date.",
  "datePublished": "2026-09-19",
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
    "@id": "https://mabims.dev/en/blog/kenapa-tanggal-hijriah-berganti-saat-magrib"
  }
}
</script>
