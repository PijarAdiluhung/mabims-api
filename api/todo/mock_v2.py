"""Hilal chart v2 — FINAL design: "dusk" vertical, consolidated.

One style, one format (720x1280). No moontex / no inset view:
the in-sky crescent is drawn procedurally (bright limb facing the sun)
and the bottom card is a MABIMS criteria table.

Output: api/todo/output/mock_dusk_vert.png
"""

from __future__ import annotations

import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "hilal-visualizer"))

from astronomy import calculate_at_sunset, find_moonset, get_illumination_at  # noqa: E402

OUT = HERE / "output"
W, H = 720, 1280
AZ_SPAN = 30.0
FONTS = "C:/Windows/Fonts/"


# ── data ──

def _sunset_hm(d: datetime, lat: float, lon: float, tz_hours: float = 7.0):
    """Local sunset (HH, MM) via Skyfield almanac — no hardcoded Maghrib."""
    import os
    import tempfile

    from skyfield.almanac import find_discrete, sunrise_sunset
    from skyfield.api import Loader, wgs84

    directory = os.environ.get("MABIMS_EPHEMERIS_DIR") or Path(tempfile.gettempdir()) / "mabims-ephemeris"
    loader = Loader(str(directory))
    ts = loader.timescale(builtin=True)
    eph = loader("de421.bsp")
    obs = wgs84.latlon(lat, lon)
    start = d.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=tz_hours)
    end = start + timedelta(days=1)
    t0 = ts.utc(start.year, start.month, start.day, start.hour, start.minute)
    t1 = ts.utc(end.year, end.month, end.day, end.hour, end.minute)
    times, events = find_discrete(t0, t1, sunrise_sunset(eph, obs))
    for t, ev in zip(times, events):
        if not ev:
            local = t.utc_datetime() + timedelta(hours=tz_hours)
            return local.hour, local.minute
    return 18, 0


def fetch_case(date: datetime, hijri: str, eve: str) -> dict:
    lat, lon = -6.2088, 106.8456  # Jakarta
    sh, sm = _sunset_hm(date, lat, lon)
    a = calculate_at_sunset(date, sh, sm, lat, lon, utc_offset=7.0)
    moonset = find_moonset(date, lat, lon, utc_offset=7.0)
    phase = get_illumination_at(date, sh, sm, days_ahead=0.5, lat=lat, lon=lon)
    alt_ok = a.moon_alt >= 3.0
    elong_ok = a.elongation >= 6.4
    greg = f"{date.day} {['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'][date.month]} {date.year}"
    return dict(
        sun_alt=float(a.sun_alt), sun_az=float(a.sun_az),
        moon_alt=float(a.moon_alt), moon_az=float(a.moon_az),
        elong=float(a.elongation), illum=float(a.illumination), phase=float(phase),
        age_h=float(a.lunar_age_days) * 24, moonset=moonset,
        sunset=f"{sh:02d}:{sm:02d}",
        alt_ok=alt_ok, elong_ok=elong_ok, visible=alt_ok and elong_ok,
        hijri=hijri, greg=greg,
        loc="Jakarta, Indonesia", label=eve,
    )


# ── primitives ──

