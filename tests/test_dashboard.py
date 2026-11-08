import unittest
import pandas as pd
from scripts.dashboard_data import prepare_dashboard, demo_inputs


class DashboardTests(unittest.TestCase):
    def test_demo(self):
        meta, spotify, _ = demo_inputs()
        summary, by_country = prepare_dashboard(meta, spotify)
        self.assertEqual(len(by_country), 4)
        self.assertAlmostEqual(summary.iloc[0]["spend"], 540)
        self.assertAlmostEqual(summary.iloc[0]["saves"], 296)
        self.assertAlmostEqual(summary.iloc[0]["landing_page_views"], 545)
        self.assertAlmostEqual(summary.iloc[0]["saves_per_dollar"], 296 / 540)

    def test_country_mismatch(self):
        meta = pd.DataFrame({"country": ["US"], "spend": [10]})
        spotify = pd.DataFrame({"country": ["PL"], "saves": [2]})
        with self.assertRaisesRegex(ValueError, "Unmatched"):
            prepare_dashboard(meta, spotify)

    def test_reject_negative_spend(self):
        meta = pd.DataFrame({"country": ["US"], "spend": [-10]})
        spotify = pd.DataFrame({"country": ["US"], "saves": [2]})
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            prepare_dashboard(meta, spotify)

    def test_no_multiply_from_duplicate_countries(self):
        meta = pd.DataFrame({"country": ["US", "US"], "spend": [10, 5], "actions": ['[]', '[]']})
        spotify = pd.DataFrame({"country": ["US", "US"], "saves": [3, 2]})
        summary, _ = prepare_dashboard(meta, spotify)
        self.assertEqual(summary.iloc[0]["spend"], 15)
        self.assertEqual(summary.iloc[0]["saves"], 5)

if __name__ == "__main__":
    unittest.main()
