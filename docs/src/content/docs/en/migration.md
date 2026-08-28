---
title: Migration from Aladhan
description: Switch from Aladhan API / Umm al-Qura to MABIMS — same code, better dates for Indonesia.
---

This guide is for developers already using the [Aladhan API](https://aladhan.com) (or other
Umm al-Qura-based APIs) who want to switch to MABIMS.

## Why migrate?

| | Aladhan / Umm al-Qura | MABIMS |
|---|---|---|
| Data source | Saudi government | Kemenag RI |
| Method | Saudi rukyah | Neo MABIMS (≥3° hilal, ≥6.4° elongation) |
| Accuracy for Indonesia | ±1 day | Official |
| Authentication | Depends on provider | None required |
| Date format | `DD-MM-YYYY` | `YYYY-MM-DD` |

## Endpoint comparison

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

### Today

**Aladhan:** No separate `/today` endpoint — you must call `/gToH` with today's date manually.

**MABIMS:**

```javascript
const res = await fetch("https://api.mabims.dev/api/v1/today");
const data = await res.json();
// data.output.date, data.output.month_name, data.output.year
```

## Response format differences

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

## Quick reference

| Aspect | Aladhan | MABIMS |
|---|---|---|
| Base URL | `https://api.aladhan.com/v1` | `https://api.mabims.dev/api/v1` |
| Date format | `DD-MM-YYYY` | `YYYY-MM-DD` |
| Response wrapper | `data.hijri`, `data.gregorian` | `output.date`, `output.day`, `output.month_name` |
| Auth | Depends | None |
| Today's date | Manual `/gToH` call | `/today` |

## Migration tips

1. **Change base URL** from `api.aladhan.com/v1` to `api.mabims.dev/api/v1`
2. **Switch date format** from `DD-MM-YYYY` to `YYYY-MM-DD`
3. **Update response parsing** — MABIMS uses `output` instead of `data.hijri`
4. **Use `/today`** instead of calling `/gToH` manually every day
5. **Check `source`** — MABIMS marks whether data is from the official table (`mabims`) or computed (`mabims-computed`)
