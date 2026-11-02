"""Dependency-free checks for publication chronology, metadata, and status rendering."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import cv_publications, data, ordered_publications, publication


class PublicationTests(unittest.TestCase):
    def test_unposted_first_then_year_then_manual_order(self):
        entries = [
            {"id": "older-preprint", "category": "under_submission", "year": 2025, "order": 1},
            {"id": "accepted", "category": "conference", "year": 2027, "order": 50},
            {"id": "newer-preprint", "category": "under_submission", "year": 2026, "order": 30},
            {"id": "same-year-journal", "category": "journal", "year": 2026, "order": 20},
            {"id": "unposted", "category": "under_submission", "order": 999},
        ]
        self.assertEqual([p["id"] for p in ordered_publications(entries)], [
            "unposted", "accepted", "same-year-journal", "newer-preprint", "older-preprint"
        ])

    def test_submission_badge_is_not_an_award(self):
        pub = next(p for p in data("publications.json") if p["id"] == "parallel-hac-low-dimensions")
        rendered = publication(pub, 1)
        self.assertIn('<p class="pub-submission">Under Submission</p>', rendered)
        self.assertNotIn('class="pub-award"', rendered)
        self.assertIn('class="pub-year">2025</span>', rendered)
        self.assertIn('arXiv', rendered)
        self.assertIn('(Under Submission)', cv_publications([pub]))

    def test_acceptance_updates_and_new_journal(self):
        pubs = {p["id"]: p for p in data("publications.json")}
        for identifier in ("ultrakmeans", "ef1"):
            pub = pubs[identifier]
            self.assertEqual(pub["category"], "conference")
            self.assertEqual(pub["status"], "to_appear")
            self.assertIn('class="pub-status">to appear</span>', publication(pub, 1))
        self.assertEqual(pubs["ultrakmeans"]["year"], 2027)
        self.assertEqual(pubs["ultrakmeans"]["venue"], "PPoPP")
        self.assertNotIn('<a ', publication(pubs["ultrakmeans"], 1))
        self.assertEqual(pubs["mv-ivf"]["venue"], "VecDB")
        journal = pubs["set-cover-exponential-clocks"]
        self.assertEqual(journal["category"], "journal")
        self.assertEqual(journal["year"], 2027)
        self.assertEqual(journal["links"][0]["url"], 'https://doi.org/10.1016/j.orl.2026.107553')

    def test_award_and_undated_submission_remain_supported(self):
        award = next(p for p in data("publications.json") if p["id"] == "ufo-trees")
        self.assertIn('class="pub-award">Best Paper Nominee</p>', publication(award, 1))
        draft = {"id": "draft", "category": "under_submission", "title": "Draft", "authors": ["Kishen N Gowda"], "venue": "Under Submission", "links": []}
        rendered = publication(draft, 1)
        self.assertNotIn('class="pub-year"', rendered)
        self.assertNotIn('href="#"', rendered)

    def test_cv_journals_use_venue_without_a_type_prefix(self):
        for pub in data("publications.json"):
            if pub["category"] != "journal":
                continue
            with self.subTest(publication=pub["id"]):
                rendered = cv_publications([pub])
                self.assertNotIn("Journal:", rendered)
                self.assertIn(f'{pub["venue"]} {pub["year"]}', rendered)


if __name__ == "__main__":
    unittest.main()
