---
title: Cakupan Data
description: Seberapa jauh cakupan data MABIMS, dan apa yang terjadi di luar cakupan tersebut.
---

## Cakupan otoritatif

Tabel pencarian MABIMS yang dikelola saat ini mencakup:

```{=html}
2024-01-13 → 2026-12-31
```

Awal bulan MABIMS ditetapkan berdasarkan kriteria pengamatan bulan lokal, sehingga tabel diproduksi per tahun oleh otoritas Kemenag. Tabel ini **tidak** diekstrapolasi secara astronomis.

## Di luar tabel: perhitungan ke depan saja

Permintaan setelah akhir tabel dijawab dengan perhitungan maju (forward-only):

1. **`mabims-computed`** — kriteria Neo MABIMS dihitung langsung di Sabang
   (tinggi hilal ≥ 3° dan elongasi ≥ 6,4° saat matahari terbenam pada hari ke-29).
   Aturan sama dengan tabel kurasi, sehingga tetap *on-method*.
   Bulan dengan margin keputusan di bawah 0,25° mendapat peringatan borderline.
2. **`fallback:aladhan-ummalqura`** — Umm al-Qura via Aladhan sebagai upaya terakhir,
   diambil lazy per bulan dan di-cache di origin.

:::caution[Tidak ada berjalan mundur]
Sistem **tidak** dapat mengkonversi tanggal sebelum 2024-01-13. Algoritma berjalan mundur (backward walk) belum tersedia.
:::

## Batas keras

| Arah | Batas | Keterangan |
|------|-------|------------|
| Mundur | 2024-01-13 | Tidak ada konversi sebelum tanggal ini |
| Maju | 2053-08-01 | Tidak ada konversi setelah tanggal ini |

Tanggal di luar batas ini akan ditolak dengan error `date_out_of_supported_range`.

## Monitoring

[`GET /meta`](/endpoints/meta) menampilkan `computed_active`, `computed_months`,
`fallback_active`, dan `fallback_months`. Panel [status langsung](/playground) di halaman Playground membacanya secara real time.
