"""
Aladhan API wrapper for Hijri calendar resolution and prayer times.
Uses Umm al-Qura calendar (method=4).
"""

import requests
from datetime import datetime, timedelta
from typing import Optional


class HijriMonth:
    """Maps Hijri month names to numbers."""
    MONTHS = {
        'muharram': 1, 'muhammad': 1,
        'safar': 2,
        'rabi al-awwal': 3, 'rabi i': 3, 'rabiul awwal': 3,
        'rabi al-thani': 4, 'rabi ii': 4, 'rabiul akhir': 4,
        'jumada al-ula': 5, 'jumada i': 5, 'jumada al-awwal': 5,
        'jumada al-thani': 6, 'jumada ii': 6, 'jumada al-akhir': 6,
        'rajab': 7,
        'shaban': 8, "sha'ban": 8, "sha'ban": 8, "syaban": 8,
        'ramadhan': 9, 'ramadan': 9, 'ramadhan': 9,
        'shawwal': 10,
        'dhul qi\'dah': 11, 'dhu al-qidah': 11, 'dzulqaidah': 11,
        'dhul hijjah': 12, 'dhu al-hijjah': 12, 'dzulhijjah': 12,
    }

    MONTH_NAMES = {
        1: 'Muharram', 2: 'Safar', 3: 'Rabi al-Awwal',
        4: 'Rabi al-Thani', 5: 'Jumada al-Ula', 6: 'Jumada al-Thani',
        7: 'Rajab', 8: "Sha'ban", 9: 'Ramadhan', 10: 'Shawwal',
        11: "Dhu al-Qi'dah", 12: 'Dhu al-Hijjah',
    }

    @classmethod
    def to_number(cls, name: str) -> int:
        """Convert month name to number. Raises ValueError if not found."""
        normalized = name.lower().strip()
        if normalized in cls.MONTHS:
            return cls.MONTHS[normalized]
        # Try partial match
        for key, val in cls.MONTHS.items():
            if normalized in key or key in normalized:
                return val
        raise ValueError(f"Unknown Hijri month: '{name}'. Valid: {list(set(cls.MONTHS.values()))}")

    @classmethod
    def to_name(cls, number: int) -> str:
        return cls.MONTH_NAMES.get(number, f'Month {number}')

    @classmethod
    def prev_month(cls, number: int) -> int:
        """Get the previous month number."""
        return 12 if number == 1 else number - 1


