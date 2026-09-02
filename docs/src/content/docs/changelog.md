---
title: Changelog
description: Riwayat perubahan API dan dokumentasi MABIMS.
---

## 1.4.0 — 2026-09-02

### Added

- **Data kurasi 2023** — tabel resmi Kemenag RI kini dimulai 23 Januari 2023 (Rajab 1444 H), menambah cakupan resmi setahun ke belakang.
- **Tier retro `mabims-retro`** — tanggal di bawah tabel kurasi kini bisa diakses dengan `retro=true` (hingga 1945-01-01), dihitung dengan memproyeksikan kriteria Neo MABIMS ke belakang. Seed komputasi diperluas mundur sampai 1970. Error baru: `invalid_retro`.

## 1.3.0 — 2026-09-01

### Added

- **JavaScript SDK** — `mabims-hijri` paket npm offline-first. Bundle data MABIMS 2024-2026, `today()`, `convert()`, `range()`, `month()`, `year()`, `events()`, `hilal.info()`. Tanpa dependency, works di Node, browser, edge runtime.
- **SDK docs** — halaman `/sdk` (instalasi, quick start, error handling, framework examples) dan `/sdk/reference` (dokumentasi lengkap semua fungsi). Bilingual ID+EN.
- **Landing page** — kartu "JavaScript SDK" menempati posisi terakhir di feature cards.
- **Quickstart** — callout kuning ke SDK di bawah contoh kode.

---

## 1.2.1 — 2026-08-29

### Fixed

- **CORS header pada respons CDN** — `Access-Control-Allow-Origin` sebelumnya hanya ditambahkan saat request memiliki header `Origin`. BunnyCDN menyimpan varian tanpa header CORS, mem-block `fetch()` lintas-origin di browser. Kini semua respons (termasuk OPTIONS, error, dan GET tanpa Origin) selalu menyertakan header CORS.
- **README `/range` error table** — kolom `range_too_large` salah menampilkan "400 days", diperbaiki menjadi 45 hari.
- **404 page di sitemap** — `/en/404/` tidak lagi disertakan dalam sitemap.

### Changed

- **`calendar` default diseragamkan** — `/convert` dan `/range` default `gregorian` (sesuai format input `YYYY-MM-DD`). `/month`, `/year`, `/events` default `hijri` (sesuai filosofi API). Sebelumnya inkonsisten: `/year` saja yang default `hijri`.
- **Dokumentasi disusun ulang** — `/convert` & `/range` digabung satu halaman (gregorian), `/month` & `/year` digabung satu halaman (hijri), `/events` terpisah.

### Security

- **`X-Content-Type-Options: nosniff`** — ditambahkan ke semua respons API.

---

## 1.2.0 — 2026-08-29

### Added

- **GET /year** — semua hari dalam satu tahun (12 bulan sekaligus). `calendar` harus `hijri` atau `gregorian`. Respons berisi object `months` dengan kunci 1–12, masing-masing berisi array item sama seperti `/range`. Lebih praktis daripada memanggil `/month` 12 kali.

### Changed

- **`/range` max 45 hari** — batas `/range` untuk `calendar=gregorian` diturunkan dari 400 hari menjadi 45 hari. Untuk rentang lebih panjang, gunakan `/month` atau `/year`.

### Fixed

- **Hilal viz caching di docs** — dokumentasi salah menyatakan `Cache-Control: private` untuk `/hilal/info` dan `/hilal/viz`. Kode sebenarnya mengirim `public, s-maxage=86400` (CDN-cached). Docs kini mencerminkan perilaku aktual.

### Updated

- Playground Kalender kini menggunakan `/year` (1 request) alih-alih 12 panggilan `/month`.
- Dokumentasi: `/range` limit diperbarui di semua halaman (ID & EN), landing page, sidebar, README.

---

## 1.1.1 — 2026-08-29

### Fixed

- **Hijri bulan di luar tabel** — `/month` dan `/range` dengan `calendar=hijri` kini dilayani dari tier komputasi Neo MABIMS (sebelumnya hanya tanggal resmi tabel yang bisa diakses lewat dua endpoint ini).
- **Bug hari-31 pada `/range` Hijriah** — `/range?calendar=hijri` gagal dengan `out_of_coverage` saat rentang melewati batas bulan (hijriah tidak punya tanggal 31). Kini berjalan dengan melintasi bulan Hijriah per-bulan.
- **30 Safar ditolak** — `YYYY-02-30` adalah tanggal Hijriah sah (Safar dapat 30 hari) tetapi ditolak sebagai `invalid_date` karena parser Gregorian tidak mengenal 30 Februari. Parser Hijriah kini memisahkan validasi sintaks (hari 1–30) dari keberadaan data; hari yang benar-benar tidak ada (mis. hari-30 pada bulan berumur 29 hari) mengembalikan `404 date_not_found` dengan jujur.

