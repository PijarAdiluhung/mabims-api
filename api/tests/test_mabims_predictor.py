from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.mabims_astro import criteria_on_day29, month_length
from app.mabims_predictor import next_hijri_month, predict_month_starts

API_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = API_DIR / "data" / "calendar_data.json"


def official_starts() -> list[tuple[date, tuple[int, int]]]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    g2h = raw["gregorian_to_hijri"]
    starts = []
    for g in sorted(g2h):
        hy, hm, hd = (int(x) for x in g2h[g].split("-"))
        if hd == 1:
            starts.append((date.fromisoformat(g), (hy, hm)))
    return starts


def test_hijri_month_rollover():
    assert next_hijri_month(1446, 7) == (1446, 8)
    assert next_hijri_month(1446, 12) == (1447, 1)


def test_month_lengths_are_29_or_30():
    starts = official_starts()
    for i in range(len(starts) - 1):
        actual = (starts[i + 1][0] - starts[i][0]).days
        computed = month_length(starts[i][0])
        assert computed == actual == computed


def test_predictor_reproduces_official_table():
    starts = official_starts()
    predicted = predict_month_starts(starts[0][1], starts[0][0], len(starts))
    assert len(predicted) == len(starts)
    for g, h in starts:
        assert predicted[h] == g, f"month {h}: predicted {predicted[h]}, official {g}"


def test_borderline_month_1448_06_is_visible():
    result = criteria_on_day29(date(2026, 11, 11))
    assert result.visible is True
