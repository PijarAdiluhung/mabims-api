from __future__ import annotations

from datetime import date

from app.mabims_predictor import month_length, next_hijri_month, predict_month_starts


def test_next_hijri_month_normal():
    assert next_hijri_month(1446, 5) == (1446, 6)


def test_next_hijri_month_year_cross():
    assert next_hijri_month(1446, 12) == (1447, 1)


def test_month_length_returns_29_or_30():
    result = month_length(date(2025, 1, 1))
    assert result in (29, 30)


def test_predict_month_starts_count():
    starts = predict_month_starts((1446, 9), date(2025, 3, 1), 6)
    assert len(starts) == 6


def test_predict_month_starts_consecutive():
    starts = predict_month_starts((1446, 9), date(2025, 3, 1), 6)
    keys = sorted(starts.keys())
    for i in range(len(keys) - 1):
        y1, m1 = keys[i]
        y2, m2 = keys[i + 1]
        expected_next = next_hijri_month(y1, m1)
        assert (y2, m2) == expected_next
        assert starts[(y2, m2)] >= starts[(y1, m1)]


def test_predict_month_starts_known_anchor():
    starts = predict_month_starts((1446, 9), date(2025, 3, 1), 3)
    assert starts[(1446, 9)] == date(2025, 3, 1)
