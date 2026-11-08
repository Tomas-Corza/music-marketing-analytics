import unittest
from unittest.mock import Mock, patch
from scripts.export_meta import REPORTS, report_fields, fetch_report


class TestExporter(unittest.TestCase):
    def test_ten_reports(self):
        self.assertEqual(len(REPORTS), 10)

    def test_video_fields_in_overall_ad_report(self):
        self.assertIn('video_p95_watched_actions', report_fields('ad', None))
        self.assertNotIn('video_p95_watched_actions', report_fields('ad', 'country'))

    @patch('scripts.export_meta.time.sleep')
    def test_async_export_and_pagination(self, _sleep):
        session = Mock()
        responses = [
            {'report_run_id': '123'},
            {'async_status': 'Job Running'},
            {'async_status': 'Job Completed'},
            {'data': [{'campaign_name': 'Example A'}], 'paging': {'next': 'https://example.org/page2'}},
            {'data': [{'campaign_name': 'Example B'}]},
        ]
        with patch('scripts.export_meta.api_request', side_effect=responses) as api:
            rows = fetch_report(session, 'https://example.org', 'act_123',
                                '2026-08-01', '2026-08-31', 'campaign')
        self.assertEqual(len(rows), 2)
        self.assertEqual(api.call_count, 5)


if __name__ == '__main__':
    unittest.main()
