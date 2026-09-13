from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

import contrarian
import research

HISTORY_RETRIES = 3
LATEST_MARKS: dict[str, dict] = {}


def robust_screen_ticker(ticker: str, company: str) -> tuple[dict | None, str]:
    stock = yf.Ticker(ticker)
    hist = pd.DataFrame()
    last_error: Exception | None = None

    for attempt in range(HISTORY_RETRIES):
        try:
            hist = stock.history(period="2y", interval="1d", auto_adjust=True)
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
    actions = []
    for date, bar in hist.iterrows():
        dividend = research.as_number(bar.get("Dividends")) or 0
        split = research.as_number(bar.get("Stock Splits")) or 0
        if dividend or split:
            actions.append({"date": pd.Timestamp(date).date().isoformat(), "dividend": dividend, "split": split})
    LATEST_MARKS[ticker] = {"ticker": ticker, "company": company, "price": last_close,
                            "date": contrarian.price_date_from_history(hist), "actions": actions}
    prev_close = float(close.iloc[-2])
    five_day_close = float(close.iloc[-6])
    twenty_day_close = float(close.iloc[-21])

    one_day = contrarian.pct_change(last_close, prev_close)
    five_day = contrarian.pct_change(last_close, five_day_close)
    twenty_day = contrarian.pct_change(last_close, twenty_day_close)

    candidate_trigger = contrarian.assess_price_trigger(one_day, five_day, twenty_day, near_miss=False)
    near_miss_trigger = contrarian.assess_price_trigger(one_day, five_day, twenty_day, near_miss=True)
    context = research.price_context(hist)
    LATEST_MARKS[ticker]["median_turnover"] = context["median_turnover_20d_aud"]

    if candidate_trigger:
        signal_type = "candidate"
        trigger = candidate_trigger
    elif near_miss_trigger:
        signal_type = "near_miss"
        trigger = near_miss_trigger
    elif context["volatility_trigger"]:
        signal_type = "near_miss"
        trigger = "Volatility watch: " + context["volatility_trigger"]
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
    company, enriched_market_cap = contrarian.improve_company_name(stock, company, market_cap)
    if enriched_market_cap is not None:
        market_cap = enriched_market_cap
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
    gate_key, gate_label = contrarian.risk_gate(avoid_flags, market_cap, "", headlines)
    review_score = contrarian.attention_score(
        one_day,
        five_day,
        twenty_day,
        volume_spike,
        candidate_thresholds=(
            contrarian.ONE_DAY_DROP,
            contrarian.FIVE_DAY_DROP,
            contrarian.TWENTY_DAY_DROP,
        ),
    )

    row = {
        "rank": "",
        "signal_type": signal_type,
        "ticker": ticker,
        "company": company,
        "price_date": contrarian.price_date_from_history(hist),
        "last_price": contrarian.safe_round(last_close),
        "market_cap_aud_approx": market_cap,
        "one_day_pct": contrarian.safe_round(one_day),
        "five_day_pct": contrarian.safe_round(five_day),
        "twenty_day_pct": contrarian.safe_round(twenty_day),
        "volume_spike_vs_20d": contrarian.safe_round(volume_spike),
        "trigger": trigger,
        "attention_score": review_score,
        "attention_band": contrarian.attention_band(review_score),
        "risk_gate": gate_key,
        "risk_gate_label": gate_label,
        "avoid_flags": avoid_flags,
        "news_headlines": headlines,
        "news_sources": contrarian.flatten_news_field(news_items, "source"),
        "news_urls": contrarian.flatten_news_field(news_items, "link"),
        "news_published": contrarian.flatten_news_field(news_items, "published"),
        "openai_score": "",
        "openai_classification": "",
        "openai_rationale": "",
        "manual_review_notes": (
            "Check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the event is temporary or permanent. "
            + market_cap_status
        ).strip(),
        "error": "",
    }
    row.update(context)
    today = contrarian.datetime.now(contrarian.PERTH_TZ).date().isoformat()
    return research.enrich_signal(row, stock, hist, today), signal_type


def main() -> None:
    if not research.CACHE_PATH.exists():
        research.write_json(research.CACHE_PATH, {})
    contrarian.screen_ticker = robust_screen_ticker
    contrarian.main()
    research.write_json(contrarian.REPORTS_DIR / "latest_prices.json", LATEST_MARKS)
    if research.SETTINGS["experimental_universe_enabled"]:
        run_experimental()
    else:
        pd.DataFrame(columns=contrarian.REPORT_COLUMNS).to_csv("reports/experimental_candidates.csv", index=False)
    from dashboard import main as build_dashboard
    build_dashboard()


def run_experimental() -> None:
    """Explicitly supplied broader names; never mix them into the A300 baseline."""
    names = pd.read_csv("config/experimental_watchlist.csv").fillna("")
    baseline = set(contrarian.load_watchlist()["ticker"])
    previous_cap = contrarian.MIN_MARKET_CAP
    rows = []
    try:
        contrarian.MIN_MARKET_CAP = research.SETTINGS["experimental_min_market_cap_aud"]
        for _, entry in names.drop_duplicates("ticker").iterrows():
            ticker = contrarian.normalise_asx_ticker(str(entry["ticker"]))
            if ticker in baseline:
                continue
            row, status = robust_screen_ticker(ticker, str(entry.get("company", "")))
            if row and status in {"candidate", "near_miss"}:
                row["universe_lane"] = "experimental"
                row["research_status"] = "experimental_incomplete"
                rows.append(row)
    finally:
        contrarian.MIN_MARKET_CAP = previous_cap
    pd.DataFrame(rows, columns=contrarian.REPORT_COLUMNS).to_csv("reports/experimental_candidates.csv", index=False)


if __name__ == "__main__":
    main()
