from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

import contrarian


HISTORY_RETRIES = 3


def robust_screen_ticker(ticker: str, company: str) -> tuple[dict | None, str]:
    stock = yf.Ticker(ticker)
    hist = pd.DataFrame()
    last_error: Exception | None = None

    for attempt in range(HISTORY_RETRIES):
        try:
            hist = stock.history(period="3mo", interval="1d", auto_adjust=True)
            if not hist.empty:
                break
        except Exception as exc:
            last_error = exc
        if attempt < HISTORY_RETRIES - 1:
            time.sleep(0.7 * (attempt + 1))

    if hist.empty:
        detail = f": {last_error}" if last_error else ""
        return {
            "ticker": ticker,
            "company": company,
            "error": f"price fetch failed after {HISTORY_RETRIES} attempts{detail}",
        }, "error"

    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()
    if len(close) < 21:
        return None, "insufficient_price_history"

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    five_day_close = float(close.iloc[-6])
    twenty_day_close = float(close.iloc[-21])

    one_day = contrarian.pct_change(last_close, prev_close)
    five_day = contrarian.pct_change(last_close, five_day_close)
    twenty_day = contrarian.pct_change(last_close, twenty_day_close)

    candidate_trigger = contrarian.assess_price_trigger(one_day, five_day, twenty_day, near_miss=False)
    near_miss_trigger = contrarian.assess_price_trigger(one_day, five_day, twenty_day, near_miss=True)

    if candidate_trigger:
        signal_type = "candidate"
        trigger = candidate_trigger
    elif near_miss_trigger:
        signal_type = "near_miss"
        trigger = near_miss_trigger
    else:
        # Do not make an additional Yahoo market-cap request for the vast majority
        # of securities that have not triggered a price event.
        return None, "no_price_drop_trigger"

    # Market cap is checked only after a price event has triggered. This dramatically
    # reduces network calls for a ~300-stock universe and therefore reduces rate-limit
    # failures. Membership of the broad A300 universe provides a useful fallback if
    # Yahoo temporarily cannot return market cap for an otherwise valid signal.
    market_cap = contrarian.get_market_cap(stock)
    market_cap_status = ""
    if market_cap is not None and market_cap < contrarian.MIN_MARKET_CAP:
        return None, "below_market_cap_threshold"
    if market_cap is None:
        market_cap_status = "Market cap temporarily unavailable; retained because ticker is in the broad A300 universe."

    avg_volume_20d = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else None
    last_volume = float(volume.iloc[-1]) if len(volume) else None
    volume_spike = last_volume / avg_volume_20d if avg_volume_20d and avg_volume_20d > 0 else None

    news_items = contrarian.fetch_news(company, ticker)
    headlines = contrarian.flatten_headlines(news_items)
    avoid_flags = contrarian.identify_avoid_flags(headlines)

    row = {
        "rank": "",
        "signal_type": signal_type,
        "ticker": ticker,
        "company": company,
        "last_price": contrarian.safe_round(last_close),
        "market_cap_aud_approx": market_cap,
        "one_day_pct": contrarian.safe_round(one_day),
        "five_day_pct": contrarian.safe_round(five_day),
        "twenty_day_pct": contrarian.safe_round(twenty_day),
        "volume_spike_vs_20d": contrarian.safe_round(volume_spike),
        "trigger": trigger,
        "avoid_flags": avoid_flags,
        "news_headlines": headlines,
        "openai_score": "",
        "openai_classification": "",
        "openai_rationale": "",
        "manual_review_notes": (
            "Check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the event is temporary or permanent. "
            + market_cap_status
        ).strip(),
        "error": "",
    }
    return row, signal_type


def main() -> None:
    contrarian.screen_ticker = robust_screen_ticker
    contrarian.main()


if __name__ == "__main__":
    main()
