---
title: GET /range & /month
description: Konversi massal untuk rentang tanggal dan grid kalender.
---

## GET /range

Mengkonversi setiap hari dalam rentang yang diminta.

```
GET /api/v1/range?start={YYYY-MM-DD}&end={YYYY-MM-DD}&calendar={gregorian|hijri}
```

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `start` / `end` | string | ya | Tanggal ISO; `start ≤ end`; rentang maks 400 hari |
| `calendar` | string | tidak (default `gregorian`) | Kalender dari batas input |

```json
{
  "input": { "start": "2025-01-01", "end": "2025-01-03", "calendar": "gregorian" },
  "count": 3,
  "items": [
    { "gregorian": "2025-01-01", "hijri": "1446-07-01", "source": "mabims" },
    { "gregorian": "2025-01-02", "hijri": "1446-07-02", "source": "mabims" },
    { "gregorian": "2025-01-03", "hijri": "1446-07-03", "source": "mabims" }
  ],
  "warnings": []
}
```

Setiap item membawa `source` masing-masing, karena rentang yang melewati batasan data MABIMS dapat mencampur data resmi dan data komputed.

Untuk `calendar=hijri`, rentang dapat melampaui cakupan tabel resmi — bulan Hijriah di luar tabel dilayani dari perhitungan Neo MABIMS (hingga ±2053 / Hijriah 1473). Batas `start`/`end` tetap maks 400 hari.

## GET /month

Wrapper praktis untuk mendapatkan 1 bulan penuh.

```
GET /api/v1/month?year={Y}&month={M}&calendar={gregorian|hijri}
```

Untuk `calendar=hijri`, respons berisi setiap tanggal Gregorian yang menjadi acuan dari bulan Hijriah tersebut (29–30 item). Bulan Hijriah di luar tabel resmi (mis. tahun mendatang) tetap dilayani dari perhitungan Neo MABIMS selama masih dalam rentang yang didukung. Bentuk item sama dengan `/range`.

## Kesalahan

Semua kesalahan mengembalikan JSON dengan format standar:

```json
{
  "error": {
    "code": "range_too_large",
    "message": "Range is limited to 400 days."
  }
}
```

| `code` | HTTP | Penyebab |
|---|---|---|
| `invalid_step` | 400 | Step bukan `day` |
| `range_too_large` | 400 | Rentang > 400 hari |
| `out_of_coverage` | 400 | Tanggal di luar cakupan tabel |
| `invalid_month` | 400 | Bulan bukan 1–12 |
| `invalid_year` | 400 | Tahun di luar batas yang didukung |
