---
title: GET /meta
description: Cakupan tabel, versi data, dan status fallback.
---

Kebenaran tentang dataset yang machine-readable.

```
GET /api/v1/meta
```

```json
{
  "version": "1.0.0",
  "data_version": "9f2c41aa7b03",
  "coverage": { "first": "2025-01-01", "last": "2026-12-31" },
  "fallback_active": false,
  "fallback_months": [],
  "docs_url": "https://mabims.pixostudio.id"
}
```

| Field | Deskripsi |
|---|---|
| `data_version` | Hash pendek dari tabel MABIMS — berubah ketika tabel diperbarui |
| `coverage` | Rentang Gregorian yang dicakup oleh tabel otoritatif |
| `fallback_active` | `true` setelah ada permintaan yang dilayani dari fallback Umm al-Qura |
| `fallback_months` | Bulan-bulan mana yang diambil ke layer fallback |

## Perilaku klien yang direkomendasikan

1. Poll `/meta` secara harian (murah dan dapat di-cache selama 5 menit).
2. Jika `fallback_active` bernilai true, tampilkan pemberitahuan halus di UI Anda — tanggal bisa bergeser ±1 hari dari pengumuman masjid lokal.
3. Beri peringatan jika `fallback_active` tetap true selama lebih dari beberapa hari: tabel tahunan perlu diperbarui di upstream.

## GET /healthz

Probe liveness untuk monitor uptime. Mengembalikan `{"status": "ok", "version": "..."}` dengan `Cache-Control: no-store`.
