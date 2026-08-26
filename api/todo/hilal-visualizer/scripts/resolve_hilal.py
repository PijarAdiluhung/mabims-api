#!/usr/bin/env python3
"""
Resolve hilal visualizer arguments.

Modes:
  - "next" or "next hilal": Find current Hijri month, visualize the NEXT month
  - "prev" or "previous hilal": Find current Hijri month, visualize THIS month
  - Direct month name: Use that month directly

Usage:
  python3 resolve_hilal.py --location "London" --mode "next" [--year 1448]
  python3 resolve_hilal.py --location "Jakarta" --month "Safar" [--year 1448]
"""

import sys
import os
import argparse
import json
import requests
from datetime import datetime

# Hijri month names
HIJRI_MONTHS = {
    1: ('Muharram', 'محرم'),
    2: ('Safar', 'صفر'),
    3: ('Rabi al-Awwal', 'ربيع الأول'),
    4: ('Rabi al-Thani', 'ربيع الثاني'),
    5: ('Jumada al-Ula', 'جمادى الأولى'),
    6: ('Jumada al-Thani', 'جمادى الثانية'),
    7: ('Rajab', 'رجب'),
    8: ('Sha\'ban', 'شعبان'),
    9: ('Ramadhan', 'رمضان'),
    10: ('Shawwal', 'شوال'),
    11: ('Dhu al-Qi\'dah', 'ذو القعدة'),
    12: ('Dhu al-Hijjah', 'ذو الحجة'),
}

MONTH_NAME_TO_NUM = {v[0].lower(): k for k, v in HIJRI_MONTHS.items()}
MONTH_NAME_TO_NUM.update({v[0].replace("'", "").lower(): k for k, v in HIJRI_MONTHS.items()})


def get_current_hijri_date(lat, lon):
    """Get current Hijri date from Aladhan API."""
    today = datetime.now()
    url = f"https://api.aladhan.com/v1/gToH/{today.strftime('%d-%m-%Y')}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()['data']['hijri']
        month_data = data['month']
        if isinstance(month_data, dict):
            month_num = month_data['number']
        else:
            month_num = int(month_data)
        return month_num, int(data['year']), data['day']
    except Exception as e:
        print(f"Warning: Could not get current Hijri date: {e}", file=sys.stderr)
        return None, None, None


def parse_month_input(month_str):
    """Parse month name or number."""
    if month_str.isdigit():
        num = int(month_str)
        if 1 <= num <= 12:
            return num, HIJRI_MONTHS[num][0]
    else:
        key = month_str.lower().strip()
        if key in MONTH_NAME_TO_NUM:
            num = MONTH_NAME_TO_NUM[key]
            return num, HIJRI_MONTHS[num][0]
    return None, None


def main():
    parser = argparse.ArgumentParser(description='Resolve Hilal Visualizer arguments')
    parser.add_argument('--location', '-l', required=True, help='Location name')
    parser.add_argument('--month', '-m', help='Hijri month name or number')
    parser.add_argument('--mode', help='Mode: "next" or "prev"')
    parser.add_argument('--year', '-y', type=int, help='Hijri year')
    parser.add_argument('--lat', type=float, help='Latitude')
    parser.add_argument('--lon', type=float, help='Longitude')
    args = parser.parse_args()

    # Get coordinates from location name
    # Import from main.py's KNOWN_LOCATIONS
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from main import KNOWN_LOCATIONS

    lat, lon = None, None
    if args.location.lower() in KNOWN_LOCATIONS:
        lat, lon, _ = KNOWN_LOCATIONS[args.location.lower()]
    elif args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
    else:
        print(json.dumps({"error": f"Unknown location: {args.location}. Use --lat and --lon."}))
        sys.exit(1)

    # Determine target month
    mode = (args.mode or '').lower().strip()
    target_month_num = None
    target_month_name = None
    hijri_year = args.year

    if mode in ('next', 'next hilal', 'next_hilal'):
        # Get current Hijri date
        curr_month, curr_year, _ = get_current_hijri_date(lat, lon)
        if curr_month is None:
            print(json.dumps({"error": "Could not determine current Hijri date"}))
            sys.exit(1)
        # Next month = current month + 1
        target_month_num = curr_month + 1
        if target_month_num > 12:
            target_month_num = 1
            if hijri_year is None:
                hijri_year = curr_year + 1
        if hijri_year is None:
            hijri_year = curr_year
        target_month_name = HIJRI_MONTHS[target_month_num][0]
        print(f"Mode: next hilal → {target_month_name} {hijri_year}", file=sys.stderr)

    elif mode in ('prev', 'prev hilal', 'previous hilal', 'previous_hilal', 'previous'):
        # Get current Hijri date
        curr_month, curr_year, _ = get_current_hijri_date(lat, lon)
        if curr_month is None:
            print(json.dumps({"error": "Could not determine current Hijri date"}))
            sys.exit(1)
        # This month
        target_month_num = curr_month
        if hijri_year is None:
            hijri_year = curr_year
        target_month_name = HIJRI_MONTHS[target_month_num][0]
        print(f"Mode: prev hilal → {target_month_name} {hijri_year}", file=sys.stderr)

    elif args.month:
        target_month_num, target_month_name = parse_month_input(args.month)
        if target_month_num is None:
            print(json.dumps({"error": f"Unknown month: {args.month}"}))
            sys.exit(1)
        if hijri_year is None:
            hijri_year = 1448  # Default
        print(f"Direct month: {target_month_name} {hijri_year}", file=sys.stderr)

    else:
        print(json.dumps({"error": "Provide --month or --mode (next/prev)"}))
        sys.exit(1)

    # Output JSON for the batch
    result = {
        "month": target_month_name,
        "year": hijri_year,
        "location": args.location,
        "lat": lat,
        "lon": lon,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
