#!/usr/bin/env python3
"""
Hilal Visualizer — Sky finding chart for hilal sighting.

Usage:
    python main.py --month "Ramadhan" --lat -6.2088 --lon 106.8456 --year 1447
    python main.py --month "Ramadhan" --location "Jakarta" --year 1447

Output: Sky chart showing where to look for the hilal at sunset.
"""

import argparse
import os
import sys
import random
import string
from send2trash import send2trash
from PIL import Image

from calendar_api import HijriMonth, get_previous_month_dates
from astronomy import calculate_at_sunset, get_moon_phase_name, find_moonset, get_illumination_at
from composer import sky_chart
from zoneinfo import ZoneInfo
from datetime import datetime


# ── Known locations ──
# Format: (lat, lon, timezone_name)
# timezone_name: IANA timezone (e.g., 'Asia/Jakarta', 'Europe/London')
# This automatically handles DST transitions!
KNOWN_LOCATIONS = {
    # Indonesia
    'jakarta': (-6.2088, 106.8456, 'Asia/Jakarta'),
    'makassar': (-5.1477, 119.4327, 'Asia/Makassar'),
    'jayapura': (-2.5916, 140.6690, 'Asia/Jayapura'),
    'medan': (3.5952, 98.6722, 'Asia/Jakarta'),
    'bandung': (-6.9175, 107.6191, 'Asia/Jakarta'),
    'surabaya': (-7.2575, 112.7521, 'Asia/Jakarta'),
    'yogyakarta': (-7.7956, 110.3695, 'Asia/Jakarta'),
    'semarang': (-6.9666, 110.4196, 'Asia/Jakarta'),
    'denpasar': (-8.6500, 115.2167, 'Asia/Makassar'),
    'malang': (-7.9666, 112.6326, 'Asia/Jakarta'),
    # Southeast Asia
    'kuala lumpur': (3.1390, 101.6869, 'Asia/Kuala_Lumpur'),
    'singapore': (1.3521, 103.8198, 'Asia/Singapore'),
    'bangkok': (13.7563, 100.5018, 'Asia/Bangkok'),
    'manila': (14.5995, 120.9842, 'Asia/Manila'),
    # Middle East
    'makkah': (21.4225, 39.8262, 'Asia/Riyadh'),
    'madinah': (24.4672, 39.6024, 'Asia/Riyadh'),
    'riyadh': (24.7136, 46.6753, 'Asia/Riyadh'),
    'dubai': (25.2048, 55.2708, 'Asia/Dubai'),
    'muscat': (23.5880, 58.3829, 'Asia/Muscat'),
    'tehran': (35.6892, 51.3890, 'Asia/Tehran'),
    'istanbul': (41.0082, 28.9784, 'Europe/Istanbul'),
    'cairo': (30.0444, 31.2357, 'Africa/Cairo'),
    # Europe
    'london': (51.5074, -0.1278, 'Europe/London'),
    'paris': (48.8566, 2.3522, 'Europe/Paris'),
    'berlin': (52.5200, 13.4050, 'Europe/Berlin'),
    'honolulu': (21.3069, -157.8583, 'Pacific/Honolulu'),
    'moscow': (55.7558, 37.6173, 'Europe/Moscow'),
    # Americas
    'new york': (40.7128, -74.0060, 'America/New_York'),
    'los angeles': (34.0522, -118.2437, 'America/Los_Angeles'),
    'chicago': (41.8781, -87.6298, 'America/Chicago'),
    'toronto': (43.6532, -79.3832, 'America/Toronto'),
    'rio': (-22.9068, -43.1729, 'America/Sao_Paulo'),
    'rio de janeiro': (-22.9068, -43.1729, 'America/Sao_Paulo'),
    'sao paulo': (-23.5505, -46.6333, 'America/Sao_Paulo'),
    # South Asia
    'karachi': (24.8607, 67.0011, 'Asia/Karachi'),
    'lahore': (31.5204, 74.3587, 'Asia/Karachi'),
    'delhi': (28.7041, 77.1025, 'Asia/Kolkata'),
    'dhaka': (23.8103, 90.4125, 'Asia/Dhaka'),
    # East Asia
    'tokyo': (35.6762, 139.6503, 'Asia/Tokyo'),
    # Africa
    'lagos': (6.5244, 3.3792, 'Africa/Lagos'),
    'nairobi': (-1.2921, 36.8219, 'Africa/Nairobi'),
    'casablanca': (33.5731, -7.5898, 'Africa/Casablanca'),
    # Oceania
    'sydney': (-33.8688, 151.2093, 'Australia/Sydney'),
    'melbourne': (-37.8136, 144.9631, 'Australia/Melbourne'),
}


def get_utc_offset(timezone_name: str, date: datetime) -> float:
    """Get UTC offset for a timezone on a specific date (handles DST)."""
    tz = ZoneInfo(timezone_name)
    localized = date.replace(tzinfo=tz)
    return localized.utcoffset().total_seconds() / 3600


