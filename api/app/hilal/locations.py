"""Observer locations supported by the hilal endpoints (M1 set)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    slug: str
    display: str  # Indonesian display label for the chart
    lat: float
    lon: float
    tz: str


LOCATIONS: dict[str, Location] = {
    "jakarta": Location("jakarta", "Jakarta, Indonesia", -6.2088, 106.8456, "Asia/Jakarta"),
    "malang": Location("malang", "Malang, Indonesia", -7.9666, 112.6326, "Asia/Jakarta"),
    "sabang": Location(
        "sabang", "Sabang, Indonesia", 5.0 + 53.0 / 60.0, 95.0 + 19.0 / 60.0, "Asia/Jakarta"
    ),
    "makkah": Location("makkah", "Makkah, Arab Saudi", 21.4225, 39.8262, "Asia/Riyadh"),
    "hawaii": Location("hawaii", "Hawaii, Amerika Serikat", 21.3069, -157.8583, "Pacific/Honolulu"),
}

DEFAULT_LOCATION = "jakarta"


def get_location(slug: str | None) -> Location:
    if not slug:
        return LOCATIONS[DEFAULT_LOCATION]
    loc = LOCATIONS.get(slug.strip().lower())
    if loc is None:
        raise KeyError(slug)
    return loc
