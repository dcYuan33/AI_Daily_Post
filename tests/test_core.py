import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.main import resolve_report_date
from app.models import DailyReport, ReportItem
from app.render import render_markdown, save_report


class FakeSettings:
    timezone = __import__("zoneinfo").zoneinfo.ZoneInfo("Asia/Shanghai")


class CoreTests(unittest.TestCase):
    def test_default_report_date_is_previous_local_day(self):
        # Explicit dates are stable and do not depend on the machine clock.
        self.assertEqual(resolve_report_date(FakeSettings(), "2026-10-05"), date(2026, 10, 5))

    def test_markdown_contains_sources(self):
        report = DailyReport(
            title="AI 日报｜2026-10-05",
            report_date="2026-10-05",
            generated_at="2026-10-06T09:17:00+08:00",
            items=[ReportItem(
                title="测试新闻",
                time="2026-10-05",
                category="模型与研究",
                summary="这是测试摘要。",
                sources=[{"name": "OpenAI News", "tier": "A", "url": "https://example.com/news"}],
            )],
        )
        output = render_markdown(report)
        self.assertIn("测试新闻", output)
        self.assertIn("OpenAI News（A）", output)
        self.assertIn("https://example.com/news", output)

    def test_save_report(self):
        report = DailyReport("AI 日报｜2026-10-05", "2026-10-05", "now", [])
        with tempfile.TemporaryDirectory() as directory:
            md, html = save_report(report, Path(directory))
            self.assertTrue(md.exists())
            self.assertTrue(html.exists())
            self.assertIn("暂未发现", md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
