import unittest

import pandas as pd

from scripts.analyze_spotify import calculate


class SpotifyEfficiencyTests(unittest.TestCase):
    def test_observed_efficiency(self):
        meta = pd.DataFrame({"spend": [100.0]})
        spotify = pd.DataFrame({"saves": [50], "listeners": [200]})
        result = calculate(meta, spotify, [])
        self.assertAlmostEqual(result.loc[0, "saves_per_dollar"], 0.5)
        self.assertAlmostEqual(result.loc[0, "cost_per_save"], 2.0)
        self.assertAlmostEqual(result.loc[0, "save_rate_pct"], 25.0)

    def test_zero_denominators(self):
        result = calculate(pd.DataFrame({"spend": [0]}), pd.DataFrame({"saves": [0], "listeners": [0]}), [])
        self.assertTrue(pd.isna(result.loc[0, "saves_per_dollar"]))
        self.assertTrue(pd.isna(result.loc[0, "cost_per_save"]))
        self.assertTrue(pd.isna(result.loc[0, "save_rate_pct"]))

    def test_grouping_and_baseline(self):
        meta = pd.DataFrame({"country": ["US", "PL"], "spend": [20, 10]})
        spotify = pd.DataFrame({"country": ["PL", "US"], "saves": [50, 30]})
        baseline = pd.DataFrame({"country": ["US", "PL"], "expected_saves": [10, 40]})
        result = calculate(meta, spotify, ["country"], baseline).set_index("country")
        self.assertAlmostEqual(result.loc["US", "cost_per_estimated_incremental_save"], 1.0)
        self.assertAlmostEqual(result.loc["PL", "cost_per_estimated_incremental_save"], 1.0)

    def test_unmatched_groups_fail(self):
        with self.assertRaises(ValueError):
            calculate(pd.DataFrame({"country": ["US"], "spend": [10]}),
                      pd.DataFrame({"country": ["PL"], "saves": [2]}), ["country"])


if __name__ == "__main__":
    unittest.main()
