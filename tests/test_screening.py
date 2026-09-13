import unittest
from unittest.mock import Mock, patch

import pandas as pd

import contrarian
import run_monitor


class ScreeningTests(unittest.TestCase):
    def test_trigger_with_missing_market_cap_is_retained_but_flagged(self) -> None:
        stock = Mock()
        stock.history.return_value = pd.DataFrame({
            "Close": [100.0] * 20 + [80.0], "Volume": [100] * 20 + [200],
        }, index=pd.bdate_range("2026-01-01", periods=21))
        news = [{"title": "Company update", "source": "", "link": "", "published": ""}]
        with patch.object(run_monitor.yf, "Ticker", return_value=stock), patch.object(
            contrarian, "get_market_cap", return_value=None,
        ), patch.object(contrarian, "improve_company_name", return_value=("AAA", None)), patch.object(
            contrarian, "fetch_news", return_value=news,
        ):
            row, status = run_monitor.robust_screen_ticker("AAA.AX", "AAA")
        self.assertEqual(status, "candidate")
        self.assertEqual(row["risk_gate"], "size_unverified")
        self.assertEqual(row["attention_score"], 100)
        self.assertIn("20D", row["trigger"])
        self.assertEqual(row["price_date"], "2026-01-29")


if __name__ == "__main__":
    unittest.main()
