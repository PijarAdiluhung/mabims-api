---
title: Cakupan Data
description: Seberapa jauh tabel MABIMS mencakup, dan apa yang terjadi di luar cakupan tersebut.
---

## Cakupan otoritatif

Tabel pencarian MABIMS yang dikelola saat ini mencakup:

```{=html}
2025-01-01 → 2026-12-31
```

Awal bulan MABIMS ditetapkan berdasarkan kriteria pengamatan bulan lokal, sehingga tabel diproduksi per tahun oleh otoritas agama regional. Tabel ini **tidak** diekstrapolasi secara astronomis.

## Di luar tabel: fallback yang ditandai

Permintaan di luar cakupan tetap dijawab — dari sumber **Umm al-Qura** (Aladhan), diambil secara lazy per bulan Hijriah/Gregorian dan di-cache di origin.

Respons ini tidak pernah diam tentang asal-usulnya:

```json
{
  "source": "fallback:aladhan-ummalqura",
  "warnings": [
    "Date is outside MABIMS table coverage; served from the Umm al-Qura fallback and may differ from MABIMS by around one day."
  ]
}
```

:::caution[Selisih ±1 hari]
Umm al-Qura dan MABIMS bisa berbeda pendapat tentang awal bulan. Untuk tanggal-tanggal penting keagamaan selama periode fallback, verifikasi pengumuman lokal setempat.
:::

## Monitoring

[`GET /meta`](/endpoints/meta) menampilkan `fallback_active` dan `fallback_months`. Panel [status langsung](/playground) di halaman Playground membacanya secara real time.
