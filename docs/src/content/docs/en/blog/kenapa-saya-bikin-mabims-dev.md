---
title: "The Story Behind MABIMS API"
description: "From Kemenag's website showing wrong dates, to going viral, to being taken down... here's why mabims.dev was created."
date: 2026-08-27
tags:
  - Story
  - MABIMS
  - Kemenag
  - Hijri
excerpt: "Kemenag's website used to display Hijri dates on its homepage. Many people, including myself, relied on it. Just open the website, check the top corner, and you'd know today's Hijri date. Until one day, a viral post appeared..."
featured: true
cover:
  image: ../../../../assets/eclipse.jpg
  alt: Lunar eclipse
authors:
  - pijar
---

There's a funny (and slightly sad) story behind mabims.dev.

Kemenag's website used to display Hijri dates on its homepage. Many people, including myself, relied on it. Just open the website, check the top corner, and you'd know today's Hijri date.

Until one day, a viral post appeared. The Kemenag calendar said the 30th, but the Kemenag website said the 1st of the next month had already started. Off by one day.

The post spread everywhere. People questioned why an official site could differ from the calendar it itself issued.

## The solution? Just delete it

At the time I didn't know the details behind it — whether it was a bug, a miscalculation, or what. What I knew was that the ending was remarkably elegant: **the Hijri date on the website was deleted**. Not fixed, deleted. Problem solved, I guess... but it felt kind of off.

## A few years later, I became a junior dev

When I started working as a developer, I finally understood what probably happened. If you want to display a Hijri calendar on a website, the easiest way is to use a library or call a third-party API. And almost every Hijri calendar library/API you can easily find defaults to **Umm al-Qura** — Saudi Arabia's official calendar.

It makes sense that this is what's used. The documentation is thorough, easy to integrate, free. But Umm al-Qura is designed for Saudi Arabia's needs, not for Kemenag RI's moon sighting or isbat session results. That's why it can differ by ±1 day from what's announced in Indonesia — exactly the incident that went viral.

So it was likely not a "bug" in the sense of a code error. It was a bug caused by using the wrong data source for the Indonesian context.

## Filling the gap

After realizing this, I thought: if other developers in Indonesia want to build an app that displays the Hijri calendar and want it to match Kemenag's decision (not Saudi's), the options are very limited. Most have to scrape manually or maintain their own table (spoiler: developer ≠ astronomer).

That's why I built **mabims.dev**: a Hijri calendar API sourced from Kemenag RI's official calendar, using Neo MABIMS criteria for fallback beyond table coverage. Free, no API key, just call the endpoint.

Realistically... I don't know if many people will use it. But at least one app will definitely use it: [kajian.malangmengaji.com](https://kajian.malangmengaji.com), which I also built. If no other developers need it, fine — this API will keep running for my own app.

But if you're developing an app that needs an accurate Hijri calendar for Indonesia, feel free to use it. Free, open source, and hopefully it will never need to be taken down because it was caught showing the wrong date :)

---

**Try it now:**

```bash
curl "https://api.mabims.dev/api/v1/today"
```

Full documentation at [mabims.dev/quickstart](https://mabims.dev/en/quickstart).
