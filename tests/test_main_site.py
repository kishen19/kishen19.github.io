"""Main-site safeguards: asset paths, consolidated content, and an isolated CV build."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build
from validate import Page


class MainSiteTests(unittest.TestCase):
    def test_main_assets_do_not_depend_on_experimental(self):
        page = Page(build.ROOT / "index.html")
        self.assertFalse(any("experimental/" in target or target.startswith("../") for target in page.targets))
        self.assertIn("page-top", page.ids)
        self.assertIn("contact1", page.ids)
        text = page.path.read_text()
        self.assertNotIn("@@", text)
        self.assertNotIn("curve-preview", text)
        self.assertNotIn("facebook", text.lower())
        self.assertIn('content="https://kishen19.github.io/assets/img/og.png"', text)

    def test_obsolete_sources_are_removed(self):
        for name in ("publications.json", "assets/js/publications.js", "data", "output", "_archive"):
            with self.subTest(path=name):
                self.assertFalse((build.ROOT / name).exists())

    def test_editable_main_content_is_consolidated(self):
        for name in ("publications.json", "news.json", "profile.json"):
            with self.subTest(path=name):
                self.assertTrue((build.ROOT / "content" / name).is_file())
                self.assertTrue(build.data(name))
        self.assertEqual(build.CV_OUTPUT.parent, build.ROOT / "assets/files")

    def test_cv_local_artifact_is_a_production_url(self):
        pub = next(pub for pub in build.data("publications.json") if pub["id"] == "mv-ivf")
        text = build.cv_publications([pub])
        self.assertIn("https://kishen19.github.io/assets/files/publications/mvivf.pdf", text)
        self.assertNotIn("experimental/", text)

    def test_cv_exclusion_and_source_remain_explicit(self):
        pub = {"id": "private", "title": "Not for CV", "cv": False}
        self.assertNotIn("Not for CV", build.cv_publications([pub]))
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(build, "CV_SOURCE", Path(directory)):
                source = build.generate_cv_source(build.ordered_publications())
                self.assertIn("Generated from content/publications.json", (source / "3_publications.tex").read_text())
                self.assertNotEqual(source, build.ROOT / "CV")
                self.assertEqual((source / "2_education.tex").read_bytes(), (build.ROOT / "CV/2_education.tex").read_bytes())


if __name__ == "__main__":
    unittest.main()
