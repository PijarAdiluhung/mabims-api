"""Hilal visibility map card — 720x1280 PNG.

A 1:1 visual port of the approved mock (temp/mock_map.py): same gradient, same
type scale, same table-panel geometry as ``/hilal/viz`` (chart.py). The sky
graphic is replaced by a full-bleed map that is exactly as tall as the viz's
sky block (title bottom -> horizon at y=704), with the legend overlaid on the
bottom of that block.

Criteria (same as the rest of the API): topocentric mar'i moon altitude
(Bennett refraction) >= 3.0 deg AND geocentric elongation >= 6.4 deg at each
display point's local sunset.
"""

from __future__ import annotations

import io
import json
from datetime import date
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Segoe UI"]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import ListedColormap, to_rgba  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from shapely.geometry import shape  # noqa: E402
from skyfield.api import wgs84  # noqa: E402

from ..mabims_astro import _eph  # noqa: E402
from ..mabims_sites import _refraction_deg_arr  # noqa: E402
from . import astrocache  # noqa: E402
from .chart import (  # noqa: E402
    GREG_MONTHS_ID,
    LOGO_PATH,
    _draw_header,
    _fit_text,
    _fmt_alt,
    _fmt_elong,
    _palette,
    _txt,
    _vgrad,
    font,
)

API_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = API_DIR / "data"
GEO_DIR = DATA_DIR / "geo"
POINTS_PATH = DATA_DIR / "map_points.json"

ALT_MIN = 3.0
ELONG_MIN = 6.4
SUNSET_ALT = -0.8333

# ── layout (mirrors chart.py) ──
W, H = 720, 1280
HORIZON_Y = int(H * 0.55)          # 704 — same ground line as the viz
BLOCK_TOP = 120                    # map starts just under the subtitle
LEGEND_H = 44                      # legend strip overlaid at the block bottom
MAP_H = HORIZON_Y - BLOCK_TOP      # 584 = viz sky-graphic height

# ── palette ──
OCEAN = "#141c30"
WORLD_LAND = "#2b3548"
WORLD_EDGE = "#3f4b64"
LAND = "#3b465e"
LAND_EDGE = "#5d6a86"
PROV = "#7d89a6"
GRAT = "#8a93a8"
YELLOW = "#fecf46"
GREEN = "#7ed957"
GRAY = "#6b7280"
CREAM = "#f5e9d0"
ORANGE = "#ff9f43"
PURPLE = "#c86bff"
PANEL = "#241a35"

LON0, LON1 = 94.0, 142.0
CENTER_LAT = -2.5

# World minimap: coarse real-sunset grid; only the visible region is filled.
GLOBAL_STEP = 3.0
GLOBAL_LAT = 60.0


# ───────────────────────── cached inputs ─────────────────────────
@lru_cache(maxsize=1)
def _points() -> tuple[tuple[str, float, float], ...]:
    raw = json.loads(POINTS_PATH.read_text(encoding="utf-8"))
    return tuple((p["name"], float(p["lat"]), float(p["lon"])) for p in raw["points"])


@lru_cache(maxsize=1)
def _boundary():
    return shape(
        json.loads((GEO_DIR / "indonesia_boundary.geojson").read_text(encoding="utf-8"))[
            "features"
        ][0]["geometry"]
    )


@lru_cache(maxsize=2)
def _world_features(include_indonesia: bool = False):
    raw = json.loads((GEO_DIR / "ne_110m_admin_0_countries.geojson").read_text(encoding="utf-8"))
    out = []
    for f in raw["features"]:
        name = f["properties"].get("ADMIN") or f["properties"].get("name")
        if name == "Indonesia" and not include_indonesia:
            continue
        out.append(shape(f["geometry"]))
    return tuple(out)


@lru_cache(maxsize=1)
def _province_rings():
    raw = json.loads((GEO_DIR / "indonesia_provinces_raw.geojson").read_text(encoding="utf-8"))
    rings: list = []
    for f in raw["features"]:
        g = shape(f["geometry"])
        parts = g.geoms if g.geom_type == "MultiPolygon" else [g]
        rings.extend(np.asarray(p.exterior.coords) for p in parts)
    return tuple(rings)


