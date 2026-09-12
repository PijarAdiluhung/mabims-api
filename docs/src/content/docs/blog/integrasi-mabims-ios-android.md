---
title: "Cara Integrasi MABIMS API ke Aplikasi iOS & Android"
description: "Cara pasang kalender Hijriah kriteria MABIMS di app native iOS/Android biar tetap akurat walau offline, pakai pola cache /year + live /today, contoh Swift & Kotlin."
date: 2026-09-12
tags:
  - Integrasi
  - Tutorial
  - Mobile
  - Hijriah
  - MABIMS
  - Swift
  - Kotlin
excerpt: "Cara pasang kalender Hijriah kriteria MABIMS di app native iOS/Android biar tetap akurat walau offline, pakai pola cache /year + live /today, contoh Swift & Kotlin."
cover:
  image: ../../../assets/hp.jpg
  alt: Aplikasi mobile integrasi MABIMS API
authors:
  - pijar
---

Di [post sebelumnya](https://mabims.dev/blog/cara-tampilkan-tanggal-hijriah/) kita bahas cara nampilin tanggal Hijriah di website: tinggal fetch `/today`, cache sejam di server, selesai. Gampang, karena web itu asumsinya selalu online.

App mobile beda cerita. User bisa buka app pas mode pesawat, di daerah sinyal lemah, atau bahkan sengaja mode offline. Kalau app cuma andelin `fetch('/today')` tanpa fallback, begitu offline ya tanggal Hijriah-nya nggak muncul sama sekali. Untuk widget masjid/pesantren atau app ibadah, itu masalah beneran, bukan cuma UX yang kurang mulus.

Jadi buat native app (Swift/Kotlin), strateginya perlu 2 lapis: satu untuk kondisi online (akurat, real-time), satu untuk fallback offline (dari cache lokal).

## Kenapa Harus MABIMS (Bukan Umm al-Qura)?

Kalau install library kalender Hijriah dari package manager, hampir semua defaultnya pakai kriteria [Umm al-Qura](https://en.wikipedia.org/wiki/Umm_al-Qura_calendar) (kalender resmi Arab Saudi), gampang ditemukan, dokumentasinya lengkap, tapi bisa beda ±1 hari dari tanggal yang diumumkan [Kemenag RI](https://kemenag.go.id). Buat app yang dipakai user Indonesia (jadwal puasa, hari besar, dsb), selisih sehari itu bisa bikin awam. Ceritanya lebih lengkap ada di [Cerita di Balik MABIMS API](https://mabims.dev/blog/kenapa-saya-bikin-mabims-dev/), soal kenapa post itu dan API ini dibuat.

## Arsitektur 2 Layer

**Layer 1: Cache tahunan (`/year`) sebagai fallback offline**

Fetch sekali:

```
GET https://api.mabims.dev/api/v1/year?year=2026&calendar=gregorian
```

Pakai `calendar=gregorian` (bukan `hijri`), karena kalender Kemenag itu dipublikasikan per tahun Masehi ("Kalender 2026"), jadi lebih natural nyimpen & nge-refresh per tahun Masehi juga. Satu fetch langsung dapet Januari-Desember lengkap, gampang di-lookup dari tanggal device yang juga Masehi.

Simpan hasilnya lokal ([Room](https://developer.android.com/training/data-storage/room)/[SharedPreferences](https://developer.android.com/reference/android/content/SharedPreferences) di Android, atau file JSON + [UserDefaults](https://developer.apple.com/documentation/foundation/userdefaults) di iOS). Ini yang dipakai kalau app lagi offline.

**Layer 2: `/today` live setiap app dibuka & online**

```
GET https://api.mabims.dev/api/v1/today?tz={timezone_device}
```

Ini source of truth paling akurat, karena bisa nangkep update data terbaru dari Kemenag. Alur baca di app:

1. Ada koneksi? → hit `/today`, tampilkan hasilnya.
2. Gagal (timeout/no network)? → fallback: cari tanggal hari ini di cache `/year` lokal.

Network-first, bukan cache-first, karena `/today` murah (response-nya kecil) dan sudah dilayani lewat CDN edge cache dengan TTL yang kedaluwarsa persis tengah malam lokal, jadi hampir nggak pernah nyampe origin.

## Kapan Refresh Cache `/year`?

Simpel: **terjadwal sekali di akhir Desember**, fetch ulang `/year` untuk tahun Masehi berikutnya (background task: [`BGAppRefreshTask`](https://developer.apple.com/documentation/backgroundtasks/bgtaskrefresh) di iOS, [`WorkManager`](https://developer.android.com/reference/androidx/work/WorkManager) periodic di Android).

Satu catatan penting: pendekatan ini sengaja simpel dan cukup buat kebanyakan kasus, karena `calendar=gregorian` bikin siklus refresh-nya align sama tahun Masehi (bukan tahun Hijriah yang bergeser ~11 hari tiap tahun seperti kalau kita cache per tahun Hijriah). Tapi tetap kasih **safety net**: kalau suatu saat `/today` gagal dan hasil lookup dari cache ternyata nggak ketemu (data belum ke-refresh, atau app baru pertama kali dipasang lewat pertengahan tahun), trigger fetch `/year` on-the-spot saat itu juga, jangan nunggu jadwal Desember berikutnya.

## Contoh Kode: Swift (iOS)

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

    // Layer 2: live, dipanggil tiap app dibuka
    func today() async -> (date: String, warnings: [String]) {
        let tz = TimeZone.current.identifier
        if let url = URL(string: "\(baseURL)/today?tz=\(tz)") {
            if let (data, _) = try? await URLSession.shared.data(from: url),
               let decoded = try? JSONDecoder().decode(TodayResponse.self, from: data) {
                return (decoded.output.date, decoded.warnings)
            }
        }
        // fallback ke cache lokal
        return fallbackFromCache() ?? ("-", [])
    }

    private func fallbackFromCache() -> (String, [String])? {
        guard let cached = UserDefaults.standard.data(forKey: cacheKey) else { return nil }
        // parse & cari entry yang tanggal gregorian-nya == hari ini
        // (struktur /year: { months: { "1": [...], "2": [...] } })
        // ...lookup logic sesuai model kamu
        return nil // placeholder
    }

    // Layer 1: refresh tahunan, dipanggil dari BGAppRefreshTask akhir Desember
    // atau on-the-spot kalau fallback gagal nemu data
    func refreshYearCache(year: Int) async {
        guard let url = URL(string: "\(baseURL)/year?year=\(year)&calendar=gregorian") else { return }
        if let (data, _) = try? await URLSession.shared.data(from: url) {
            UserDefaults.standard.set(data, forKey: cacheKey)
            UserDefaults.standard.set(year, forKey: cacheYearKey)
        }
    }
}
```

Daftarin refresh task di `AppDelegate`/`SceneDelegate` pakai `BGTaskScheduler`, jadwalin sekali per tahun sekitar 28–31 Desember.

## Contoh Kode: Kotlin (Android)

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
    // Layer 2: live, dipanggil tiap app dibuka
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
        // lookup tanggal gregorian hari ini dari cached JSON (/year response)
        return null // placeholder, parsing sesuai model kamu
    }

    // Layer 1: refresh tahunan via WorkManager, akhir Desember
    // atau on-the-spot kalau fallback gagal nemu data
    suspend fun refreshYearCache(year: Int) {
        val response = api.getYear(year = year, calendar = "gregorian")
        prefs.edit().putString("hijri_year_cache", response.toRawJson()).apply()
        prefs.edit().putInt("hijri_year_cache_year", year).apply()
    }
}
```

Schedule-in lewat `WorkManager` periodic request (interval 1 tahun, atau lebih praktis: one-time request yang di-reschedule tiap kali jalan, dipicu sekitar akhir Desember).

## Edge Case yang Wajib Dipikirin

- **First launch tanpa internet sama sekali.** Kalau app baru diinstall dan langsung dibuka offline, cache `/year` belum ada. Opsinya: bundle snapshot data minimal di dalam app (assets/`res/raw` di Android, bundle resource di iOS), atau paksa user online sekali di onboarding.
- **Timezone.** Jangan hardcode `Asia/Jakarta`. Ambil dari `TimeZone.current.identifier` (Swift) atau `TimeZone.getDefault().id` (Kotlin), kirim sebagai param `tz`.
- **Field `warnings`.** Kalau nggak kosong (misalnya tanggal deket ambang visibilitas hilal), tampilkan indikator kecil di UI, misalnya "bisa geser 1 hari dari pengumuman resmi", biar user nggak kaget kalau nanti ada revisi.

## Bonus: Pakai React Native/Expo?

Kalau stack-nya React Native, alternatif yang lebih simpel: pakai package **[mabims-hijri](https://mabims.dev/sdk)**, data 2023-2026 udah dibundle langsung di package, jadi nggak perlu arsitektur cache manual sama sekali untuk kasus umum.

```
npm install mabims-hijri
```

## Penutup

Referensi lengkap tiap endpoint ada di:

- [Quickstart](https://mabims.dev/quickstart)
- [GET /today](https://mabims.dev/endpoints/today)
- [GET /month & /year](https://mabims.dev/endpoints/month-year)

Kalau app kamu butuh rate limit lebih tinggi atau SLA (misal buat app skala besar), hubungi <halo@pixostudio.id>.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Integrasi MABIMS API ke Aplikasi iOS & Android: Strategi Cache Offline-First",
  "description": "Cara pasang kalender Hijriah kriteria MABIMS di app native iOS/Android biar tetap akurat walau offline, pakai pola cache /year + live /today, contoh Swift & Kotlin.",
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
    "@id": "https://mabims.dev/blog/integrasi-mabims-ios-android"
  }
}
</script>