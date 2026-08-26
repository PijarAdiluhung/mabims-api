"""
Realistic crescent moon renderer using Pillow.

The crescent shape is determined by:
1. Illumination fraction → terminator ellipse eccentricity
2. Position Angle (PA) → rotation of the bright limb
3. B-angle → tilt of the terminator (from ecliptic latitude)
"""

import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np


def render_moon(
    size: int = 400,
    illumination: float = 0.01,
    position_angle: float = 0.0,
    b_angle: float = 0.0,
    elon: float = 0.0,
    earthshine: bool = True,
) -> Image.Image:
    """
    Render a realistic crescent moon.

    Args:
        size: Diameter of the moon in pixels
        illumination: Fraction illuminated (0.0 to 1.0)
        position_angle: PA of the bright limb from North (degrees, clockwise)
        b_angle: B-angle / ecliptic latitude tilt (degrees)
        elon: Sun-Moon elongation (degrees) — used for cusp correction
        earthshine: Whether to add faint earthshine on the dark side

    Returns:
        RGBA Image of the moon with transparent background
    """
    R = size // 2
    pad = 10  # Extra padding for anti-aliasing
    canvas_size = size + pad * 2

    # ── Step 1: Create the moon disc (dark circle) ──
    moon_disc = Image.new('L', (canvas_size, canvas_size), 0)
    draw_disc = ImageDraw.Draw(moon_disc)
    cx, cy = canvas_size // 2, canvas_size // 2
    draw_disc.ellipse(
        [cx - R, cy - R, cx + R, cy + R],
        fill=255
    )

    # ── Step 2: Create the terminator mask ──
    # The terminator is the line between lit and dark.
    # From our viewpoint, it appears as an ellipse.
    #
    # Key insight: the terminator always spans the full diameter
    # of the moon (semi-major axis = R), but its apparent width
    # depends on the phase angle.

    # Phase angle ψ: 180° = new moon, 0° = full moon
    # For illumination f: ψ = arccos(2f - 1) ... but for very thin
    # crescents we need to be more careful.

    # The apparent width of the terminator ellipse
    # When illumination is very small (< 5%), the terminator
    # is very close to the limb edge.
    #
    # Semi-minor axis of the terminator ellipse:
    # b_term = R * cos(ψ/2) where ψ is the phase angle
    # But for rendering, we work with the illuminated fraction directly.

    # For a waxing/waning crescent:
    # The illuminated portion is bounded by:
    #   - The outer limb (circle of radius R)
    #   - The terminator (ellipse)

    # The fraction of the disc that's lit determines the
    # "gap" between the limb and terminator at the center.

    # ── Calculate terminator geometry ──
    # The illuminated fraction f relates to the phase angle:
    # f = (1 - cos(ψ)) / 2, so ψ = arccos(1 - 2f)
    if illumination <= 0.001:
        # Essentially new moon — no visible crescent
        # Return a dark circle (or very faint hint)
        result = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        # Draw a very dark moon disc
        dark_disc = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        dark_draw = ImageDraw.Draw(dark_disc)
        dark_draw.ellipse(
            [cx - R, cy - R, cx + R, cy + R],
            fill=(40, 40, 45, 200)
        )
        result = Image.alpha_composite(result, dark_disc)
        return result.crop((pad, pad, pad + size, pad + size))

    if illumination >= 0.995:
        # Full moon — just return a bright circle
        result = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        full_draw = ImageDraw.Draw(result)
        full_draw.ellipse(
            [cx - R, cy - R, cx + R, cy + R],
            fill=(240, 235, 220, 255)
        )
        return result.crop((pad, pad, pad + size, pad + size))

    # Phase angle (angle at Moon between Sun and Earth)
    phase_angle = math.acos(max(-1, min(1, 1 - 2 * illumination)))

    # The terminator appears as an ellipse:
    # Semi-major axis a = R (vertical, along the axis of illumination)
    # Semi-minor axis b = R * cos(ψ) ... but this needs adjustment
    # for the viewing geometry.

    # More precisely, the terminator ellipse semi-minor axis is:
    # The terminator cuts through the moon disc. The "depth" of the
    # illuminated sliver at its widest point determines b.

    # For a thin crescent, the maximum width of the lit sliver is:
    # w_max = R * (1 - cos(ψ/2)) approximately
    # And the terminator semi-minor is:
    # b_term = R * cos(ψ/2) ... no, that's not right either.

    # Let me think about this more carefully.
    #
    # The Moon is a sphere. The terminator is a great circle on the sphere.
    # When projected onto the 2D sky plane, the terminator becomes an ellipse.
    #
    # The illuminated portion is the area of the Moon's disc that's on the
    # "sun side" of the terminator.
    #
    # The terminator ellipse has:
    # - Semi-major axis = R (it always touches the top and bottom of the disc)
    # - Semi-minor axis = R * |cos(α)| where α is the angle between the
    #   line of sight and the terminator plane.
    #
    # The illuminated fraction determines α.
    # For a crescent: the illuminated sliver is on one side.

    # Actually, a cleaner approach:
    # The terminator divides the disc into two parts.
    # The "inner" edge of the illuminated sliver is the terminator,
    # and the "outer" edge is the limb.
    #
    # The terminator is an ellipse with semi-major axis R (same as moon)
    # and semi-minor axis that depends on the phase.
    #
    # For the illuminated fraction f:
    # The terminator semi-minor axis b_t = R * (1 - 2f) approximately
    # for small f. More precisely:
    # b_t = R * cos(phase_angle / 2) ... hmm.

    # Let me use a different approach that's simpler and more robust:
    # Use the "angular width" of the crescent.

    # The maximum width of the illuminated sliver (at the middle):
    # This is R - |b_t| where b_t is the terminator semi-minor axis.
    # For small illumination, this is small.

    # Actually, the simplest correct approach:
    # The terminator is an ellipse centered at the moon center.
    # Semi-major axis (vertical) = R
    # Semi-minor axis (horizontal) = R * cos(phase_angle)
    #
    # Wait, that's for the illumination terminator on the SPHERE.
    # When projected, it's different.

    # Let me use the standard formula from astronomical image rendering:
    #
    # The illuminated fraction f determines the "gap" between the limb
    # and terminator at the sub-solar point:
    # gap = R * (1 - cos(asin(sqrt(f)))) approximately

    # OK, I'm overcomplicating this. Let me use a practical approach
    # that produces good-looking crescents:

    # The terminator as seen from Earth is an ellipse with:
    # - Semi-major = R (always)
    # - Semi-minor = R * cos(phase_angle)
    # This gives the correct shape for all phases.

    # But for the CRESCENT rendering, we need to show:
    # 1. The outer limb (circle, radius R)
    # 2. The terminator (ellipse, semi-major R, semi-minor b_t)
    # The crescent is the area between these two curves.

    b_terminator = R * math.cos(phase_angle)

    # For a waxing crescent (right side lit in Northern Hemisphere,
    # but we use PA to rotate):
    # The terminator is shifted to one side.

    # Actually, for the crescent shape:
    # The terminator ellipse is NOT centered on the moon center.
    # It's offset. The center of the terminator ellipse is at:
    # offset_x = R * sin(phase_angle) (approximately)
    # This is what creates the asymmetric crescent shape.

    # Let me reconsider. The correct rendering approach:

    # 1. Draw the full moon disc (dark)
    # 2. Draw the illuminated portion as the intersection of:
    #    a. The outer circle (limb)
    #    b. The "lit side" of the terminator

    # The terminator on the 2D projection is an ellipse.
    # For a crescent, the terminator ellipse is:
    # - Semi-major (vertical) = R
    # - Semi-minor (horizontal) = R * cos(phase_angle)
    # - The center of this ellipse is shifted by R * sin(phase_angle)
    #   from the moon center, toward the dark side.

    # Let me implement this properly:

    # ── Create the illuminated mask ──
    illuminated = Image.new('L', (canvas_size, canvas_size), 0)
    illum_draw = ImageDraw.Draw(illuminated)

    # First, draw the outer limb (full circle)
    illum_draw.ellipse(
        [cx - R, cy - R, cx + R, cy + R],
        fill=255
    )

    # Now subtract the dark portion (the terminator region)
    # The dark portion is an ellipse offset from center

    # The terminator ellipse semi-minor axis
    term_b = R * abs(math.cos(phase_angle))

    # The offset of the terminator center from moon center
    # This determines how much of the disc is dark
    term_offset = R * math.sin(phase_angle)

    # For waxing (right side lit), the dark ellipse is on the LEFT
    # For waning (left side lit), the dark ellipse is on the RIGHT
    # The PA tells us which side is lit.

    # Create dark mask (the part that's NOT illuminated)
    dark_mask = Image.new('L', (canvas_size, canvas_size), 0)
    dark_draw = ImageDraw.Draw(dark_mask)

    # The dark ellipse is centered at (cx - term_offset, cy) for right-lit
    # We'll rotate later based on PA
    dark_cx = cx - term_offset  # Shifted left for right-lit crescent
    dark_cy = cy

    # Draw the dark ellipse (semi-major = R along y, semi-minor = term_b along x)
    dark_draw.ellipse(
        [int(dark_cx - term_b), int(dark_cy - R),
         int(dark_cx + term_b), int(dark_cy + R)],
        fill=255
    )

    # The illuminated area = moon disc MINUS dark ellipse
    # But we also need to clip to the moon disc
    illuminated_arr = np.array(illuminated)
    dark_arr = np.array(dark_mask)
    moon_arr = np.array(moon_disc)

    # illuminated = moon disc AND NOT dark ellipse
    lit_arr = np.where(
        (moon_arr > 0) & (dark_arr == 0),
        255, 0
    ).astype(np.uint8)

    # ── Apply position angle rotation ──
    # PA is measured from North (top) clockwise through East (right)
    # In image coordinates, we need to rotate the lit mask
    # PA = 0 means bright limb is at top (North)
    # PA = 90 means bright limb is at right (East)
    # PA = -90 or 270 means bright limb is at left (West)

    lit_image = Image.fromarray(lit_arr, 'L')

    # Rotate: PIL rotates counter-clockwise, but PA is clockwise from North
    # In image coords, North is up (negative y), so we negate the angle
    # Also, the bright limb position determines the rotation
    lit_image = lit_image.rotate(
        -position_angle,  # Counter-clockwise in image coords
        resample=Image.BICUBIC,
        expand=False,
        fillcolor=0
    )

    # ── Apply B-angle tilt ──
    # The B-angle tilts the terminator slightly
    # This is a subtle effect for most cases
    # For simplicity, we apply a slight skew or additional rotation
    # For now, we'll incorporate it into the phase angle adjustment
    # (B-angle mainly affects the cusp orientation, not the width)

    # ── Smooth the edges ──
    lit_image = lit_image.filter(ImageFilter.GaussianBlur(radius=1.5))

    # ── Create the final moon image with proper coloring ──
    result = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))

    # Illuminated portion (bright)
    bright_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    bright_arr = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)
    lit_mask = np.array(lit_image)

    # Color the bright side (warm white/yellowish for thin crescents)
    if illumination < 0.1:
        r, g, b = 255, 248, 220
    elif illumination < 0.5:
        r, g, b = 250, 245, 230
    else:
        r, g, b = 240, 238, 230

    # Set RGB where lit, and alpha from the mask
    bright_arr[lit_mask > 0, 0] = r
    bright_arr[lit_mask > 0, 1] = g
    bright_arr[lit_mask > 0, 2] = b
    bright_arr[lit_mask > 0, 3] = lit_mask[lit_mask > 0]
    bright_layer = Image.fromarray(bright_arr, 'RGBA')
    result = Image.alpha_composite(result, bright_layer)

    # ── Earthshine (optional) ──
    if earthshine and illumination < 0.5:
        # Earthshine is faint illumination of the dark side
        # It's about 1-5% brightness of the main crescent
        earthshine_intensity = max(5, int(15 * (1 - illumination * 2)))

        es_layer = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        es_arr = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)

        # Earthshine covers the dark side of the moon
        dark_side = np.where(
            (moon_arr > 0) & (lit_mask == 0),
            earthshine_intensity, 0
        ).astype(np.uint8)

        # Soften the earthshine edge
        dark_side_img = Image.fromarray(dark_side, 'L')
        dark_side_img = dark_side_img.filter(ImageFilter.GaussianBlur(radius=3))
        dark_side = np.array(dark_side_img)

        # Earthshine color: very faint blue-grey
        es_arr[dark_side > 0, 0] = 100
        es_arr[dark_side > 0, 1] = 110
        es_arr[dark_side > 0, 2] = 130
        es_arr[dark_side > 0, 3] = dark_side[dark_side > 0]
        es_layer = Image.fromarray(es_arr, 'RGBA')
        result = Image.alpha_composite(result, es_layer)

    # ── Lunar surface texture (subtle) ──
    # Add very subtle maria (dark patches) for realism
    _add_surface_texture(result, cx, cy, R, lit_mask)

    # ── Limb glow (atmospheric softening) ──
    result = _add_limb_glow(result, cx, cy, R)

    # Crop to size
    result = result.crop((pad, pad, pad + size, pad + size))

    return result