# ───────────────────────── astronomy ─────────────────────────
def _compute(lat: np.ndarray, lon: np.ndarray, evening: date, iters: int = 3):
    eph = _eph()
    ts, earth, sun, moon = eph.ts, eph._earth, eph._sun, eph._moon
    obs = earth + wgs84.latlon(lat, lon)
    jd = ts.utc(*evening.timetuple()[:3]).tt + (18.0 - lon / 15.0) / 24.0
    dt = 60 / 86400.0

    def salt(j):
        return obs.at(ts.tt_jd(j)).observe(sun).apparent().altaz()[0].degrees

    for _ in range(iters):
        a = salt(jd)
        jd = jd - (a - SUNSET_ALT) / ((salt(jd + dt) - a) / dt)
    t = ts.tt_jd(jd)
    alt = obs.at(t).observe(moon).apparent().altaz()[0].degrees
    alt = alt + _refraction_deg_arr(alt)
    elong = earth.at(t).observe(sun).apparent().separation_from(
        earth.at(t).observe(moon).apparent()
    ).degrees
    return alt, elong


def _grid(evening: date, step: float, lat0: float, lat1: float, lon0: float, lon1: float):
    lats = np.linspace(lat0, lat1, int((lat1 - lat0) / step) + 1)
    lons = np.linspace(lon0, lon1, int((lon1 - lon0) / step) + 1)
    lo, la = np.meshgrid(lons, lats)

    # read-through cache: geometry is deterministic, so the kind encodes it
    kind_base = f"mapgrid{step:g}:{lat0:.3f}:{lat1:.3f}:{lon0:.3f}:{lon1:.3f}"
    altg_c = astrocache.load(evening, kind_base + ":alt")
    elongg_c = astrocache.load(evening, kind_base + ":elong")
    if altg_c is not None and elongg_c is not None:
        return lo, la, altg_c, elongg_c

    alt, elong = _compute(la.ravel(), lo.ravel(), evening)
    nlat, nlon = len(lats), len(lons)
    return lo, la, alt.reshape(nlat, nlon), elong.reshape(nlat, nlon)


# ───────────────────────── map band ─────────────────────────
@lru_cache(maxsize=4)
def _buffered_boundary(deg: float):
    """The expensive part of the Indonesia clip (shapely buffer, ~8 s).
    Deterministic per deg — built once per process, reused by every render."""
    buf = _boundary().buffer(deg)
    parts = buf.geoms if buf.geom_type == "MultiPolygon" else [buf]
    verts_list: list = []
    codes_list: list = []
    for p in parts:
        xy = np.asarray(p.exterior.coords)
        verts_list.append(xy)
        codes_list.append([MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2) + [MplPath.CLOSEPOLY])
    return tuple(verts_list), tuple(codes_list)


def _buffer_patch(boundary, deg, ax):
    verts_all, codes_all = _buffered_boundary(deg)
    verts = [v for pair in verts_all for v in pair]
    codes = [node for pair in codes_all for node in pair]
    return PathPatch(MplPath(verts, codes), transform=ax.transData, facecolor="none", edgecolor="none")


def _fill_geom(ax, geom, **kw):
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for p in parts:
        x, y = p.exterior.xy
        ax.fill(x, y, **kw)


def _outline_geom(ax, geom, **kw):
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for p in parts:
        x, y = p.exterior.xy
        ax.plot(x, y, **kw)


@lru_cache(maxsize=32)
def _global_visibility(evening: date) -> np.ndarray:
    """Low-res world grid of the verdict at each cell's own local sunset.

    Real sunset solve (3 Newton steps is converged to <0.4 s / <0.001 deg).
    Latitude is clamped to +/-60 so polar day/night cells, which have no
    sunset to evaluate, are never computed. ~1 s for the whole globe; cached
    per evening both in-process and in the sqlite astro cache once primed.
    """
    lats = np.arange(-GLOBAL_LAT, GLOBAL_LAT + GLOBAL_STEP, GLOBAL_STEP)
    lons = np.arange(-180.0, 180.0 + GLOBAL_STEP, GLOBAL_STEP)
    lo, la = np.meshgrid(lons, lats)

    verdict_c = astrocache.load(evening, "world3:verdict")
    if verdict_c is not None:
        return verdict_c

    alt, elong = _compute(la.ravel(), lo.ravel(), evening, iters=3)
    return ((alt >= ALT_MIN) & (elong >= ELONG_MIN)).reshape(la.shape).astype(float)


