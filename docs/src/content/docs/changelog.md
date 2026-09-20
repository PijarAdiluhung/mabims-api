---
title: Changelog
description: Riwayat perubahan API dan dokumentasi MABIMS.
---

## 1.9.0 — 2026-09-20

### Added

- **Parameter `include` di `GET /api/v1/events`** — 5 hari besar bawaan tetap direspons apa adanya; kini bisa diminta tambahan: `include=extra` membuka peringatan tingkat 2 (Isra Mi'raj 27 Rajab, Nuzulul Quran 17 Ramadan, Arafah 9 Dzulhijjah, Tasu'a 9 Muharam, Asyura 10 Muharam, Hari Tasyrik 11–13 Dzulhijjah), `include=ayyamul_bidh` membuka puasa hari putih (13–15 setiap bulan Hijriah, 14–16 di Dzulhijjah karena tanggal 13 adalah Hari Tasyrik, satu event berkisar per bulan, 12 setahun), slug individual bisa dipilih satu per satu, dan `include=all` mengembalikan semuanya.
- **Field `date_range` pada item event** — event multi-hari (`tasyrik`, `ayyamul_bidh`) membawa `hijri_start`, `hijri_end`, `gregorian_start`, `gregorian_end`; event satu hari bernilai `date_range: null`. Field opsional, tidak breaking.
- **Gema `input.include`** — respons menggema set include yang diminta (tersortir, `null` bila tanpa parametro) supaya klien bisa memverifikasi.
- **400 `invalid_include`** — token yang tidak dikenal (mis. `include=ayahsura`) ditolak dengan pesan yang menyebut nilai yang salah.

### Notes

- Untuk klien: panggilan lama tetap mendapatkan `count: 5` dengan envelope yang sama; hanya permintaan opt-in yang bentuknya berubah. Semua tanggal baru adalah pemetaan Hijriah tetap — di dalam tabel kurasi `source: mabims`, di luar tabel mengikuti tier computed/retro seperti hari bawaan.
- SDK npm `mabims-hijri@1.4.0` mendukung `events(year, calendar, { include })` dengan token yang sama, menghitung tambahan secara offline dari tabel yang di-bundle.

---

## 1.8.2 — 2026-09-19

### Added

- **ETag + 304 Not Modified di semua respons 200** — setiap respons membawa header **ETag**; kirim `If-None-Match: <etag>` (perbandingan lemah, atau `*`) dan server menjawab **304 tanpa body** dengan `Cache-Control` dan ETag yang sama. Berlaku di semua endpoint cacheable (`/today`, `today/{date}`, `convert`, `range`, `month`, `year`, `events`, `/hilal/*`).
- **Kode error `invalid_bare` dan `invalid_download`** — parameter `bare`/`download` di `/hilal/viz` dan `/hilal/map` kini divalidasi ketat; nilai selain boolean ditolak 400.
- **`GET /api/v1/months`** — endpoint statis baru yang mengembalikan 12 nama bulan Hijriah beserta nomornya. Tidak perlu parameter, aman di-cache (`max-age=86400`), rate-limit exempt. Cocok untuk mengisi dropdown atau label di UI.

### Changed

- **Envelope error seragam `{"error":{"code","message"}}` di seluruh respons** — termasuk 404 path tidak dikenal (`not_found`) dan **429 rate limiter** (`rate_limit_exceeded`) yang kini menyertakan header **`Retry-After`** (detik).
- **Tidak ada lagi 422 mentah FastAPI** — input pecahan yang salah bentuk kini 400 (`invalid_year`/`invalid_month`/`missing_parameter`), dan boolean rusak kini 400 `invalid_<nama>`; `retro`/`next`/`bare`/`download` menerima `true`/`false` (tidak peka huruf besar/kecil) dan `1`/`0`. Parameter yang hilang atau kosong = `false`.
- **Seed komputasi kini menutup seluruh rentang yang didukung** — kira-kira 1945-01-01 (bulan Hijriah mulai 1944-12-17) sampai 2100-01-01, jadi tidak ada lagi komputasi lazy saat runtime. Sebelumnya seed hanya 1970 → ~2050.
- **Warning borderline diperketat** — bulan Hijriah ditandai "mendekati ambang visibilitas Neo MABIMS" **hanya bila** malam ke-29-nya **lolos** kedua kriteria (alt ≥ 3,0°, elongasi ≥ 6,4°) dengan margin **< 0,25°**. Bulan yang ditolak (tidak ada titik lolos) tidak pernah mendapat warning ini; kira-kira 3% bulan terhitung borderline.
- **`/meta` kini melaporkan versi 1.8.2**, dan spec OpenAPI mendokumentasikan `contact`/`license`/`externalDocs`, contoh parameter, serta respons 304.
- **Komponen OpenAPI yang dapat digunakan kembali** — parameter `retro`, `next`, `bare`, `download` dan respons error (404, 429, 400, 500, 503) kini didefinisikan sekali di `components/parameters` dan `components/responses`, lalu direferensikan dengan `$ref` di seluruh endpoint. Spec lebih ringkas dan deskripsi tidak drift antar-endpoint.

