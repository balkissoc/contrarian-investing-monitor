import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import research
import validation


class ResearchTests(unittest.TestCase):
    def test_event_does_not_inflate_its_own_volatility_baseline(self):
        closes = [100.0]
        for i in range(99):
            closes.append(closes[-1] * (1.005 if i % 2 else .995))
        closes.append(closes[-1] * .9)
        hist = pd.DataFrame({"Close": closes, "Volume": [20000] * len(closes)}, index=pd.bdate_range("2026-01-01", periods=len(closes)))
        result = research.price_context(hist)
        self.assertLess(result["one_day_z"], -15)
        self.assertIn("1D", result["volatility_trigger"])
        self.assertIsNone(result["twelve_month_pct"])

    def test_unknown_fundamentals_never_clear_research(self):
        result = research.evidence_gate({})
        self.assertEqual(result["research_status"], "incomplete")
        self.assertEqual(result["research_lane"], "unclassified_missing_data")
        self.assertIn("Debt", result["required_information"])

    def test_hybrid_treats_losses_cyclicals_and_banks_differently(self):
        for sector, income, fcf, lane in (("Technology", 100, 80, "core_research"), ("Technology", 100, -10, "turnaround_research"), ("Basic Materials", 100, 80, "cyclical_research"), ("Financial Services", 100, -10, "sector_specialist")):
            self.assertEqual(research.evidence_gate({"sector":sector,"net_income":income,"free_cash_flow":fcf})["research_lane"],lane)

    def test_currency_and_zero_debt_are_preserved_without_conversion(self):
        result = research.snapshot_from_info({"financialCurrency":"USD", "totalDebt":0, "freeCashflow":-1}, "AAA.AX", "2026-09-13")
        self.assertEqual(result["fundamental_currency"], "USD")
        self.assertEqual(result["total_debt"], 0)
        self.assertIsNone(result["total_cash"])

    def test_mismatched_benchmark_dates_are_not_forward_filled(self):
        stock = pd.Series(range(100,107),index=pd.bdate_range("2026-01-01",periods=7))
        self.assertIsNone(research.aligned_return(stock.iloc[:-1], stock, 5))
        self.assertAlmostEqual(research.aligned_return(stock, stock, 5), (106/101-1)*100, places=5)

    def test_alert_repeats_are_suppressed_but_cumulative_changes_resurface(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"alerts.json"
            def run(day, price):
                return research.annotate_alerts(pd.DataFrame([{"ticker":"AAA.AX", "signal_type":"candidate", "last_price":price, "attention_score":80}]),day,path).iloc[0]["alert_status"]
            self.assertEqual(run("2026-09-01",100),"new")
            self.assertEqual(run("2026-09-01",100),"new")
            self.assertEqual(run("2026-09-02",98),"repeat")
            self.assertEqual(run("2026-09-03",96),"repeat")
            self.assertEqual(run("2026-09-04",94),"changed")


class ValidationTests(unittest.TestCase):
    def test_anchor_keeps_original_type_instead_of_later_upgrade(self):
        log = pd.DataFrame([{"ticker":"AAA.AX","signal_date":"2026-01-01","signal_type":"near_miss"},{"ticker":"AAA.AX","signal_date":"2026-01-02","signal_type":"candidate"}])
        self.assertEqual(validation.event_anchors(log)[0]["signal_type"], "near_miss")

    def test_entry_is_after_scan_not_signal_price_date_and_benchmark_matches(self):
        dates = pd.bdate_range("2026-01-01",periods=10)
        prices = pd.Series(range(100,110),index=dates,dtype=float)
        row = {"ticker":"AAA.AX","signal_type":"candidate","signal_date":"2026-01-02","price_date":"2026-01-01"}
        result = validation.measure_event(row,{"AAA.AX":(prices,prices),research.SETTINGS["market_benchmark"]:(prices,prices)},"2026-01-14")
        self.assertEqual(result["entry_date"],"2026-01-05")
        self.assertEqual(result["entry_raw_close"],102)
        self.assertAlmostEqual(result["net_return_5d_pct"],validation.net_return(102,107),places=4)
        self.assertEqual(result["excess_5d_pct"],0)

    def test_missing_and_pending_entries_never_become_zero_return_wins(self):
        row = {"ticker":"AAA.AX","signal_type":"candidate","signal_date":"2026-01-02"}
        self.assertEqual(validation.measure_event(row,{},"2026-01-03")["status"],"history_unavailable")
        prices=pd.Series([100],index=pd.to_datetime(["2026-01-02"]))
        result=validation.measure_event(row,{"AAA.AX":(prices,prices)},"2026-01-03")
        self.assertEqual(result["status"],"awaiting_entry")
        self.assertNotIn("net_return_5d_pct",result)

    def test_month_horizon_is_calendar_based_and_costs_reduce_return(self):
        dates=pd.bdate_range("2025-01-01","2026-01-08")
        prices=pd.Series(100.0,index=dates)
        result=validation.measure_event({"ticker":"AAA.AX","signal_type":"candidate","signal_date":"2025-01-01"},{"AAA.AX":(prices,prices)},"2026-01-08")
        self.assertLess(result["net_return_12m_pct"],0)
        self.assertNotIn("net_return_24m_pct",result)

    def test_legacy_rows_do_not_enter_prospective_cohorts(self):
        row={"ticker":"AAA.AX","signal_type":"candidate","signal_date":"2026-01-02"}
        with tempfile.TemporaryDirectory() as directory:
            validation.update_validation(pd.DataFrame([row]),{},"2026-01-03",Path(directory))
            result=research.read_json(Path(directory)/"validation_summary.json")
        self.assertEqual(result["prospective_events"],0)
        self.assertEqual(result["legacy_events"],1)


if __name__ == "__main__":
    unittest.main()
