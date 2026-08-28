---
title: GET /events
description: Tanggal hari besar Islam (1 Muharram, Maulid, Awal Ramadan, Idul Fitri, Idul Adha) dari tabel MABIMS, diperluas dengan data komputasi di luar cakupan tabel.
---

Mengembalikan tanggal **hari besar Islam** untuk satu tahun kalender. Di dalam cakupan
tabel MABIMS, tanggal langsung dari tabel resmi Kemenag — tabel yang sama dengan
`/convert`. Di luar cakupan tabel, tanggal dikomputasi secara langsung menggunakan kriteria
Neo MABIMS (ketinggian hilal ≥ 3° dan elonagasi ≥ 6.4° saat matahari terbenam di Sabang),
sehingga Anda bisa mendapatkan tanggal hari besar bertahun-tahun ke depan.

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

- Di dalam cakupan tabel, `source` adalah `mabims`. Di luar cakupan, `source` adalah
  `mabims-computed` (kriteria Neo MABIMS).
- Peringatan disertakan saat data komputasi digunakan — periksa array
  `warnings[]` di respons.
- Untuk `calendar=gregorian`, endpoint memperkirakan tahun hijriah yang tumpang tindih
  dengan tahun gregorian yang diminta dan menyelesaikan setiap event di tahun-tahun tersebut.
- Seperti `/convert`, respons di dalam cakupan tabel di-cache di CDN secara immutable.

## Error

```json
{
  "error": {
    "code": "invalid_year",
    "message": "..."
  }
}
```

| `code` | HTTP | Penyebab |
|---|---|---|
| `invalid_calendar` | 400 | Calendar bukan `gregorian` atau `hijri` |
| `invalid_year` | 400 | Tahun di luar batas yang didukung |
