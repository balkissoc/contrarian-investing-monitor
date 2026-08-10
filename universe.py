from __future__ import annotations

import html
import re
import time
import urllib.parse
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


WATCHLIST_PATH = Path("config/watchlist_asx.csv")
RESOLUTION_CACHE_PATH = Path("config/a300_resolution_cache.csv")
MIN_ACCEPTABLE = 250
MAX_ACCEPTABLE = 380

GLOBAL_X_A300_URL = "https://www.globalxetfs.com.au/funds/a300/"
MARKET_INDEX_URL = "https://www.marketindex.com.au/asx300"
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

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


def clean_company(value: object) -> str:
    text = html.unescape(str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def company_key(value: object) -> str:
    text = clean_company(value).upper()
    text = re.sub(r"[^A-Z0-9 ]", " ", text)
    words = [
        word
        for word in text.split()
        if word not in {"LIMITED", "LTD", "PLC", "GROUP", "HOLDINGS", "HOLDING", "CORP", "CORPORATION"}
    ]
    return " ".join(words)[:80]


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [" ".join(str(x) for x in col if str(x) != "nan").strip() for col in out.columns]
    else:
        out.columns = [str(c).strip() for c in out.columns]
    return out


def load_cached_watchlist() -> pd.DataFrame:
    if not WATCHLIST_PATH.exists():
        return pd.DataFrame(columns=["ticker", "company"])
    cached = pd.read_csv(WATCHLIST_PATH)
    if "ticker" not in cached.columns:
        return pd.DataFrame(columns=["ticker", "company"])
    if "company" not in cached.columns:
        cached["company"] = ""
    cached["ticker"] = cached["ticker"].map(normalise_code)
    cached["company"] = cached["company"].map(clean_company)
    return cached[cached["ticker"] != ""][["ticker", "company"]].drop_duplicates("ticker").reset_index(drop=True)


def load_resolution_cache() -> pd.DataFrame:
    if not RESOLUTION_CACHE_PATH.exists():
        return pd.DataFrame(columns=["source_name", "source_sedol", "ticker", "company"])
    cache = pd.read_csv(RESOLUTION_CACHE_PATH, dtype=str).fillna("")
    for col in ["source_name", "source_sedol", "ticker", "company"]:
        if col not in cache.columns:
            cache[col] = ""
    cache["ticker"] = cache["ticker"].map(normalise_code)
    return cache[["source_name", "source_sedol", "ticker", "company"]]


def save_resolution_cache(cache: pd.DataFrame) -> None:
    RESOLUTION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = cache.copy().fillna("")
    out = out[out["ticker"] != ""]
    out = out.drop_duplicates(subset=["source_sedol", "source_name"], keep="last")
    out.to_csv(RESOLUTION_CACHE_PATH, index=False)


def fetch_global_x_holdings() -> pd.DataFrame:
    response = requests.get(GLOBAL_X_A300_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))

    best: pd.DataFrame | None = None
    for raw in tables:
        table = flatten_columns(raw)
        lower = {str(c).strip().lower(): c for c in table.columns}
        name_col = next((lower[k] for k in lower if k == "name" or "holding" in k and "name" in k), None)
        sedol_col = next((lower[k] for k in lower if "sedol" in k), None)
        if name_col is None or sedol_col is None:
            continue
        candidate = pd.DataFrame({
            "source_name": table[name_col].map(clean_company),
            "source_sedol": table[sedol_col].astype(str).str.strip(),
        })
        candidate = candidate[candidate["source_name"] != ""]
        candidate = candidate.drop_duplicates(subset=["source_sedol", "source_name"]).reset_index(drop=True)
        if best is None or len(candidate) > len(best):
            best = candidate

    if best is None:
        raise RuntimeError("Global X A300 holdings table was not found.")
    if not (MIN_ACCEPTABLE <= len(best) <= MAX_ACCEPTABLE):
        raise RuntimeError(f"Global X A300 holdings returned an unexpected {len(best)} rows.")

    print(f"Global X A300: loaded {len(best)} holdings names.")
    return best


