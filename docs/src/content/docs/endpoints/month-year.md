---
title: GET /month & /year
description: Grid kalender bulanan dan tahunan.
---

## GET /month

Wrapper praktis untuk mendapatkan 1 bulan penuh.

```
GET /api/v1/month?year={Y}&month={M}&calendar={hijri|gregorian}
```

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `year` | int | ya | Tahun Hijriah atau Gregorian |
| `month` | int | ya | Bulan 1–12 |
| `calendar` | string | tidak (default `hijri`) | Kalender dari input `year` |

Untuk `calendar=hijri`, respons berisi setiap tanggal Gregorian yang menjadi acuan dari bulan Hijriah tersebut (29–30 item). Bulan Hijriah di luar tabel publik (mis. tahun mendatang) tetap dilayani dari perhitungan Neo MABIMS selama masih dalam rentang yang didukung. Bentuk item sama dengan `/range`.

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

Untuk `calendar=hijri`, bulan Hijriah di luar tabel publik tetap dilayani dari perhitungan Neo MABIMS selama masih dalam rentang yang didukung.

## Kesalahan

| `code` | HTTP | Penyebab |
|---|---|---|
| `invalid_month` | 400 | Bulan bukan 1–12 |
| `invalid_year` | 400 | Tahun di luar batas yang didukung |
| `invalid_calendar` | 400 | Parameter `calendar` bukan `hijri` atau `gregorian` |
| `out_of_coverage` | 400 | Bulan di luar cakupan tabel |
| `date_out_of_supported_range` | 400 | Tanggal di luar rentang yang didukung |
