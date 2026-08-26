"""Offline smoke test: render one hilal sky chart, no network.

Calendar data is hardcoded (eve of 1 Ramadhan 1447, Jakarta) so Aladhan
is never called. Skyfield reads de421.bsp from its cache dir — run with
that dir as cwd, e.g.:

    & api\\.venv\\Scripts\\python.exe api\\todo\\offline_test.py
    (workdir: %TEMP%\\mabims-ephemeris)

Output: api/todo/output/offline_test_29_shaban_1447_jakarta.png
"""

from __future__ import annotations

import math
import sys
import types
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
VIZ_DIR = HERE / "hilal-visualizer"
sys.path.insert(0, str(VIZ_DIR))


class _ShimMoonTex:
    """Pillow-only stand-in for MoonTex (whose 'noise' dep needs MSVC).

    Draws a phase disc via terminator-ellipse geometry; composer.py then
    rotates/resizes it exactly as it would a real MoonTex frame.
    """

    def __init__(self, image_size: int = 300, **_: object) -> None:
        self.size = image_size

    def generate(self, phase_offset: float = 0.5, **_: object) -> Image.Image:
        illum = max(0.0, min(1.0, 1.0 - float(phase_offset)))
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        c = s // 2
        r = s // 2 - 2
        d.ellipse([c - r, c - r, c + r, c + r], fill=(238, 235, 226, 255))
        if 0.001 < illum < 0.999:
            psi = math.acos(max(-1.0, min(1.0, 1 - 2 * illum)))
            b = r * abs(math.cos(psi))
            off = r * math.sin(psi)
            mask = Image.new("L", (s, s), 0)
            ImageDraw.Draw(mask).ellipse(
                [c - off - b, c - r, c - off + b, c + r], fill=255
            )
            img.paste(Image.new("RGBA", (s, s), (8, 8, 12, 255)), (0, 0), mask)
        return img


try:
    import moontex  # noqa: F401
except ModuleNotFoundError:
    shim = types.ModuleType("moontex")
    shim.MoonTex = _ShimMoonTex  # type: ignore[attr-defined]
    sys.modules["moontex"] = shim


def _render(label: str, date: datetime, out_name: str) -> None:
    from astronomy import (
        calculate_at_sunset,
        find_moonset,
        get_illumination_at,
        get_moon_phase_name,
    )
    from composer import sky_chart

    lat, lon = -6.2088, 106.8456  # Jakarta

    astro = calculate_at_sunset(date, 18, 15, lat, lon, utc_offset=7.0)
    moonset = find_moonset(date, lat, lon, utc_offset=7.0)
    phase_illum = get_illumination_at(date, 18, 15, days_ahead=0.5, lat=lat, lon=lon)

    print(f"\n== {label} ==")
    print(f"Sun alt/az     : {astro.sun_alt:+.2f} / {astro.sun_az:.2f}")
    print(f"Moon alt/az    : {astro.moon_alt:+.2f} / {astro.moon_az:.2f}")
    print(f"Elongation     : {astro.elongation:.2f} deg")
    print(f"Illumination   : {astro.illumination * 100:.2f}%")
    print(f"Phase (+12h)   : {phase_illum * 100:.2f}%")
    print(f"Lunar age      : {astro.lunar_age_days:+.2f} d")
    print(f"Moonset        : {moonset}")
    print(f"Phase name     : {get_moon_phase_name(astro.illumination)}")

    chart = sky_chart(
        width=1000,
        height=600,
        sun_az=astro.sun_az,
        sun_alt=astro.sun_alt,
        moon_az=astro.moon_az,
        moon_alt=astro.moon_alt,
        moon_pa=astro.position_angle,
        moon_illum=astro.illumination,
        moon_elong=astro.elongation,
        phase_illum=phase_illum,
        center_az=(astro.sun_az + astro.moon_az) / 2,
        az_range=30,
        alt_min=-10,
        alt_max=30,
        show_grid=True,
        show_compass=True,
        location_name="Jakarta, Indonesia",
        gregorian_date=date.strftime("%d %b %Y"),
        hijri_label=label,
        sunset_time="18:15",
        moonset_time=moonset,
        lunar_age=astro.lunar_age_days,
    )

    out_dir = HERE / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / out_name
    chart.save(out_path)
    print(f"Saved: {out_path}")


def main() -> None:
    _render("29 Sha'ban 1447 AH", datetime(2026, 2, 17),
            "offline_test_29_shaban_1447_jakarta.png")
    _render("30 Sha'ban 1447 AH", datetime(2026, 2, 18),
            "offline_test_30_shaban_1447_jakarta.png")


if __name__ == "__main__":
    main()