### Notes

- Bagi klien: tangani `Retry-After` saat 429 dan gunakan `If-None-Match` untuk menghemat bandwidth — fallback 304 membuat polling murah.

---

## 1.8.1 — 2026-09-18

### Added

- **Referensi OpenAPI kini lengkap per endpoint** — setiap endpoint mendeklarasikan blok `responses`-nya sendiri (400/404/429, dst.) dengan contoh body error, sehingga API client (Scalar, Swagger UI, generator) menampilkan skenario kesalahan yang nyata, bukan generik. Lihat `openapi.json` atau [Scalar playground](https://api.mabims.dev/playground).
- **`servers` di spec OpenAPI** — spesifikasi menyatakan `https://api.mabims.dev` sebagai server, jadi klien yang di-generate/interaktif selalu resolve ke origin live tanpa konfigurasi tambahan.
- **API client tersemat di setiap halaman endpoint** — tombol *Test Request* membuka Scalar API client dengan spec live; fallback playground penuh tetap tersedia.

### Changed

- **Deskripsi OpenAPI ditulis ulang dan diterjemahkan** — ringkasan & deskripsi tiap endpoint ditulis ulang untuk kejelasan, lalu dialihbahasakan ke Indonesia.
- **Halaman endpoint docs distruktur ulang** — setiap endpoint kini punya kartu permintaan (`GET /…` + tombol *Test Request*) gaya Scalar, parameter, contoh dan error digroup per endpoint, serta baris permintaan yang kini memuat parameter opsional (`next`, `retro`).

### Notes

- Murni dokumentasi/spesifikasi — tidak ada perubahan perilaku runtime API maupun kontrak respons.

---

## 1.8.0 — 2026-09-16

### Added

- **`?next=true` di `GET /today`** — ikut mengembalikanHijriah yang mulai berlaku saat maghrib petang ini (pemetaan hari sipil berikutnya) lewat objek `next` dengan `source`-nya sendiri. API tidak menghitung maghrib — klien yang memutuskan ganti tanggal pakai jam salat maghribnya sendiri. Zona waktu mengikuti perilaku `/today`.
- **Koreksi Sidang Isbat** — bila Sidang Isbat menetapkan awal bulan berbeda dari kalender terbit Kemenag, kini ada jalur koreksi resminya: `/meta` memunculkan **`divergences[]`** (riwayat koreksi, terbaru dulu) dan **`table_version`** (token versi riwayat; `"none"` kalau belum pernah ada koreksi, berubah setiap kali koreksi diterapkan).
- **Warning `kemenag_override:`** — respons yang menyentuh bulan terkoreksi (dan bulan sebelumnya, yang panjangnya ikut berubah) membawa peringatan berisi tanggal resmi (Sidang Isbat) vs kalender terbit, plus selisih harinya. Berjalan otomatis di semua endpoint konversi, bulan/tahun, events, dan `/hilal/info`; `source` tetap `mabims`.

### Notes

- Selama belum ada koreksi tercatat, tidak ada yang berubah: `divergences[]` kosong dan `table_version = "none"`. Semuanya tambahan field dan warning, tanpa breaking change.
- Detail integrasi klien: halaman [Sidang Isbat & Koreksi](/isbat-koreksi).

---

## 1.7.0 — 2026-09-13

### Added

- **Kartu bare (/hilal/viz + /hilal/map `?bare=true`)** — menghilangkan panel kriteria dan mengembalikan kartu resolusi tinggi **1440×1520** (header + grafik + callout/verdict + logo) untuk dipakai sebagai gambar hero di web. Kartu penuh 720×1280 tidak berubah. Varian bare ikut dipra-render ke image pack CDN (satu tar dengan `viz/` + `map/` + `viz-bare/` + `map-bare/`).
- **`download=true` (/hilal/viz + /hilal/map)** — mengirim `Content-Disposition: attachment` sehingga tautan unduh bekerja lintas-origin (atribut `download` HTML diabaikan untuk URL lintas-origin).
- **`GET /api/v1/hilal/history?from=&to=`** — ringkasan per bulan untuk seluruh rentang Hijriah (default **1444-08 → 1475-12**) dari indeks terhitung `api/data/hilal_index.json` (`scripts/generate_hilal_index.py`), sehingga daftar riwayat cukup satu permintaan. Rate limit 240/menit.
- **`scripts/build_imagepack.py`** — pembangun image pack satu perintah: render (atau `--skip-render`) lalu tulis tar deterministik + `manifest.json` dengan `render_version` dari daftar titik + display points + sumber renderer.
- **Halaman publik `/hilal`** — tanggal Hijriah hari ini, hitung mundur malam penentuan, peta + grafik bare yang bisa di-zoom, dan daftar riwayat dengan panel info inline. Situs kini memakai `LandingLayout.astro` bersama untuk landing dan `/hilal`.

---

## 1.6.1 — 2026-09-11

### Changed

- **Performa hilal 10× lebih cepat** — kartu peta/grafik kini membaca hasil astronomi dari **cache SQLite fakta astronomi** (grid 0,25°, 95 titik, 25 titik pengamatan, minimap dunia), dikunci per malam pengamatan + tag ephemeris + fingerprint daftar titik. Runtime hanya membaca; penulisan dilakukan skrip build (`scripts/prime_astro_cache.py`, resumable + paralel). Cache diunduh otomatis saat boot pertama ke volume `/data` (URL `MABIMS_ASTROCACHE_URL`), pola sama dengan file ephemeris.
- **Ephemeris de421 → de440s** (cakupan JPL 1849–2150) dan **batas maju 2053-08-01 → 2100-01-01**. Seed komputasi diperpanjang sampai 2099-12-31.
- **Kap render kartu PNG: Hijri 1444–1475** — `hilal_image_range` di `/meta` kini adalah batas keras `/hilal/viz`+`/hilal/map` di luar rentang itu endpoint menolak dengan `out_of_coverage` (kap data tanggal tetap `coverage.forward_ceil` = 2100). Kartu pra-render terpaket tetap 1444–1450; bulan lain di dalam kap dirender on-demand beberapa detik dari cache astronomi.
- **Kartu peta: tabel kriteria → indikator rentang (gauge)** — baris `ALT. BULAN`/`ELONGASI` di `/hilal/map` kini menampilkan rentang **min–maks seluruh 95 titik tampilan** sebagai bar: merah = titik di bawah batas MABIMS, hijau = titik yang lolos, jarum dengan label `min. MABIMS` di ambang 3,0°/6,4°. Skalanya adaptif per bulan (mengisi bar di bulan nyaman, menunjukkan seberapa batin bulan batas). Chip LOLOS/GAGAL dan kolom MIN./STATUS dihapus.
- **Font kartu hilal: DejaVu → Selawik** — semua teks kartu `viz` + `map` kini memakai **Selawik** (SIL OFL, metrik-identik dengan Segoe UI), dikemas di `api/app/hilal/assets/` sehingga render Windows/laptop dan server Linux identik.
- **Kartu pra-render kini di-host CDN (image pack)** — set 1444–1450 (viz+map, 168 PNG) tidak lagi dikomit ke repo; kini berupa tar berversi + `manifest.json` di CDN (`MABIMS_IMAGEPACK_URL`, default `mabims-dev.b-cdn.net/hilal_images`). Saat runtime manifest di-probe, tar diunduh, diverifikasi sha256, dan diekstrak per-file ke volume `/data` (`app/hilal/imagepack.py`) — kartu lazy di luar rentang tidak ikut terhapus. Kegagalan tercatat di log `mabims.imagepack` dan endpoint jatuh ke render on-demand. `MABIMS_DISABLE_IMAGEPACK=1` untuk menonaktifkan.

### Notes

- Perbaikan iterasi Newton 8→3 pada pencarian matahari terbenam: telah diukur tanpa perbedaan hasil (maks 0,00015°). Tidak ada perubahan nilai atau verdict — hanya kecepatan.

---

## 1.6.0 — 2026-09-10

### Added

- **`/hilal/map`** — kartu peta 720×1280 wilayah visibilitas hilal seluruh Nusantara: area yang memenuhi kriteria Neo MABIMS saat matahari terbenam, garis batas ketinggian 3° dan elongasi 6,4°, serta **95 titik tampilan** (hijau = memenuhi, abu-abu = tidak). Titik penentu dari model 25 titik ditandai cincin kuning. Tabel kartu memakai titik penentu yang **sama dengan `/hilal/viz`**, ditambah rekap `TITIK MEMENUHI`/`TITIK TIDAK MEMENUHI`. Rate limit 30/jam, `Cache-Control` imutabel.
- **Playground hilal** kini menampilkan peta dan grafik langit berdampingan, masing-masing dengan tautan unduh PNG.

### Notes

- 95 titik peta adalah set **tampilan** untuk menunjukkan cakupan; verdict bulan tetap berasal dari model 25 titik pengamatan dan tidak berubah (0 perbedaan panjang bulan pada 1970–2051).

---

## 1.5.0 — 2026-09-09

### Changed

- **Kriteria hilal multi-titik (`neo-mabims-multisite`)** — verdict hilal kini mengikuti konvensi Kemenag: ketinggian hilal **toposentris** (terkoreksi refraksi) ≥ 3,0° dan elongasi **geosentris** ≥ 6,4°, dievaluasi pada matahari terbenam lokal masing-masing titik pada hari ke-29 di **25 titik pengamatan pesisir** dari Sabang sampai Rote (sebelumnya: altitud geosentris di Sabang saja). Terpenuhi di satu titik manapun → bulan 29 hari. Tervalidasi 48/48 terhadap tabel kurasi.
- **Seed komputasi diregenerasi** dengan model baru — **10 awal bulan bergeser ±1 hari** (7 retro: 1393-02, 1395-03, 1396-03, 1398-02, 1410-03, 1428-11, 1436-10; 3 forward: 1452-05, 1466-07, 1467-11). Tabel kurasi tidak berubah.
- **Semantik `/hilal/info`** — `moon_alt_deg`, `elongation_deg`, `moon_az_deg`, `sun_alt_deg`, `sunset`, `moonset` kini menggambarkan **titik penentu** (sebelumnya Sabang); waktu ditampilkan dalam zona waktu lokal titik tersebut (WIB/WITA). Bentuk respons tetap sama.
- **`/hilal/viz`** — adegan langit, tabel kriteria, dan waktu semuanya di titik penentu; baris baru **TITIK PENGAMAT**; lokasi di header diganti baris titik pengamatan.
- `/meta` — `method` sekarang `neo-mabims-multisite`.

### Added

- **`deciding_site`** di `/hilal/info` — object `{ name, lat, lon, elev_m, tz }` titik yang digambarkan: titik penentu bila terlihat, atau titik dengan margin terbaik bila tidak terpenuhi di manapun (selalu terisi).
- **`sites_checked`** di `/hilal/info` — jumlah titik pengamatan yang dievaluasi (25).
- **Daftar titik sebagai data** — [`api/data/hilal_sites.json`](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json): menambah/mengubah titik kini PR data, bukan perubahan kode.

### Notes

- Perubahan bentuk respons bersifat *additive* (minor), tetapi semantik beberapa field berubah — klien yang mengandalkan nilai altitud/elongasi Sabang sebaiknya membaca `deciding_site`.

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
