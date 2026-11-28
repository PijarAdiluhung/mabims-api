---
title: "Who's Using MABIMS API? Come Say Hi"
description: "MABIMS API serves around 3,000 devices a day and I know almost none of them. If you're one of them, stop by for a minute."
date: 2026-11-28
tags:
  - Story
  - MABIMS
  - Community
  - Open Source
excerpt: "Yesterday this API took around 10,000 requests from about 3,300 devices. I don't know the name of a single one of them. It's not laziness, it's because MABIMS API is deliberately keyless and has no sign-up. So I read the CDN logs, and the results were pretty funny."
cover:
  image: ../../../../assets/thank-you.jpg
  alt: Illustration thanking MABIMS API users
authors:
  - pijar
---

Yesterday this API took around 10,000 requests from about 3,300 devices. I don't know the name of a single one of them.

That's not laziness. MABIMS API is deliberately keyless, with no registration and no accounts. Anyone can call an endpoint right away. Convenient if you just want to try it, but the side effect is that I never learn who's using it.

Out of curiosity, I spent my weekend reading the CDN logs. The results were funny.

## What the logs show

About 87% of the traffic comes from one Android app I don't recognise.

Android apps usually identify themselves in the User-Agent. All I receive is this:

```text
Dalvik/2.1.0 (Linux; U; Android 16; SM-A065F Build/BP2A.250605.031.A3)
```

That's Android's default User-Agent, not an app name. So there are around 3,000 phones using this API every day and I don't know what app I'm looking at.

There's also a Flutter app that keeps opening `/month` and `/year`. And one screen that looks like a TV somewhere, asking for `/today` every hour and almost always getting a `304`. A few sites show up clearly from the Referer header. The rest are crawlers and uptime bots.

The busiest hours are actually before dawn. Between 04:00 and 06:00 WIB traffic jumps, then falls away towards midnight. For a Hijri calendar, that pattern makes perfect sense.

## Why I want to know who

Three reasons, and none of them are about collecting a fee.

**First, I want to say thank you.** These days building an API keeps getting easier. Building one that's actually useful? That's still hard. If someone is using it for a real product, I want to know, and I want to thank them directly.

**Second, I want to be able to give notice before anything changes.** If the response shape changes, or there's a new limit, or some data needs correcting, I have no way to reach you. All I have is a log, and it's gone after three days.

**Third, sometimes the problem isn't on my side and I can't tell anyone.** This week one client kept sending `?date=` to `/events`. That endpoint takes `year`, so the request keeps getting rejected, around 150 times a day. Maybe that's your site, and maybe you don't know yet.

## If you're up for it, here's how to say hi

Open an issue on [GitHub mabims-api](https://github.com/PijarAdiluhung/mabims-api/issues) with your project name and a link (drop a star while you're at it, hehe).

You don't need to explain your code. A project name and one link is enough. If a few come in, I'll put together a "Used by" page so other people can see real examples, and so anyone just starting out has something to learn from.

## If you'd rather stay anonymous

That's fine. Genuinely fine.

This API stays free, stays keyless, and will never ask for identity. I'm just curious, not collecting. If you'd rather stay quiet, keep using it exactly as you do now. Nothing changes.

But if you have a minute, one comment would make my day.

Thank you for using MABIMS API. Barakallahu fiikum.

Pijar, out.
