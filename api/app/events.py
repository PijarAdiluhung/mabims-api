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

_BY_MONTH_DAY: dict[tuple[int, int], EventDefinition] = {
    (definition.month, definition.day): definition for definition in EVENT_DEFINITIONS
}


def find_events(h2g: dict[str, str], year: int, calendar: str) -> list[tuple[EventDefinition, str, str]]:
    prefix = f"{year:04d}-"
    found: list[tuple[EventDefinition, str, str]] = []
    for h_iso, g_iso in h2g.items():
        probe = h_iso if calendar == "hijri" else g_iso
        if not probe.startswith(prefix):
            continue
        definition = _BY_MONTH_DAY.get((int(h_iso[5:7]), int(h_iso[8:10])))
        if definition is not None:
            found.append((definition, g_iso, h_iso))
    found.sort(key=lambda row: row[1])
    return found
