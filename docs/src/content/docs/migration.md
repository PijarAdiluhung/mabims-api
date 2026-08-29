---
title: Migration dari Aladhan
description: Pindah dari Aladhan API / Umm al-Qura ke MABIMS — satu kode, tanggal lebih akurat untuk Indonesia.
---

Panduan ini untuk developer yang sudah menggunakan [Aladhan API](https://aladhan.com) (atau API berbasis Umm al-Qura lainnya) dan ingin beralih ke MABIMS.

## Kenapa migrasi?

| | Aladhan / Umm al-Qura | MABIMS |
|---|---|---|
| Sumber data | Pemerintah Saudi | Kemenag RI |
| Metode | Rukyah Saudi | Neo MABIMS (≥3° hilal, ≥6.4° elongasi) |
| Akurasi untuk Indonesia | ±1 hari | Resmi |
| Autentikasi | Tergantung provider | Tidak perlu |
| Format tanggal | `DD-MM-YYYY` | `YYYY-MM-DD` |

## Perbandingan endpoint

### Gregorian → Hijri

**Aladhan:**

```javascript
const res = await fetch("https://api.aladhan.com/v1/gToH/18-02-2026");
const { data } = await res.json();
// data.hijri.day, data.hijri.month.en, data.hijri.year
```

**MABIMS:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/convert?date=2026-02-18&calendar=gregorian");
const data = await res.json();
// data.output.day, data.output.month_name, data.output.year
```

### Hijri → Gregorian

**Aladhan:**

```javascript
const res = await fetch("https://api.aladhan.com/v1/hToG/15-08-1447");
const { data } = await res.json();
// data.gregorian.date (format: "18-02-2026")
```

**MABIMS:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/convert?date=1447-08-15&calendar=hijri");
const data = await res.json();
// data.output.date (format: "2026-02-18")
```

### Hari ini

**Aladhan:** Tidak ada endpoint `/today` yang terpisah — harus hit `/gToH` dengan tanggal hari ini.

**MABIMS:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/today");
const data = await res.json();
// data.output.date, data.output.month_name, data.output.year
```

## Perbedaan format response

### Aladhan

```json
{
  "code": 200,
  "status": "OK",
  "data": {
    "hijri": {
      "date": "15-08-1447",
      "day": "15",
      "month": { "number": 8, "en": "Rabi' al-awwal", "ar": "رَبِيع ٱلْأَوَّل" },
      "year": "1447"
    },
    "gregorian": {
      "date": "18-02-2026",
      "day": "18",
      "month": { "number": 2, "en": "February" },
      "year": "2026"
    }
  }
}
```

### MABIMS

```json
{
  "input": { "date": "2026-02-18", "calendar": "gregorian" },
  "output": {
    "date": "1447-08-15",
    "calendar": "hijri",
    "day": 15,
    "month": 8,
    "month_name": "Rabiul Awal",
    "year": 1447
  },
  "source": "mabims",
  "warnings": []
}
```

## Ringkasan perubahan

| Aspek | Aladhan | MABIMS |
|---|---|---|
| Base URL | `https://api.aladhan.com/v1` | `https://api.mabims.dev/api/v1` |
| Tanggal input | `DD-MM-YYYY` | `YYYY-MM-DD` |
| Response wrapper | `data.hijri`, `data.gregorian` | `output.date`, `output.day`, `output.month_name` |
| Autentikasi | Tergantung | Tidak perlu |
| Hari ini | Hit `/gToH` manual | `/today` |

## Tips migrasi

1. **Ganti base URL** dari `api.aladhan.com/v1` ke `api.mabims.dev/api/v1`
2. **Ubah format tanggal** dari `DD-MM-YYYY` ke `YYYY-MM-DD`
3. **Sesuaikan parsing response** — MABIMS menggunakan `output` bukan `data.hijri`
4. **Gunakan `/today`** alih-alih hit `/gToH` manual setiap hari
5. **Periksa `source`** — MABIMS menandai apakah data dari tabel publik (`mabims`) atau komputasi (`mabims-computed`)
