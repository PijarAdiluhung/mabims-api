"""Borderline-month flagging: only genuine near-threshold passes qualify.

Regression for the "close to threshold" warning noise: rejected sighting
evenings (no site meets both criteria) must never be flagged, regardless of
how close the best site came on one criterion.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.mabims_computed import BORDERLINE_MARGIN_DEG, MabimsCalcProvider
from app.mabims_sites import MultiSiteSighting, SiteSighting

SYNTHETIC_START = date(1400, 1, 1)


def _provider_with_margins(margins: dict[str, float]) -> MabimsCalcProvider:
    """Seed a provider with continuous synthetic months per border case."""
    from datetime import timedelta

    # Blocks must be contiguous; one month per margin case in 1400.
    hypothetical = [
        ("1400-01", 30), ("1400-02", 29), ("1400-03", 30),
        ("1400-04", 29), ("1400-05", 30), ("1400-06", 29),
    ]
    g2h: dict[str, str] = {}
    cursor = SYNTHETIC_START
    for (ym, length), (_, _) in zip(hypothetical, sorted(margins.items()), strict=True):
        for day in range(1, length + 1):
            g_iso = (cursor + timedelta(days=day - 1)).isoformat()
            g2h[g_iso] = f"{ym}-{day:02d}"
        cursor += timedelta(days=length)
    h2g = {v: k for k, v in g2h.items()}
    provider = MabimsCalcProvider((1400, 1), SYNTHETIC_START)
    provider.seed_from_pairs(h2g, margins=margins)
    assert provider._blocks, "seed must produce blocks"
    return provider


def _sighting(
    alt: float,
    elong: float,
    alt2: float | None = None,
    elong2: float | None = None,
) -> MultiSiteSighting:
    sites = [
        SiteSighting(
            site="alpha",
            alt_deg=alt,
            alt_refracted_deg=alt,
            elong_deg=elong,
        )
    ]
    if alt2 is not None and elong2 is not None:
        sites.append(
            SiteSighting(
                site="beta",
                alt_deg=alt2,
                alt_refracted_deg=alt2,
                elong_deg=elong2,
            )
        )
    return MultiSiteSighting(evaluated_on=date(1400, 1, 29), sites=tuple(sites))


def test_decider_margin_uses_visible_site_not_best_failure():
    # Site alpha passes thin (0.1 above the altitude floor); only one site.
    ms = _sighting(alt=3.1, elong=7.0)
    assert ms.visible
    assert ms.decider_margin_deg() == pytest.approx(0.1)  # min(0.1, 0.6)


def test_decider_margin_negative_on_rejection():
    # Nothing passes: beta close on one criterion below the floor.
    ms = _sighting(alt=5.0, elong=6.35)
    assert not ms.visible
    assert ms.decider_margin_deg() < 0


def test_decider_margin_negative_even_when_failure_is_quasi():
    # Elongation just below 6.4 -> a clean rejection regardless of altitude.
    ms = _sighting(alt=10.0, elong=6.39)
    assert not ms.visible
    assert ms.decider_margin_deg() == pytest.approx(-0.01)


def test_decider_margin_zero_means_visible_on_threshold():
    # >= semantics: exactly on both thresholds counts as a pass with margin 0.
    ms = _sighting(alt=3.0, elong=6.4)
    assert ms.visible
    assert ms.decider_margin_deg() == 0.0


def test_borderline_only_flags_genuine_thin_passes():
    provider = _provider_with_margins(
        {
            "1400-01": 0.10,   # thin pass -> flagged
            "1400-02": 0.60,   # comfortable pass -> not flagged
            "1400-03": -0.05,  # rejected -> never flagged (the old bug)
            "1400-04": 0.25 - 1e-9,  # just under the cutoff -> flagged
            "1400-05": 0.0,    # exactly on threshold: pass, but 0 is not strict borderline
            "1400-06": -1.2,   # deep rejection -> not flagged
        }
    )
    flagged = provider.borderline_months()
    assert flagged == ["1400-01", "1400-04"]


def test_borderline_constant_matches_gate():
    assert BORDERLINE_MARGIN_DEG == 0.25

