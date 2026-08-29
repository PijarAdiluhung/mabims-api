---
title: GET /year
description: Semua hari dalam satu tahun — 12 bulan sekaligus.
---

## GET /year

Mengembalikan semua hari dalam 12 bulan sebuah tahun. Lebih praktis daripada memanggil `/month` 12 kali.

```
GET /api/v1/year?year={Y}&calendar={hijri|gregorian}
```

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `year` | int | ya | Tahun Hijriah atau Gregorian |
| `calendar` | string | tidak (default `hijri`) | Kalender dari input `year` |

```json
{
  "input": { "year": 1447, "calendar": "hijri" },
  "count": 354,
  "months": {
    "1": [
      { "gregorian": "2025-06-27", "hijri": "1447-01-01", "source": "mabims" },
      { "gregorian": "2025-06-28", "hijri": "1447-01-02", "source": "mabims" }
    ],
    "2": [ "..." ],
    "3": [ "..." ],
    "4": [ "..." ],
    "5": [ "..." ],
    "6": [ "..." ],
    "7": [ "..." ],
    "8": [ "..." ],
    "9": [ "..." ],
    "10": [ "..." ],
    "11": [ "..." ],
    "12": [ "..." ]
  },
  "warnings": []
}
```

Setiap kunci bulan berisi array item dengan format yang sama dengan `/range`. Total `count` adalah jumlah hari di seluruh tahun.

Untuk `calendar=hijri`, bulan Hijriah di luar tabel resmi tetap dilayani dari perhitungan Neo MABIMS selama masih dalam rentang yang didukung.

## Kesalahan

| `code` | HTTP | Penyebab |
|---|---|---|
| `invalid_year` | 400 | Tahun di luar batas yang didukung |
| `invalid_calendar` | 400 | Parameter `calendar` bukan `hijri` atau `gregorian` |
| `out_of_coverage` | 400 | Bulan di luar cakupan tabel |
| `date_out_of_supported_range` | 400 |Tanggal di luar rentang yang didukung |
