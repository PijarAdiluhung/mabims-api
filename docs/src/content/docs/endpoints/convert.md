---
title: GET /convert
description: Konversi satu tanggal antara kalender Gregorian dan Hijriah.
---

Mengkonversi satu tanggal ke arah yang ditentukan oleh `calendar`.

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
  "output": { "date": "1446-07-03", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

**400** — format tanggal tidak valid atau kalender tidak dikenal (`invalid_date`, `invalid_calendar`, `missing_parameter`)
**404** — `date_not_found`: tidak ada pasangan untuk tanggal tersebut; periksa [/meta](/endpoints/meta)

## Caching

Respons bersifat immutable per input dan dikirim dengan `Cache-Control: max-age=86400` — aman di-cache di layer mana pun selama satu hari penuh.

:::note
`/convert` tidak bergantung pada zona waktu berdasarkan desain. Hanya [`/today`](/endpoints/today) yang menerima parameter `tz`, karena "hari ini" tergantung dari mana Anda bertanya.
:::
