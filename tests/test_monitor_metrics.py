import unittest

from monitor_metrics import attention_band, attention_score, risk_gate


class AttentionScoreTests(unittest.TestCase):
    def test_stronger_multi_window_signal_scores_higher(self) -> None:
        near = attention_score(-4, -5, -8, 0.9)
        candidate = attention_score(-8, -14, -22, 2.1)
        self.assertGreater(candidate, near)
        self.assertGreaterEqual(candidate, 80)
        self.assertEqual(attention_band(candidate), "Immediate review")

    def test_score_is_bounded(self) -> None:
        self.assertEqual(attention_score(-100, -100, -100, 20), 100)
        self.assertEqual(attention_score(2, 4, 8, 0.5), 0)


class RiskGateTests(unittest.TestCase):
    def test_headline_flag_takes_priority(self) -> None:
        key, label = risk_gate("capital raising", 1_000_000_000, "watch only", "Headline")
        self.assertEqual(key, "headline_risk")
        self.assertIn("Headline", label)

    def test_missing_market_cap_is_not_described_as_clear(self) -> None:
        key, _ = risk_gate("", None, "not_run", "Headline")
        self.assertEqual(key, "size_unverified")


if __name__ == "__main__":
    unittest.main()
