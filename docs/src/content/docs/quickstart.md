---
title: Quickstart
description: Buat request pertama Anda dalam waktu kurang dari satu menit.
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
  "output": { "date": "1448-03-11", "calendar": "hijri", "day": 11, "month": 3, "month_name": "Rabiul Akhir", "year": 1448 },
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

- `mabims` — dari data publik Kemenag
- `mabims-computed` — dihitung dengan kriteria Neo MABIMS

Perlakukan `warnings` sebagai pemberitahuan kepada pengguna apabila ia mengandung payload (tidak kosong).

## Akses melalui browser

API ini bersifat publik dan CORS-nya fleksibel, aplikasi client-side di domain mana pun dapat memanggilnya secara langsung.
Panggilan server-side juga tidak dibatasi. Lihat [Akses & Batas Rate](/access) untuk kebijakan lengkap dan detail perlindungan penyalahgunaan.

## Langkah selanjutnya

- Referensi parameter lengkap: [Referensi API](/endpoints/convert-range)
- Coba langsung: [Playground](/playground)
- OpenAPI spec: [api.mabims.dev/openapi.json](https://api.mabims.dev/openapi.json)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebAPI",
  "name": "MABIMS API",
  "description": "API konversi tanggal Hijriah-Masehi berdasarkan kriteria resmi MABIMS Kemenag RI. Gratis, tanpa API key.",
  "url": "https://api.mabims.dev",
  "documentation": "https://mabims.dev/quickstart",
  "openAPISpec": "https://api.mabims.dev/openapi.json",
  "provider": {
    "@type": "Organization",
    "name": "mabims.dev",
    "url": "https://mabims.dev"
  },
  "potentialAction": [
    {
      "@type": "InvokeAction",
      "name": "Get today's Hijri date",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/today?tz={timezone}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Convert Gregorian to Hijri",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/convert?date={date}&calendar=gregorian",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Convert Hijri to Gregorian",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/convert?date={date}&calendar=hijri",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get Islamic events",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/events?year={year}&calendar={calendar}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get month calendar",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/month?year={year}&month={month}&calendar={calendar}",
        "contentType": "application/json"
      }
    },
    {
      "@type": "InvokeAction",
      "name": "Get hilal visibility",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": "https://api.mabims.dev/api/v1/hilal/info?month={month}&year={year}",
        "contentType": "application/json"
      }
    }
  ]
}
</script>
