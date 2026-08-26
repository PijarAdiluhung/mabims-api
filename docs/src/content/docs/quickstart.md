---
title: Quickstart
description: Buat permintaan konversi MABIMS pertama Anda dalam waktu kurang dari satu menit.
---

Base URL:

```
https://api.mabims.dev/api/v1
```

## Tanggal Hijriah hari ini

Kasus penggunaan yang paling umum: berapa tanggal Hijriah hari ini?

```bash
curl "https://api.mabims.dev/api/v1/today"
```

```json
{
  "input": { "date": "2026-08-24", "calendar": "gregorian", "tz": "Asia/Jakarta" },
  "output": { "date": "1448-03-11", "calendar": "hijri" },
  "source": "mabims",
  "warnings": []
}
```

`today` secara default menggunakan **Asia/Jakarta (UTC+7)**. Anda bisa override dengan zona IANA atau UTC offset apa pun:

```bash
curl "https://api.mabims.dev/api/v1/today?tz=Asia/Kuala_Lumpur"
curl "https://api.mabims.dev/api/v1/today?tz=UTC+8"
```

## Konversi tanggal tertentu

```bash
curl "https://api.mabims.dev/api/v1/convert?date=2025-01-03&calendar=gregorian"
curl "https://api.mabims.dev/api/v1/convert?date=1446-07-03&calendar=hijri"
```

## Selalu periksa `source`

Setiap respons membawa field `source`:

- `mabims` — otoritatif, dari sumber resmi Kemenag (2024-01-13 s/d 2026-12-31)
- `mabims-computed` — dihitung dengan kriteria Neo MABIMS (setelah 2026-12-31, sampai 2053)

Perlakukan `warnings` sebagai pemberitahuan kepada pengguna apabila ia mengandung payload (tidak kosong).

## Akses melalui browser

API ini bersifat publik dan CORS-nya fleksibel — aplikasi client-side di domain mana pun dapat memanggilnya secara langsung.
Panggilan server-side juga tidak dibatasi. Lihat [Akses & Batas Rate](/access) untuk kebijakan lengkap dan detail perlindungan penyalahgunaan.

## Langkah selanjutnya

- Referensi parameter lengkap: [Referensi API](/endpoints/convert)
- Coba langsung: [Playground](/playground)
