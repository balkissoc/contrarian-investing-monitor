from __future__ import annotations

import html
import os
import re
import time
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
OPENFIGI_MAPPING_URL = "https://api.openfigi.com/v3/mapping"
OPENFIGI_API_KEY = os.getenv("OPENFIGI_API_KEY", "").strip()

# Use a deliberately conservative batch/rate so the mapper also works without an
# OpenFIGI API key. Once SEDOLs are cached, subsequent daily refreshes are very fast.
OPENFIGI_BATCH_SIZE = 5
OPENFIGI_BATCH_PAUSE_SECONDS = 2.6
OPENFIGI_MAX_RETRIES = 4

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
        if word not in {
            "LIMITED", "LTD", "PLC", "GROUP", "HOLDINGS", "HOLDING",
            "CORP", "CORPORATION", "THE",
        }
    ]
    return " ".join(words)[:100]


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
    cached = pd.read_csv(WATCHLIST_PATH, dtype=str).fillna("")
    if "ticker" not in cached.columns:
        return pd.DataFrame(columns=["ticker", "company"])
    if "company" not in cached.columns:
        cached["company"] = ""
    cached["ticker"] = cached["ticker"].map(normalise_code)
    cached["company"] = cached["company"].map(clean_company)
    return (
        cached[cached["ticker"] != ""][["ticker", "company"]]
        .drop_duplicates("ticker")
        .reset_index(drop=True)
    )


def load_resolution_cache() -> pd.DataFrame:
    columns = ["source_name", "source_sedol", "ticker", "company", "mapping_source"]
    if not RESOLUTION_CACHE_PATH.exists():
        return pd.DataFrame(columns=columns)

    cache = pd.read_csv(RESOLUTION_CACHE_PATH, dtype=str).fillna("")
    for col in columns:
        if col not in cache.columns:
            cache[col] = ""
    cache["ticker"] = cache["ticker"].map(normalise_code)
    cache["source_sedol"] = cache["source_sedol"].astype(str).str.strip().str.upper()
    return cache[columns]


def save_resolution_cache(cache: pd.DataFrame) -> None:
    RESOLUTION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    columns = ["source_name", "source_sedol", "ticker", "company", "mapping_source"]
    out = cache.copy().fillna("")
    for col in columns:
        if col not in out.columns:
            out[col] = ""
    out["ticker"] = out["ticker"].map(normalise_code)
    out["source_sedol"] = out["source_sedol"].astype(str).str.strip().str.upper()
    out = out[(out["ticker"] != "") & (out["source_sedol"] != "")]
    out = out.drop_duplicates(subset=["source_sedol"], keep="last")
    out[columns].to_csv(RESOLUTION_CACHE_PATH, index=False)


def fetch_global_x_holdings() -> pd.DataFrame:
    response = requests.get(GLOBAL_X_A300_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))

    best: pd.DataFrame | None = None
    for raw in tables:
        table = flatten_columns(raw)
        lower = {str(c).strip().lower(): c for c in table.columns}
        name_col = next(
            (lower[k] for k in lower if k == "name" or ("holding" in k and "name" in k)),
            None,
        )
        sedol_col = next((lower[k] for k in lower if "sedol" in k), None)
        if name_col is None or sedol_col is None:
            continue

        candidate = pd.DataFrame({
            "source_name": table[name_col].map(clean_company),
            "source_sedol": table[sedol_col].astype(str).str.strip().str.upper(),
        })
        candidate = candidate[
            (candidate["source_name"] != "")
            & candidate["source_sedol"].str.fullmatch(r"[A-Z0-9]{7}", na=False)
        ]
        candidate = candidate.drop_duplicates(subset=["source_sedol"]).reset_index(drop=True)
        if best is None or len(candidate) > len(best):
            best = candidate

    if best is None:
        raise RuntimeError("Global X A300 holdings table was not found.")
    if not (MIN_ACCEPTABLE <= len(best) <= MAX_ACCEPTABLE):
        raise RuntimeError(f"Global X A300 holdings returned an unexpected {len(best)} rows.")

    print(f"Global X A300: loaded {len(best)} equity holdings with SEDOL identifiers.")
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


def score_figi_match(item: dict, source_name: str) -> int:
    ticker = normalise_code(item.get("ticker", ""))
    if not ticker:
        return -10_000

    score = 0
    market_sector = str(item.get("marketSector", "")).upper()
    security_type = str(item.get("securityType", "")).upper()
    security_type2 = str(item.get("securityType2", "")).upper()
    exch_code = str(item.get("exchCode", "")).upper()

    if market_sector == "EQUITY":
        score += 40
    if any(word in security_type2 for word in ["COMMON", "REIT", "EQUITY", "SHARE"]):
        score += 25
    if any(word in security_type for word in ["COMMON", "REIT", "EQUITY", "SHARE"]):
        score += 15
    if any(tag in exch_code for tag in ["AU", "AS", "ASX"]):
        score += 10

    source_words = set(company_key(source_name).split())
    item_words = set(company_key(item.get("name", "")).split())
    score += 5 * len(source_words & item_words)
    return score


def choose_figi_match(response_item: dict, source_name: str) -> tuple[str, str]:
    data = response_item.get("data", []) if isinstance(response_item, dict) else []
    if not isinstance(data, list) or not data:
        return "", ""

    ranked = sorted(
        (item for item in data if isinstance(item, dict)),
        key=lambda item: score_figi_match(item, source_name),
        reverse=True,
    )
    if not ranked:
        return "", ""

    best = ranked[0]
    ticker = normalise_code(best.get("ticker", ""))
    company = clean_company(best.get("name") or source_name)
    return ticker, company


