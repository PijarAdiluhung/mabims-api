---
title: GET /events
description: Tanggal hari besar Islam (1 Muharram, Maulid, Awal Ramadan, Idul Fitri, Idul Adha) dari tabel MABIMS resmi.
---

Mengembalikan tanggal **hari besar Islam** untuk satu tahun kalender, langsung dari kalender resmi Kemenag kriteria Neo MABIMS yang sama dengan `/convert`.

```
GET /api/v1/events?year={Y}&calendar={gregorian|hijri}
```

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `year` | integer | ya | Tahun kalender sesuai `calendar` (Hijriah: `1446`, Gregorian: `2025`) |
| `calendar` | string | tidak (default `gregorian`) | `gregorian` atau `hijri` |

## Respons

```json
{
  "input": { "year": 1446, "calendar": "hijri" },
  "count": 5,
  "events": [
    { "event": "1_muharram",   "name": "Tahun Baru Islam",        "hijri": "1446-01-01", "gregorian": "2024-07-07", "source": "mabims" },
    { "event": "maulid_nabi",  "name": "Maulid Nabi Muhammad Shallallahu Alaihi Wasallam", "hijri": "1446-03-12", "gregorian": "2024-09-16", "source": "mabims" },
    { "event": "awal_ramadan", "name": "Awal Ramadan",             "hijri": "1446-09-01", "gregorian": "2025-03-01", "source": "mabims" },
    { "event": "idul_fitri",   "name": "Idul Fitri",               "hijri": "1446-10-01", "gregorian": "2025-03-31", "source": "mabims" },
    { "event": "idul_adha",    "name": "Idul Adha",                "hijri": "1446-12-10", "gregorian": "2025-06-06", "source": "mabims" }
  ],
  "warnings": []
}
```

Item diurutkan berdasarkan tanggal Gregorian.

## Events yang tersedia

| `event` | Nama | Bulan Hijriah | Tanggal |
|---|---|---|---|
| `1_muharram` | Tahun Baru Islam | 1 (Muharram) | 1 |
| `maulid_nabi` | Maulid Nabi Muhammad Shallallahu Alaihi Wasallam | 3 (Rabiul Awal) | 12 |
| `awal_ramadan` | Awal Ramadan | 9 (Ramadan) | 1 |
| `idul_fitri` | Idul Fitri | 10 (Syawal) | 1 |
| `idul_adha` | Idul Adha | 12 (Zulhijah) | 10 |

## Catatan

- Data hanya dari **tabel resmi Kemenag MABIMS** (`source` selalu `mabims`), endpoint ini tidak menggunakan komputasi.
- Di luar cakupan tabel, respons tetap `200` dengan `"count": 0` dan daftar kosong. Cek
  [/meta](/endpoints/meta) untuk rentang cakupan saat ini.
- Seperti `/convert`, respons di-cache di CDN secara immutable, sehingga tanggal hari besar tidak
  pernah berubah setelah dipublikasikan.
