---
title: "Integration Tutorial"
description: "Integration examples for the mabims.dev API, from the simplest to more proper setups: JavaScript, Vue, React, and mobile."
date: 2026-08-28
tags:
  - Tutorial
  - JavaScript
  - Integration
  - Hijri
excerpt: "I built this API for developers, and I don't want integration to stop at documentation with just `GET /today` and that's it. So in this post I'll show examples from the simplest to more proper setups: plain JavaScript, Vue, React, and mobile apps."
cover:
  image: ../../../../assets/tutorial.jpg
  alt: API integration tutorial
authors:
  - pijar
---

I built this API for developers, and I don't want integration to stop at documentation with just `GET /today` and that's it. So in this post I'll show examples from the simplest to more proper setups: plain JavaScript, Vue, React, and mobile apps.

## Simplest: JavaScript

If your website only needs to display today's Hijri date, it's actually this simple:

```js
const response = await fetch("https://api.mabims.dev/api/v1/today");
const data = await response.json();

console.log(data);
```

The response looks like this:

```json
{
  "input": { "date": "2026-08-28", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-15", "calendar": "hijri", "day": 15, "month": 3, "month_name": "Rabiul Akhir", "year": 1448 },
  "source": "mabims",
  "warnings": []
}
```

Just grab the `output` field to display. It's already complete, no parsing needed:

```js
const { day, month_name, year } = data.output;
document.querySelector("#hijri-date").textContent = `${day} ${month_name} ${year} H`;
```

So if your website header has:

```html
<div id="hijri-date"></div>
```

Just call the function above and the Hijri date will appear.

No library installation. No API key. No need to build your own server just to fetch a Hijri date.

## Using timezones

This is a part I think is important.

A Hijri date isn't just about converting Gregorian → Hijri. **Timezones also determine what "today" means.**

For example, your server is in the US, but most of your users are in Indonesia. You don't want 00:30 WIB to be treated as the previous day because your server is still on the day before.

mabims.dev provides a timezone override so you can specify which timezone to use. Use the `tz` parameter:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
);

const data = await response.json();
```

For apps targeting Indonesia, I usually explicitly use `Asia/Jakarta`, `Asia/Makassar`, or `Asia/Jayapura` as needed.

## In Vue

If you use Vue, the concept is the same. The difference is we store the API result in state.

Using Composition API:

```vue
<script setup>
import { ref, onMounted } from "vue";

const hijriDate = ref(null);

onMounted(async () => {
  const response = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
  );

  hijriDate.value = await response.json();
});
</script>

<template>
  <div v-if="hijriDate">
    {{ hijriDate.output.date }}
  </div>

  <div v-else>
    Loading Hijri date...
  </div>
</template>
```

Done.

I actually recommend this approach over including a Hijri calendar library that's much larger, if your app's need is just **displaying the Hijri date**.

## In React

React is more or less the same:

```jsx
import { useEffect, useState } from "react";

export default function HijriDate() {
  const [date, setDate] = useState(null);

  useEffect(() => {
    fetch("https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta")
      .then((response) => response.json())
      .then((data) => setDate(data));
  }, []);

  if (!date) {
    return <span>Loading Hijri date...</span>;
  }

  return <span>{date.output.date}</span>;
}
```

No additional dependencies.

React just fetches the API → stores the result → renders.

## If you need a specific date

`/today` works when all you need is today's Hijri date.

But what if the user picks a date from a date picker?

Say the user picks:

> August 17, 2026

You can use the conversion endpoint:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/convert?date=2026-08-17"
);

const data = await response.json();
```

This is useful for calendars, forms, articles with publication dates, or date search features.

For example, the user picks August 17, 2026 and you want to display the Hijri version. Just send that Gregorian date to the API.

## Don't forget to check `source`

There's one thing I think is quite important when consuming this API.

The mabims.dev response includes a `source` field.

Simply put, there are two possibilities:

- `mabims` — the date comes from Kemenag's official table.
- `mabims-computed` — the date was calculated using Neo MABIMS criteria as a fallback when the date is outside the table's coverage.

Why do I expose this?

Because I don't want the API to silently return computed results while developers assume it's the official date from Kemenag.

If your app is serious about the calendar, you can store or display this information.

```js
if (data.source === "mabims-computed") {
  console.log("Date uses Neo MABIMS computed result");
}
```

And if the API returns `warnings`, don't just throw them away.

```js
if (data.warnings?.length) {
  console.warn(data.warnings);
}
```

## For mobile apps

If you're building an Android/iOS app, the principle is actually the same.

Whether it's Flutter, React Native, Kotlin, Swift, or any other framework — as long as your app can make HTTP requests, you can call this API.

Pseudocode:

```text
GET https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta
        ↓
JSON response
        ↓
Store in state
        ↓
Display:
"1448-03-15"
```

The API doesn't care whether the request comes from a browser, server, or mobile app.

## But should every page make its own API request?

Now we're getting into architecture.

If your website has 100 components that all need the Hijri date, **don't have every component call `fetch("/today")` independently.**

Fetch once, then share the result.

On the frontend, you can create your own composable/hook/service.

For example in React:

```js
export async function getHijriToday() {
  const response = await fetch(
    "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
  );

  if (!response.ok) {
    throw new Error("Failed to fetch Hijri date");
  }

  return response.json();
}
```

Then other components just use that function.

For larger apps, you can even cache the result since the Hijri date doesn't change every few seconds.

## What about SSR or backend?

This is even more interesting.

If you're using Next.js, Nuxt, Laravel, Rails, Django, or any other backend, you can also call mabims.dev from your server.

Simple example:

```js
const response = await fetch(
  "https://api.mabims.dev/api/v1/today?tz=Asia/Jakarta"
);

const hijriDate = await response.json();
```

Then your server sends that date to the browser.

The advantage is the Hijri date can already be available when the page first renders.

But if you do this, still think about caching. There's no point in your server requesting the same date multiple times a day.

## So when should you use this API?

In my opinion, if your need is just:

> "I want to display the Hijri date on my website."

Don't build your own calendar system.

Don't maintain your own table.

Don't copy-paste dates from a PDF calendar into a database.

And don't expect a calendar library that defaults to Umm al-Qura to automatically match Indonesia's needs.

Just:

```text
Website / App
      ↓
mabims.dev
      ↓
MABIMS-based Hijri date
```

If you need today's date, use `/today`.

If you need to convert a specific date, use `/convert`.

If your app needs a specific timezone, specify it explicitly.

And if your app is administratively or religiously significant, **always treat the API as a technical data source, not a replacement for official Kemenag decisions.**

That's it. Hope it helps!
