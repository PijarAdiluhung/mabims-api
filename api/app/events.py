from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventDefinition:
    slug: str
    name: str
    month: int
    day: int
    # Inclusive last day of a multi-day observance; None = single-day event.
    day_end: int | None = None


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

# Tier 2 ("extra"): big Islamic dates that are not national holidays.
# Tasyrik spans day 11-13 of Dzulhijjah (one ranged event).
EXTRA_DEFINITIONS: tuple[EventDefinition, ...] = (
    EventDefinition(
        slug="isra_miraj",
        name="Isra Mi'raj Nabi Muhammad Shallallahu Alaihi Wasallam",
        month=7,
        day=27,
    ),
    EventDefinition(slug="nuzulul_quran", name="Nuzulul Quran", month=9, day=17),
    EventDefinition(slug="arafah", name="Puasa Arafah", month=12, day=9),
    EventDefinition(slug="tasua", name="Puasa Tasu'a", month=1, day=9),
    EventDefinition(slug="asyura", name="Puasa Asyura", month=1, day=10),
    EventDefinition(slug="tasyrik", name="Hari Tasyrik", month=12, day=11, day_end=13),
)

AYYAMUL_BIDH_SLUG = "ayyamul_bidh"
AYYAMUL_BIDH_NAME = "Puasa Ayyamul Bidh"
AYYAMUL_BIDH_START_DAY = 13
AYYAMUL_BIDH_END_DAY = 15

BASE_SLUGS: frozenset[str] = frozenset(d.slug for d in EVENT_DEFINITIONS)
EXTRA_SLUGS: frozenset[str] = frozenset(d.slug for d in EXTRA_DEFINITIONS)
INCLUDE_TOKENS: frozenset[str] = frozenset(
    {"extra", AYYAMUL_BIDH_SLUG, "all"} | EXTRA_SLUGS
)


def _include_enabled(include: frozenset[str], token: str) -> bool:
    return token in include or "all" in include


def definitions_for_include(include: frozenset[str]) -> tuple[EventDefinition, ...]:
    """Definitions to evaluate for one request.

    ``include`` tokens: ``extra`` (whole tier 2), ``ayyamul_bidh`` (tier 3,
    generated in find_events), individual tier-2 slugs, ``all``. Base 5
    definitions are always present.
    """
    extra = EXTRA_DEFINITIONS if "extra" in include or "all" in include else tuple(
        d for d in EXTRA_DEFINITIONS if d.slug in include
    )
    return (*EVENT_DEFINITIONS, *extra)


def parse_include(include: str | None) -> frozenset[str]:
    """Parse and validate the ``include`` query parameter.

    Accepts ``extra``, ``ayyamul_bidh``, ``all`` and individual tier-2 slugs,
    comma-separated. Empty/None returns an empty frozenset (base 5 only).
    Raises ValueError on unknown tokens; the caller maps that to
    400 invalid_include.
    """
    if include is None or not include.strip():
        return frozenset()
    tokens: list[str] = []
    for raw in include.split(","):
        token = raw.strip()
        if not token:
            continue
        if token not in INCLUDE_TOKENS:
            raise ValueError(token)
        tokens.append(token)
    return frozenset(tokens)


def _ayyamul_bidh_definition(month: int) -> EventDefinition:
    return EventDefinition(
        slug=AYYAMUL_BIDH_SLUG,
        name=AYYAMUL_BIDH_NAME,
        month=month,
        day=AYYAMUL_BIDH_START_DAY,
        day_end=AYYAMUL_BIDH_END_DAY,
    )


def find_events(
    service,
    year: int,
    calendar: str,
    *,
    retro: bool = False,
    include: frozenset[str] = frozenset(),
) -> list[tuple[EventDefinition, str, str]]:
    found: list[tuple[EventDefinition, str, str]] = []
    definitions = definitions_for_include(include)
    want_ayyamul_bidh = _include_enabled(include, AYYAMUL_BIDH_SLUG)
    months_needed: set[tuple[int, int]] = set()

    if calendar == "hijri":
        for definition in definitions:
            months_needed.add((year, definition.month))
    else:
        # A gregorian year can span parts of 3-4 hijri years (e.g. 1975 hosts
        # events from hijri 1395 = year-580). Scan a wide window; lookups are
        # cheap and events are filtered to the requested gregorian year below.
        for hijri_year in range(year - 581, year - 576):
            for definition in definitions:
                months_needed.add((hijri_year, definition.month))

    # Ayyamul bidh needs days 13-15 of every Hijri month, so the whole year
    # window must be probed, not just the definitions' months.
    months_to_probe = set(months_needed)
    if want_ayyamul_bidh:
        if calendar == "hijri":
            months_to_probe.update((year, m) for m in range(1, 13))
        else:
            for hijri_year in range(year - 581, year - 576):
                months_to_probe.update((hijri_year, m) for m in range(1, 13))

    for hy, hm in months_to_probe:
        probe = f"{hy:04d}-{hm:02d}-01"
        if service.covers(probe, "hijri"):
            continue
        try:
            service.ensure_hijri_month(hy, hm, retro=retro)
        except Exception:
            continue

    if calendar == "hijri":
        for definition in definitions:
            h_iso = f"{year:04d}-{definition.month:02d}-{definition.day:02d}"
            result = service.lookup(h_iso, "hijri")
            if result.value is not None:
                found.append((definition, result.value, h_iso))
        if want_ayyamul_bidh:
            for month in range(1, 13):
                h_iso = f"{year:04d}-{month:02d}-{AYYAMUL_BIDH_START_DAY:02d}"
                result = service.lookup(h_iso, "hijri")
                if result.value is not None:
                    found.append((_ayyamul_bidh_definition(month), result.value, h_iso))
    else:
        for hijri_year in range(year - 581, year - 576):
            for definition in definitions:
                h_iso = f"{hijri_year:04d}-{definition.month:02d}-{definition.day:02d}"
                result = service.lookup(h_iso, "hijri")
                if result.value is not None and result.value.startswith(f"{year:04d}-"):
                    found.append((definition, result.value, h_iso))
            if want_ayyamul_bidh:
                for month in range(1, 13):
                    h_iso = f"{hijri_year:04d}-{month:02d}-{AYYAMUL_BIDH_START_DAY:02d}"
                    result = service.lookup(h_iso, "hijri")
                    if result.value is not None and result.value.startswith(f"{year:04d}-"):
                        found.append((_ayyamul_bidh_definition(month), result.value, h_iso))

    found.sort(key=lambda row: row[1])
    return found
