---
title: Sumber Data
description: Dari mana data MABIMS berasal dan status lisensinya.
---

## Sumber Utama

Data kalender bersumber dari **data publik yang dikeluarkan resmi oleh [Kementerian Agama Republik Indonesia](https://kemenag.go.id)** — tabel penanggalan MABIMS yang diterbitkan setiap tahun untuk satu tahun ke depan.

| Properti | Nilai |
|---|---|
| **Sumber** | Kementerian Agama RI — Kalender Hijriah |
| **Format asli** | PDF |
| **Cakupan tabel** | 2023-01-23 → 2026-12-31 |

## Tier Komputasi

Di luar cakupan tabel, API menghitung tanggal menggunakan kriteria **[Neo MABIMS](https://mui.or.id/baca/berita/mengenal-kriteria-hilal-mabims-standard-penentuan-awal-bulan-hijriyah-pemerintah-indonesia)** (lihat juga pengumuman resmi [Setkab](https://setkab.go.id/pemerintah-tetapkan-1-ramadan-1445h-jatuh-pada-selasa-12-maret-2024)):

| Parameter | Ambang batas |
|---|---|
| Ketinggian bulan (toposentris, terkoreksi refraksi) | ≥ 3,0° |
| Elongasi (geosentris) | ≥ 6,4° |
| Titik pengamatan | 25 titik pesisir di seluruh Indonesia — terpenuhi di **satu titik manapun** → bulan 29 hari ([daftar titik](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json)) |
| Waktu referensi | Saat matahari terbenam lokal di masing-masing titik (hari ke-29) |

## Data Peta

Kartu peta (`/hilal/map`) memakai data geografis berikut:

| Lapisan | Sumber | Lisensi |
|---|---|---|
| Daratan Indonesia + batas provinsi | [superpikar/indonesia-geojson](https://github.com/superpikar/indonesia-geojson) | ikuti repo sumber |
| Negara sekitarnya | [Natural Earth](https://www.naturalearthdata.com/) 1:110m admin-0 | Public domain |
| Titik tampilan (95) | turunan daftar 126 kota + 25 situs pengamatan MABIMS | — |

## Retro (di bawah tabel kurasi)

Tanggal sebelum 2023-01-23 tidak pernah dihasilkan oleh kriteria Neo MABIMS (kriteria ini diperkenalkan pada 2022). Membawa `retro=true` akan membuka tanggal komputasi di bawah tabel kurasi hingga 1945-01-01, ditandai `source: "mabims-retro"` dengan peringatan bahwa ini proyeksi retroaktif — bukan data resmi.

## Lisensi

Data kalender bersumber dari publikasi pemerintah Indonesia untuk kepentingan publik. Kode sumber API dilisensikan di bawah [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).
