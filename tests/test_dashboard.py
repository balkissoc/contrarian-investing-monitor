import unittest

import pandas as pd

import dashboard


class DashboardTests(unittest.TestCase):
    def test_missing_source_does_not_shift_links_onto_wrong_headline(self) -> None:
        output = dashboard.headline_details(pd.Series({
            "news_headlines": "First title | Second title", "news_sources": " | Publisher",
            "news_urls": " | https://example.com/second", "news_published": " | 2026-09-10",
        }))
        self.assertIn("<li>First title</li>", output)
        self.assertIn('rel="noopener noreferrer">Second title</a>', output)
        self.assertIn("Publisher · 10 Sep 2026", output)

    def test_legacy_history_is_not_presented_as_validated_maturity(self) -> None:
        perf = pd.DataFrame([{
            "signal_date": "2026-01-01", "ticker": "AAA.AX", "signal_type": "candidate",
            "signal_price": 100, "current_price": 110, "days_since_signal": 30,
        }])
        metrics, table, _ = dashboard.performance_section(perf)
        self.assertIn("Awaiting history refresh", table)
        self.assertIn("1 episodes await", table)
        self.assertNotIn("+10.00%", metrics)

    def test_invalid_and_old_run_dates_warn(self) -> None:
        self.assertIn("freshness is unknown", dashboard.freshness_banner("Unknown"))
        self.assertNotIn("hidden", dashboard.freshness_banner("2020-01-01 22:00:00 UTC"))

    def test_generated_dashboard_contains_every_current_result(self) -> None:
        output = dashboard.build_dashboard()
        candidates = dashboard.read_csv(dashboard.CANDIDATES_PATH)
        near_misses = dashboard.read_csv(dashboard.NEAR_MISSES_PATH)
        self.assertEqual(output.count('class="signal-card '), len(candidates) + len(near_misses))
        self.assertIn("data-show-more", output)
        self.assertIn("Fixed-horizon outcomes", output)

    def test_daily_repeats_are_condensed_into_episodes(self) -> None:
        performance = pd.DataFrame([
            {"signal_date": "2026-01-01", "ticker": "AAA.AX", "company": "AAA", "signal_type": "near_miss", "signal_price": 10, "current_price": 12, "days_since_signal": 30},
            {"signal_date": "2026-01-03", "ticker": "AAA.AX", "company": "AAA", "signal_type": "candidate", "signal_price": 9, "current_price": 12, "days_since_signal": 28},
            {"signal_date": "2026-01-06", "ticker": "AAA.AX", "company": "AAA", "signal_type": "candidate", "signal_price": 8, "current_price": 12, "days_since_signal": 25},
            {"signal_date": "2026-01-20", "ticker": "AAA.AX", "company": "AAA", "signal_type": "near_miss", "signal_price": 11, "current_price": 12, "days_since_signal": 11},
            {"signal_date": "2026-01-02", "ticker": "BBB.AX", "company": "BBB", "signal_type": "near_miss", "signal_price": 5, "current_price": 4, "days_since_signal": 29},
        ])
        episodes = dashboard.build_episodes(performance)
        self.assertEqual(len(episodes), 3)
        first_aaa = episodes[(episodes["ticker"] == "AAA.AX") & (episodes["episode"] == 1)].iloc[0]
        self.assertEqual(first_aaa["signal_type"], "candidate")
        self.assertEqual(first_aaa["signal_days"], 3)

    def test_utc_timestamp_is_presented_in_awst(self) -> None:
        self.assertEqual(
            dashboard.display_run_time("2026-09-06 23:18:24 UTC"),
            "07 Sep 2026, 07:18 AWST",
        )


if __name__ == "__main__":
    unittest.main()
