from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventDefinition:
    slug: str
    name: str
    month: int
    day: int


EVENT_DEFINITIONS: tuple[EventDefinition, ...] = (
    EventDefinition(slug="1_muharram", name="Tahun Baru Islam", month=1, day=1),
    EventDefinition(
        slug="maulid_nabi",
        name="Maulid Nabi Muhammad Shallallahu Alaihi Wasallam",
        month=3,
        day=12,
    ),
    EventDefinition(slug="awal_ramadan", name="Awal Ramadan", month=9, day=1),
    EventDefinition(slug="idul_fitri", name="Idul Fitri", month=10, day=1),
    EventDefinition(slug="idul_adha", name="Idul Adha", month=12, day=10),
)

def find_events(service, year: int, calendar: str) -> list[tuple[EventDefinition, str, str]]:
    found: list[tuple[EventDefinition, str, str]] = []
    months_needed: set[tuple[int, int]] = set()

    if calendar == "hijri":
        for definition in EVENT_DEFINITIONS:
            months_needed.add((year, definition.month))
    else:
        for hijri_year in range(year - 579, year - 576):
            for definition in EVENT_DEFINITIONS:
                months_needed.add((hijri_year, definition.month))

    for hy, hm in months_needed:
        probe = f"{hy:04d}-{hm:02d}-01"
        if service.covers(probe, "hijri"):
            continue
        try:
            service.ensure_hijri_month(hy, hm)
        except Exception:
            continue

    if calendar == "hijri":
        for definition in EVENT_DEFINITIONS:
            h_iso = f"{year:04d}-{definition.month:02d}-{definition.day:02d}"
            result = service.lookup(h_iso, "hijri")
            if result.value is not None:
                found.append((definition, result.value, h_iso))
    else:
        for hijri_year in range(year - 579, year - 576):
            for definition in EVENT_DEFINITIONS:
                h_iso = f"{hijri_year:04d}-{definition.month:02d}-{definition.day:02d}"
                result = service.lookup(h_iso, "hijri")
                if result.value is not None and result.value.startswith(f"{year:04d}-"):
                    found.append((definition, result.value, h_iso))

    found.sort(key=lambda row: row[1])
    return found
