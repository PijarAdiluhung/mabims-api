---
title: GET /hilal
description: Visibilitas hilal — data kriteria dan grafik langit untuk malam penentuan awal bulan Hijriah.
---

Dua endpoint untuk **visibilitas hilal**: malam penentuan adalah selalu **malam tanggal 29**
bulan berjalan — malam orang-orang keluar melihat hilal. Bila hilal tidak terlihat, bulan
lengkap 30 hari dan awal bulan bergeser sehari. Batas bulan diambil dari **tabel MABIMS
otoritatif** (bukan Umm al-Qura), sedangkan data astronomis dihitung **toposentris untuk
lokasi pemantau** — matahari terbenam aktual, posisi bulan, elongasi, iluminasi, usia
bulan, dan waktu terbenamnya bulan.

```
GET /api/v1/hilal/info?month={bulan}&year={tahun}&location={lokasi}   → JSON
GET /api/v1/hilal/viz?month={bulan}&year={tahun}&location={lokasi}    → PNG 720×1280
```

`info` berisi angka + verdict; `viz` merender grafik langit "ke mana melihat" dengan
tabel kriteria yang sama. Keduanya publik namun dibatasi rate limit ketat
(`info` 60/jam, `viz` 30/jam per IP).

## Parameter

| Parameter | Tipe | Wajib | Deskripsi |
|---|---|---|---|
| `month` | int 1–12 | ya | Bulan Hijriah **target** (grafik menampilkan malam penentuannya) |
| `year` | int | ya | Tahun Hijriah target |
| `location` | string | tidak (default `jakarta`) | `jakarta` · `malang` · `sabang` · `makkah` · `hawaii` |

## Contoh

```bash
curl "https://api.mabims.dev/api/v1/hilal/info?month=9&year=1447&location=jakarta"
```

```json
{
  "input": { "month": 9, "year": 1447, "location": "jakarta" },
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
pada saat matahari terbenam di lokasi yang diminta. Perlu dicatat: penetapan awal bulan
pada tabel tetap merujuk titik Sabang — data astronomis per lokasi menjelaskan
*bagaimana langit terlihat dari kota Anda* pada malam yang sama.

## Grafik (`/hilal/viz`)

PNG vertikal 720×1280 berisi: langit senja dengan bulan sabit (arah cahaya menghadap
matahari), pil verdict (`TERLIHAT` / `TIDAK TERLIHAT` / `DI BAWAH HORIZON`), dan tabel
kriteria `PARAMETER · MIN. MABIMS · STATUS`. Saat kriteria gagal, bulan sengaja tidak
digambar — langit menampilkan kenyataan. Output deterministik per parameter.

## Perilaku caching

- `Cache-Control: private, max-age=86400` — hasil deterministik per parameter, namun
  tidak di-cache publik di CDN.
- Render adalah operasi CPU: gunakan `location` dan parameter minimal yang Anda butuhkan,
  dan hormati rate limit.

## Error

| Kode | HTTP | Penyebab |
|---|---|---|
| `invalid_location` | 400 | Lokasi tidak dikenal |
| `out_of_coverage` | 400 | Bulan/tahun di luar cakupan tabel (lihat `/meta`) |
| `computation_unavailable` | 503 | Gagal menghitung astronomi |
| `render_failed` | 500 | Gagal merender PNG |
