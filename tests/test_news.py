"""Static news dates, filtering, draft handling, and accessible archive rendering."""
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from news import news_date, news_groups, news_records, news_text, render_news


def record(identifier, when, **extra):
    return {"id": identifier, "date": when, "text": identifier, **extra}


class NewsTests(unittest.TestCase):
    def test_inline_links(self):
        markup = news_text("Our [paper](#mv-ivf) at [a workshop](https://example.org/?a=1&b=2).")
        self.assertIn('<a href="#mv-ivf">paper</a>', markup)
        self.assertIn('<a href="https://example.org/?a=1&amp;b=2" target="_blank" rel="noopener noreferrer">a workshop</a>.', markup)
        self.assertEqual(news_text("[PDF](assets/files/paper.pdf)"), '<a href="assets/files/paper.pdf">PDF</a>')
        self.assertIn('href="https://example.org/Topic_(paper)"', news_text("[topic](https://example.org/Topic_(paper))"))

    def test_inline_links_escape_html_and_reject_unsafe_urls(self):
        self.assertEqual(news_text('[<b>paper</b>](#paper)'), '<a href="#paper">&lt;b&gt;paper&lt;/b&gt;</a>')
        for url in ("javascript:alert(1)", "data:text/html,test", "//example.org", "https:\\example.org", "https://[invalid"):
            with self.subTest(url=url):
                self.assertNotIn('<a ', news_text(f'[paper]({url})'))
        self.assertEqual(news_text('[unfinished]( and <b>plain</b>'), '[unfinished]( and &lt;b&gt;plain&lt;/b&gt;')

    def test_labels_and_date_validation(self):
        self.assertEqual(news_date("2025-07"), (2025, 7, "Jul 2025", "2025-07"))
        self.assertEqual(news_date("2024-02-29")[2], "Feb 2024")
        self.assertEqual(news_date("2023–2024"), (2024, None, "2023–2024", None))
        for value in ("2025-13", "2025-2", "2025-02-29", "2025–2023", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                news_date(value)

    def test_sorted_recent_cap_and_complete_history(self):
        config = {"items": [record("old", "2024-01"), record("one", "2026-09"), record("new", "2026-11"), record("two", "2026-10"), record("overflow", "2026-08")]}
        recent, archive, _ = news_groups(config, date(2026, 11, 1))
        self.assertEqual([item["id"] for item in recent], ["new", "two", "one"])
        self.assertEqual([item["id"] for item in archive], ["overflow", "old"])

    def test_calendar_cutoff_year_rollover_and_future_events(self):
        config = {"settings": {"max_age_months": 3}, "items": [record("jan", "2027-01"), record("dec", "2026-12"), record("nov", "2026-11"), record("boundary", "2026-10")]}
        recent, archive, _ = news_groups(config, date(2027, 1, 1))
        self.assertEqual([item["id"] for item in recent], ["jan", "dec", "nov"])
        self.assertEqual([item["id"] for item in archive], ["boundary"])
        recent, _, _ = news_groups({"items": [record("upcoming", "2027-02")]}, date(2026, 11, 1))
        self.assertEqual(recent[0]["id"], "upcoming")

    def test_no_backfill_and_disable_age_limit(self):
        config = {"items": [record("old", "2020-01")]}
        recent, archive, _ = news_groups(config, date(2026, 11, 1))
        self.assertEqual(recent, [])
        self.assertEqual(len(archive), 1)
        config["settings"] = {"max_age_months": None, "max_visible": 2}
        self.assertEqual(len(news_groups(config, date(2026, 11, 1))[0]), 1)

    def test_legacy_dates_are_archived_not_invented(self):
        config = {"items": [record("legacy", "2026", date_todo="Confirm month")]}
        recent, archive, _ = news_groups(config, date(2026, 11, 1))
        self.assertEqual(recent, [])
        self.assertEqual(archive[0]["label"], "2026")
        with self.assertRaises(ValueError):
            news_records({"items": [record("legacy", "2026")]})

    def test_drafts_empty_and_bad_configuration(self):
        self.assertEqual(render_news({"items": [{"id": "draft", "draft": True}]}), "")
        self.assertEqual(render_news({"items": []}), "")
        for settings in ({"max_visible": 0}, {"max_age_months": -1}, {"max_age_months": True}, None):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                news_records({"settings": settings, "items": []})
        with self.assertRaises(ValueError):
            news_records({"items": [record("same", "2025-01"), record("same", "2025-02")]})

    def test_static_content_escaping_and_archive_accessibility(self):
        config = {"items": [record("recent", "2026-11", text="Will be attending <a workshop>."), record("old", "2025-01")]}
        markup = render_news(config, date(2026, 11, 1))
        self.assertIn("Will be attending &lt;a workshop&gt;.", markup)
        self.assertIn('<time class="news-date" datetime="2026-11">Nov 2026</time>', markup)
        self.assertIn("Earlier News", markup)
        self.assertIn('role="region" aria-labelledby="earlier-news-label" tabindex="0"', markup)
        self.assertIn('id="news-old"', markup)
        self.assertNotIn("Earlier notes", markup)


if __name__ == "__main__":
    unittest.main()
