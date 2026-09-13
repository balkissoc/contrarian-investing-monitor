import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

import contrarian


class PerformanceLogTests(unittest.TestCase):
    def test_exchange_session_date_survives_timezone_removal(self) -> None:
        dates = pd.date_range("2026-09-10", periods=2, tz="Australia/Sydney")
        data = pd.DataFrame({"Close": [10, 11]}, index=dates)
        series = contrarian._history_series(data, "AAA.AX", "Close", 1)
        self.assertEqual(series.index[0], pd.Timestamp("2026-09-10"))

    def test_missing_adjusted_prices_are_not_substituted_with_raw_prices(self) -> None:
        data = pd.DataFrame({"Close": [10, 11]}, index=pd.date_range("2026-09-10", periods=2))
        with patch.object(contrarian.yf, "download", return_value=data):
            self.assertEqual(contrarian.download_performance_history(["AAA.AX"], "2026-09-10", "2026-09-12"), {})

    def test_failed_refresh_preserves_history_and_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "performance_log.csv"
            pd.DataFrame([{
                "signal_date": "2026-01-01", "ticker": "AAA.AX", "signal_type": "candidate",
                "signal_price": 100, "current_price": 109, "return_pct": 9,
                "last_checked": "2026-01-14",
            }]).to_csv(log_path, index=False)
            with patch.object(contrarian, "PERFORMANCE_LOG_PATH", log_path), patch.object(
                contrarian, "download_performance_history", return_value={},
            ):
                result = contrarian.update_performance_log("2026-01-15", pd.DataFrame(), pd.DataFrame())
        self.assertEqual(result.iloc[0]["return_pct"], 9)
        self.assertEqual(result.iloc[0]["last_checked"], "2026-01-14")
        self.assertEqual(result.iloc[0]["history_status"], "refresh_unavailable")

    def test_truncated_company_name_is_enriched(self) -> None:
        stock = Mock()
        stock.get_info.return_value = {
            "longName": "Nine Entertainment Co. Holdings Limited",
            "marketCap": 1_450_000_000,
        }
        name, market_cap = contrarian.improve_company_name(
            stock,
            "NINE ENTERTAINMENT CO HOLDIN",
            1_440_000_000,
        )
        self.assertEqual(name, "Nine Entertainment Co. Holdings Limited")
        self.assertEqual(market_cap, 1_440_000_000)

    def test_performance_is_updated_from_one_downloaded_history(self) -> None:
        dates = pd.bdate_range("2026-01-01", periods=10)
        raw = pd.Series(range(100, 110), index=dates, dtype=float)
        adjusted = raw.copy()
        signal = pd.DataFrame([{
            "ticker": "AAA.AX",
            "company": "AAA Limited",
            "signal_type": "candidate",
            "price_date": "2026-01-01",
            "last_price": 100.0,
            "openai_score": "",
            "openai_classification": "not_run",
        }])

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "performance_log.csv"
            with patch.object(contrarian, "PERFORMANCE_LOG_PATH", log_path), patch.object(
                contrarian,
                "download_performance_history",
                return_value={"AAA.AX": (raw, adjusted)},
            ) as download:
                result = contrarian.update_performance_log("2026-01-14", signal, pd.DataFrame())

        download.assert_called_once()
        row = result.iloc[0]
        self.assertEqual(row["trading_sessions_since_signal"], 9)
        self.assertEqual(row["return_pct"], 9.0)
        self.assertEqual(row["return_5d_pct"], 5.0)
        self.assertTrue(pd.isna(row["return_20d_pct"]))
        self.assertEqual(row["history_status"], "refreshed")
        self.assertEqual(row["current_price_date"], "2026-01-14")


if __name__ == "__main__":
    unittest.main()
