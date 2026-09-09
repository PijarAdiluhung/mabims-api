---
title: Sumber Data
description: Dari mana data MABIMS berasal dan status lisensinya.
---

## Sumber Utama

Data kalender bersumber dari **data publik yang dikeluarkan resmi oleh Kementerian Agama Republik Indonesia** — tabel penanggalan MABIMS yang diterbitkan setiap tahun untuk satu tahun ke depan.

| Properti | Nilai |
|---|---|
| **Sumber** | Kementerian Agama RI — Kalender Hijriah |
| **Format asli** | PDF |
| **Cakupan tabel** | 2023-01-23 → 2026-12-31 |

## Tier Komputasi

Di luar cakupan tabel, API menghitung tanggal menggunakan kriteria **Neo MABIMS**:

| Parameter | Ambang batas |
|---|---|
| Ketinggian bulan (toposentris, terkoreksi refraksi) | ≥ 3,0° |
| Elongasi (geosentris) | ≥ 6,4° |
| Titik pengamatan | 25 titik pesisir di seluruh Indonesia — terpenuhi di **satu titik manapun** → bulan 29 hari ([daftar titik](https://github.com/PijarAdiluhung/mabims-api/blob/main/api/data/hilal_sites.json)) |
| Waktu referensi | Saat matahari terbenam lokal di masing-masing titik (hari ke-29) |

## Retro (di bawah tabel kurasi)

Tanggal sebelum 2023-01-23 tidak pernah dihasilkan oleh kriteria Neo MABIMS (kriteria ini diperkenalkan pada 2022). Membawa `retro=true` akan membuka tanggal komputasi di bawah tabel kurasi hingga 1945-01-01, ditandai `source: "mabims-retro"` dengan peringatan bahwa ini proyeksi retroaktif — bukan data resmi.

## Lisensi

Data kalender bersumber dari publikasi pemerintah Indonesia untuk kepentingan publik. Kode sumber API dilisensikan di bawah [MIT License](https://github.com/PijarAdiluhung/mabims-api/blob/main/LICENSE).
