---
title: GET /hilal
description: Hilal visibility — criteria data and sky chart for the evening that decides a Hijri month start.
---

Two endpoints for **hilal visibility**: the deciding evening is always the **29th** of the
current month — the night people actually go looking for the crescent. If it is not seen,
the month completes 30 days and the start shifts a day. Month boundaries come from the
**authoritative MABIMS tables** (not Umm al-Qura), while the astronomy is computed
**topocentrically for the observer's location** — actual sunset, moon position,
elongation, illumination, moon age and moonset.

```
GET /api/v1/hilal/info?month={month}&year={year}&location={location}   → JSON
GET /api/v1/hilal/viz?month={month}&year={year}&location={location}    → PNG 720×1280
```

`info` carries the numbers + verdict; `viz` renders a "where to look" sky chart with the
same criteria table. Both are public but tightly rate limited
(`info` 60/hour, `viz` 30/hour per IP).

## Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `month` | int 1–12 | yes | **Target** Hijri month (the chart shows its deciding evening) |
| `year` | int | yes | Target Hijri year |
| `location` | string | no (default `jakarta`) | `jakarta` · `malang` · `sabang` · `makkah` · `hawaii` |

## Example

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

## Visibility criteria

`visible = alt_ok && elong_ok` follows the same **Neo MABIMS criteria** as the computed
table: moon altitude (refraction-corrected) ≥ **3.0°** and elongation ≥ **6.4°** at
sunset for the requested location. Note that the table's month boundaries remain tied to
Sabang — the per-location astronomy describes *how the sky looks from your city* on the
same evening.

## Chart (`/hilal/viz`)

A 720×1280 vertical PNG: sunset sky with the crescent (bright limb facing the sun), a
verdict pill (`TERLIHAT` / `TIDAK TERLIHAT` / `DI BAWAH HORIZON`) and a
`PARAMETER · MABIMS MIN · STATUS` criteria table. When the criteria fail the moon is
deliberately not drawn — the sky tells the truth. Output is deterministic per parameter.

![Sample hilal visibility chart — 29 Sya'ban 1447 H, Jakarta](/viz.png)

## Caching

- `Cache-Control: private, max-age=86400` — deterministic per parameter but not
  publicly CDN-cached.
- Rendering is CPU work: request only what you need and respect the rate limits.

## Errors

| Code | HTTP | Cause |
|---|---|---|
| `invalid_location` | 400 | Unknown location |
| `out_of_coverage` | 400 | Month/year outside table coverage (see `/meta`) |
| `computation_unavailable` | 503 | Astronomy computation failed |
| `render_failed` | 500 | PNG rendering failed |
