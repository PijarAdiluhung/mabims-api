---
title: Memulai
description: Buat permintaan konversi MABIMS pertama Anda dalam waktu kurang dari satu menit.
---

Base URL:

```
https://api.example.com/api/v1
```

## Tanggal Hijriah hari ini

Kasus penggunaan yang paling umum — tanggal Hijriah hari ini?

```bash
curl "https://api.example.com/api/v1/today"
```

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

`today` secara default menggunakan **Asia/Jakarta (UTC+7)**. Override dengan zona IANA atau UTC offset apa pun:

```bash
curl "https://api.example.com/api/v1/today?tz=Asia/Kuala_Lumpur"
curl "https://api.example.com/api/v1/today?tz=UTC+8"
```

## Konversi tanggal tertentu

```bash
curl "https://api.example.com/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl "https://api.example.com/api/v1/convert?date=1446-07-03&calendar=hijri"
```

## Selalu periksa `source`

Setiap respons membawa field `source`:

- `mabims` — otoritatif, dari tabel yang dikelola
- `fallback:aladhan-ummalqura` — perkiraan; bisa berbeda ±1 hari dari pengamatan lokal

Perlakukan `warnings` sebagai pemberitahuan kepada pengguna ketika tidak kosong.

## Akses melalui browser

API ini bersifat publik dan CORS-nya fleksibel — aplikasi client-side di domain mana pun dapat memanggilnya secara langsung.
Panggilan server-side juga tidak dibatasi. Lihat [Akses & Batas Rate](/access) untuk kebijakan lengkap dan detail perlindungan penyalahgunaan.

## Langkah selanjutnya

- Referensi parameter lengkap: [Referensi API](/endpoints/convert)
- Coba langsung: [Playground](/playground)