def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(FONTS + n, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def txt(d: ImageDraw.ImageDraw, xy, s, f, fill, anchor="la") -> None:
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def vgrad(w: int, h: int, stops: list[tuple[float, tuple]]) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = (t - p0) / max(1e-6, p1 - p0)
                col = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        for x in range(w):
            px[x, y] = col + (255,)
    return img


def starfield(img: Image.Image, box: tuple, n: int, horizon_y: int,
              seed: int = 11, max_alpha: int = 140) -> None:
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, min(y1, horizon_y - 6))
        fade = max(0.0, (horizon_y - y) / max(1, horizon_y - y0))
        a = int(max_alpha * fade * rnd.uniform(0.3, 1.0))
        r = rnd.choice([1, 1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 214, a))
        if rnd.random() < 0.04:
            d.line([x - 5, y, x + 5, y], fill=(255, 240, 214, a // 2), width=1)
            d.line([x, y - 5, x, y + 5], fill=(255, 240, 214, a // 2), width=1)
    img.alpha_composite(layer)


def glow(img: Image.Image, cx: float, cy: float, r: float, color: tuple, alpha: int = 70) -> None:
    r = int(r)
    pad = r * 3
    layer = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([pad - r, pad - r, pad + r, pad + r], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=r * 0.6))
    img.alpha_composite(layer, (int(cx - pad), int(cy - pad)))


def visibility_factor(data: dict) -> float:
    """1.0 = comfortably visible, 0.0 = at/below MABIMS threshold (invisible)."""
    f = min((data["moon_alt"] - 3.0) / 4.0, (data["elong"] - 6.4) / 5.0)
    return max(0.0, min(1.0, f))


def verdict_label(data: dict) -> str:
    if data["moon_alt"] < 0:
        return "DI BAWAH HORIZON"
    if not data["visible"]:
        return "TIDAK TERLIHAT"
    return "TERLIHAT"


def flat_crescent(size: int, illum: float, tilt: float, color: tuple,
                  limb_scale: float = 1.0, alpha: int = 255,
                  blur: float = 0.0) -> Image.Image:
    """Icon crescent: disc minus offset punch (dx = 2r*eff), lit limb on the
    left at tilt=0; rotated so the bright limb points at the sun.

    limb_scale thins the sliver, alpha fades it, blur softens it — all driven
    by visibility_factor so marginal moons actually look invisible.
    """
    s = size * 3
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c, r = s // 2, s // 2 - 4
    mask = Image.new("L", (s, s), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([c - r, c - r, c + r, c + r], fill=255)
    eff = min(0.98, (0.02 + 0.98 * max(0.0, min(1.0, illum))) * limb_scale)
    md.ellipse([c - r + 2 * r * eff, c - r, c + r + 2 * r * eff, c + r], fill=0)
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", (s, s), color + (255,)), (0, 0), mask)
    layer = layer.rotate(tilt, resample=Image.BICUBIC).resize((size, size), Image.LANCZOS)
    if blur > 0.05:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        a = layer.getchannel("A").point(lambda v: v * alpha // 255)
        layer.putalpha(a)
    return layer


def pill(img: Image.Image, x: int, y: int, text: str, fill, fg,
         f: ImageFont.FreeTypeFont, pad_x=18, pad_y=10) -> int:
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.rounded_rectangle([x, y, x + tw + pad_x * 2, y + th + pad_y * 2 + 4],
                        radius=(th + pad_y * 2 + 4) // 2, fill=fill)
    d.text((x + pad_x, y + pad_y - bb[1] // 2), text, font=f, fill=fg)
    return tw + pad_x * 2


def az_to_x(az: float, center_az: float, span: float, x0: int, x1: int) -> float:
    return x0 + (az - (center_az - span / 2)) / span * (x1 - x0)


def alt_to_y(alt: float, alt_hi: float, horizon_y: int, top_y: int,
             alt_lo: float = -8.0, bottom_y: int | None = None) -> float:
    if alt >= 0:
        return horizon_y - (alt / alt_hi) * (horizon_y - top_y)
    bottom = bottom_y if bottom_y is not None else horizon_y + (horizon_y - top_y) * 0.35
    return horizon_y + (-alt / -alt_lo) * (bottom - horizon_y)


# ── sky scene ──

def draw_sky_scene(img: Image.Image, data: dict, box: tuple, pal: dict,
                   moon_size: int, sun_size: int, alt_hi: float = 18.0) -> None:
    x0, y0, x1, horizon_y = box
    d = ImageDraw.Draw(img)
    c_az = (data["sun_az"] + data["moon_az"]) / 2
    mx = az_to_x(data["moon_az"], c_az, AZ_SPAN, x0, x1)
    sx = az_to_x(data["sun_az"], c_az, AZ_SPAN, x0, x1)
    my = alt_to_y(data["moon_alt"], alt_hi, horizon_y, y0 + 30)
    sy = alt_to_y(data["sun_alt"], alt_hi, horizon_y, y0 + 30)

    if data["sun_alt"] < 0:
        glow(img, sx, horizon_y + 4, sun_size * 2.2, pal["sun"], alpha=90)
        steps = int(min(sy, horizon_y + 90) - horizon_y) // 10
        for i in range(max(0, steps)):
            yy = horizon_y + 6 + i * 10
            d.line([sx, yy, sx, yy + 5], fill=pal["sun_dim"], width=2)
    else:
        d.ellipse([sx - sun_size, sy - sun_size, sx + sun_size, sy + sun_size],
                  fill=pal["sun"])
    d.line([x0, horizon_y, x1, horizon_y], fill=pal["horizon"], width=2)

    f = visibility_factor(data)
    if f > 0:
        glow(img, mx, my, moon_size, pal["moon_glow"], alpha=int(60 * f))
        tilt = 180.0 - math.degrees(math.atan2(sy - my, sx - mx))
        cres = flat_crescent(
            moon_size, data["illum"], tilt=tilt, color=pal["moon"],
            limb_scale=0.5 + 0.5 * f,
            alpha=int(255 * f),
            blur=(1.0 - f) * 3.0,
        )
        img.alpha_composite(cres, (int(mx - moon_size / 2), int(my - moon_size / 2)))
    txt(d, (sx - 8, horizon_y + 12), "W", font(20, bold=True), pal["horizon"], anchor="ra")
    return mx, my


def draw_verdict_pill(img: Image.Image, data: dict, mx: float, my: float,
                      moon_size: int, pal: dict, horizon_y: int) -> None:
    """Verdict pill floats beside the moon; drawn after hills (on top).
    Clamped to sit above the horizon when the moon is below it."""
    d = ImageDraw.Draw(img)
    vt = verdict_label(data)
    pf = font(22, bold=True)
    bb = d.textbbox((0, 0), vt, font=pf)
    pw = bb[2] - bb[0] + 40
    px = mx + moon_size / 2 + 24
    if px + pw > W - 40:
        px = mx - moon_size / 2 - 24 - pw
    py = min(int(my) - 23, horizon_y - 70)
    pill(img, int(max(40, px)), py, vt,
         pal["good"] if data["visible"] else pal["bad"], (30, 16, 24), pf,
         pad_x=20, pad_y=10)


# ── criteria table ──

def criteria_table(img: Image.Image, data: dict, box: tuple, pal: dict) -> None:
    """Three sizes: 18 row labels, 28 bold headers/min/chips, 36 bold values."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    f_lab = font(18)
    f_head = font(28, bold=True)
    f_min = font(36)
    f_value = font(36, bold=True)
    xr = x1 - 8
    xm = x0 + (x1 - x0) * 0.46
    chip_w, chip_h = 116, 44

    txt(d, (x0, y0), "PARAMETER", f_head, pal["muted"])
    txt(d, (xm + 56, y0), "MIN. MABIMS", f_head, pal["muted"], anchor="ma")
    txt(d, (xr, y0), "STATUS", f_head, pal["muted"], anchor="ra")
    d.line([x0, y0 + 40, x1, y0 + 40], fill=pal["border"], width=1)

    crit = [
        ("ALT. BULAN", f"{data['moon_alt']:+.1f}\u00b0", "\u2265 3.0\u00b0", data["alt_ok"]),
        ("ELONGASI", f"{data['elong']:.1f}\u00b0", "\u2265 6.4\u00b0", data["elong_ok"]),
    ]
    chips = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(chips)
    yy = y0 + 52
    crit_h = 96
    for lab, val, mn, ok in crit:
        col = pal["good"] if ok else pal["bad"]
        txt(d, (x0, yy + 8), lab, f_lab, pal["muted"])
        txt(d, (x0, yy + 32), val, f_value, col)
        txt(d, (xm, yy + 34), mn, f_min, pal["muted"])
        tag = "LOLOS" if ok else "GAGAL"
        cd.rounded_rectangle([xr - chip_w, yy + 26, xr, yy + 26 + chip_h],
                             radius=14, fill=col + (52,))
        tbb = cd.textbbox((0, 0), tag, font=f_head)
        cd.text((xr - chip_w // 2 - (tbb[2] - tbb[0]) // 2,
                 yy + 26 + (chip_h - tbb[3]) // 2 - 2), tag, font=f_head, fill=col)
        yy += crit_h
    img.alpha_composite(chips)
    d = ImageDraw.Draw(img)

    yy += 2
    d.line([x0, yy, x1, yy], fill=pal["border"], width=1)
    yy += 14
    rows = [
        ("ILUMINASI", f"{data['illum'] * 100:.1f}%"),
        ("MATAHARI TERBENAM", data["sunset"]),
        ("BULAN TERBENAM", data["moonset"]),
    ]
    simple_h = (y1 - yy) // len(rows)
    for i, (lab, val) in enumerate(rows):
        ry = yy + i * simple_h
        if i:
            d.line([x0, ry, x1, ry], fill=(66, 40, 60), width=1)
        cy = ry + simple_h // 2
        txt(d, (x0, cy), lab, f_head, pal["muted"], anchor="lm")
        txt(d, (xr, cy), val, f_value, pal["text"], anchor="rm")


# ── composition ──

def render(data: dict) -> Image.Image:
    pal = dict(horizon=(255, 214, 153), sun=(255, 120, 70), sun_dim=(255, 160, 90, 130),
               moon=(255, 244, 224), moon_glow=(255, 190, 120), ground=(38, 22, 34),
               text=(255, 244, 230), muted=(255, 214, 170), card=(43, 26, 46),
               border=(90, 52, 74), good=(126, 217, 87), bad=(255, 99, 99),
               accent=(255, 209, 102))

    img = vgrad(W, H, [(0.0, (31, 18, 53)), (0.45, (94, 44, 74)),
                       (0.72, (196, 96, 66)), (0.86, (242, 166, 90)), (1.0, (52, 30, 40))])
    horizon_y = int(H * 0.55)
    starfield(img, (0, 190, W, int(H * 0.35)), n=int(W * H / 4400),
              horizon_y=int(H * 0.35))
    mx, my = draw_sky_scene(img, data, (40, 190, W - 40, horizon_y), pal,
                            moon_size=170, sun_size=36, alt_hi=14.0)

    # flat hills silhouette (smooth sine ridge)
    d = ImageDraw.Draw(img)
    pts = [(0, horizon_y + 2)]
    for xx in range(0, W + 24, 24):
        hh = 20 + 14 * math.sin(xx / 97.0) + 9 * math.sin(xx / 33.0 + 1.7)
        pts.append((xx, horizon_y - max(6, hh)))
    pts += [(W, horizon_y + 2), (W, H), (0, H)]
    d.polygon(pts, fill=pal["ground"])
    d.line([0, horizon_y, W, horizon_y], fill=pal["horizon"], width=2)
    draw_verdict_pill(img, data, mx, my, 170, pal, horizon_y)

    # header
    txt(d, (40, 32), data["hijri"], font(50, bold=True), pal["text"])
    txt(d, (40, 96), f"{data['greg']}  \u00b7  {data['loc']}", font(28), pal["muted"])
    txt(d, (40, 140), data["label"], font(24, bold=True), pal["accent"])

    # stats card
    card_y = horizon_y + 30
    card_h = H - card_y - 52
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [32, card_y, W - 32, card_y + card_h], radius=24, fill=pal["card"] + (215,))
    img.alpha_composite(overlay)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([32, card_y, W - 32, card_y + card_h], radius=24,
                        outline=pal["border"], width=1)
    criteria_table(img, data, (64, card_y + 26, W - 64, card_y + card_h - 20), pal)

    # logo watermark (docs/public/mabims-long.png), centered below the card
    logo = Image.open(HERE.parent.parent / "docs" / "public" / "mabims-long.png").convert("RGBA")
    lh = 40
    lw = int(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    img.alpha_composite(logo, ((W - lw) // 2, H - lh - 10))
    return img


def main() -> None:
    cases = [
        (datetime(2026, 2, 18), "30 Sya'ban 1447 H",
         "VISIBILITAS 1 RAMADHAN 1447 H", "mock_dusk_vert.png"),
    ]
    # Candidate evenings from the MABIMS computed table
    import json

    ct_path = HERE.parent / "data" / "computed_table.json"
    h2g = json.loads(ct_path.read_text()).get("hijri_to_gregorian", {})
    for hkey, hijri, eve, name in [
        ("1447-09-29", "29 Ramadhan 1447 H",
         "VISIBILITAS 1 SYAWAL 1447 H", "mock_dusk_syawal.png"),
        ("1447-10-29", "29 Syawal 1447 H",
         "VISIBILITAS 1 DZULQA'DAH 1447 H", "mock_dusk_dzulqadah.png"),
        ("1447-12-29", "29 Dzulhijjah 1447 H",
         "VISIBILITAS 1 MUHARRAM 1448 H", "mock_dusk_muharram.png"),
    ]:
        g = h2g.get(hkey)
        if g:
            y, m, dd = map(int, g.split("-"))
            cases.append((datetime(y, m, dd), hijri, eve, name))
    for date, hijri, eve, name in cases:
        data = fetch_case(date, hijri, eve)
        print(f"{hijri}: alt {data['moon_alt']:+.2f}  elong {data['elong']:.2f}  "
              f"illum {data['illum'] * 100:.2f}%  terbenam {data['sunset']}/"
              f"{data['moonset']}  terlihat={data['visible']}")
        OUT.mkdir(exist_ok=True)
        p = OUT / name
        render(data).convert("RGB").save(p)
        print(f"saved {p}")


if __name__ == "__main__":
    main()
