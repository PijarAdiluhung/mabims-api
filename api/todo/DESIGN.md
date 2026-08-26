# Hilal Chart — Design Spec (dusk vertical, 720x1280)

Polish plan. All spacing on an 8px grid; one type scale; fixed layout zones.
Implement as a `TOKENS` dict in code so `chart.py` stays declarative.

## Type scale (Segoe UI / DejaVu fallback)

Card uses THREE sizes — 18 (row labels), 28 bold (headers, MIN. MABIMS values,
chips), 36 bold (all values). Sky/header have their own scale.
All user-facing text is Indonesian.

| Token | Size | Weight | Color | Used for |
|---|---|---|---|---|
| `display` | 50 | bold | text | Hijri title ("30 Sya'ban 1447 H") |
| `meta` | 28 | regular | muted | Tanggal · lokasi |
| `overline` | 24 | bold | accent | "VISIBILITAS 1 RAMADHAN 1447 H" (no "MALAM" — ambiguous re: malam 29/30) |
| `verdict` | 22 | bold | dark-on-green/red | pill beside moon: TERLIHAT / TIDAK TERLIHAT / DI BAWAH HORIZON |
| `label` | 18 | regular | muted | ALT. BULAN, ELONGASI (criteria rows only) |
| `head` | 28 | bold | muted | PARAMETER · MIN. MABIMS (centered over column) · STATUS · simple-row labels |
| `min` | 36 | regular | muted | ≥ 3.0° / ≥ 6.4° (faint, value-sized) |
| `chip` | 28 | bold | chip color | LOLOS / GAGAL |
| `value` | 36 | bold | good/bad/text | ALL values |
| `logo` | 40px tall | — | gold PNG | `docs/public/mabims-long.png`, centered below card |

Chips: fixed 116x44, radius 14, tinted fill (good/bad @ 20% alpha).

## Layout zones (y pixels)

```
0    ─ header:   title y40 · meta y96 · overline y134   (ends ~164)
170  ─ sky:      stars, moon (170px), sun glow
742  ─ horizon + hills
772  ─ card:     pad top 28 / bottom 24 · inner x 64..656
1228 ─ card end · watermark y1246
```

## Card / table spec

- Header row y+28, rule under it (border color).
- **Criteria rows: height 96 each** — label top, value 12px below.
  Fixes current crowding (ELONGATION label nearly touching +8.7°).
- Columns (fixed left edges, no floating middle):
  - PARAMETER x=64
  - MABIMS MIN x=380 (left-aligned)
  - STATUS right-aligned to x=648
- **Chips: fixed 96x36, radius 12, centered text, tinted fill (good/bad @ 20% alpha)**
  — uniform geometry instead of text-hugging pills.
- Divider, then 3 simple rows at 56px with 10%-alpha hairlines between.
- Vertical budget: 28 + 30(header) + 192 + 34 + 168 + 24 ≈ 476 ≤ card 456 →
  trim simple rows to 52 if needed (computed, not hardcoded).

## Sky polish

- Sun glow: two layers (tight bright r=40 + wide soft r=110).
- Stars: 2 radii only (1/2px); no cross-sparkles within 120px of moon.
- Second horizon ridge behind hills (lighter ground color, offset -18px) for depth.
- No floating alt annotation — the VISIBLE/NOT VISIBLE pill floats beside the
  moon instead (right of disc; falls to the left side when it would overflow).

## Visibility degradation (limb realism)

Crescent geometry: disc minus same-size punch circle offset by
`dx = 2r · eff` → limb width ≈ dx. Tilt = `180° − atan2(sun − moon)`.
Moon size fixed 170px.

Visibility factor: `f = clamp(min((alt − 3)/4, (elong − 6.4)/5), 0.0, 1.0)`

| Effect | Formula | PASS (f≈0.93) | at/below threshold (f=0) |
|---|---|---|---|
| limb width | `eff = (0.02 + 0.98·illum) · (0.5 + 0.5·f)` | ~0.97× | not drawn |
| opacity | `alpha = 255·f` | ~94% | **0 — invisible** |
| blur | `(1 − f) · 3px` | ~0.2px | n/a |
| moon glow | `60·f` alpha | ~56 | 0 |

Pill states: `TERLIHAT` (alt ≥ 3 & elong ≥ 6.4) · `TIDAK TERLIHAT` (above horizon,
below a threshold) · `DI BAWAH HORIZON` (alt < 0). Pill floats beside the moon,
falls to its left on overflow, and clamps above the horizon line.

Sunset/moonset: computed per observer via Skyfield almanac (no hardcoded Maghrib,
no Aladhan). Verified cases (all from computed table):
- 30 Sya'ban 1447 (18 Feb 2026) — TERLIHAT, alt +8.9° elong 11.1°
- 29 Syawal 1447 (18 Apr 2026) — TERLIHAT, alt +7.9° elong 13.3° (pill left-flip)
- 29 Ramadhan 1447 (19 Mar 2026) — TIDAK TERLIHAT, alt +1.9° elong 5.2° (30-day month by construction)
- 29 Zulhijjah 1447 (15 Jun 2026) — TIDAK TERLIHAT, alt +2.1° elong 5.9° (malam 1 Muharram 1448)

Rationale: when the criteria say NOT VISIBLE, the chart shows no moon at all —
the sky itself tells the truth; the pill carries the verdict.

## Color (unchanged)

dusk palette as in `mock_v2.py` `pal` dict; chips read from `good`/`bad`.

## Acceptance checks

1. Title no wider than ~60% of canvas; pill never collides.
2. No text pair closer than 12px vertically.
3. Card has no dead bottom space; rows evenly distributed.
4. Both PASS and FAIL states render (test render both).
5. Deterministic output (seeded stars).
