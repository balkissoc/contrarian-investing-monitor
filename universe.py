from __future__ import annotations

import html
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


WATCHLIST_PATH = Path("config/watchlist_asx.csv")
MIN_ACCEPTABLE = 250
MAX_ACCEPTABLE = 380

SOURCES = [
    ("Market Index ASX 300", "https://www.marketindex.com.au/asx300"),
    ("S&P Dow Jones ASX 300", "https://www.spglobal.com/spdji/en/indices/equity/sp-asx-300/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}


def normalise_code(value: object) -> str:
    code = str(value).strip().upper()
    code = re.sub(r"\.AX$", "", code)
    code = re.sub(r"[^A-Z0-9]", "", code)
    if not re.fullmatch(r"[A-Z0-9]{2,5}", code):
        return ""
    return f"{code}.AX"


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [" ".join(str(x) for x in col if str(x) != "nan").strip() for col in out.columns]
    else:
        out.columns = [str(c).strip() for c in out.columns]
    return out


def table_candidate(df: pd.DataFrame) -> pd.DataFrame | None:
    df = flatten_columns(df)
    lower = {str(c).strip().lower(): c for c in df.columns}

    code_col = next(
        (lower[k] for k in lower if k in {"code", "ticker", "symbol", "asx code"} or k.endswith(" code")),
        None,
    )
    company_col = next(
        (
            lower[k]
            for k in lower
            if k in {"company", "company name", "name", "constituent", "holding name"}
            or "company" in k
            or "constituent" in k
            or "holding name" in k
        ),
        None,
    )

    if code_col is None:
        return None

    out = pd.DataFrame()
    out["ticker"] = df[code_col].map(normalise_code)
    out["company"] = df[company_col].astype(str).str.strip() if company_col is not None else ""
    out = out[out["ticker"] != ""]
    out = out.drop_duplicates(subset=["ticker"]).reset_index(drop=True)
    return out


def extract_from_tables(text: str) -> pd.DataFrame | None:
    try:
        tables = pd.read_html(StringIO(text))
    except Exception:
        return None

    best: pd.DataFrame | None = None
    for table in tables:
        candidate = table_candidate(table)
        if candidate is None:
            continue
        if best is None or len(candidate) > len(best):
            best = candidate
    return best


def strip_tags(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_marketindex_links(text: str) -> pd.DataFrame | None:
    pairs: list[tuple[str, str]] = []

    # Market Index stock links commonly use /asx/CODE. Capture the visible text as a
    # best-efforts company label; the ticker is what the scanner strictly requires.
    for match in re.finditer(
        r'href=["\']/asx/([a-z0-9]{2,5})["\'][^>]*>(.*?)</a>',
        text,
        flags=re.I | re.S,
    ):
        ticker = normalise_code(match.group(1))
        label = strip_tags(match.group(2))
        if ticker:
            pairs.append((ticker, label))

    # Some versions of the page embed the stock list as JSON.
    json_patterns = [
        r'"code"\s*:\s*"([A-Z0-9]{2,5})".{0,250}?"(?:company|companyName|name)"\s*:\s*"([^"\\]+)"',
        r'"(?:company|companyName|name)"\s*:\s*"([^"\\]+)".{0,250}?"code"\s*:\s*"([A-Z0-9]{2,5})"',
    ]
    for idx, pattern in enumerate(json_patterns):
        for match in re.finditer(pattern, text, flags=re.I | re.S):
            if idx == 0:
                code, company = match.group(1), match.group(2)
            else:
                company, code = match.group(1), match.group(2)
            ticker = normalise_code(code)
            if ticker:
                pairs.append((ticker, html.unescape(company).strip()))

    if not pairs:
        return None

    out = pd.DataFrame(pairs, columns=["ticker", "company"])
    out = out.drop_duplicates(subset=["ticker"]).reset_index(drop=True)
    return out


def fetch_source(name: str, url: str) -> pd.DataFrame | None:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = response.text

    candidates: list[pd.DataFrame] = []
    table = extract_from_tables(text)
    if table is not None:
        candidates.append(table)

    if "marketindex.com.au" in url:
        links = extract_marketindex_links(text)
        if links is not None:
            candidates.append(links)

    if not candidates:
        print(f"{name}: no stock list could be extracted.")
        return None

    best = max(candidates, key=len)
    print(f"{name}: extracted {len(best)} unique tickers.")
    return best


def load_cached() -> pd.DataFrame:
    if not WATCHLIST_PATH.exists():
        return pd.DataFrame(columns=["ticker", "company"])
    cached = pd.read_csv(WATCHLIST_PATH)
    if "ticker" not in cached.columns:
        return pd.DataFrame(columns=["ticker", "company"])
    if "company" not in cached.columns:
        cached["company"] = ""
    cached["ticker"] = cached["ticker"].map(normalise_code)
    cached = cached[cached["ticker"] != ""].drop_duplicates("ticker")
    return cached[["ticker", "company"]].reset_index(drop=True)


def refresh_universe() -> pd.DataFrame:
    failures: list[str] = []
    for name, url in SOURCES:
        try:
            candidate = fetch_source(name, url)
            if candidate is not None and MIN_ACCEPTABLE <= len(candidate) <= MAX_ACCEPTABLE:
                WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
                candidate.to_csv(WATCHLIST_PATH, index=False)
                print(f"Universe refreshed from {name}: {len(candidate)} tickers written to {WATCHLIST_PATH}.")
                return candidate
            if candidate is not None:
                failures.append(f"{name}: unexpected size {len(candidate)}")
            else:
                failures.append(f"{name}: no usable list")
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            print(f"Universe source failed ({name}): {exc}")

    cached = load_cached()
    if len(cached) >= MIN_ACCEPTABLE:
        print(f"All live universe sources failed; retaining cached universe of {len(cached)} tickers.")
        for failure in failures:
            print(f"- {failure}")
        return cached

    raise RuntimeError(
        "Could not refresh an ASX-300-sized universe and the cached watchlist is too small. "
        + " | ".join(failures)
    )


def main() -> None:
    universe = refresh_universe()
    print(f"Ready to scan {len(universe)} ASX tickers.")


if __name__ == "__main__":
    main()
