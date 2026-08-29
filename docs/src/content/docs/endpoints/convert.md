---
title: GET /convert
description: Konversi satu tanggal antara kalender Gregorian dan Hijriah.
---

Mengkonversi satu tanggal dari satu sistem ke sistem yang lain, dengan arah yang ditentukan secara implisit oleh `calendar`.

```
GET /api/v1/convert?date={YYYY-MM-DD}&calendar={gregorian|hijri}
```

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `date` | string | ya | Tanggal ISO (`YYYY-MM-DD`) |
| `calendar` | string | tidak (default `hijri`) | Kalender dari tanggal input |

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

## Caching

Respons bersifat immutable per input dan dikirim dengan `Cache-Control: max-age=86400` — aman di-cache di layer mana pun selama satu hari penuh.

:::note
`/convert` tidak bergantung pada zona waktu berdasarkan desain. Hanya [`/today`](/endpoints/today) yang menerima parameter `tz`, karena "hari ini" tergantung dari mana Anda bertanya.
:::
