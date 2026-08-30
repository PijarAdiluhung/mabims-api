---
title: Tentang MABIMS.dev
description: API open-source gratis untuk kalender Hijriah Indonesia berdasarkan data resmi MABIMS Kementerian Agama RI.
---

## Apa itu MABIMS.dev?

MABIMS.dev adalah API open-source gratis yang menyediakan ekosistem kalender Hijriah untuk Indonesia. API ini menggunakan data resmi MABIMS yang diterbitkan oleh Kementerian Agama Republik Indonesia, bukan Umm al-Qura (standar Arab Saudi).

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