def _world_minimap(ax, evening: date) -> None:
    """Birds-eye inset: the alt-3/elong-6.4 region around the globe."""
    ins = ax.inset_axes([0.028, 0.135, 0.205, 0.13], transform=ax.transAxes, zorder=13)
    ins.set_facecolor(OCEAN)
    ins.imshow(
        _global_visibility(evening),
        extent=(-180.0, 180.0, -GLOBAL_LAT, GLOBAL_LAT),
        origin="lower",
        cmap=ListedColormap([(0.0, 0.0, 0.0, 0.0), to_rgba(YELLOW, 0.35)]),
        interpolation="nearest",
        aspect="auto",
        zorder=1,
    )
    for geom in _world_features(include_indonesia=True):
        _outline_geom(ins, geom, color="#c9d2e0", lw=0.22, alpha=0.45, zorder=2)
    ins.set_xlim(-180.0, 180.0)
    ins.set_ylim(-90.0, 90.0)
    ins.set_aspect("equal")
    ins.set_xticks([])
    ins.set_yticks([])
    for spine in ins.spines.values():
        spine.set_color(WORLD_EDGE)
        spine.set_linewidth(0.8)


def _render_map(lo, la, altg, elongg, pts, alt, elong, hero, bounds, evening,
                px=(2160, int(2160 * MAP_H / W)), dpi=300):
    lon0, lon1, lat0, lat1 = bounds
    margin = np.minimum(altg - ALT_MIN, elongg - ELONG_MIN)
    Wp, Hp = px
    fig = plt.figure(figsize=(Wp / dpi, Hp / dpi), dpi=dpi)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(OCEAN)

    boundary = _boundary()
    clip = _buffer_patch(boundary, 2.0, ax)

    for geom in _world_features():
        _fill_geom(ax, geom, facecolor=WORLD_LAND, edgecolor=WORLD_EDGE, linewidth=0.2, zorder=1)
    _fill_geom(ax, boundary, facecolor=LAND, edgecolor=LAND_EDGE, linewidth=0.25, zorder=2)

    if _province_rings():
        ax.add_collection(
            LineCollection(list(_province_rings()), colors=[PROV], linewidths=0.3,
                           alpha=0.22, zorder=3)
        )

    for lon in range(95, 142, 5):
        ax.plot([lon, lon], [lat0, lat1], color=GRAT, lw=0.3, ls=(0, (1, 3)), alpha=0.3, zorder=4)
    for lat in range(-20, 17, 5):
        ax.plot([lon0, lon1], [lat, lat], color=GRAT, lw=0.3, ls=(0, (1, 3)), alpha=0.3, zorder=4)

    if margin.max() > 0:
        cf = ax.contourf(lo, la, margin, levels=[0, margin.max() + 1e-9], colors=[YELLOW],
                         alpha=0.18, zorder=5)
        cb = ax.contour(lo, la, margin, levels=[0], colors=[YELLOW], linewidths=1.6, zorder=7)
        for cs in (cf, cb):
            cs.set_clip_path(clip)
    # Isolines are deliberately NOT clipped to the Indonesia buffer: clipping
    # cut them mid-run and left clabel text floating where the line vanished.
    # Letting them run to the map edge reads as continuous isolines instead.
    ca = ax.contour(lo, la, altg, levels=[ALT_MIN], colors=[ORANGE], linewidths=0.9,
                    linestyles="dashed", alpha=0.95, zorder=6)
    ce = ax.contour(lo, la, elongg, levels=[ELONG_MIN], colors=[PURPLE], linewidths=0.9,
                    linestyles="dashed", alpha=0.95, zorder=6)
    ax.clabel(ca, fmt="alt 3\u00b0", fontsize=5.4, colors=ORANGE, inline=True)
    ax.clabel(ce, fmt="el 6.4\u00b0", fontsize=5.4, colors=PURPLE, inline=True)

    seen = (alt >= ALT_MIN) & (elong >= ELONG_MIN)
    for i, (_n, latp, lonp) in enumerate(pts):
        if seen[i]:
            ax.scatter(lonp, latp, s=32, c=GREEN, edgecolors="#20301a", linewidths=0.5, zorder=9)
        else:
            ax.scatter(lonp, latp, s=26, facecolors="none", edgecolors=GRAY, linewidths=0.9, zorder=8)

    bn, blat, blon, halt, helong = hero
    ax.scatter(blon, blat, s=150, facecolors="none", edgecolors=YELLOW, linewidths=1.7, zorder=11)
    ax.scatter(blon, blat, s=320, facecolors="none", edgecolors=YELLOW, linewidths=0.9,
               alpha=0.55, zorder=11)
    dy = -3.6 if blat > 1.5 else 3.6
    dx = 2.2 if blon < 110 else -2.2
    ax.annotate(
        f"{bn}\n{_fmt_alt(halt)} / {_fmt_elong(helong)}",
        xy=(blon, blat), xytext=(blon + dx, blat + dy), color=CREAM, fontsize=11.5,
        ha="left" if dx > 0 else "right", va="center",
        bbox=dict(boxstyle="round,pad=0.45", fc=PANEL, ec=YELLOW, lw=1.0, alpha=0.95),
        arrowprops=dict(arrowstyle="-", color=YELLOW, lw=0.8), zorder=12,
    )

    _world_minimap(ax, evening)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=OCEAN)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


