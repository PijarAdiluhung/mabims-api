---
title: GET /meta
description: Cakupan tabel, versi data, dan status fallback.
---

Info tentang dataset yang machine-readable.

```
GET /api/v1/meta
```

```json
{
  "version": "1.0.0",
  "data_version": "9f2c41aa7b03",
  "coverage": { "first": "2024-01-13", "last": "2026-12-31" },
  "fallback_active": false,
  "fallback_months": [],
  "computed_active": false,
  "computed_months": [],
  "method": "neo-mabims-sabang",
  "docs_url": "https://mabims.dev"
}
```

| Field | Deskripsi |
|---|---|
| `data_version` | Hash pendek dari tabel MABIMS yang berubah ketika tabel diperbarui |
| `coverage` | Rentang Gregorian yang dicakup oleh tabel otoritatif |
| `computed_active` | `true` setelah ada permintaan yang dilayani dari kalendar hitungan Neo MABIMS |
| `computed_months` | Bulan-bulan mana yang sudah dihitung via kriteria Neo MABIMS |
| `method` | Metode perhitungan di luar tabel (`neo-mabims-sabang`) |

## Perilaku klien yang direkomendasikan

1. Poll `/meta` secara harian (murah dan dapat di-cache selama 5 menit).
2. Jika `computed_active` bernilai true, tampilkan pemberitahuan halus di UI Anda — tanggal bisa bergeser ±1 hari dari pengumuman resmi.

## GET /healthz

Probe liveness untuk monitor uptime. Mengembalikan `{"status": "ok", "version": "..."}` dengan `Cache-Control: no-store`.
