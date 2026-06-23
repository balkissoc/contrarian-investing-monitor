from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
import yfinance as yf

WATCHLIST_PATH = Path("config/watchlist_asx.csv")
REPORTS_DIR = Path("reports")

MIN_MARKET_CAP = int(os.getenv("MIN_MARKET_CAP", "500000000"))
ONE_DAY_DROP = float(os.getenv("ONE_DAY_DROP", "-7"))
FIVE_DAY_DROP = float(os.getenv("FIVE_DAY_DROP", "-12"))
TWENTY_DAY_DROP = float(os.getenv("TWENTY_DAY_DROP", "-20"))

SEND_EMAIL = os.getenv("SEND_EMAIL", "true").lower() in {"1", "true", "yes"}
EMAIL_TO = os.getenv("EMAIL_TO", "balkissoc@gmail.com")
EMAIL_FROM = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USERNAME")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

REPORT_COLUMNS = [
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
    "manual_review_notes",
    "error",
]


@dataclass
class ScanResult:
    output_path: Path
    summary_path: Path
    latest_csv_path: Path
    run_time: str
    total_scanned: int
    candidates: int
    status_counts: dict[str, int]
    dataframe: pd.DataFrame


def pct_change(current: float, previous: float) -> float | None:
    if previous is None or previous == 0:
        return None
    return (current / previous - 1) * 100


def safe_round(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def money(value: int | float | None) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"A${value:,.0f}"


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


def screen_ticker(ticker: str, company: str) -> tuple[dict | None, str]:
    stock = yf.Ticker(ticker)

    try:
        hist = stock.history(period="2mo", interval="1d", auto_adjust=True)
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

    trigger = assess_trigger(one_day, five_day, twenty_day)
    if not trigger:
        return None, "no_price_drop_trigger"

    avg_volume_20d = float(volume.iloc[-21:-1].mean()) if len(volume) >= 21 else None
    last_volume = float(volume.iloc[-1]) if len(volume) else None
    volume_spike = last_volume / avg_volume_20d if avg_volume_20d and avg_volume_20d > 0 else None

    return {
        "rank": "",
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
        "error": "",
    }, "candidate"


def build_markdown_summary(result: ScanResult) -> str:
    lines = [
        "# Latest Contrarian Monitor Summary",
        "",
        f"Run time: {result.run_time}",
        f"Watchlist scanned: {result.total_scanned}",
        f"Candidates found: {result.candidates}",
        f"Report file: `{result.output_path.name}`",
        "",
        "## Thresholds",
        "",
        f"- Minimum market capitalisation: A${MIN_MARKET_CAP:,.0f}",
        f"- 1-day fall: {ONE_DAY_DROP}% or worse",
        f"- 5-day fall: {FIVE_DAY_DROP}% or worse",
        f"- 20-day fall: {TWENTY_DAY_DROP}% or worse",
        "",
    ]

    if result.candidates:
        lines.extend(["## Candidates", ""])
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
        ]
        table = result.dataframe[display_cols].copy()
        table["market_cap_aud_approx"] = table["market_cap_aud_approx"].apply(money)
        lines.append(table.to_markdown(index=False))
        lines.extend([
            "",
            "## Manual review discipline",
            "",
            "Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.",
        ])
    else:
        lines.extend([
            "## Result",
            "",
            "No stocks triggered the price-drop screen in this run.",
        ])

    lines.extend(["", "## Scan status", ""])
    for status, count in sorted(result.status_counts.items()):
        lines.append(f"- {status}: {count}")

    return "\n".join(lines) + "\n"


def build_email_body(result: ScanResult) -> str:
    if result.candidates == 0:
        return (
            "Daily contrarian investing monitor\n\n"
            f"Run time: {result.run_time}\n"
            f"Watchlist scanned: {result.total_scanned}\n"
            "Candidates found: 0\n\n"
            "No ASX stocks in the watchlist triggered the configured price-drop thresholds today.\n\n"
            "Thresholds:\n"
            f"- Market cap: A${MIN_MARKET_CAP:,.0f}+\n"
            f"- 1-day fall: {ONE_DAY_DROP}% or worse\n"
            f"- 5-day fall: {FIVE_DAY_DROP}% or worse\n"
            f"- 20-day fall: {TWENTY_DAY_DROP}% or worse\n"
        )

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
    ]
    table = result.dataframe[display_cols].copy()
    table["market_cap_aud_approx"] = table["market_cap_aud_approx"].apply(money)

    return (
        "Daily contrarian investing monitor\n\n"
        f"Run time: {result.run_time}\n"
        f"Watchlist scanned: {result.total_scanned}\n"
        f"Candidates found: {result.candidates}\n\n"
        f"{table.to_string(index=False)}\n\n"
        "Manual review discipline: check ASX announcements, debt, liquidity, free cash flow, regulatory issues and whether the adverse event is temporary or permanent.\n"
    )


def send_email_report(result: ScanResult) -> None:
    if not SEND_EMAIL:
        print("Email disabled by SEND_EMAIL setting.")
        return

    if not SMTP_USERNAME or not SMTP_PASSWORD or not EMAIL_FROM or not EMAIL_TO:
        print("Email not sent. Missing SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM or EMAIL_TO secret/env value.")
        return

    subject_status = f"{result.candidates} candidate(s)" if result.candidates else "no candidates"
    subject = f"Contrarian monitor: {subject_status}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.set_content(build_email_body(result))

    if result.output_path.exists():
        message.add_attachment(
            result.output_path.read_bytes(),
            maintype="text",
            subtype="csv",
            filename=result.output_path.name,
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)

    print(f"Email sent to {EMAIL_TO}.")


def run_scan() -> ScanResult:
    if not WATCHLIST_PATH.exists():
        raise FileNotFoundError(f"Watchlist not found: {WATCHLIST_PATH}")

    watchlist = pd.read_csv(WATCHLIST_PATH)
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
    summary_path = REPORTS_DIR / "latest_summary.md"

    df = pd.DataFrame(rows, columns=REPORT_COLUMNS)
    if not df.empty:
        df = df.sort_values(
            by=["one_day_pct", "five_day_pct", "twenty_day_pct"],
            ascending=True,
            na_position="last",
        ).reset_index(drop=True)
        df["rank"] = range(1, len(df) + 1)

    df.to_csv(output_path, index=False)
    df.to_csv(latest_csv_path, index=False)

    result = ScanResult(
        output_path=output_path,
        summary_path=summary_path,
        latest_csv_path=latest_csv_path,
        run_time=run_time,
        total_scanned=len(watchlist),
        candidates=len(df),
        status_counts=status_counts,
        dataframe=df,
    )

    summary_path.write_text(build_markdown_summary(result), encoding="utf-8")
    return result


def main() -> None:
    result = run_scan()
    send_email_report(result)

    print(f"Created report: {result.output_path}")
    print(f"Updated latest report: {result.latest_csv_path}")
    print(f"Updated summary: {result.summary_path}")
    print(f"Watchlist scanned: {result.total_scanned}")
    print(f"Candidates found: {result.candidates}")
    print("Status counts:")
    for status, count in sorted(result.status_counts.items()):
        print(f"- {status}: {count}")

    if result.dataframe.empty:
        print("No candidates triggered today.")
    else:
        print(result.dataframe.to_string(index=False))


if __name__ == "__main__":
    main()
