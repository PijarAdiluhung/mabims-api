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

## Di luar tabel: dua lapis perhitungan

Permintaan di luar cakupan tetap dijawab, dengan urutan berikut:

1. **`mabims-computed`** — kriteria Neo MABIMS dihitung langsung di Sabang
   (tinggi hilal ≥ 3° dan elongasi ≥ 6,4° saat matahari terbenam pada hari ke-29).
   Aturannya sama dengan tabel kurasi, sehingga tetap *on-method* tanpa batas waktu.
   Bulan dengan margin keputusan di bawah 0,25° mendapat peringatan borderline.
2. **`fallback:aladhan-ummalqura`** — Umm al-Qura via Aladhan sebagai upaya terakhir,
   diambil lazy per bulan dan di-cache di origin.

Respons ini akan menjelaskan secara gamblang asal-usulnya:

```json
{
  "source": "mabims-computed",
  "warnings": [
    "Date is outside the curated MABIMS table; computed with the Neo MABIMS criteria (hilal altitude >= 3 deg and elongation >= 6.4 deg at Sabang sunset)."
  ]
}
```

:::caution[Selisih ±1 hari]
Bulan hasil perhitungan yang berada dekat ambang visibilitas bisa bergeser ketika
pengumuman resmi keluar. Untuk tanggal penting keagamaan di luar cakupan tabel,
verifikasi pengumuman lokal setempat.
:::

## Monitoring

[`GET /meta`](/endpoints/meta) menampilkan `computed_active`, `computed_months`,
`fallback_active`, dan `fallback_months`. Panel [status langsung](/playground) di halaman Playground membacanya secara real time.
