---
title: GET /range & /month
description: Konversi massal untuk rentang tanggal dan grid kalender.
---

## GET /range

Mengkonversi setiap hari dalam rentang yang inklusif.

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

Setiap item membawa `source` masing-masing — rentang yang melewati batas tabel dapat mencampur data otoritatif dan fallback.

## GET /month

Wrapper praktis yang menyelesaikan grid bulan penuh.

```
GET /api/v1/month?year={Y}&month={M}&calendar={gregorian|hijri}
```

Untuk `calendar=hijri`, respons berisi setiap tanggal Gregorian yang menjadi acuan dari bulan Hijriah tersebut — tepat seperti yang dibutuhkan oleh tampilan bulan Hijriah (29–30 item). Bentuk item sama dengan `/range`.

## Kesalahan

`invalid_step` · `range_too_large` (>400 hari) · `out_of_coverage` · `invalid_month`
· `invalid_year` — semua mengembalikan `400` dengan amplop kesalahan standar.
