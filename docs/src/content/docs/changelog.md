---
title: Changelog
description: Riwayat perubahan API dan dokumentasi MABIMS.
---

## 1.1.1 — 2026-08-29

### Fixed

- **Hijri bulan di luar tabel** — `/month` dan `/range` dengan `calendar=hijri` kini dilayani dari tier komputasi Neo MABIMS (sebelumnya hanya tanggal resmi tabel yang bisa diakses lewat dua endpoint ini).
- **Bug hari-31 pada `/range` Hijriah** — `/range?calendar=hijri` gagal dengan `out_of_coverage` saat rentang melewati batas bulan (hijriah tidak punya tanggal 31). Kini berjalan dengan melintasi bulan Hijriah per-bulan.
- **30 Safar ditolak** — `YYYY-02-30` adalah tanggal Hijriah sah (Safar dapat 30 hari) tetapi ditolak sebagai `invalid_date` karena parser Gregorian tidak mengenal 30 Februari. Parser Hijriah kini memisahkan validasi sintaks (hari 1–30) dari keberadaan data; hari yang benar-benar tidak ada (mis. hari-30 pada bulan berumur 29 hari) mengembalikan `404 date_not_found` dengan jujur.

---

## Documentation Updates — 2026-08-29

- Playground Kalender baru (`/playground/kalender`) — kalender Hijriah setahun penuh, dua kolom, render langsung dari endpoint `/month` dan `/events`. Angka besar = tanggal Hijriah, kecil = tanggal Masehi, Jumat ditandai kuning, badge hari besar, penanda hari ini.
- Logika playground Kalender dipindah ke modul bersama (`src/lib/kalender.core.js`) agar versi ID & EN sama.
- Dokumentasi `/range` & `/month` diperbarui: arah `calendar=hijri` kini dilayani dari tier komputasi di luar tabel resmi.

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