def post_openfigi_jobs(jobs: list[dict[str, str]]) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "contrarian-investing-monitor/1.0",
    }
    if OPENFIGI_API_KEY:
        headers["X-OPENFIGI-APIKEY"] = OPENFIGI_API_KEY

    last_error: Exception | None = None
    for attempt in range(OPENFIGI_MAX_RETRIES):
        try:
            response = requests.post(
                OPENFIGI_MAPPING_URL,
                headers=headers,
                json=jobs,
                timeout=30,
            )
            if response.status_code == 429:
                wait_seconds = 65
                reset_header = response.headers.get("ratelimit-reset", "").strip()
                try:
                    if reset_header:
                        wait_seconds = max(5, min(90, int(float(reset_header)) + 2))
                except Exception:
                    pass
                print(f"OpenFIGI rate limit reached; waiting {wait_seconds}s before retry.")
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise RuntimeError("OpenFIGI returned an unexpected response shape.")
            return payload
        except Exception as exc:
            last_error = exc
            if attempt < OPENFIGI_MAX_RETRIES - 1:
                wait_seconds = 3 * (attempt + 1)
                print(f"OpenFIGI request failed ({exc}); retrying in {wait_seconds}s.")
                time.sleep(wait_seconds)

    raise RuntimeError(f"OpenFIGI mapping failed after {OPENFIGI_MAX_RETRIES} attempts: {last_error}")


def resolve_global_x_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    cache = load_resolution_cache()

    # Only trust mappings created by the identifier-based OpenFIGI process. Earlier
    # fuzzy-name cache entries are deliberately ignored and will be replaced.
    trusted_cache = cache[
        (cache["mapping_source"] == "openfigi")
        & (cache["ticker"] != "")
        & (cache["source_sedol"] != "")
    ].copy()
    cached_by_sedol = {
        str(row.source_sedol).strip().upper(): (row.ticker, row.company)
        for row in trusted_cache.itertuples()
    }

    resolved_rows: list[dict[str, str]] = []
    cache_rows: list[dict[str, str]] = []
    pending: list[dict[str, str]] = []

    for row in holdings.itertuples(index=False):
        source_name = clean_company(row.source_name)
        sedol = str(row.source_sedol).strip().upper()
        cached = cached_by_sedol.get(sedol)
        if cached:
            ticker, company = cached
            resolved_rows.append({"ticker": ticker, "company": company or source_name})
        else:
            pending.append({"source_name": source_name, "source_sedol": sedol})

    print(
        f"OpenFIGI resolution: {len(resolved_rows)} holdings loaded from trusted cache; "
        f"{len(pending)} SEDOLs require mapping."
    )

    unresolved: list[str] = []
    for start in range(0, len(pending), OPENFIGI_BATCH_SIZE):
        batch = pending[start:start + OPENFIGI_BATCH_SIZE]
        jobs = [
            {"idType": "ID_SEDOL", "idValue": row["source_sedol"]}
            for row in batch
        ]
        results = post_openfigi_jobs(jobs)

        # OpenFIGI returns one response item per submitted mapping job, in order.
        for row, response_item in zip(batch, results):
            ticker, company = choose_figi_match(response_item, row["source_name"])
            if ticker:
                resolved_rows.append({"ticker": ticker, "company": company or row["source_name"]})
                cache_rows.append({
                    "source_name": row["source_name"],
                    "source_sedol": row["source_sedol"],
                    "ticker": ticker,
                    "company": company or row["source_name"],
                    "mapping_source": "openfigi",
                })
            else:
                unresolved.append(row["source_name"])

        completed = min(start + len(batch), len(pending))
        if completed % 25 == 0 or completed == len(pending):
            print(f"OpenFIGI mapped {completed}/{len(pending)} uncached SEDOLs...")
        if start + OPENFIGI_BATCH_SIZE < len(pending):
            time.sleep(OPENFIGI_BATCH_PAUSE_SECONDS)

    if cache_rows:
        combined = pd.concat([trusted_cache, pd.DataFrame(cache_rows)], ignore_index=True)
        save_resolution_cache(combined)

    resolved = pd.DataFrame(resolved_rows, columns=["ticker", "company"])
    resolved = resolved[resolved["ticker"] != ""].drop_duplicates("ticker").reset_index(drop=True)

    print(
        f"Global X/OpenFIGI resolution: {len(resolved)} unique ASX tickers; "
        f"{len(unresolved)} unresolved holdings."
    )
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

    # Primary source: Global X A300 publishes the holdings and SEDOL identifiers for
    # its portfolio of roughly the 300 largest Australian listed companies.
    try:
        holdings = fetch_global_x_holdings()
        resolved = resolve_global_x_holdings(holdings)
        if len(resolved) >= MIN_ACCEPTABLE:
            return write_universe(resolved, "Global X A300 holdings via OpenFIGI SEDOL mapping")
        failures.append(f"Global X A300 resolved only {len(resolved)} unique tickers")
    except Exception as exc:
        failures.append(f"Global X A300/OpenFIGI: {exc}")
        print(f"Global X A300 universe refresh failed: {exc}")

    # Secondary live source if its page exposes ticker links.
    try:
        market_index = extract_marketindex_tickers()
        return write_universe(market_index, "Market Index ASX 300")
    except Exception as exc:
        failures.append(f"Market Index: {exc}")
        print(f"Market Index universe refresh failed: {exc}")

    # Once a good universe has been built, a temporary source outage must never cause
    # a silent collapse back to the old 20-stock fallback.
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