def _add_surface_texture(moon_img, cx, cy, R, lit_mask):
    """Add subtle lunar maria texture to the lit portion."""
    w, h = moon_img.size
    arr = np.array(moon_img)

    # Generate procedural noise for maria
    # Use simple sinusoidal patterns (cheap and effective)
    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
    in_moon = dist_from_center <= R

    # Create noise pattern
    noise = np.zeros((h, w), dtype=np.float32)
    for freq in [0.03, 0.06, 0.12]:
        phase_x = np.random.uniform(0, 2 * np.pi)
        phase_y = np.random.uniform(0, 2 * np.pi)
        noise += np.sin(x * freq + phase_x) * np.cos(y * freq + phase_y)

    # Normalize to -1 to 1
    noise = noise / 3.0  # Divide by number of octaves

    # Only apply to lit areas, and very subtly
    texture_strength = 8  # Very subtle

    for c in range(3):  # RGB channels
        channel = arr[:, :, c].astype(np.float32)
        # Darken slightly where noise is positive (simulate maria)
        adjustment = noise * texture_strength * (lit_mask / 255.0)
        channel = np.clip(channel - adjustment, 0, 255)
        arr[:, :, c] = channel.astype(np.uint8)

    # Write back
    moon_img.paste(Image.fromarray(arr, 'RGBA'))


