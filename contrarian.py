from __future__ import annotations

import json
import os
import re
import smtplib
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yfinance as yf

try:
    from openai import OpenAI
except Exception:  # OpenAI is optional; the script still runs without it.
    OpenAI = None  # type: ignore


WATCHLIST_PATH = Path("config/watchlist_asx.csv")
REPORTS_DIR = Path("reports")
PERFORMANCE_LOG_PATH = REPORTS_DIR / "performance_log.csv"
DASHBOARD_PATH = Path("index.html")

MIN_MARKET_CAP = int(os.getenv("MIN_MARKET_CAP", "500000000"))
ONE_DAY_DROP = float(os.getenv("ONE_DAY_DROP", "-7"))
FIVE_DAY_DROP = float(os.getenv("FIVE_DAY_DROP", "-12"))
TWENTY_DAY_DROP = float(os.getenv("TWENTY_DAY_DROP", "-20"))

NEAR_ONE_DAY_DROP = float(os.getenv("NEAR_ONE_DAY_DROP", "-4"))
NEAR_FIVE_DAY_DROP = float(os.getenv("NEAR_FIVE_DAY_DROP", "-8"))
NEAR_TWENTY_DAY_DROP = float(os.getenv("NEAR_TWENTY_DAY_DROP", "-15"))

AUTO_ASX300 = os.getenv("AUTO_ASX300", "true").lower() in {"1", "true", "yes"}
MAX_NEWS_ITEMS = int(os.getenv("MAX_NEWS_ITEMS", "5"))
MAX_OPENAI_CLASSIFICATIONS = int(os.getenv("MAX_OPENAI_CLASSIFICATIONS", "12"))
YFINANCE_SLEEP_SECONDS = float(os.getenv("YFINANCE_SLEEP_SECONDS", "0.05"))

SEND_EMAIL = os.getenv("SEND_EMAIL", "true").lower() in {"1", "true", "yes"}
EMAIL_TO = os.getenv("EMAIL_TO", "balkissoc@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USERNAME")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

AVOID_KEYWORDS = [
    "administration",
    "administrator",
    "bankruptcy",
    "breach of covenant",
    "capital raising",
    "class action",
    "covenant",
    "debt restructure",
    "default",
    "dilution",
    "downgrade",
    "fraud",
    "going concern",
    "impairment",
    "insolvency",
    "investigation",
    "liquidity warning",
    "receivership",
    "regulatory investigation",
    "restatement",
    "share suspension",
    "solvency",
    "suspended",
    "trading halt",
]

REPORT_COLUMNS = [
    "rank",
    "signal_type",
    "ticker",
    "company",
    "last_price",
    "market_cap_aud_approx",
    "one_day_pct",
    "five_day_pct",
    "twenty_day_pct",
    "volume_spike_vs_20d",
    "trigger",
    "avoid_flags",
    "news_headlines",
    "openai_score",
    "openai_classification",
    "openai_rationale",
    "manual_review_notes",
    "error",
]


@dataclass
class ScanResult:
    output_path: Path
    latest_csv_path: Path
    near_miss_path: Path
    latest_near_miss_path: Path
    summary_path: Path
    performance_log_path: Path
    run_time: str
    today: str
    total_scanned: int
    candidates: int
    near_misses: int
    status_counts: dict[str, int]
    candidates_df: pd.DataFrame
    near_misses_df: pd.DataFrame
    performance_df: pd.DataFrame


def pct_change(current: float, previous: float) -> float | None:
    if previous is None or previous == 0:
        return None
    return (current / previous - 1) * 100


