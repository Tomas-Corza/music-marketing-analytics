import unittest
import pandas as pd
from scripts.analyze_meta import action_count, summarize

class TestAnalysis(unittest.TestCase):
    def test_lpv_parsing(self):
        self.assertEqual(action_count('[{"action_type":"landing_page_view","value":"9"}]'), 9)
        self.assertEqual(action_count('[]'), 0)
    def test_zero_lpv(self):
        frame = pd.DataFrame([{'campaign_name':'Example', 'spend':10, 'impressions':100, 'actions':'[]'}])
        result = summarize(frame, ['campaign_name'])
        self.assertEqual(result.iloc[0]['spend'], 10)
        self.assertTrue(pd.isna(result.iloc[0]['cost_per_lpv']))

if __name__ == '__main__':
    unittest.main()