---

## Documentation Updates — 2026-08-29

### Legal Compliance

- **Footer redesigned** — inline legal links (Ketentuan · Privasi · Sumber Data · Disclaimer), dropped inline disclaimer text.
- **New pages**: `/terms`, `/privacy`, `/data-sources`, `/disclaimer` (bilingual ID+EN), collapsed under "Legal" sidebar group.
- **Hilal viz labels updated** — verdict pill: "MEMENUHI KRITERIA" / "TIDAK MEMENUHI" / "MENDEKATI BATAS" / "DI BAWAH HORIZON". Chips: "MEMENUHI" / "TIDAK MEMENUHI".
- **Wording fixes** — "official/resmi" → "data publik" across README, landing page, footer, hilal docs, endpoint docs, playground, quickstart, FAQ, migration. Softened government affiliation language.
- **Schema descriptions** — `source`, `warnings`, `visible`, `alt_ok`, `elong_ok` fields now have OpenAPI descriptions.
- **Disclaimer section** added to README with non-affiliation clause.

### Updated

- Playground Kalender baru (`/playground/kalender`) — kalender Hijriah setahun penuh, dua kolom, render langsung dari endpoint `/month` dan `/events`. Angka besar = tanggal Hijriah, kecil = tanggal Masehi, Jumat ditandai kuning, badge hari besar, penanda hari ini.
- Logika playground Kalender dipindah ke modul bersama (`src/lib/kalender.core.js`) agar versi ID & EN sama.
- Dokumentasi `/range` & `/month` diperbarui: arah `calendar=hijri` kini dilayani dari tier komputasi di luar tabel publik.

---

## Documentation Updates — 2026-08-28

- Landing page with live JSON preview and latency badge
- Documentation site (Astro + Starlight)
- Blog (3 articles: story, tutorial, hilal behind-the-scenes)
- FAQ page (bilingual)
- Playground (converter + hilal visualization)
- Migration guide from Aladhan API
- Error response examples in all API reference pages
- Sidebar reorganized: "FAQ - Pertanyaan", Changelog

---

## 1.1.0 — 2026-08-27

### Added

- **GET /events** — tanggal hari besar Islam (1 Muharram, Maulid Nabi, Awal Ramadan, Idul Fitri, Idul Adha) dari tabel MABIMS, diperluas dengan data komputasi di luar cakupan tabel.
- **GET /hilal/info** — data visibilitas hilal: kriteria Neo MABIMS (hilal ≥ 3°, elongasi ≥ 6.4°), posisi bulan, verdict TERLIHAT / TIDAK TERLIHAT.
- **GET /hilal/viz** — PNG visualisasi langit senja 720×1280: posisi bulan, arah sabit, tabel kriteria, perhitungan di titik Sabang.

---

## 1.0.0 — 2026-08-25

### Added

- **GET /today** — tanggal Hijriah untuk "sekarang", timezone-aware (default Asia/Jakarta). TTL edge-cache dinamis.
- **GET /today/{date}** — varian immutable untuk tanggal spesifik, cache-forever.
- **GET /convert** — konversi satu tanggal antara Gregorian dan Hijriah (dua arah). `Cache-Control: max-age=86400`.
- **GET /range** — konversi massal untuk rentang tanggal (maks 400 hari). Setiap item membawa `source` masing-masing.
- **GET /month** — grid kalender bulanan, 29–30 item per bulan.
- **Tabel MABIMS resmi** — data dari Kemenag RI, cakupan 2024-01-13 hingga 2026-12-31.
- **Fallback chain** — MABIMS table → Neo MABIMS computed (Sabang).
- **CDN caching** — Bunny CDN, dynamic TTL berdasarkan timezone, origin hanya melihat ~1 request per lokasi edge per hari.
- **CORS** — fleksibel, aplikasi client-side di domain mana pun bisa memanggil langsung.
- **Rate limiting** — 240 request per menit per IP, 429 when exceeded.
- **GET /meta** — info cakupan data, status fallback, versi data.
- **GET /healthz** — liveness probe untuk monitoring uptime.
- **CI/CD** — GitHub Actions, ruff + mypy, schema contract tests, yearly table regen workflow.
