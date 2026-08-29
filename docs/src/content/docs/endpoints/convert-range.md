---
title: GET /convert & /range
description: Konversi satu tanggal dan konversi massal rentang tanggal.
---

## GET /convert

Mengkonversi satu tanggal dari satu sistem ke sistem yang lain, dengan arah yang ditentukan secara implisit oleh `calendar`.

```
GET /api/v1/convert?date={YYYY-MM-DD}&calendar={gregorian|hijri}
```

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `date` | string | ya | Tanggal ISO (`YYYY-MM-DD`) |
| `calendar` | string | tidak (default `gregorian`) | Kalender dari tanggal input |

## Respons

**200 OK**

```json
{
  "input": { "date": "2025-01-03", "calendar": "gregorian" },
  "output": { "date": "1446-07-03", "calendar": "hijri", "day": 3, "month": 7, "month_name": "Rajab", "year": 1446 },
  "source": "mabims",
  "warnings": []
}
```

**400** — format tanggal tidak valid atau kalender tidak dikenal

```json
{
  "error": {
    "code": "invalid_date",
    "message": "'bukan-tanggal' is not a valid ISO date (YYYY-MM-DD)."
  }
}
```

| `code` | Penyebab |
|---|---|
| `invalid_date` | Format tanggal bukan `YYYY-MM-DD` |
| `invalid_calendar` | Parameter `calendar` bukan `gregorian` atau `hijri` |
| `missing_parameter` | Query parameter `date` tidak ada |
| `out_of_coverage` | Tanggal di luar cakupan tabel; lihat [/meta](/endpoints/meta) |

**404** — `date_not_found`: tidak ada pasangan untuk tanggal tersebut

```json
{
  "error": {
    "code": "date_not_found",
    "message": "No calendar pair exists for 2023-01-01 (gregorian). See /api/v1/meta for coverage."
  }
}
```

:::note
`/convert` tidak bergantung pada zona waktu berdasarkan desain. Hanya [`/today`](/endpoints/today) yang menerima parameter `tz`, karena "hari ini" tergantung dari mana Anda bertanya.
:::

---

## GET /range

Mengkonversi setiap hari dalam rentang yang diminta.

```
GET /api/v1/range?start={YYYY-MM-DD}&end={YYYY-MM-DD}&calendar={gregorian|hijri}
```

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `start` / `end` | string | ya | Tanggal ISO; `start ≤ end`; rentang maks 45 hari |
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

Setiap item membawa `source` masing-masing, karena rentang yang melewati batasan data MABIMS dapat mencampur data publik dan data komputed.

Untuk `calendar=hijri`, rentang dapat melampaui cakupan tabel publik — bulan Hijriah di luar tabel dilayani dari perhitungan Neo MABIMS (hingga ±2053 / Hijriah 1473). Batas `start`/`end` tetap maks 45 hari.

## Caching

Respons bersifat immutable per input dan dikirim dengan `Cache-Control: max-age=86400` — aman di-cache di layer mana pun selama satu hari penuh.

## Kesalahan

Semua kesalahan mengembalikan JSON dengan format standar:

```json
{
  "error": {
    "code": "range_too_large",
    "message": "Range is limited to 45 days."
  }
}
```

| `code` | HTTP | Penyebab |
|---|---|---|
| `invalid_step` | 400 | Step bukan `day` |
| `range_too_large` | 400 | Rentang > 45 hari |
| `out_of_coverage` | 400 | Tanggal di luar cakupan tabel |
