"""Hilal sky chart renderer — port of the approved mock (api/todo/mock_v2.py).

Layout, type scale and behavior are specified in api/todo/DESIGN.md:
dusk vertical 720x1280, Indonesian labels, criteria table with MABIMS
thresholds, visibility-driven moon rendering, logo watermark.
"""

from __future__ import annotations

import math
import random
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 720, 1280
AZ_SPAN = 30.0

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_PATH = ASSETS / "mabims-long.png"

GREG_MONTHS_ID = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu/",
    "/usr/share/fonts/TTF/",
    "C:/Windows/Fonts/",
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["DejaVuSans-Bold.ttf", "segoeuib.ttf", "arialbd.ttf"]
        if bold
        else ["DejaVuSans.ttf", "segoeui.ttf", "arial.ttf"]
    )
    for directory in _FONT_DIRS:
        for name in names:
            try:
                return ImageFont.truetype(directory + name, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


# ── visibility model ──

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


# ── primitives ──

def _txt(d: ImageDraw.ImageDraw, xy, s, f, fill, anchor="la") -> None:
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def _vgrad(w: int, h: int, stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    px = img.load()
    assert px is not None
    for y in range(h):
        t = y / max(1, h - 1)
        col = stops[-1][1]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                frac = (t - p0) / max(1e-6, p1 - p0)
                col = (
                    int(c0[0] + (c1[0] - c0[0]) * frac),
                    int(c0[1] + (c1[1] - c0[1]) * frac),
                    int(c0[2] + (c1[2] - c0[2]) * frac),
                )
                break
        row = (col[0], col[1], col[2], 255)
        for x in range(w):
            px[x, y] = row
    return img


def _starfield(img: Image.Image, box: tuple, n: int, horizon_y: int,
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


def _glow(img: Image.Image, cx: float, cy: float, r: float, color: tuple, alpha: int = 70) -> None:
    r = int(r)
    pad = r * 3
    layer = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([pad - r, pad - r, pad + r, pad + r], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=r * 0.6))
    img.alpha_composite(layer, (int(cx - pad), int(cy - pad)))


def _flat_crescent(size: int, illum: float, tilt: float, color: tuple,
                   limb_scale: float = 1.0, alpha: int = 255,
                   blur: float = 0.0) -> Image.Image:
    """Icon crescent: disc minus offset punch (dx = 2r*eff), lit limb on the
    left at tilt=0; rotated so the bright limb points at the sun."""
    s = size * 3
    c, r = s // 2, s // 2 - 4
    mask = Image.new("L", (s, s), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([c - r, c - r, c + r, c + r], fill=255)
    eff = min(0.98, (0.02 + 0.98 * max(0.0, min(1.0, illum))) * limb_scale)
    md.ellipse([c - r + 2 * r * eff, c - r, c + r + 2 * r * eff, c + r], fill=0)
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", (s, s), color + (255,)), (0, 0), mask)
    layer = layer.rotate(tilt, resample=Image.Resampling.BICUBIC).resize(
        (size, size), Image.Resampling.LANCZOS
    )
    if blur > 0.05:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        a = layer.getchannel("A").point(lambda v: v * alpha // 255)
        layer.putalpha(a)
    return layer


def _pill(img: Image.Image, x: int, y: int, text: str, fill, fg,
          f: ImageFont.FreeTypeFont | ImageFont.ImageFont,
          pad_x: int = 18, pad_y: int = 10) -> int:
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.rounded_rectangle([x, y, x + tw + pad_x * 2, y + th + pad_y * 2 + 4],
                        radius=(th + pad_y * 2 + 4) // 2, fill=fill)
    d.text((x + pad_x, y + pad_y - bb[1] // 2), text, font=f, fill=fg)
    return int(tw + pad_x * 2)


def _az_to_x(az: float, center_az: float, span: float, x0: int, x1: int) -> float:
    return x0 + (az - (center_az - span / 2)) / span * (x1 - x0)


def _alt_to_y(alt: float, alt_hi: float, horizon_y: int, top_y: int,
              alt_lo: float = -8.0, bottom_y: int | None = None) -> float:
    if alt >= 0:
        return horizon_y - (alt / alt_hi) * (horizon_y - top_y)
    bottom = bottom_y if bottom_y is not None else horizon_y + (horizon_y - top_y) * 0.35
    return horizon_y + (-alt / -alt_lo) * (bottom - horizon_y)


# ── palette ──

def _palette() -> dict:
    return dict(
        horizon=(255, 214, 153), sun=(255, 120, 70), sun_dim=(255, 160, 90, 130),
        moon=(255, 244, 224), moon_glow=(255, 190, 120), ground=(38, 22, 34),
        text=(255, 244, 230), muted=(255, 214, 170), card=(43, 26, 46),
        border=(90, 52, 74), good=(126, 217, 87), bad=(255, 99, 99),
        accent=(255, 209, 102),
    )


# ── scene ──

def _draw_sky_scene(img: Image.Image, data: dict, box: tuple, pal: dict,
                    moon_size: int, sun_size: int, alt_hi: float = 14.0) -> tuple[float, float]:
    x0, y0, x1, horizon_y = box
    d = ImageDraw.Draw(img)
    c_az = (data["sun_az"] + data["moon_az"]) / 2
    mx = _az_to_x(data["moon_az"], c_az, AZ_SPAN, x0, x1)
    sx = _az_to_x(data["sun_az"], c_az, AZ_SPAN, x0, x1)
    my = _alt_to_y(data["moon_alt"], alt_hi, horizon_y, y0 + 30)
    sy = _alt_to_y(data["sun_alt"], alt_hi, horizon_y, y0 + 30)

    if data["sun_alt"] < 0:
        _glow(img, sx, horizon_y + 4, sun_size * 2.2, pal["sun"], alpha=90)
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
        _glow(img, mx, my, moon_size, pal["moon_glow"], alpha=int(60 * f))
        tilt = 180.0 - math.degrees(math.atan2(sy - my, sx - mx))
        cres = _flat_crescent(
            moon_size, data["illum"], tilt=tilt, color=pal["moon"],
            limb_scale=0.5 + 0.5 * f,
            alpha=int(255 * f),
            blur=(1.0 - f) * 3.0,
        )
        img.alpha_composite(cres, (int(mx - moon_size / 2), int(my - moon_size / 2)))
    _txt(d, (sx - 8, horizon_y + 12), "B", font(20, bold=True), pal["horizon"], anchor="ra")
    return mx, my


def _draw_verdict_pill(img: Image.Image, data: dict, mx: float, my: float,
                       moon_size: int, pal: dict, horizon_y: int) -> None:
    d = ImageDraw.Draw(img)
    vt = verdict_label(data)
    pf = font(22, bold=True)
    bb = d.textbbox((0, 0), vt, font=pf)
    pw = bb[2] - bb[0] + 40
    px = mx + moon_size / 2 + 24
    if px + pw > W - 40:
        px = mx - moon_size / 2 - 24 - pw
    py = min(int(my) - 23, horizon_y - 70)
    _pill(img, int(max(40, px)), py, vt,
          pal["good"] if data["visible"] else pal["bad"], (30, 16, 24), pf,
          pad_x=20, pad_y=10)


def _criteria_table(img: Image.Image, data: dict, box: tuple, pal: dict) -> None:
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

    _txt(d, (x0, y0), "PARAMETER", f_head, pal["muted"])
    _txt(d, (xm + 56, y0), "MIN. MABIMS", f_head, pal["muted"], anchor="ma")
    _txt(d, (xr, y0), "STATUS", f_head, pal["muted"], anchor="ra")
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
        _txt(d, (x0, yy + 8), lab, f_lab, pal["muted"])
        _txt(d, (x0, yy + 32), val, f_value, col)
        _txt(d, (xm, yy + 34), mn, f_min, pal["muted"])
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
        _txt(d, (x0, cy), lab, f_head, pal["muted"], anchor="lm")
        _txt(d, (xr, cy), val, f_value, pal["text"], anchor="rm")


# ── composition ──

def render_chart(data: dict) -> Image.Image:
    """Render the dusk-vertical chart for a prepared data dict.

    Keys: hijri, greg, loc, label, sunset, moonset, moon_alt, moon_az, sun_alt,
    sun_az, elong, illum, alt_ok, elong_ok, visible.
    """
    pal = _palette()
    img = _vgrad(W, H, [(0.0, (31, 18, 53)), (0.45, (94, 44, 74)),
                        (0.72, (196, 96, 66)), (0.86, (242, 166, 90)), (1.0, (52, 30, 40))])
    horizon_y = int(H * 0.55)
    _starfield(img, (0, 190, W, int(H * 0.35)), n=int(W * H / 4400),
               horizon_y=int(H * 0.35))
    mx, my = _draw_sky_scene(img, data, (40, 190, W - 40, horizon_y), pal,
                             moon_size=170, sun_size=36, alt_hi=14.0)

    d = ImageDraw.Draw(img)
    pts: list[tuple[float, float]] = [(0, horizon_y + 2)]
    for xx in range(0, W + 24, 24):
        hh = 20 + 14 * math.sin(xx / 97.0) + 9 * math.sin(xx / 33.0 + 1.7)
        pts.append((xx, horizon_y - max(6.0, hh)))
    pts += [(W, horizon_y + 2), (W, H), (0, H)]
    d.polygon(pts, fill=pal["ground"])
    d.line([0, horizon_y, W, horizon_y], fill=pal["horizon"], width=2)
    _draw_verdict_pill(img, data, mx, my, 170, pal, horizon_y)

    _txt(d, (40, 32), data["hijri"], font(50, bold=True), pal["text"])
    _txt(d, (40, 96), f"{data['greg']}  \u00b7  {data['loc']}", font(28), pal["muted"])
    _txt(d, (40, 140), data["label"], font(24, bold=True), pal["accent"])

    card_y = horizon_y + 30
    card_h = H - card_y - 52
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [32, card_y, W - 32, card_y + card_h], radius=24, fill=pal["card"] + (215,))
    img.alpha_composite(overlay)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([32, card_y, W - 32, card_y + card_h], radius=24,
                        outline=pal["border"], width=1)
    _criteria_table(img, data, (64, card_y + 26, W - 64, card_y + card_h - 20), pal)

    logo = Image.open(LOGO_PATH).convert("RGBA")
    lh = 40
    lw = int(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    img.alpha_composite(logo, ((W - lw) // 2, H - lh - 10))
    return img


def chart_png_bytes(data: dict) -> bytes:
    import io

    buf = io.BytesIO()
    render_chart(data).convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def build_chart_data(*, hijri_label: str, evening_date: date, location_display: str,
                     visibility_label: str, sunset: str, moonset: str, moon_alt: float,
                     moon_az: float, sun_alt: float, sun_az: float, elong: float,
                     illum: float, alt_ok: bool, elong_ok: bool) -> dict:
    """Assemble the renderer's data dict from typed inputs."""
    return {
        "hijri": hijri_label,
        "greg": f"{evening_date.day} {GREG_MONTHS_ID[evening_date.month]} {evening_date.year}",
        "loc": location_display,
        "label": visibility_label,
        "sunset": sunset,
        "moonset": moonset,
        "moon_alt": float(moon_alt),
        "moon_az": float(moon_az),
        "sun_alt": float(sun_alt),
        "sun_az": float(sun_az),
        "elong": float(elong),
        "illum": float(illum),
        "alt_ok": bool(alt_ok),
        "elong_ok": bool(elong_ok),
        "visible": bool(alt_ok and elong_ok),
    }