def get_hijri_calendar(hijri_year: int, hijri_month: int, lat: float, lon: float) -> list:
    """
    Get the Hijri calendar mapping for a given hijri year/month.
    Returns list of dicts with hijri day, gregorian date, and timings.

    Note: The Aladhan API hijriCalendar endpoint returns the ENTIRE hijri month,
    mapping each hijri day to its gregorian equivalent.
    """
    # Aladhan API: /v1/hijriCalendar/{year}/{month}
    # year/month are HIJRI year/month
    url = f"https://api.aladhan.com/v1/hijriCalendar/{hijri_year}/{hijri_month}"
    params = {
        'latitude': lat,
        'longitude': lon,
        'method': 4,  # Umm al-Qura
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get('code') != 200:
        raise RuntimeError(f"Aladhan API error: {data.get('status', 'unknown')}")

    results = []
    for entry in data['data']:
        hijri = entry['date']['hijri']
        greg = entry['date']['gregorian']

        # Parse gregorian date
        greg_date_str = greg['date']  # DD-MM-YYYY
        greg_date = datetime.strptime(greg_date_str, '%d-%m-%Y')

        # Parse maghrib time
        maghrib_str = entry['timings']['Maghrib']
        # Format: "HH:MM (TZ)" or "HH:MM"
        maghrib_clean = maghrib_str.split(' ')[0]  # Remove timezone suffix
        maghrib_parts = maghrib_clean.split(':')
        maghrib_hour = int(maghrib_parts[0])
        maghrib_min = int(maghrib_parts[1])

        # Check if timing crosses midnight (e.g., high latitudes)
        # For our purposes (Indonesia/near equator), this shouldn't happen

        results.append({
            'hijri_day': int(hijri['day']),
            'hijri_month': int(hijri['month']['number']),
            'hijri_month_name': hijri['month']['en'],
            'hijri_year': int(hijri['year']),
            'gregorian_date': greg_date,
            'maghrib_hour': maghrib_hour,
            'maghrib_min': maghrib_min,
            'timings': entry['timings'],
        })

    return results


def get_month_length(hijri_year: int, hijri_month: int, lat: float, lon: float) -> int:
    """Get the number of days in a Hijri month (29 or 30)."""
    cal = get_hijri_calendar(hijri_year, hijri_month, lat, lon)
    return len(cal)


def get_previous_month_dates(
    target_hijri_year: int,
    target_hijri_month: int,
    lat: float,
    lon: float,
) -> dict:
    """
    Given a target Hijri month (e.g., Ramadhan), find:
    - The 29th of the previous month (always exists)
    - The 30th of the previous month (if it exists)
    - The 1st of the target month

    Returns dict with Gregorian dates and Maghrib times.
    """
    prev_month = HijriMonth.prev_month(target_hijri_month)
    prev_year = target_hijri_year

    # If previous month is Dhul Hijjah (12) and target is Muharram (1),
    # the previous year's Dhul Hijjah
    if target_hijri_month == 1:
        prev_year = target_hijri_year - 1

    # Get the full previous month calendar
    prev_cal = get_hijri_calendar(prev_year, prev_month, lat, lon)
    month_length = len(prev_cal)

    # Find specific days
    day_29 = None
    day_30 = None
    day_1_target = None

    for entry in prev_cal:
        if entry['hijri_day'] == 29:
            day_29 = entry
        elif entry['hijri_day'] == 30:
            day_30 = entry

    # Get 1st of target month
    target_cal = get_hijri_calendar(target_hijri_year, target_hijri_month, lat, lon)
    for entry in target_cal:
        if entry['hijri_day'] == 1:
            day_1_target = entry
            break

    return {
        'previous_month': {
            'name': HijriMonth.to_name(prev_month),
            'number': prev_month,
            'year': prev_year,
            'length': month_length,
        },
        'target_month': {
            'name': HijriMonth.to_name(target_hijri_month),
            'number': target_hijri_month,
            'year': target_hijri_year,
        },
        'day_29': day_29,  # Always exists
        'day_30': day_30,  # None if month is 29 days
        'day_1_target': day_1_target,
    }


# ── Quick test ──
if __name__ == '__main__':
    # Example: Jakarta, looking for Ramadhan 1447
    lat, lon = -6.2088, 106.8456

    # First, let's figure out what Hijri year/month "Ramadhan" corresponds to now
    # We'll test with a known value
    print("=== Testing Aladhan API ===")

    dates = get_previous_month_dates(1447, 9, lat, lon)
    print(f"\nTarget: {dates['target_month']['name']} {dates['target_month']['year']}")
    print(f"Previous: {dates['previous_month']['name']} ({dates['previous_month']['length']} days)")

    if dates['day_29']:
        d = dates['day_29']
        print(f"\n29 {d['hijri_month_name']}: {d['gregorian_date'].strftime('%d %b %Y')} "
              f"@ {d['maghrib_hour']:02d}:{d['maghrib_min']:02d} Maghrib")

    if dates['day_30']:
        d = dates['day_30']
        print(f"30 {d['hijri_month_name']}: {d['gregorian_date'].strftime('%d %b %Y')} "
              f"@ {d['maghrib_hour']:02d}:{d['maghrib_min']:02d} Maghrib")

    if dates['day_1_target']:
        d = dates['day_1_target']
        print(f"1  {d['hijri_month_name']}: {d['gregorian_date'].strftime('%d %b %Y')} "
              f"@ {d['maghrib_hour']:02d}:{d['maghrib_min']:02d} Maghrib")
