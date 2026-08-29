---
title: GET /hilal
description: Visibilitas hilal — data kriteria dan grafik langit untuk malam penentuan awal bulan Hijriah.
---

Ada dua endpoint untuk **visibilitas hilal**, dan malam penentuan selalu **malam tanggal 29**, malam rukyatul hilal. Bila hilal tidak terlihat, bulan
lengkap 30 hari dan awal bulan bergeser sehari. Batas bulan diambil dari **penanggalan Kemenag kriteria MABIMS**, dan data astronomis dihitung dengan **perhitungan geosentris di Sabang**, sebagai lokasi paling barat di Indonesia.

```
GET /api/v1/hilal/info?month={bulan}&year={tahun}   → JSON
GET /api/v1/hilal/viz?month={bulan}&year={tahun}    → PNG 720×1280
```

`info` berisi angka + verdict (terlihat atau tidak); `viz` merender grafik langit "ke mana melihat". Keduanya publik namun dibatasi rate limit ketat
(`info` 60/jam, `viz` 30/jam per IP).

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `month` | int 1–12 | ya | Bulan Hijriah **target** (grafik menampilkan malam penentuannya) |
| `year` | int | ya | Tahun Hijriah target |

Titik hisab tunggal: **Sabang, Indonesia** (5°53′N 95°19′E, WIB). Endpoint ini untuk memperkirakan
*apa yang mungkin diumumkan pemerintah Indonesia*.

## Contoh

```bash
curl "https://api.mabims.dev/api/v1/hilal/info?month=9&year=1447"
```

```json
{
  "input": { "month": 9, "year": 1447 },
  "month": { "name": "Ramadhan", "number": 9, "year": 1447, "start": "2026-02-19" },
  "previous_month": { "name": "Sya'ban", "number": 8, "year": 1447, "length": 30 },
  "evening": {
    "hijri_date": "29 Sya'ban 1447 H",
    "hijri_day": 29,
    "gregorian_date": "2026-02-17",
    "sunset": "18:14",
    "moonset": "18:51",
    "moon_alt_deg": 8.78,
    "moon_az_deg": 263.98,
    "sun_alt_deg": -0.83,
    "elongation_deg": 11.07,
    "illumination_pct": 1.07,
    "age_hours": 23.2,
    "alt_ok": true,
    "elong_ok": true,
    "visible": true
  },
  "source": "mabims",
  "warnings": []
}
```

## Kriteria visibilitas

`visible = alt_ok && elong_ok` mengikuti **kriteria Neo MABIMS** yang sama dengan
tabel computed: ketinggian bulan (terkoreksi refraksi) ≥ **3,0°** dan elongasi ≥ **6,4°**
pada saat matahari terbenam di Sabang. Nilai altitud/elongasi/azimut bersifat **geosentris**
(konvensi hisab Indonesia); waktu matahari/bulan terbenam tetap dihitung toposentris untuk
Sabang karena itu fenomena pengamat.

## Grafik (`/hilal/viz`)

PNG vertikal 720×1280 berisi: langit senja dengan bulan sabit (arah cahaya menghadap
matahari), pil verdict (`TERLIHAT` / `TIDAK TERLIHAT` / `DI BAWAH HORIZON`), dan tabel
kriteria `PARAMETER · MIN. MABIMS · STATUS`. Output deterministik per parameter.

![Contoh grafik visibilitas hilal — 29 Sya'ban 1447 H, Sabang](/viz.png)

## Perilaku caching

- `Cache-Control: public, max-age=86400, s-maxage=86400` — hasil deterministik per parameter,
  di-cache publik di CDN (CDN mendapat satu render per edge location per hari).
- Render adalah operasi CPU: gunakan parameter minimal yang Anda butuhkan,
  dan hormati rate limit.

## Error

| Kode | HTTP | Penyebab |
|---|---|---|
| `out_of_coverage` | 400 | Bulan/tahun di luar cakupan tabel (lihat `/meta`) |
| `computation_unavailable` | 503 | Gagal menghitung astronomi |
| `render_failed` | 500 | Gagal merender PNG |