def run(
    month_name: str,
    lat: float,
    lon: float,
    hijri_year: int = None,
    location_name: str = 'Custom',
    utc_offset: float = 7.0,
    tz_name: str = None,
    output_dir: str = 'output',
):
    """Main execution pipeline."""
    print(f"\n{'='*60}")
    print(f"  🌙 Hilal Visualizer")
    print(f"{'='*60}")
    print(f"  Location: {location_name} ({lat:.4f}, {lon:.4f})")
    print(f"  Target:   {month_name}")

    # ── Step 1: Resolve Hijri calendar ──
    print(f"\n📅 Resolving Hijri calendar...")

    if hijri_year is None:
        hijri_year = 1447
        print(f"  (Using default Hijri year: {hijri_year})")

    target_month = HijriMonth.to_number(month_name)
    dates = get_previous_month_dates(hijri_year, target_month, lat, lon)

    prev = dates['previous_month']
    print(f"  Previous: {prev['name']} ({prev['length']} days)")
    print(f"  Target:   {dates['target_month']['name']} {dates['target_month']['year']}")

    # Build list of dates to render
    render_dates = []

    if dates['day_29']:
        d = dates['day_29']
        render_dates.append({
            'date': d['gregorian_date'],
            'maghrib': (d['maghrib_hour'], d['maghrib_min']),
            'hijri_day': d['hijri_day'],
            'hijri_month_name': d['hijri_month_name'],
            'hijri_year': d['hijri_year'],
            'label': f"{d['hijri_day']} {d['hijri_month_name']}",
        })

    if dates['day_30']:
        d = dates['day_30']
        render_dates.append({
            'date': d['gregorian_date'],
            'maghrib': (d['maghrib_hour'], d['maghrib_min']),
            'hijri_day': d['hijri_day'],
            'hijri_month_name': d['hijri_month_name'],
            'hijri_year': d['hijri_year'],
            'label': f"{d['hijri_day']} {d['hijri_month_name']}",
        })
    elif dates['day_1_target']:
        d = dates['day_1_target']
        render_dates.append({
            'date': d['gregorian_date'],
            'maghrib': (d['maghrib_hour'], d['maghrib_min']),
            'hijri_day': d['hijri_day'],
            'hijri_month_name': d['hijri_month_name'],
            'hijri_year': d['hijri_year'],
            'label': f"{d['hijri_day']} {d['hijri_month_name']}",
        })

    # ── Step 2 & 3: Calculate astronomy for each date ──
    print(f"\n🔭 Calculating astronomical data...")

    results = []
    for rd in render_dates:
        date = rd['date']
        h, m = rd['maghrib']
        print(f"\n  {rd['label']} ({date.strftime('%d %b %Y')}) — Maghrib: {h:02d}:{m:02d}")

        # Calculate UTC offset for this specific date (handles DST)
        try:
            if tz_name:
                utc_offset = get_utc_offset(tz_name, date)
                print(f"    UTC offset: {utc_offset:+.1f}h ({tz_name})")
            else:
                print(f"    Using default UTC offset: {utc_offset:+.1f}h")
        except NameError:
            print(f"    Using default UTC offset: {utc_offset:+.1f}h")

        astro = calculate_at_sunset(
            gregorian_date=date,
            maghrib_hour=h,
            maghrib_min=m,
            lat=lat,
            lon=lon,
            utc_offset=utc_offset,
        )

        print(f"    Sun Alt:     {astro.sun_alt:+.2f}°")
        print(f"    Sun Az:      {astro.sun_az:.2f}°")
        print(f"    Moon Alt:    {astro.moon_alt:+.2f}°")
        print(f"    Moon Az:     {astro.moon_az:.2f}°")
        print(f"    Elongation:  {astro.elongation:.2f}°")
        print(f"    Illum:       {astro.illumination*100:.2f}%")
        print(f"    Lunar Age:   {astro.lunar_age_days:+.2f} days")

        # Find moonset time
        moonset = find_moonset(
            gregorian_date=date,
            lat=lat,
            lon=lon,
            utc_offset=utc_offset,
        )
        print(f"    Moonset:     {moonset}")

        results.append((rd, astro, moonset))

    # ── Step 4: Generate sky charts ──
    print(f"\n🎨 Generating sky charts...")

    os.makedirs(output_dir, exist_ok=True)
    canvas_w, canvas_h = 1000, 600

    for rd, astro, moonset in results:
        # Center view on the average of sun and moon azimuth
        # This gives the best "where to look" perspective
        center_az = (astro.sun_az + astro.moon_az) / 2

        # Get illumination for +12hrs (for phase box visibility)
        phase_illum = None
        if astro.elongation >= 5.5:
            try:
                phase_illum = get_illumination_at(
                    rd['date'],
                    maghrib_hour=rd['maghrib'][0],
                    maghrib_min=rd['maghrib'][1],
                    days_ahead=0.5,  # 12 hours
                    lat=lat,
                    lon=lon
                )
                print(f"    🌙 Phase illum (+12h): {phase_illum*100:.1f}%")
            except Exception:
                phase_illum = None

        chart = sky_chart(
            width=canvas_w,
            height=canvas_h,
            sun_az=astro.sun_az,
            sun_alt=astro.sun_alt,
            moon_az=astro.moon_az,
            moon_alt=astro.moon_alt,
            moon_pa=astro.position_angle,
            moon_illum=astro.illumination,
            moon_elong=astro.elongation,
            phase_illum=phase_illum,
            center_az=center_az,
            az_range=30,       # Zoomed in: 30° field of view
            alt_min=-10,
            alt_max=30,
            show_grid=True,
            show_compass=True,
            location_name=location_name,
            gregorian_date=rd['date'].strftime('%d %b %Y'),
            hijri_label=f"{rd['hijri_day']} {rd['hijri_month_name']} {rd['hijri_year']} AH",
            sunset_time=f"{rd['maghrib'][0]:02d}:{rd['maghrib'][1]:02d}",
            moonset_time=moonset,
            lunar_age=astro.lunar_age_days,
        )

        # Generate filename (ASCII only, with cache-busting hash)
        greg_date = rd['date']
        day_str = f"{rd['hijri_day']:02d}"
        # Transliterate Arabic characters to ASCII
        month_str = (rd['hijri_month_name']
                     .replace("'", "a").replace("'", "a").replace("'", "a")
                     .replace("ʿ", "a").replace("'", "a")
                     .replace("ā", "a").replace("ū", "u").replace("ī", "i")
                     .replace("ḍ", "d").replace("ḥ", "h").replace("ṣ", "s")
                     .replace("ṭ", "t").replace("ẓ", "z").replace("ġ", "g")
                     .replace("ʿ", "a").replace("'", "")
                     .encode('ascii', 'ignore').decode('ascii'))
        # Cache-busting: 6 random alphanumeric chars
        cache_bust = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        filename = f"{day_str}_{month_str}_{greg_date.strftime('%Y%m%d')}_{cache_bust}.png"
        filepath = os.path.join(output_dir, filename)

        chart.save(filepath, quality=95)
        print(f"  ✅ Saved: {filepath}")

    print(f"\n{'='*60}")
    print(f"  Done! {len(results)} charts saved to {output_dir}/")
    print(f"{'='*60}\n")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Hilal Visualizer — Sky finding chart for hilal sighting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --month Ramadhan --location Jakarta
  python main.py --month Shawwal --lat -6.2088 --lon 106.8456 --year 1447
  python main.py --month "Dhu al-Hijjah" --location "Makkah"
        """
    )

    parser.add_argument('--month', '-m', required=True,
                        help='Target Hijri month name (e.g., Ramadhan, Shawwal)')
    parser.add_argument('--year', '-y', type=int, default=None,
                        help='Hijri year (default: auto-detect)')
    parser.add_argument('--location', '-l', type=str, default=None,
                        help='Known location name (Jakarta, Makassar, etc.)')
    parser.add_argument('--lat', type=float, default=None,
                        help='Latitude (decimal degrees)')
    parser.add_argument('--lon', type=float, default=None,
                        help='Longitude (decimal degrees)')
    parser.add_argument('--utc-offset', type=float, default=None,
                        help='UTC offset in hours (default: 7 for WIB)')
    parser.add_argument('--output', '-o', default='output',
                        help='Output directory (default: output)')

    args = parser.parse_args()

    # Resolve location
    if args.location:
        location_name = args.location
        if args.location.lower() in KNOWN_LOCATIONS:
            lat, lon, tz_name = KNOWN_LOCATIONS[args.location.lower()]
            # Calculate UTC offset for the target date (handles DST automatically)
            utc_offset = 7.0  # Default, will be overridden per-date
            print(f"Using known location: {args.location} ({lat}, {lon}) — {tz_name}")
        else:
            print(f"Warning: Unknown location '{args.location}'. Using lat/lon if provided.")
            if args.lat is None or args.lon is None:
                print("Error: --lat and --lon required for unknown locations.")
                sys.exit(1)
            lat = args.lat
            lon = args.lon
            tz_name = None  # Unknown timezone, use --utc-offset
            utc_offset = args.utc_offset or 7.0
    elif args.lat is not None and args.lon is not None:
        lat = args.lat
        lon = args.lon
        location_name = "Custom"
        tz_name = None
        utc_offset = args.utc_offset or 7.0
    else:
        print("Error: Provide either --location or --lat/--lon")
        sys.exit(1)

    run(
        month_name=args.month,
        lat=lat,
        lon=lon,
        hijri_year=args.year,
        location_name=location_name,
        utc_offset=utc_offset,
        tz_name=tz_name,
        output_dir=args.output,
    )


if __name__ == '__main__':
    main()