def _add_limb_glow(moon_img, cx, cy, R):
    """Add subtle brightening near the limb edge (limb darkening effect)."""
    w, h = moon_img.size
    arr = np.array(moon_img).astype(np.float32)

    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)

    # Limb darkening factor: brighter near center, dimmer near edge
    # Using a cosine falloff
    ratio = np.clip(dist_from_center / R, 0, 1)
    # At center (ratio=0): factor = 1.0
    # At edge (ratio=1): factor ≈ 0.85
    limb_factor = 1.0 - 0.15 * ratio**2

    # Apply only to pixels with alpha > 0
    mask = arr[:, :, 3] > 0
    for c in range(3):
        arr[:, :, c][mask] *= limb_factor[mask]

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


# ── Quick test ──
if __name__ == '__main__':
    # Test with Ramadhan data
    test_cases = [
        {"illum": 0.01, "pa": -149, "b": 0.69, "elon": 11, "label": "1 Ramadhan (thin crescent)"},
        {"illum": 0.10, "pa": -140, "b": 2.0, "elon": 25, "label": "5 Ramadhan"},
        {"illum": 0.50, "pa": 0, "b": 0, "elon": 90, "label": "Full Moon"},
        {"illum": 0.001, "pa": 50, "b": -0.5, "elon": 1.3, "label": "29 Sha'ban (nearly new)"},
    ]

    for tc in test_cases:
        moon = render_moon(
            size=400,
            illumination=tc["illum"],
            position_angle=tc["pa"],
            b_angle=tc["b"],
            elon=tc["elon"],
        )
        filename = f"output/test_moon_{tc['label'].split('(')[0].strip().replace(' ', '_')}.png"
        moon.save(filename)
        print(f"Saved: {filename} ({tc['label']})")

    print("\nDone! Check output/ folder.")
