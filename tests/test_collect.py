import unittest
from datetime import date, datetime
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from app.collect import _local_date, _page_date, _rss_candidates, collect_candidates, enrich_candidates, fetch_page
from app.models import Candidate


class CollectionTests(unittest.TestCase):
    def test_rss_dates_use_report_timezone(self):
        self.assertEqual(_local_date(datetime.fromisoformat("2026-10-06T20:00:00+00:00")), date(2026, 10, 7))
        self.assertEqual(_local_date(datetime.fromisoformat("2026-10-07T20:00:00+00:00")), date(2026, 10, 8))
        self.assertEqual(_local_date(datetime(2026, 10, 7)), date(2026, 10, 7))

    def test_jsonld_publication_date_precedes_unrelated_time(self):
        soup = BeautifulSoup('''<time datetime="2026-10-08"></time>
            <script type="application/ld+json">{"@graph":[
              {"@type":"NewsArticle","datePublished":"2026-10-07T12:00:00Z"}
            ]}</script>''', "html.parser")
        self.assertEqual(_page_date(soup), datetime.fromisoformat("2026-10-07T12:00:00+00:00"))

    @patch("app.collect.requests.get")
    def test_fetch_preserves_date_before_text_cleanup(self, get):
        get.return_value = Mock(url="https://example.com/news", text='''<html><body>
            <script type="application/ld+json">{"@type":"BlogPosting","datePublished":"2026-10-07"}</script>
            <article><header><time datetime="2026-10-07"></time></header>
            <p>A new developer tool with a verifiable announcement and detailed documentation.</p></article>
            </body></html>''')
        _, content, published = fetch_page("https://example.com/news")
        self.assertIn("developer tool", content)
        self.assertEqual(published, datetime(2026, 10, 7))

    @patch("app.collect.fetch_page", return_value=("https://example.com/article", "body", None))
    def test_article_budget_covers_late_sources_and_is_stable(self, fetch):
        candidates = [Candidate(source, tier, "https://example.com/", str(i), f"https://example.com/{source}/{i}")
                      for source, tier in [("first", "A"), ("second", "B"), ("last", "C")]
                      for i in range(20)]
        enriched = enrich_candidates(candidates, max_articles=6)
        self.assertEqual([item.source_name for item in enriched], ["first", "second", "last"] * 2)
        self.assertEqual(fetch.call_count, 6)

    @patch("app.collect.enrich_candidates")
    @patch("app.collect.load_sources", return_value=[])
    def test_collection_does_not_send_known_old_news_to_ai(self, load, enrich):
        items = [Candidate("Test", "A", "https://example.com/", title, f"https://example.com/{title}", published_at=stamp)
                 for title, stamp in [("today", datetime(2026, 10, 7)),
                                      ("old", datetime(2026, 10, 6)), ("unknown", None)]]
        enrich.return_value = items
        self.assertEqual([item.title for item in collect_candidates(None, date(2026, 10, 7))], ["today", "unknown"])

    @patch("app.collect.requests.get")
    def test_rss_excludes_next_local_day_not_previous_utc_day(self, get):
        get.return_value = Mock(content=b'''<rss version="2.0"><channel><title>AI</title>
            <item><title>Included</title><link>https://example.com/yes</link>
              <pubDate>Tue, 06 Oct 2026 20:00:00 GMT</pubDate></item>
            <item><title>Next day</title><link>https://example.com/no</link>
              <pubDate>Wed, 07 Oct 2026 20:00:00 GMT</pubDate></item>
            </channel></rss>''')
        source = {"rss": "https://example.com/rss", "url": "https://example.com/", "name": "Test", "tier": "A"}
        entries = _rss_candidates(source, date(2026, 10, 7))
        self.assertEqual([entry.title for entry in entries], ["Included"])


if __name__ == "__main__":
    unittest.main()
