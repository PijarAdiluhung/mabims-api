---
title: Tentang MABIMS.dev
description: API open-source gratis untuk kalender Hijriah Indonesia berdasarkan data resmi MABIMS Kementerian Agama RI.
---

## Apa itu MABIMS.dev?

MABIMS.dev adalah API open-source unofficial gratis yang menyediakan ekosistem kalender Hijriah untuk Indonesia. API ini menggunakan data resmi MABIMS yang diterbitkan oleh Kementerian Agama Republik Indonesia, bukan Umm al-Qura (standar Arab Saudi).

## Untuk Siapa?

- **Developer** yang membangun aplikasi web atau mobile dengan fitur kalender Hijriah
- **Aplikasi masjid dan pesantren** yang perlu menampilkan tanggal puasa, Idul Fitri, dan Idul Adha sesuai pengumuman Kemenag
- **Sekolah dan universitas Islam** yang mengintegrasikan kalender Hijriah ke sistem akademik
- **Siapapun** yang butuh tanggal Hijri Indonesia yang akurat

## Mengapa MABIMS, Bukan Umm al-Qura?

Hampir semua API dan library kalender Hijriah menggunakan Umm al-Qura sebagai default. Umm al-Qura adalah kalender resmi Arab Saudi yang dirancang untuk kebutuhan di sana, bukan untuk Indonesia.

Karena metode rukyah dan lokasi pengamatannya berbeda, hasilnya bisa selisih ±1 hari dari keputusan resmi Kemenag — terutama untuk awal Ramadhan, Idul Fitri, dan Idul Adha. MABIMS.dev menggunakan data tabel publik Kemenag RI dan kriteria Neo MABIMS (ketinggian hilal ≥ 3°, elongasi ≥ 6,4° di Sabang saat matahari terbenam) untuk tanggal di luar cakupan tabel.

## Apa Saja yang Tersedia?

| Endpoint | Fungsi |
|---|---|
| `GET /today` | Tanggal Hijri hari ini (timezone-aware) |
| `GET /convert` | Konversi satu tanggal (Masehi ↔ Hijriah) |
| `GET /range` | Konversi bulk hingga 45 hari |
| `GET /month` | Semua hari dalam satu bulan |
| `GET /year` | Semua hari dalam satu tahun (12 bulan) |
| `GET /events` | Hari besar Islam (Ramadan, Idul Fitri, Idul Adha, 1 Muharram, Maulid Nabi) |
| `GET /hilal/info` | Data visibilitas hilal (JSON) |
| `GET /hilal/viz` | Grafik langit hilal (PNG 720×1280) |

## Cara Integrasi Kalender Hijriah

MABIMS.dev adalah REST API standar — bisa dipakai dari JavaScript, PHP, Python, Dart, Swift, Kotlin, atau bahasa apapun yang bisa melakukan HTTP request. Tidak perlu library khusus.

**Tanggal Hijri hari ini:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/today");
const { day, month_name, year } = (await res.json()).output;
// "1448-03-14" → "14 Rabiul Akhir 1448 H"
```

**Konversi tanggal tertentu:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/convert?date=2026-03-01&calendar=gregorian");
const { date } = (await res.json()).output;
// "1447-08-30"
```

**Kalender satu tahun penuh:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/year?year=1448&calendar=hijri");
const { months } = await res.json();
// 12 array, masing-masing berisi semua hari dalam bulan Hijri
```

Lihat [Quickstart](/quickstart) untuk panduan lengkap atau coba langsung di [Playground](/playground/converter).

## Dibandingkan dengan Alternatif

Untuk konteks Indonesia, MABIMS.dev lebih akurat dari Umm al-Qura (standar Saudi yang bisa selisih ±1 hari) dan Aladhan API (yang juga default ke Umm al-Qura). MABIMS.dev menggunakan data resmi Kemenag RI, bukan data dari otoritas negara lain.

Jika Anda saat ini menggunakan Aladhan API, lihat panduan [Migration dari Aladhan](/migration) untuk perbandingan format respons dan contoh kode migrasi.

## Spesifikasi

| | |
|---|---|
| API | FastAPI + Pydantic v2 |
| Data | Tabel MABIMS (Hijri 1445–1448) + Neo MABIMS criteria (hingga ~2053) |
| Spesifikasi | OpenAPI 3.1 |
| Lisensi | MIT |
| Sumber | [github.com/PijarAdiluhung/mabims-api](https://github.com/PijarAdiluhung/mabims-api) |

## Mulai Sekarang

```bash
curl "https://api.mabims.dev/api/v1/today"
```

Lihat [Quickstart](/quickstart) atau coba langsung di [Playground](/playground/converter).