def safe_round(value: float | None, digits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def money(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"A${value:,.0f}"


def normalise_asx_ticker(code: str) -> str:
    code = str(code).strip().upper()
    code = re.sub(r"[^A-Z0-9]", "", code)
    if not code:
        return ""
    if code.endswith("AX"):
        return f"{code[:-2]}.AX"
    return f"{code}.AX"


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


def load_watchlist() -> pd.DataFrame:
    if AUTO_ASX300:
        try:
            watchlist = fetch_asx300_watchlist()
            if not watchlist.empty:
                return watchlist
        except Exception as exc:
            print(f"ASX 300 auto-fetch failed; falling back to config/watchlist_asx.csv: {exc}")

    if not WATCHLIST_PATH.exists():
        raise FileNotFoundError(f"Watchlist not found: {WATCHLIST_PATH}")

    watchlist = pd.read_csv(WATCHLIST_PATH)
    if "ticker" not in watchlist.columns:
        raise ValueError("Watchlist must contain a 'ticker' column.")

    if "company" not in watchlist.columns:
        watchlist["company"] = ""

    watchlist["ticker"] = watchlist["ticker"].apply(
        lambda x: str(x).strip().upper() if str(x).strip().upper().endswith(".AX") else normalise_asx_ticker(str(x))
    )
    watchlist["company"] = watchlist["company"].fillna("").astype(str).str.strip()
    watchlist = watchlist[watchlist["ticker"].str.endswith(".AX")]
    watchlist = watchlist.drop_duplicates(subset=["ticker"]).reset_index(drop=True)
    return watchlist[["ticker", "company"]]


def fetch_asx300_watchlist() -> pd.DataFrame:
    """
    Best-efforts free ASX 300 source.

    Wikipedia is used only to build a broad free watchlist. The screener later applies
    its own market-cap filter, so a stale constituent list is tolerable for monitoring.
    """
    url = "https://en.wikipedia.org/wiki/S%26P/ASX_300"
    headers = {"User-Agent": "contrarian-investing-monitor/1.0"}
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    tables = pd.read_html(response.text)
    candidates: list[pd.DataFrame] = []

    for table in tables:
        cols = [str(c).strip().lower() for c in table.columns]
        table.columns = cols
        code_col = next((c for c in cols if c in {"code", "asx code", "ticker", "symbol"}), None)
        company_col = next((c for c in cols if c in {"company", "company name", "name"}), None)
        if code_col:
            temp = pd.DataFrame()
            temp["ticker"] = table[code_col].apply(normalise_asx_ticker)
            temp["company"] = table[company_col].astype(str) if company_col else ""
            temp = temp[temp["ticker"].str.endswith(".AX")]
            if len(temp) >= 100:
                candidates.append(temp)

    if not candidates:
        raise ValueError("Could not locate a suitable ASX 300 table.")

    watchlist = pd.concat(candidates, ignore_index=True)
    watchlist = watchlist.drop_duplicates(subset=["ticker"]).reset_index(drop=True)
    print(f"Loaded {len(watchlist)} tickers from ASX 300 source.")
    return watchlist[["ticker", "company"]]


def assess_price_trigger(
    one_day: float | None,
    five_day: float | None,
    twenty_day: float | None,
    *,
    near_miss: bool = False,
) -> str:
    if near_miss:
        one, five, twenty = NEAR_ONE_DAY_DROP, NEAR_FIVE_DAY_DROP, NEAR_TWENTY_DAY_DROP
    else:
        one, five, twenty = ONE_DAY_DROP, FIVE_DAY_DROP, TWENTY_DAY_DROP

    triggers: list[str] = []
    if one_day is not None and one_day <= one:
        triggers.append(f"1D <= {one}%")
    if five_day is not None and five_day <= five:
        triggers.append(f"5D <= {five}%")
    if twenty_day is not None and twenty_day <= twenty:
        triggers.append(f"20D <= {twenty}%")
    return "; ".join(triggers)


def fetch_news(company: str, ticker: str) -> list[dict[str, str]]:
    query = f"{ticker.replace('.AX', '')} {company} ASX stock news"
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-AU&gl=AU&ceid=AU:en"
    headers = {"User-Agent": "contrarian-investing-monitor/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as exc:
        print(f"News fetch failed for {ticker}: {exc}")
        return []

    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:MAX_NEWS_ITEMS]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source = ""
        source_el = item.find("source")
        if source_el is not None and source_el.text:
            source = source_el.text.strip()

        if title:
            items.append({
                "title": title,
                "source": source,
                "published": pub_date,
                "link": link,
            })
    return items


def flatten_headlines(news_items: list[dict[str, str]]) -> str:
    return " | ".join(item["title"] for item in news_items if item.get("title"))


def identify_avoid_flags(headlines: str) -> str:
    text = headlines.lower()
    flags = sorted({keyword for keyword in AVOID_KEYWORDS if keyword in text})
    return "; ".join(flags)


def classify_with_openai(row: dict[str, Any], news_items: list[dict[str, str]]) -> dict[str, Any]:
    if not OPENAI_API_KEY or OpenAI is None:
        return {
            "openai_score": "",
            "openai_classification": "not_run",
            "openai_rationale": "OpenAI classification not run. Add OPENAI_API_KEY to GitHub Actions secrets to enable it.",
        }

    prompt = {
        "role": "user",
        "content": (
            "You are a cautious event-driven equities analyst. Assess whether a sharp fall in an ASX stock "
            "looks like a temporary panic, a justified sell-off, or permanent impairment risk. "
            "Do not recommend buying. Return strict JSON with keys: score, classification, rationale. "
            "Score: 1=avoid/permanent impairment risk, 2=high risk, 3=watch only, 4=possible temporary overreaction, 5=strong manual-review candidate.\n\n"
            f"Ticker: {row.get('ticker')}\n"
            f"Company: {row.get('company')}\n"
            f"Market cap approx: {row.get('market_cap_aud_approx')}\n"
            f"1D %: {row.get('one_day_pct')}\n"
            f"5D %: {row.get('five_day_pct')}\n"
            f"20D %: {row.get('twenty_day_pct')}\n"
            f"Volume spike: {row.get('volume_spike_vs_20d')}\n"
            f"Price trigger: {row.get('trigger')}\n"
            f"Avoid flags: {row.get('avoid_flags')}\n"
            f"News headlines: {json.dumps(news_items, ensure_ascii=False)}"
        ),
    }

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[prompt],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            "openai_score": parsed.get("score", ""),
            "openai_classification": parsed.get("classification", ""),
            "openai_rationale": parsed.get("rationale", ""),
        }
    except Exception as exc:
        return {
            "openai_score": "",
            "openai_classification": "error",
            "openai_rationale": f"OpenAI classification failed: {exc}",
        }


def screen_ticker(ticker: str, company: str) -> tuple[dict | None, str]:
    stock = yf.Ticker(ticker)

    try:
        hist = stock.history(period="3mo", interval="1d", auto_adjust=True)
        time.sleep(YFINANCE_SLEEP_SECONDS)
    except Exception as exc:
        return {
            "ticker": ticker,
            "company": company,
            "error": f"price fetch failed: {exc}",
        }, "error"

    if hist.empty or len(hist) < 21:
        return None, "insufficient_price_history"

    market_cap = get_market_cap(stock)
    if market_cap is None:
        return None, "market_cap_unavailable"
    if market_cap < MIN_MARKET_CAP:
        return None, "below_market_cap_threshold"

    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()

    if len(close) < 21:
        return None, "insufficient_close_history"

    last_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    five_day_close = float(close.iloc[-6])
    twenty_day_close = float(close.iloc[-21])

    one_day = pct_change(last_close, prev_close)
    five_day = pct_change(last_close, five_day_close)
    twenty_day = pct_change(last_close, twenty_day_close)

    candidate_trigger = assess_price_trigger(one_day, five_day, twenty_day, near_miss=False)
    near_miss_trigger = assess_price_trigger(one_day, five_day, twenty_day, near_miss=True)

    if candidate_trigger:
        signal_type = "candidate"
        trigger = candidate_trigger
    elif near_miss_trigger:
        signal_type = "near_miss"
        trigger = near_miss_trigger
    else:
        return None, "no_price_drop_trigger"

    avg_volume_20d = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else None
    last_volume = float(volume.iloc[-1]) if len(volume) else None
    volume_spike = last_volume / avg_volume_20d if avg_volume_20d and avg_volume_20d > 0 else None

    news_items = fetch_news(company, ticker)
    headlines = flatten_headlines(news_items)
    avoid_flags = identify_avoid_flags(headlines)

    row = {
        "rank": "",
        "signal_type": signal_type,
        "ticker": ticker,
        "company": company,
        "last_price": safe_round(last_close),
        "market_cap_aud_approx": market_cap,
        "one_day_pct": safe_round(one_day),
        "five_day_pct": safe_round(five_day),
        "twenty_day_pct": safe_round(twenty_day),
        "volume_spike_vs_20d": safe_round(volume_spike),
        "trigger": trigger,
        "avoid_flags": avoid_flags,
        "news_headlines": headlines,
        "openai_score": "",
        "openai_classification": "",
        "openai_rationale": "",
        "manual_review_notes": "Check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the event is temporary or permanent.",
        "error": "",
    }

    return row, signal_type


def add_openai_classifications(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    scored = 0
    for index, row in df.iterrows():
        if scored >= MAX_OPENAI_CLASSIFICATIONS:
            df.at[index, "openai_classification"] = "not_run_limit_reached"
            df.at[index, "openai_rationale"] = f"Skipped after {MAX_OPENAI_CLASSIFICATIONS} classifications to control API cost."
            continue

        news_items = [
            {"title": title.strip()}
            for title in str(row.get("news_headlines", "")).split("|")
            if title.strip()
        ]
        result = classify_with_openai(row.to_dict(), news_items)
        for key, value in result.items():
            df.at[index, key] = value
        scored += 1

    return df


def update_performance_log(today: str, candidates_df: pd.DataFrame, near_misses_df: pd.DataFrame) -> pd.DataFrame:
    REPORTS_DIR.mkdir(exist_ok=True)
    columns = [
        "signal_date",
        "ticker",
        "company",
        "signal_type",
        "signal_price",
        "current_price",
        "days_since_signal",
        "return_pct",
        "last_checked",
        "openai_score_at_signal",
        "openai_classification_at_signal",
    ]

    if PERFORMANCE_LOG_PATH.exists():
        log = pd.read_csv(PERFORMANCE_LOG_PATH)
    else:
        log = pd.DataFrame(columns=columns)

    new_signals = pd.concat([candidates_df, near_misses_df], ignore_index=True)
    for _, row in new_signals.iterrows():
        existing = (
            (log.get("signal_date", pd.Series(dtype=str)).astype(str) == today)
            & (log.get("ticker", pd.Series(dtype=str)).astype(str) == str(row["ticker"]))
            & (log.get("signal_type", pd.Series(dtype=str)).astype(str) == str(row["signal_type"]))
        )
        if not existing.any():
            log.loc[len(log)] = {
                "signal_date": today,
                "ticker": row["ticker"],
                "company": row["company"],
                "signal_type": row["signal_type"],
                "signal_price": row["last_price"],
                "current_price": row["last_price"],
                "days_since_signal": 0,
                "return_pct": 0,
                "last_checked": today,
                "openai_score_at_signal": row.get("openai_score", ""),
                "openai_classification_at_signal": row.get("openai_classification", ""),
            }

    for index, row in log.iterrows():
        ticker = str(row.get("ticker", "")).strip()
        if not ticker:
            continue
        try:
            hist = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=True)
            if not hist.empty:
                current_price = float(hist["Close"].dropna().iloc[-1])
                signal_price = float(row.get("signal_price", 0))
                signal_date = pd.to_datetime(row.get("signal_date"), errors="coerce")
                today_dt = pd.to_datetime(today)
                days_since = int((today_dt - signal_date).days) if pd.notna(signal_date) else ""
                return_pct = pct_change(current_price, signal_price)
                log.at[index, "current_price"] = safe_round(current_price)
                log.at[index, "days_since_signal"] = days_since
                log.at[index, "return_pct"] = safe_round(return_pct)
                log.at[index, "last_checked"] = today
        except Exception as exc:
            print(f"Performance revaluation failed for {ticker}: {exc}")

    log = log[columns]
    log.to_csv(PERFORMANCE_LOG_PATH, index=False)
    return log


def table_to_markdown(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_None._"
    table = df[cols].copy()
    if "market_cap_aud_approx" in table.columns:
        table["market_cap_aud_approx"] = table["market_cap_aud_approx"].apply(money)
    return table.to_markdown(index=False)


def build_markdown_summary(result: ScanResult) -> str:
    lines = [
        "# Latest Contrarian Monitor Summary",
        "",
        f"Run time: {result.run_time}",
        f"Watchlist scanned: {result.total_scanned}",
        f"Candidates found: {result.candidates}",
        f"Near misses found: {result.near_misses}",
        f"Candidate report: `{result.output_path.name}`",
        f"Near-miss report: `{result.near_miss_path.name}`",
        "",
        "## Thresholds",
        "",
        f"- Minimum market capitalisation: A${MIN_MARKET_CAP:,.0f}",
        f"- Candidate 1-day fall: {ONE_DAY_DROP}% or worse",
        f"- Candidate 5-day fall: {FIVE_DAY_DROP}% or worse",
        f"- Candidate 20-day fall: {TWENTY_DAY_DROP}% or worse",
        f"- Near-miss 1-day fall: {NEAR_ONE_DAY_DROP}% or worse",
        f"- Near-miss 5-day fall: {NEAR_FIVE_DAY_DROP}% or worse",
        f"- Near-miss 20-day fall: {NEAR_TWENTY_DAY_DROP}% or worse",
        "",
        "## Candidates",
        "",
    ]

    display_cols = [
        "rank",
        "ticker",
        "company",
        "last_price",
        "market_cap_aud_approx",
        "one_day_pct",
        "five_day_pct",
        "twenty_day_pct",
        "volume_spike_vs_20d",
        "trigger",
        "avoid_flags",
        "openai_score",
        "openai_classification",
    ]
    lines.append(table_to_markdown(result.candidates_df, display_cols))

    lines.extend(["", "## Near Misses", ""])
    lines.append(table_to_markdown(result.near_misses_df, display_cols))

    lines.extend([
        "",
        "## Manual review discipline",
        "",
        "Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.",
        "",
        "## Scan status",
        "",
    ])
    for status, count in sorted(result.status_counts.items()):
        lines.append(f"- {status}: {count}")

    if not result.performance_df.empty:
        perf = result.performance_df.sort_values(["signal_date", "ticker"], ascending=[False, True]).head(20)
        lines.extend(["", "## Latest Performance Log Snapshot", ""])
        lines.append(perf.to_markdown(index=False))

    return "\n".join(lines) + "\n"


def build_dashboard_html(result: ScanResult) -> str:
    def df_to_html(df: pd.DataFrame, cols: list[str]) -> str:
        if df.empty:
            return "<p><em>None.</em></p>"
        display = df[cols].copy()
        if "market_cap_aud_approx" in display.columns:
            display["market_cap_aud_approx"] = display["market_cap_aud_approx"].apply(money)
        return display.to_html(index=False, escape=True)

    cols = [
        "rank",
        "ticker",
        "company",
        "last_price",
        "market_cap_aud_approx",
        "one_day_pct",
        "five_day_pct",
        "twenty_day_pct",
        "trigger",
        "avoid_flags",
        "openai_score",
        "openai_classification",
    ]

    perf_html = "<p><em>No performance log yet.</em></p>"
    if not result.performance_df.empty:
        perf = result.performance_df.sort_values(["signal_date", "ticker"], ascending=[False, True]).head(25)
        perf_html = perf.to_html(index=False, escape=True)

    return f"""<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contrarian Investing Monitor</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 32px auto; padding: 0 20px; line-height: 1.45; color: #111827; }}
    h1 {{ color: #0b5ed7; }}
    .card {{ border: 1px solid #d0d7de; border-radius: 8px; padding: 18px; margin: 16px 0; background: #f8fafc; overflow-x: auto; }}
    .warning {{ border-left: 5px solid #f59e0b; background: #fffbeb; }}
    .button {{ display: inline-block; padding: 10px 14px; margin: 6px 8px 6px 0; background: #0b5ed7; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
    .button.secondary {{ background: #374151; }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    .metric {{ display: inline-block; min-width: 170px; padding: 12px; margin: 6px 10px 6px 0; border: 1px solid #d0d7de; border-radius: 8px; background: white; }}
    .metric strong {{ display:block; font-size: 22px; }}
  </style>
</head>
<body>
  <h1>Contrarian Investing Monitor</h1>

  <div class="card warning">
    <strong>Research aide only.</strong> This tool screens for possible contrarian opportunities. It does not recommend trades, verify solvency, or replace manual review of ASX announcements and financial statements.
  </div>

  <div class="card">
    <h2>Latest run</h2>
    <div class="metric"><span>Run time</span><strong>{result.run_time}</strong></div>
    <div class="metric"><span>Watchlist scanned</span><strong>{result.total_scanned}</strong></div>
    <div class="metric"><span>Candidates</span><strong>{result.candidates}</strong></div>
    <div class="metric"><span>Near misses</span><strong>{result.near_misses}</strong></div>
    <p>
      <a class="button" href="https://github.com/balkissoc/contrarian-investing-monitor/actions/workflows/daily.yml">Run GitHub Action</a>
      <a class="button secondary" href="https://github.com/balkissoc/contrarian-investing-monitor/tree/main/reports">Reports Folder</a>
      <a class="button secondary" href="reports/latest_candidates.csv">Latest Candidates CSV</a>
      <a class="button secondary" href="reports/latest_near_misses.csv">Latest Near Misses CSV</a>
      <a class="button secondary" href="reports/performance_log.csv">Performance Log CSV</a>
    </p>
  </div>

  <div class="card">
    <h2>Candidates</h2>
    {df_to_html(result.candidates_df, cols)}
  </div>

  <div class="card">
    <h2>Near Misses</h2>
    {df_to_html(result.near_misses_df, cols)}
  </div>

  <div class="card">
    <h2>Performance Log</h2>
    {perf_html}
  </div>

  <div class="card">
    <h2>Thresholds</h2>
    <table>
      <tr><th>Test</th><th>Candidate</th><th>Near miss</th></tr>
      <tr><td>Minimum market capitalisation</td><td colspan="2">A${MIN_MARKET_CAP:,.0f}</td></tr>
      <tr><td>1-day fall</td><td>{ONE_DAY_DROP}% or worse</td><td>{NEAR_ONE_DAY_DROP}% or worse</td></tr>
      <tr><td>5-day fall</td><td>{FIVE_DAY_DROP}% or worse</td><td>{NEAR_FIVE_DAY_DROP}% or worse</td></tr>
      <tr><td>20-day fall</td><td>{TWENTY_DAY_DROP}% or worse</td><td>{NEAR_TWENTY_DAY_DROP}% or worse</td></tr>
    </table>
  </div>
</body>
</html>
"""


def build_email_body(result: ScanResult) -> str:
    display_cols = [
        "rank",
        "ticker",
        "company",
        "last_price",
        "market_cap_aud_approx",
        "one_day_pct",
        "five_day_pct",
        "twenty_day_pct",
        "trigger",
        "avoid_flags",
        "openai_score",
        "openai_classification",
    ]

    body = [
        "Daily contrarian investing monitor",
        "",
        f"Run time: {result.run_time}",
        f"Watchlist scanned: {result.total_scanned}",
        f"Candidates found: {result.candidates}",
        f"Near misses found: {result.near_misses}",
        "",
        "Candidate thresholds:",
        f"- Market cap: A${MIN_MARKET_CAP:,.0f}+",
        f"- 1-day fall: {ONE_DAY_DROP}% or worse",
        f"- 5-day fall: {FIVE_DAY_DROP}% or worse",
        f"- 20-day fall: {TWENTY_DAY_DROP}% or worse",
        "",
        "Candidates:",
        table_to_markdown(result.candidates_df, display_cols),
        "",
        "Near misses:",
        table_to_markdown(result.near_misses_df.head(15), display_cols),
        "",
        "Manual review discipline: check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the adverse event is temporary or permanent.",
    ]
    return "\n".join(body)


def send_email_report(result: ScanResult) -> None:
    if not SEND_EMAIL:
        print("Email disabled by SEND_EMAIL setting.")
        return

    if not SMTP_USERNAME or not SMTP_PASSWORD or not EMAIL_FROM or not EMAIL_TO:
        print("Email not sent. Missing SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM or EMAIL_TO secret/env value.")
        return

    subject = f"Contrarian monitor: {result.candidates} candidate(s), {result.near_misses} near miss(es)"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.set_content(build_email_body(result))

    for path in [result.output_path, result.near_miss_path, result.performance_log_path]:
        if path.exists():
            message.add_attachment(
                path.read_bytes(),
                maintype="text",
                subtype="csv",
                filename=path.name,
            )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

    print(f"Email sent to {EMAIL_TO}.")


def sort_signal_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values(
        by=["one_day_pct", "five_day_pct", "twenty_day_pct"],
        ascending=True,
        na_position="last",
    ).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df


def run_scan() -> ScanResult:
    watchlist = load_watchlist()
    rows: list[dict] = []
    status_counts: dict[str, int] = {}

    for _, row in watchlist.iterrows():
        ticker = str(row["ticker"]).strip()
        company = str(row.get("company", "")).strip()
        result, status = screen_ticker(ticker, company)
        status_counts[status] = status_counts.get(status, 0) + 1
        if result:
            rows.append(result)

    REPORTS_DIR.mkdir(exist_ok=True)
    run_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    output_path = REPORTS_DIR / f"contrarian_candidates_{today}.csv"
    latest_csv_path = REPORTS_DIR / "latest_candidates.csv"
    near_miss_path = REPORTS_DIR / f"near_misses_{today}.csv"
    latest_near_miss_path = REPORTS_DIR / "latest_near_misses.csv"
    summary_path = REPORTS_DIR / "latest_summary.md"

    all_df = pd.DataFrame(rows, columns=REPORT_COLUMNS)
    candidates_df = all_df[all_df["signal_type"] == "candidate"].copy() if not all_df.empty else pd.DataFrame(columns=REPORT_COLUMNS)
    near_misses_df = all_df[all_df["signal_type"] == "near_miss"].copy() if not all_df.empty else pd.DataFrame(columns=REPORT_COLUMNS)

    candidates_df = sort_signal_df(candidates_df)
    near_misses_df = sort_signal_df(near_misses_df)

    candidates_df = add_openai_classifications(candidates_df)
    near_misses_df = add_openai_classifications(near_misses_df)

    candidates_df.to_csv(output_path, index=False)
    candidates_df.to_csv(latest_csv_path, index=False)
    near_misses_df.to_csv(near_miss_path, index=False)
    near_misses_df.to_csv(latest_near_miss_path, index=False)

    performance_df = update_performance_log(today, candidates_df, near_misses_df)

    result = ScanResult(
        output_path=output_path,
        latest_csv_path=latest_csv_path,
        near_miss_path=near_miss_path,
        latest_near_miss_path=latest_near_miss_path,
        summary_path=summary_path,
        performance_log_path=PERFORMANCE_LOG_PATH,
        run_time=run_time,
        today=today,
        total_scanned=len(watchlist),
        candidates=len(candidates_df),
        near_misses=len(near_misses_df),
        status_counts=status_counts,
        candidates_df=candidates_df,
        near_misses_df=near_misses_df,
        performance_df=performance_df,
    )

    summary_path.write_text(build_markdown_summary(result), encoding="utf-8")
    DASHBOARD_PATH.write_text(build_dashboard_html(result), encoding="utf-8")
    return result


def main() -> None:
    result = run_scan()
    send_email_report(result)

    print(f"Created candidate report: {result.output_path}")
    print(f"Updated latest candidate report: {result.latest_csv_path}")
    print(f"Created near-miss report: {result.near_miss_path}")
    print(f"Updated latest near-miss report: {result.latest_near_miss_path}")
    print(f"Updated summary: {result.summary_path}")
    print(f"Updated performance log: {result.performance_log_path}")
    print(f"Updated dashboard: {DASHBOARD_PATH}")
    print(f"Watchlist scanned: {result.total_scanned}")
    print(f"Candidates found: {result.candidates}")
    print(f"Near misses found: {result.near_misses}")
    print("Status counts:")
    for status, count in sorted(result.status_counts.items()):
        print(f"- {status}: {count}")

    if result.candidates_df.empty:
        print("No candidates triggered today.")
    else:
        print(result.candidates_df.to_string(index=False))


if __name__ == "__main__":
    main()