# ───────────────────────── card ─────────────────────────
def _legend(img, pal, y, h):
    band = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle([0, 0, W, h], fill=(14, 20, 40, 200))
    img.alpha_composite(band, (0, y))

    d = ImageDraw.Draw(img)
    f = font(15)
    fg = pal["muted"]
    cy = y + h // 2
    x: float = 36

    d.ellipse([x, cy - 7, x + 14, cy + 7], fill=GREEN)
    d.text((x + 22, cy), "memenuhi", font=f, fill=fg, anchor="lm")
    x += 22 + d.textlength("memenuhi", font=f) + 34

    d.ellipse([x, cy - 7, x + 14, cy + 7], outline=GRAY, width=2)
    d.text((x + 22, cy), "tidak", font=f, fill=fg, anchor="lm")
    x += 22 + d.textlength("tidak", font=f) + 34

    d.rectangle([x, cy - 7, x + 22, cy + 7], fill=YELLOW)
    d.text((x + 30, cy), "wilayah hilal", font=f, fill=fg, anchor="lm")
    x += 30 + d.textlength("wilayah hilal", font=f) + 34

    for k in range(0, 20, 6):
        d.line([(x + k, cy), (x + k + 3, cy)], fill=ORANGE, width=2)
    d.text((x + 28, cy), "alt 3\u00b0", font=f, fill=fg, anchor="lm")
    x += 28 + d.textlength("alt 3\u00b0", font=f) + 34

    for k in range(0, 20, 6):
        d.line([(x + k, cy), (x + k + 3, cy)], fill=PURPLE, width=2)
    d.text((x + 28, cy), "elong 6.4\u00b0", font=f, fill=fg, anchor="lm")


