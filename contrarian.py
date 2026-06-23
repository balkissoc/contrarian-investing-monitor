from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

WATCHLIST_PATH = Path("config/watchlist_asx.csv")
REPORTS_DIR = Path("reports")

MIN_MARKET_CAP = int(os.getenv("MIN_MARKET_CAP", "500000000"))
ONE_DAY_DROP = float(os.getenv("ONE_DAY_DROP", "-7"))
FIVE_DAY_DROP = float(os.getenv("FIVE_DAY_DROP", "-12"))
TWENTY_DAY_DROP = float(os.getenv("TWENTY_DAY_DROP", "-20"))


def pct_change(current: float, previous: float) -> float | None:
    if previous is None or previous == 0:
        return None
    return (current / previous - 1) * 100


def safe_round(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def get_market_cap(stock: yf.Ticker) -> int | None:
    try:
        fast_info = getattr(stock, "fast_info", None)
        if fast_info:
            market_cap = fast_info.get("market_cap")
            if market_cap:
                return int(market_cap)
    except Exception:
        pass

    try:
        market_cap = stock.info.get("marketCap")
        if market_cap:
            return int(market_cap)
    except Exception:
        pass

    return None


def assess_trigger(one_day: float | None, five_day: float | None, twenty_day: float | None) -> str:
    triggers: list[str] = []
    if one_day is not None and one_day <= ONE_DAY_DROP:
        triggers.append(f"1D <= {ONE_DAY_DROP}%")
    if five_day is not None and five_day <= FIVE_DAY_DROP:
        triggers.append(f"5D <= {FIVE_DAY_DROP}%")
    if twenty_day is not None and twenty_day <= TWENTY_DAY_DROP:
        triggers.append(f"20D <= {TWENTY_DAY_DROP}%")
    return "; ".join(triggers)


def screen_ticker(ticker: str, company: str) -> dict | None:
    stock = yf.Ticker(ticker)

    try:
        hist = stock.history(period="2mo", interval="1d", auto_adjust=True)
    except Exception as exc:
        return {
            "ticker": ticker,
            "company": company,
            "error": f"price fetch failed: {exc}",
        }

    if hist.empty or len(hist) < 21:
        return None

    market_cap = get_market_cap(stock)
    if market_cap is None or market_cap < MIN_MARKET_CAP:
        return None

    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()

    if len(close) < 21:
        return None

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    five_day_close = float(close.iloc[-6])
    twenty_day_close = float(close.iloc[-21])

    one_day = pct_change(last_close, prev_close)
    five_day = pct_change(last_close, five_day_close)
    twenty_day = pct_change(last_close, twenty_day_close)

    trigger = assess_trigger(one_day, five_day, twenty_day)
    if not trigger:
        return None

    avg_volume_20d = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else None
    last_volume = float(volume.iloc[-1]) if len(volume) else None
    volume_spike = last_volume / avg_volume_20d if avg_volume_20d and avg_volume_20d > 0 else None

    return {
        "ticker": ticker,
        "company": company,
        "last_price": safe_round(last_close),
        "market_cap_aud_approx": market_cap,
        "one_day_pct": safe_round(one_day),
        "five_day_pct": safe_round(five_day),
        "twenty_day_pct": safe_round(twenty_day),
        "volume_spike_vs_20d": safe_round(volume_spike),
        "trigger": trigger,
        "manual_review_notes": "Check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the event is temporary or permanent.",
    }


def main() -> None:
    if not WATCHLIST_PATH.exists():
        raise FileNotFoundError(f"Watchlist not found: {WATCHLIST_PATH}")

    watchlist = pd.read_csv(WATCHLIST_PATH)
    rows: list[dict] = []

    for _, row in watchlist.iterrows():
        ticker = str(row["ticker"]).strip()
        company = str(row.get("company", "")).strip()
        result = screen_ticker(ticker, company)
        if result:
            rows.append(result)

    REPORTS_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = REPORTS_DIR / f"contrarian_candidates_{today}.csv"

    df = pd.DataFrame(rows)
    if not df.empty and "one_day_pct" in df.columns:
        df = df.sort_values(
            by=["one_day_pct", "five_day_pct", "twenty_day_pct"],
            ascending=True,
            na_position="last",
        )

    df.to_csv(output_path, index=False)

    print(f"Created report: {output_path}")
    if df.empty:
        print("No candidates triggered today.")
    else:
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
