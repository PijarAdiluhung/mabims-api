---
title: "Integrating MABIMS API into iOS & Android Apps"
description: "How to add MABIMS-criteria Hijri dates to native iOS/Android apps that stay accurate even offline, using a /year cache + live /today pattern with Swift & Kotlin examples."
date: 2026-09-12
tags:
  - Integration
  - Tutorial
  - Mobile
  - Hijri
  - MABIMS
  - Swift
  - Kotlin
excerpt: "How to add MABIMS-criteria Hijri dates to native iOS/Android apps that stay accurate even offline, using a /year cache + live /today pattern with Swift & Kotlin examples."
cover:
  image: ../../../../assets/hp.jpg
  alt: Mobile app integrating MABIMS API
authors:
  - pijar
---

In a [previous post](https://mabims.dev/en/blog/cara-tampilkan-tanggal-hijriah/) we covered showing Hijri dates on websites: just fetch `/today`, cache for an hour on the server, done. Easy, because websites are assumed to always be online.

Mobile apps are a different story. Users might open the app in airplane mode, in a weak signal area, or intentionally go offline. If the app only relies on `fetch('/today')` with no fallback, the Hijri date simply won't appear when offline. For mosque/pesantren widgets or worship apps, this is a real problem — not just a UX hiccup.

So for native apps (Swift/Kotlin), the strategy needs two layers: one for online conditions (accurate, real-time), and one for offline fallback (from local cache).

## Why MABIMS (Not Umm al-Qura)?

If you install a Hijri calendar library from a package manager, almost all default to [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) criteria (Saudi Arabia's official calendar) — easy to find, well-documented, but can differ ±1 day from the date announced by Indonesia's [Kemenag](https://kemenag.go.id). For apps used by Indonesian users (fasting schedules, holidays, etc.), a one-day difference can confuse ordinary people. The full story is in [The Story Behind MABIMS API](https://mabims.dev/en/blog/kenapa-saya-bikin-mabims-dev/), on why this post and API were created.

## 2-Layer Architecture

**Layer 1: Annual cache (`/year`) as offline fallback**

Fetch once:

```
GET https://api.mabims.dev/api/v1/year?year=2026&calendar=gregorian
```

Use `calendar=gregorian` (not `hijri`), because Kemenag's calendar is published per Gregorian year ("Calendar 2026"), so it's more natural to store and refresh per Gregorian year too. One fetch gives you January–December complete, easy to look up from the device's Gregorian date.

Store the result locally ([Room](https://developer.android.com/training/data-storage/room)/[SharedPreferences](https://developer.android.com/reference/android/content/SharedPreferences) on Android, or JSON file + [UserDefaults](https://developer.apple.com/documentation/foundation/userdefaults) on iOS). This is what you use when the app is offline.

**Layer 2: `/today` live every time the app opens & is online**

```
GET https://api.mabims.dev/api/v1/today?tz={device_timezone}
```

This is the most accurate source of truth, because it can catch the latest data updates from Kemenag. The app's read flow:

1. Has connection? → hit `/today`, display the result.
2. Fails (timeout/no network)? → fallback: look up today's date in the local `/year` cache.

Network-first, not cache-first, because `/today` is cheap (small response) and already served via CDN edge cache with a TTL that expires exactly at local midnight, so it almost never hits the origin.

## When to Refresh the `/year` Cache?

Simple: **scheduled once at the end of December**, re-fetch `/year` for the next Gregorian year (background task: [`BGAppRefreshTask`](https://developer.apple.com/documentation/backgroundtasks/bgtaskrefresh) on iOS, periodic [`WorkManager`](https://developer.android.com/reference/androidx/work/WorkManager) on Android).

One important note: this approach is intentionally simple and sufficient for most cases, because `calendar=gregorian` makes the refresh cycle align with the Gregorian year (not the Hijri year which shifts ~11 days each year if you cache per Hijri year). But still provide a **safety net**: if `/today` fails and the cache lookup returns nothing (data hasn't been refreshed, or the app was first installed mid-year), trigger a `/year` fetch on the spot right then — don't wait for the next December schedule.

## Code Example: Swift (iOS)

```swift
import Foundation

struct HijriOutput: Codable {
    let date: String
    let day: Int
    let month: Int
    let month_name: String
    let year: Int
}

struct TodayResponse: Codable {
    let output: HijriOutput
    let source: String
    let warnings: [String]
}

final class HijriRepository {
    private let baseURL = "https://api.mabims.dev/api/v1"
    private let cacheKey = "hijri_year_cache"
    private let cacheYearKey = "hijri_year_cache_year"

    // Layer 2: live, called every time the app opens
    func today() async -> (date: String, warnings: [String]) {
        let tz = TimeZone.current.identifier
        if let url = URL(string: "\(baseURL)/today?tz=\(tz)") {
            if let (data, _) = try? await URLSession.shared.data(from: url),
               let decoded = try? JSONDecoder().decode(TodayResponse.self, from: data) {
                return (decoded.output.date, decoded.warnings)
            }
        }
        // fallback to local cache
        return fallbackFromCache() ?? ("-", [])
    }

    private func fallbackFromCache() -> (String, [String])? {
        guard let cached = UserDefaults.standard.data(forKey: cacheKey) else { return nil }
        // parse & find the entry where gregorian date == today
        // (/year structure: { months: { "1": [...], "2": [...] } })
        // ...lookup logic per your model
        return nil // placeholder
    }

    // Layer 1: annual refresh, called from BGAppRefreshTask at end of December
    // or on-the-spot if fallback fails to find data
    func refreshYearCache(year: Int) async {
        guard let url = URL(string: "\(baseURL)/year?year=\(year)&calendar=gregorian") else { return }
        if let (data, _) = try? await URLSession.shared.data(from: url) {
            UserDefaults.standard.set(data, forKey: cacheKey)
            UserDefaults.standard.set(year, forKey: cacheYearKey)
        }
    }
}
```

Register the refresh task in `AppDelegate`/`SceneDelegate` using `BGTaskScheduler`, scheduled once per year around December 28–31.

## Code Example: Kotlin (Android)

```kotlin
data class HijriOutput(
    val date: String, val day: Int, val month: Int,
    val month_name: String, val year: Int
)
data class TodayResponse(
    val output: HijriOutput, val source: String, val warnings: List<String>
)

class HijriRepository(
    private val api: MabimsApi, // Retrofit interface
    private val prefs: SharedPreferences
) {
    // Layer 2: live, called every time the app opens
    suspend fun today(): Pair<String, List<String>> {
        return try {
            val tz = java.util.TimeZone.getDefault().id
            val response = api.getToday(tz = tz)
            response.output.date to response.warnings
        } catch (e: Exception) {
            fallbackFromCache() ?: ("-" to emptyList())
        }
    }

    private fun fallbackFromCache(): Pair<String, List<String>>? {
        val cachedJson = prefs.getString("hijri_year_cache", null) ?: return null
        // lookup today's gregorian date from cached JSON (/year response)
        return null // placeholder, parse per your model
    }

    // Layer 1: annual refresh via WorkManager, end of December
    // or on-the-spot if fallback fails to find data
    suspend fun refreshYearCache(year: Int) {
        val response = api.getYear(year = year, calendar = "gregorian")
        prefs.edit().putString("hijri_year_cache", response.toRawJson()).apply()
        prefs.edit().putInt("hijri_year_cache_year", year).apply()
    }
}
```

Schedule via `WorkManager` periodic request (1-year interval, or more practical: a one-time request that reschedules itself each time it runs, triggered around end of December).

## Edge Cases to Handle

- **First launch with no internet at all.** If the app is just installed and opened offline, the `/year` cache doesn't exist yet. Options: bundle a minimal data snapshot inside the app (assets/`res/raw` on Android, bundle resource on iOS), or force the user online once during onboarding.
- **Timezone.** Don't hardcode `Asia/Jakarta`. Get it from `TimeZone.current.identifier` (Swift) or `TimeZone.getDefault().id` (Kotlin), and pass it as the `tz` param.
- **`warnings` field.** If it's not empty (e.g., date is near hilal visibility threshold), show a small indicator in the UI, like "may shift 1 day from official announcement", so users aren't surprised if a revision comes.

## Bonus: Using React Native/Expo?

If your stack is React Native, a simpler alternative: use the **[mabims-hijri](https://mabims.dev/en/sdk)** package — 2023–2026 data is bundled directly in the package, so no manual cache architecture is needed for common use cases.

```
npm install mabims-hijri
```

## Wrapping Up

Full endpoint reference at:

- [Quickstart](https://mabims.dev/en/quickstart)
- [GET /today](https://mabims.dev/en/endpoints/today)
- [GET /month & /year](https://mabims.dev/en/endpoints/month-year)

If your app needs higher rate limits or SLA (e.g., for large-scale apps), contact <halo@pixostudio.id>.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Integrating MABIMS API into iOS & Android Apps: Offline-First Cache Strategy",
  "description": "How to add MABIMS-criteria Hijri dates to native iOS/Android apps that stay accurate even offline, using a /year cache + live /today pattern with Swift & Kotlin examples.",
  "datePublished": "2026-09-12",
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
    "@id": "https://mabims.dev/en/blog/integrasi-mabims-ios-android"
  }
}
</script>