def _render_card(map_img, hero, n_total, n_seen,
                 vis_month, vis_year, greg, hijri):
    pal = _palette()
    card = _vgrad(W, H, [(0.0, (31, 18, 53)), (0.45, (94, 44, 74)),
                         (0.72, (196, 96, 66)), (0.86, (242, 166, 90)), (1.0, (52, 30, 40))])

    band = np.asarray(map_img.resize((W, MAP_H), Image.Resampling.LANCZOS).convert("RGB")).astype(float)
    bg = np.asarray(card.convert("RGB")).astype(float)
    fade = 140
    for i in range(fade):
        t = i / fade
        mw = t * t * (3 - 2 * t)
        band[i] = band[i] * mw + bg[BLOCK_TOP + i] * (1 - mw)
    card.paste(Image.fromarray(band.astype("uint8")), (0, BLOCK_TOP))
    d = ImageDraw.Draw(card)

    pts: list[tuple[float, float]] = [(0, HORIZON_Y + 2)]
    for xx in range(0, W + 24, 24):
        hh = 20 + 14 * np.sin(xx / 97.0) + 9 * np.sin(xx / 33.0 + 1.7)
        pts.append((xx, HORIZON_Y - max(6.0, hh)))
    pts += [(W, HORIZON_Y + 2), (W, H), (0, H)]
    d.polygon(pts, fill=pal["ground"])
    d.line([0, HORIZON_Y, W, HORIZON_Y], fill=pal["horizon"], width=2)

    _legend(card, pal, HORIZON_Y - LEGEND_H, LEGEND_H)

    d = ImageDraw.Draw(card)
    _draw_header(d, vis_month, greg, hijri, pal)

    card_y = HORIZON_Y + 30
    card_h = H - card_y - 52
    overlay = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [32, card_y, W - 32, card_y + card_h], radius=24, fill=pal["card"] + (215,))
    card.alpha_composite(overlay)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([32, card_y, W - 32, card_y + card_h], radius=24,
                        outline=pal["border"], width=1)

    x0, y0, x1, y1 = 64, card_y + 26, W - 64, card_y + card_h - 20
    f_lab = font(18)
    f_head = font(28, True)
    f_min = font(36)
    f_value = font(36, True)
    xr = x1 - 8
    xm = x0 + (x1 - x0) * 0.46
    chip_w, chip_h = 116, 44

    _txt(d, (x0, y0), "PARAMETER", f_head, pal["muted"])
    _txt(d, (xm + 56, y0), "MIN. MABIMS", f_head, pal["muted"], anchor="ma")
    _txt(d, (xr, y0), "STATUS", f_head, pal["muted"], anchor="ra")
    d.line([x0, y0 + 40, x1, y0 + 40], fill=pal["border"], width=1)

    alt_b, elong_b = hero[3], hero[4]
    crit = [
        ("ALT. BULAN", _fmt_alt(alt_b), "3.0\u00b0", alt_b >= ALT_MIN),
        ("ELONGASI", _fmt_elong(elong_b), "6.4\u00b0", elong_b >= ELONG_MIN),
    ]
    chips = Image.new("RGBA", card.size, (0, 0, 0, 0))
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
    card.alpha_composite(chips)
    d = ImageDraw.Draw(card)

    yy += 2
    d.line([x0, yy, x1, yy], fill=pal["border"], width=1)
    yy += 14
    rows = [
        ("TITIK PENGAMAT", hero[0].split("/")[0].strip()),
        ("TITIK MEMENUHI", f"{n_seen}/{n_total}"),
        ("TITIK TIDAK MEMENUHI", f"{n_total - n_seen}/{n_total}"),
    ]
    simple_h = (y1 - yy) // len(rows)
    for i, (lab, val) in enumerate(rows):
        ry = yy + i * simple_h
        if i:
            d.line([x0, ry, x1, ry], fill=(66, 40, 60), width=1)
        cy = ry + simple_h // 2
        lab_w = d.textlength(lab, font=f_head)
        max_val_w = xr - (x0 + lab_w + 16)
        _txt(d, (x0, cy), lab, f_head, pal["muted"], anchor="lm")
        _txt(d, (xr, cy), _fit_text(d, val, f_value, max_val_w), f_value, pal["text"], anchor="rm")

    logo = Image.open(LOGO_PATH).convert("RGBA")
    lh = 40
    lw = int(logo.width * lh / logo.height)
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    card.alpha_composite(logo, ((W - lw) // 2, H - lh - 10))
    return card


def map_png_bytes(*, evening: date, vis_month: str, vis_year: int, hijri_label: str,
                  hero: tuple[str, float, float, float, float],
                  grid_deg: float = 0.25) -> bytes:
    """Render the map card.

    ``hero`` is the authoritative deciding point from the 25-site model
    ``(name, lat, lon, alt_refracted_deg, elong_deg)`` — it drives the ringed
    marker, callout, criteria table and the ``TITIK PENGAMAT`` row. The 95
    display points drive only the dots and the memenuhi / tidak counts.
    """
    pts = _points()
    lat = np.array([p[1] for p in pts])
    lon = np.array([p[2] for p in pts])

    alt_c = astrocache.load(evening, "map_points:alt")
    elong_c = astrocache.load(evening, "map_points:elong")
    if alt_c is not None and elong_c is not None:
        alt, elong = alt_c, elong_c
    else:
        alt, elong = _compute(lat, lon, evening)
    seen = (alt >= ALT_MIN) & (elong >= ELONG_MIN)

    lat_span = (LON1 - LON0) * MAP_H / W
    lat0, lat1 = CENTER_LAT - lat_span / 2, CENTER_LAT + lat_span / 2
    bounds = (LON0, LON1, lat0, lat1)
    px = (2160, int(round(2160 * MAP_H / W)))

    lo, la, altg, elongg = _grid(evening, grid_deg, lat0, lat1, LON0, LON1)
    mimg = _render_map(lo, la, altg, elongg, pts, alt, elong, hero, bounds, evening, px)

    greg = f"{evening.day} {GREG_MONTHS_ID[evening.month]} {evening.year}"
    card = _render_card(mimg, hero, len(pts), int(seen.sum()),
                        vis_month, vis_year, greg, hijri_label)
    buf = io.BytesIO()
    card.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
