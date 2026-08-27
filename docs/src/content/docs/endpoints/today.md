---
title: GET /today
description: Endpoint utama — tanggal Hijriah hari ini, memperhatikan zona waktu.
---

Mengembalikan tanggal Hijriah untuk "sekarang" di zona waktu yang diminta. Ini adalah endpoint yang paling sering di-poll oleh aplikasi consumer, maka telah dioptimalkan. Respons memiliki **TTL edge-cache dinamis** sehingga CDN melayani hampir semua traffic.

```
GET /api/v1/today?tz={timezone}
```

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `tz` | string | tidak (default `Asia/Jakarta`, UTC+7) | Nama zona IANA (`Asia/Kuala_Lumpur`) atau UTC offset (`UTC+7`, `+08:00`) |

## Respons

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

Field `input.tz` menampilkan zona waktu yang *terdeteksi sistem* sehingga klien dapat memastikan zona yang digunakan.

## Varian immutable

```{=html}
GET /api/v1/today/{YYYY-MM-DD}
```

Konversi yang sama untuk tanggal Gregorian tertentu. Berguna sebagai resource yang stabil dan dapat di-cache selamanya, serta untuk memutar ulang hari-hari historis:

```bash
curl "https://api.mabims.dev/api/v1/today/2025-01-03"
```

## Perilaku caching

- `Cache-Control: public, max-age=60, s-maxage=<detik hingga tengah malam lokal>`
- Cache miss pada pukul 06:00 di-cache di edge selama ~18 jam; miss pada pukul 23:59 kedaluwarsa tepat setelah tengah malam sehingga tanggal berganti segera.
- Dengan jutaan permintaan/hari, origin hanya melihat sekitar satu permintaan per lokasi edge per hari.
