from __future__ import annotations

import math
from typing import Any

DEFAULT_CANDIDATE_THRESHOLDS = (-7.0, -12.0, -20.0)


def as_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def attention_score(
    one_day_pct: Any,
    five_day_pct: Any,
    twenty_day_pct: Any,
    volume_spike_vs_20d: Any = None,
    *,
    candidate_thresholds: tuple[float, float, float] = DEFAULT_CANDIDATE_THRESHOLDS,
) -> int:
    """Return a transparent 0-100 score for manual-review urgency.

    The score measures price-event strength and trading-volume confirmation only.
    It deliberately does not purport to measure value, solvency or expected return.
    """

    changes = (one_day_pct, five_day_pct, twenty_day_pct)
    ratios: list[float] = []
    for change, threshold in zip(changes, candidate_thresholds):
        number = as_number(change)
        denominator = abs(float(threshold))
        if number is None or denominator == 0:
            ratios.append(0.0)
        else:
            ratios.append(max(0.0, -number) / denominator)

    strongest_move = 55.0 * min(max(ratios, default=0.0), 1.0)
    breadth = 25.0 * min(sum(min(ratio, 1.0) for ratio in ratios) / 3.0, 1.0)
    confirmed_windows = sum(ratio >= 1.0 or math.isclose(ratio, 1.0, rel_tol=1e-10) for ratio in ratios)
    multi_window_confirmation = 5.0 * max(0, confirmed_windows - 1)

    volume = as_number(volume_spike_vs_20d)
    volume_confirmation = 0.0
    if volume is not None:
        volume_confirmation = 10.0 * min(max(volume - 1.0, 0.0), 1.0)

    return round(min(100.0, strongest_move + breadth + multi_window_confirmation + volume_confirmation))


def attention_band(score: Any) -> str:
    number = as_number(score) or 0.0
    if number >= 80:
        return "Immediate review"
    if number >= 60:
        return "High attention"
    if number >= 40:
        return "Review"
    return "Watch"


def risk_gate(
    avoid_flags: Any,
    market_cap: Any,
    classification: Any,
    headlines: Any,
) -> tuple[str, str]:
    """Return a first-pass risk/data gate without implying investment suitability."""

    flags = str(avoid_flags or "").strip()
    if flags.lower() == "nan":
        flags = ""

    classification_text = str(classification or "").strip().lower().replace("_", " ")
    headline_text = str(headlines or "").strip()
    if headline_text.lower() == "nan":
        headline_text = ""

    if flags:
        return "headline_risk", "Headline risk flag"
    if any(term in classification_text for term in ("permanent impairment", "high risk", "avoid")):
        return "ai_risk", "Automated high-risk flag"
    if as_number(market_cap) is None:
        return "size_unverified", "Market cap unverified"
    if not headline_text:
        return "news_unavailable", "No news context found"
    return "clear_first_pass", "No first-pass flags"