def extract_marketindex_tickers() -> pd.DataFrame:
    response = requests.get(MARKET_INDEX_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    text = response.text
    pairs: list[tuple[str, str]] = []

    for match in re.finditer(
        r'href=["\']/asx/([a-z0-9]{2,5})["\'][^>]*>(.*?)</a>',
        text,
        flags=re.I | re.S,
    ):
        ticker = normalise_code(match.group(1))
        company = re.sub(r"<[^>]+>", " ", match.group(2))
        company = clean_company(company)
        if ticker:
            pairs.append((ticker, company))

    out = pd.DataFrame(pairs, columns=["ticker", "company"]).drop_duplicates("ticker")
    if MIN_ACCEPTABLE <= len(out) <= MAX_ACCEPTABLE:
        print(f"Market Index fallback: extracted {len(out)} tickers directly.")
        return out.reset_index(drop=True)
    raise RuntimeError(f"Market Index exposed only {len(out)} unique ticker links.")


def yahoo_resolve(name: str) -> tuple[str, str]:
    query = f"{name} ASX"
    params = {
        "q": query,
        "quotesCount": 12,
        "newsCount": 0,
        "listsCount": 0,
        "enableFuzzyQuery": "true",
    }
    response = requests.get(YAHOO_SEARCH_URL, headers=HEADERS, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    quotes = data.get("quotes", []) or []
    asx_quotes = []
    for quote in quotes:
        symbol = str(quote.get("symbol", "")).upper().strip()
        exchange = str(quote.get("exchange", "")).upper()
        exch_disp = str(quote.get("exchDisp", "")).upper()
        if symbol.endswith(".AX") or exchange in {"ASX", "AUS"} or "ASX" in exch_disp:
            asx_quotes.append(quote)

    if not asx_quotes:
        return "", ""

    wanted = company_key(name)
    best = asx_quotes[0]
    best_score = -1
    for quote in asx_quotes:
        candidate_name = quote.get("longname") or quote.get("shortname") or quote.get("name") or ""
        key = company_key(candidate_name)
        score = 0
        if wanted and key:
            wanted_words = set(wanted.split())
            key_words = set(key.split())
            score += 10 * len(wanted_words & key_words)
            if wanted.startswith(key[: min(len(key), 12)]) or key.startswith(wanted[: min(len(wanted), 12)]):
                score += 12
        if score > best_score:
            best = quote
            best_score = score

    ticker = normalise_code(best.get("symbol", ""))
    company = clean_company(best.get("longname") or best.get("shortname") or name)
    return ticker, company


def resolve_global_x_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    cache = load_resolution_cache()
    cached_by_sedol = {
        str(row.source_sedol).strip(): (row.ticker, row.company)
        for row in cache.itertuples()
        if str(row.source_sedol).strip() and str(row.ticker).strip()
    }

    old_watchlist = load_cached_watchlist()
    old_by_name = {company_key(row.company): (row.ticker, row.company) for row in old_watchlist.itertuples() if row.company}

    resolved_rows: list[dict[str, str]] = []
    new_cache_rows: list[dict[str, str]] = []
    unresolved: list[str] = []

    for index, row in holdings.iterrows():
        source_name = clean_company(row["source_name"])
        sedol = str(row["source_sedol"]).strip()
        ticker = ""
        company = source_name

        if sedol in cached_by_sedol:
            ticker, company = cached_by_sedol[sedol]
        else:
            name_key = company_key(source_name)
            if name_key in old_by_name:
                ticker, company = old_by_name[name_key]
            else:
                try:
                    ticker, company = yahoo_resolve(source_name)
                except Exception as exc:
                    print(f"Yahoo resolution failed for {source_name}: {exc}")
                    ticker = ""
                time.sleep(0.08)

        if ticker:
            resolved_rows.append({"ticker": ticker, "company": company or source_name})
            new_cache_rows.append({
                "source_name": source_name,
                "source_sedol": sedol,
                "ticker": ticker,
                "company": company or source_name,
            })
        else:
            unresolved.append(source_name)

        if (index + 1) % 50 == 0:
            print(f"Resolved {index + 1}/{len(holdings)} Global X holdings...")

    resolved = pd.DataFrame(resolved_rows, columns=["ticker", "company"])
    resolved = resolved.drop_duplicates("ticker").reset_index(drop=True)

    if new_cache_rows:
        combined_cache = pd.concat([cache, pd.DataFrame(new_cache_rows)], ignore_index=True)
        save_resolution_cache(combined_cache)

    print(f"Global X resolution: {len(resolved)} unique ASX tickers; {len(unresolved)} unresolved names.")
    if unresolved:
        print("First unresolved holdings: " + ", ".join(unresolved[:15]))
    return resolved


def write_universe(universe: pd.DataFrame, source: str) -> pd.DataFrame:
    universe = universe.copy()
    universe["ticker"] = universe["ticker"].map(normalise_code)
    universe["company"] = universe["company"].map(clean_company)
    universe = universe[universe["ticker"] != ""].drop_duplicates("ticker").reset_index(drop=True)
    if not (MIN_ACCEPTABLE <= len(universe) <= MAX_ACCEPTABLE):
        raise RuntimeError(f"Refusing to replace watchlist with {len(universe)} tickers from {source}.")
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(WATCHLIST_PATH, index=False)
    print(f"Universe refreshed from {source}: {len(universe)} tickers written to {WATCHLIST_PATH}.")
    return universe


def refresh_universe() -> pd.DataFrame:
    failures: list[str] = []

    # Primary source: a real ETF holding roughly the 300 largest ASX-listed companies.
    try:
        holdings = fetch_global_x_holdings()
        resolved = resolve_global_x_holdings(holdings)
        if len(resolved) >= MIN_ACCEPTABLE:
            return write_universe(resolved, "Global X A300 holdings")
        failures.append(f"Global X A300 resolved only {len(resolved)} tickers")
    except Exception as exc:
        failures.append(f"Global X A300: {exc}")
        print(f"Global X A300 universe refresh failed: {exc}")

    # Secondary live source if its page exposes ticker links.
    try:
        market_index = extract_marketindex_tickers()
        return write_universe(market_index, "Market Index ASX 300")
    except Exception as exc:
        failures.append(f"Market Index: {exc}")
        print(f"Market Index universe refresh failed: {exc}")

    # Most important resilience feature: never replace a good cached ~300 list with a tiny fallback.
    cached = load_cached_watchlist()
    if len(cached) >= MIN_ACCEPTABLE:
        print(f"Live universe sources failed; retaining cached universe of {len(cached)} tickers.")
        for failure in failures:
            print(f"- {failure}")
        return cached

    raise RuntimeError(
        "Could not establish an ASX-300-sized universe and no adequate cached universe exists. "
        + " | ".join(failures)
    )


def main() -> None:
    universe = refresh_universe()
    print(f"Ready to scan {len(universe)} ASX tickers.")


if __name__ == "__main__":
    main()
