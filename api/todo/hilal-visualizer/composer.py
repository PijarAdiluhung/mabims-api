"""
Sky Finding Chart — shows where to look for the hilal.

A simple sky map centered on the western horizon at sunset.
Sun and moon are placed at their correct altitude and azimuth.
Everything to scale. No decorative moon rendering (v1).
"""

import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moontex import MoonTex
import numpy as np


# ── Colors ──
SKY_TOP = (25, 35, 65)           # Muted twilight blue (not too dark)
SKY_MID = (60, 70, 95)           # Mid sky
SKY_HORIZON = (160, 100, 55)     # Warm sunset glow
GROUND = (20, 22, 18)            # Dark ground
HORIZON_LINE = (180, 140, 80)    # Horizon line color
SUN_COLOR = (255, 200, 50)       # Sun marker
MOON_COLOR = (220, 220, 230)     # Moon marker
GRID_COLOR = (40, 50, 70)        # Grid lines
GRID_TEXT = (80, 90, 110)        # Grid labels
TEXT_COLOR = (200, 200, 210)     # Main text
TEXT_DIM = (120, 125, 140)       # Dimmer text


def _load_font(size: int, bold: bool = False):
    """Load a truetype font across Linux/Windows, falling back to PIL default."""
    names = (
        ["DejaVuSans-Bold.ttf", "arialbd.ttf", "segoeuib.ttf"]
        if bold
        else ["DejaVuSans.ttf", "arial.ttf", "segoeui.ttf"]
    )
    dirs = [
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/TTF/",
        "C:/Windows/Fonts/",
    ]
    for directory in dirs:
        for name in names:
            try:
                return ImageFont.truetype(directory + name, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def sky_chart(
    width: int,
    height: int,
    sun_az: float,      # Sun azimuth (degrees from North)
    sun_alt: float,     # Sun altitude (degrees, negative = below horizon)
    moon_az: float,     # Moon azimuth
    moon_alt: float,    # Moon altitude
    moon_pa: float = 0,  # Position angle (for crescent orientation)
    moon_illum: float = 0.01,
    moon_elong: float = 0,  # Elongation (for phase rendering)
    phase_illum: float = None,  # Illumination for phase box (use next day's if provided)
    # View parameters
    center_az: float = None,  # Center of view (default: sun azimuth)
    az_range: float = 60,     # Total azimuth range to show (degrees)
    alt_min: float = -15,     # Minimum altitude (below horizon)
    alt_max: float = 45,      # Maximum altitude
    # Labels
    show_grid: bool = True,
    show_compass: bool = True,
    # Info overlay
    location_name: str = '',
    gregorian_date: str = '',
    hijri_label: str = '',
    sunset_time: str = '',
    moonset_time: str = '',
    lunar_age: float = None,
) -> Image.Image:
    """
    Generate a sky finding chart showing sun and moon positions.

    Args:
        width, height: Canvas size in pixels
        sun_az, sun_alt: Sun position
        moon_az, moon_alt: Moon position
        moon_pa: Position angle for crescent orientation
        moon_illum: Illumination fraction (for crescent rendering)
        center_az: Azimuth to center the view on (default: sun azimuth)
        az_range: Total azimuth span in degrees
        alt_min, alt_max: Altitude range in degrees

    Returns:
        RGBA Image
    """
    # ── Determine view bounds ──
    if center_az is None:
        center_az = sun_az

    az_left = center_az - az_range / 2
    az_right = center_az + az_range / 2

    # ── Pixel mapping functions ──
    # X: azimuth → pixels (azimuth increases LEFT when looking west)
    # Actually, let's think about this from the observer's perspective:
    # Looking west (toward sunset), South is to the LEFT, North is to the RIGHT
    # So azimuth increases to the LEFT
    # But for simplicity, let's just map: left = az_left, right = az_right
    # The viewer will understand from the compass labels

    def az_to_x(az):
        """Convert azimuth to x pixel coordinate."""
        # Normalize azimuth relative to center
        frac = (az - az_left) / az_range
        return int(frac * width)

    def alt_to_y(alt):
        """Convert altitude to y pixel coordinate (y increases downward)."""
        # altitude range: alt_min to alt_max
        # y=0 at top (alt_max), y=height at bottom (alt_min)
        frac = (alt_max - alt) / (alt_max - alt_min)
        return int(frac * height)

    def deg_to_px(deg):
        """Convert degrees to pixel distance."""
        # Azimuth and altitude should have same scale
        px_per_deg_x = width / az_range
        px_per_deg_y = height / (alt_max - alt_min)
        # Use average for consistent scaling
        return (px_per_deg_x + px_per_deg_y) / 2

    px_per_deg = deg_to_px(1)

    # ── True angular sizes (in degrees) ──
    SUN_ANGULAR_DIAMETER = 0.53   # degrees
    MOON_ANGULAR_DIAMETER = 0.52  # degrees (average, varies 0.49-0.55)

    sun_radius_px = max(3, int((SUN_ANGULAR_DIAMETER / 2) * px_per_deg))
    moon_radius_px = max(3, int((MOON_ANGULAR_DIAMETER / 2) * px_per_deg))

    # ── Create the canvas ──
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)

    # ── Draw sky gradient ──
    horizon_y = alt_to_y(0)  # Y position of the horizon

    for y in range(height):
        alt = alt_max - (y / height) * (alt_max - alt_min)

        if alt >= 0:
            # Sky: gradient from horizon to zenith
            t = alt / alt_max  # 0 at horizon, 1 at top
            r = int(SKY_HORIZON[0] + (SKY_TOP[0] - SKY_HORIZON[0]) * t)
            g = int(SKY_HORIZON[1] + (SKY_TOP[1] - SKY_HORIZON[1]) * t)
            b = int(SKY_HORIZON[2] + (SKY_TOP[2] - SKY_HORIZON[2]) * t)
        else:
            # Ground: darker below horizon
            t = min(1, abs(alt) / 15)  # 0 at horizon, 1 at -15°
            r = int(SKY_HORIZON[0] * 0.4 + (GROUND[0] - SKY_HORIZON[0] * 0.4) * t)
            g = int(SKY_HORIZON[1] * 0.4 + (GROUND[1] - SKY_HORIZON[1] * 0.4) * t)
            b = int(SKY_HORIZON[2] * 0.4 + (GROUND[2] - SKY_HORIZON[2] * 0.4) * t)

        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # ── Horizon line ──
    draw.line([(0, horizon_y), (width, horizon_y)],
              fill=HORIZON_LINE, width=2)

    # ── Grid lines (altitude) ──
    # Grids removed per request

    # ── Compass directions (at horizon) ──
    if show_compass:
        font_compass = _load_font(14, bold=True)
        font_small = _load_font(9)

        # Determine which cardinal directions are visible
        compass_labels = {
            0: 'N', 45: 'NE', 90: 'E', 135: 'SE',
            180: 'S', 225: 'SW', 270: 'W', 315: 'NW',
        }

        for az_label, name in compass_labels.items():
            # Wrap azimuth to match our view
            test_az = az_label
            # Check if within view (handle wrapping)
            if az_left <= test_az <= az_right:
                x = az_to_x(test_az)
                if 20 < x < width - 20:
                    # Draw compass tick and label
                    draw.line([(x, horizon_y - 5), (x, horizon_y + 5)],
                              fill=HORIZON_LINE, width=2)
                    bbox = draw.textbbox((0, 0), name, font=font_compass)
                    tw = bbox[2] - bbox[0]
                    draw.text((x - tw // 2, horizon_y + 8), name,
                              fill=HORIZON_LINE, font=font_compass)

        # Also show degree markers at bottom
        for az_deg in range(int(az_left), int(az_right) + 1, 10):
            x = az_to_x(az_deg)
            if 10 < x < width - 10:
                draw.line([(x, horizon_y + 2), (x, horizon_y + 6)],
                          fill=(120, 100, 60), width=1)

    # ── Sun marker (to scale) ──
    sun_x = az_to_x(sun_az)
    sun_y = alt_to_y(sun_alt)

    # Sun disc (TRUE SCALE)
    draw.ellipse(
        [sun_x - sun_radius_px, sun_y - sun_radius_px,
         sun_x + sun_radius_px, sun_y + sun_radius_px],
        fill=SUN_COLOR
    )

    # If sun is below horizon, draw dotted line from horizon to sun
    if sun_alt < 0:
        _draw_dotted_line(draw, sun_x, horizon_y, sun_x, sun_y,
                          color=(200, 150, 50, 180), dash_len=6, gap_len=4)

    # Sun crosshairs (to mark exact position)
    _draw_crosshair(draw, sun_x, sun_y, size=max(14, sun_radius_px * 2), color=(255, 200, 50, 200))

    # ── Moon marker (to scale) ──
    moon_x = az_to_x(moon_az)
    moon_y = alt_to_y(moon_alt)

    # Moon disc (TRUE SCALE)
    draw.ellipse(
        [moon_x - moon_radius_px, moon_y - moon_radius_px,
         moon_x + moon_radius_px, moon_y + moon_radius_px],
        fill=MOON_COLOR
    )

    # Moon crosshair
    _draw_crosshair(draw, moon_x, moon_y, size=max(12, moon_radius_px * 2), color=(180, 180, 200, 200))

    # If moon is below horizon, draw dotted line
    if moon_alt < 0:
        _draw_dotted_line(draw, moon_x, horizon_y, moon_x, moon_y,
                          color=(150, 150, 180, 150), dash_len=6, gap_len=4)

    # ── Draw angular separation line between sun and moon ──
    # This helps visualize the elongation
    if (sun_alt > -5 or moon_alt > -5):  # Only if at least one is near horizon
        draw.line([(sun_x, sun_y), (moon_x, moon_y)],
                  fill=(100, 100, 120, 100), width=1)

    # ── Labels for sun and moon ──
    font_label = _load_font(12)

    # Sun label
    draw.text((sun_x + sun_radius_px + 6, sun_y - 6), "Sun", fill=SUN_COLOR, font=font_label)
    draw.text((sun_x + sun_radius_px + 6, sun_y + 6),
              f"alt {sun_alt:+.1f}° az {sun_az:.1f}°",
              fill=(200, 170, 80), font=font_small)

    # Moon label
    draw.text((moon_x + moon_radius_px + 6, moon_y - 6), "Moon", fill=MOON_COLOR, font=font_label)
    draw.text((moon_x + moon_radius_px + 6, moon_y + 6),
              f"alt {moon_alt:+.1f}° az {moon_az:.1f}°",
              fill=(160, 160, 180), font=font_small)

    # ── Elongation annotation ──
    elong = math.sqrt((sun_az - moon_az)**2 + (sun_alt - moon_alt)**2)
    mid_x = (sun_x + moon_x) // 2
    mid_y = (sun_y + moon_y) // 2
    draw.text((mid_x - 20, mid_y - 15),
              f"Δ {elong:.1f}°",
              fill=(120, 120, 140), font=font_small)

    # ── Text info overlay (top-left) ──
    font_info = _load_font(13)
    font_info_bold = _load_font(13, bold=True)

    info_lines = []
    if hijri_label:
        info_lines.append(hijri_label)
    if gregorian_date:
        info_lines.append(gregorian_date)
    if location_name:
        info_lines.append(location_name)

    # Astronomy details
    details = []
    if sunset_time:
        details.append(f"Sunset: {sunset_time}")
    if moonset_time:
        details.append(f"Moonset: {moonset_time}")
    if lunar_age is not None:
        details.append(f"Moon age: {lunar_age:.1f}d")
    details.append(f"Moon alt: {moon_alt:+.1f}° | Elong: {moon_elong:.1f}°")
    info_lines.append("  ".join(details))

    # Draw info box (top-left, semi-transparent bg)
    if info_lines:
        line_h = 18
        box_pad = 12
        max_w = max(draw.textbbox((0, 0), l, font=font_info)[2] for l in info_lines)
        box_w = max_w + box_pad * 2
        box_h = len(info_lines) * line_h + box_pad * 2

        # Semi-transparent background
        info_bg = Image.new('RGBA', (box_w, box_h), (10, 12, 20, 180))
        canvas.paste(info_bg, (10, 10), info_bg)
        draw = ImageDraw.Draw(canvas)  # Refresh draw after paste

        for i, line in enumerate(info_lines):
            f = font_info_bold if i == 0 else font_info
            draw.text((10 + box_pad, 10 + box_pad + i * line_h),
                      line, fill=TEXT_COLOR, font=f)

    # ── Moon phase box (bottom-right) ──
    phase_box_size = 80
    phase_box_pad = 15
    phase_box_x = width - phase_box_size - phase_box_pad
    phase_box_y = height - phase_box_size - phase_box_pad

    # Black background for moon phase
    phase_bg = Image.new('RGBA', (phase_box_size, phase_box_size), (5, 5, 10, 220))
    canvas.paste(phase_bg, (phase_box_x, phase_box_y), phase_bg)
    draw = ImageDraw.Draw(canvas)

    # Border
    draw.rectangle(
        [phase_box_x, phase_box_y,
         phase_box_x + phase_box_size - 1, phase_box_y + phase_box_size - 1],
        outline=(60, 65, 75), width=1
    )

    # Draw the moon phase inside the box
    if moon_elong < 5.5:
        # Too close to sun — pitch black (invisible)
        pass
    else:
        # Draw moon phase — use phase_illum for better visibility
        dx = sun_x - moon_x
        dy = sun_y - moon_y
        angle_to_sun = math.degrees(math.atan2(dx, -dy))

        _draw_moon_phase(
            draw, canvas,
            cx=phase_box_x + phase_box_size // 2,
            cy=phase_box_y + phase_box_size // 2,
            radius=phase_box_size // 2 - 8,
            illumination=phase_illum if phase_illum is not None else moon_illum,
            angle_to_sun=angle_to_sun,
            position_angle=moon_pa,
        )

    # Elongation label under the box
    font_tiny = _load_font(10)

    if moon_elong < 5.5:
        phase_label = "NOT VISIBLE"
        phase_color = (180, 80, 80)
    else:
        phase_label = f"Elong: {moon_elong:.1f}°"
        phase_color = TEXT_DIM

    label_bbox = draw.textbbox((0, 0), phase_label, font=font_tiny)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text(
        (phase_box_x + (phase_box_size - label_w) // 2, phase_box_y + phase_box_size + 3),
        phase_label, fill=phase_color, font=font_tiny
    )

    return canvas


def _draw_moon_phase(draw, canvas, cx, cy, radius, illumination, angle_to_sun=0, position_angle=0):
    """
    Draw a realistic moon phase using MoonTex.
    Rotated to correct position angle.
    """
    if illumination <= 0.001:
        return

    # MoonTex phase_offset: 0 = full, 0.5 = half, 1 = new
    # Convert illumination (0-1) to phase_offset (1-0)
    phase_offset = 1.0 - illumination

    # Generate moon texture (with transparent background)
    moon_size = radius * 2 + 8  # Extra padding for rotation
    moon = MoonTex(
        image_size=moon_size,
        transparent_background=True,
        shadow_factor=0.0,  # No shadow, we handle illumination ourselves
    )

    # generate() returns PIL Image directly
    moon_img = moon.generate(phase_offset=phase_offset)

    # Rotate to correct position angle
    # -PA+90 was 180° off, so add 180°: -PA+270 = -PA-90
    rotation = -position_angle - 90
    moon_img = moon_img.rotate(rotation, resample=Image.BICUBIC, expand=False)

    # Resize to final size
    final_size = radius * 2
    moon_img = moon_img.resize((final_size, final_size), Image.LANCZOS)

    # Center in canvas
    offset_x = cx - final_size // 2
    offset_y = cy - final_size // 2

    # Paste with alpha
    canvas.paste(moon_img, (offset_x, offset_y), moon_img)


def _draw_dotted_line(draw, x1, y1, x2, y2, color, dash_len=6, gap_len=4):
    """Draw a dotted line between two points."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx**2 + dy**2)
    if length == 0:
        return

    dx_norm = dx / length
    dy_norm = dy / length

    pos = 0
    drawing = True
    while pos < length:
        seg_len = dash_len if drawing else gap_len
        end_pos = min(pos + seg_len, length)

        if drawing:
            sx = int(x1 + dx_norm * pos)
            sy = int(y1 + dy_norm * pos)
            ex = int(x1 + dx_norm * end_pos)
            ey = int(y1 + dy_norm * end_pos)
            draw.line([(sx, sy), (ex, ey)], fill=color, width=1)

        pos = end_pos
        drawing = not drawing


def _draw_crosshair(draw, x, y, size=15, color=(200, 200, 200, 150)):
    """Draw crosshair markers at a point."""
    half = size // 2
    # Horizontal
    draw.line([(x - half, y), (x + half, y)], fill=color, width=1)
    # Vertical
    draw.line([(x, y - half), (x, y + half)], fill=color, width=1)
    # Center dot
    draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color)


# ── Quick test ──
if __name__ == '__main__':
    # Test with Ramadhan data
    chart = sky_chart(
        width=1000,
        height=600,
        sun_az=258.0,
        sun_alt=-0.8,
        moon_az=257.0,
        moon_alt=8.7,
        moon_illum=0.01,
        center_az=258.0,
        az_range=60,
        alt_min=-15,
        alt_max=40,
    )
    chart.save('output/test_chart.png')
    print("Saved: output/test_chart.png")
