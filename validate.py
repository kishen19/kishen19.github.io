#!/usr/bin/env python3
"""Check rendered content, local assets, anchors, shared publication data and PDF freshness."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from build import CV_OUTPUT, cv_fingerprint, publication_sort_key
from news import news_records

ROOT = Path(__file__).resolve().parent

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = []
        self.targets = []
        self.images = []
        self.publications = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "li" and "publication" in attrs.get("class", "").split():
            self.publications.append(attrs.get("id"))
        if tag in ("img", "script", "link", "a"):
            target = attrs.get("src") or attrs.get("href")
            if target:
                self.targets.append(target)
        if tag == "img":
            self.images.append((attrs.get("src"), attrs.get("alt")))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv", action="store_true", help="require PDF to match current publication data")
    args = parser.parse_args()
    errors = []
    try:
        news_records(json.loads((ROOT / "content/news.json").read_text()))
    except ValueError as error:
        errors.append(f"Invalid news data: {error}")
    pages = [Page(ROOT / name) for name in ("index.html", "publications.html")]
    pages += [Page(p) for p in (ROOT / "writing").glob("*.html")] if (ROOT / "writing").exists() else []
    for page in pages:
        if len(page.ids) != len(set(page.ids)):
            errors.append(f"Duplicate id in {page.path.name}")
        for src, alt in page.images:
            if not alt:
                errors.append(f"Missing image alt text: {src}")
        for target in page.targets:
            if target == "#":
                errors.append(f"Placeholder link in {page.path.name}")
                continue
            parsed = urlparse(target)
            if parsed.scheme or parsed.netloc:
                continue
            path, fragment = unquote(parsed.path), unquote(parsed.fragment)
            resolved = (page.path.parent / path).resolve() if path else page.path
            if not resolved.exists():
                errors.append(f"Missing target in {page.path.name}: {target}")
            elif fragment and resolved.suffix == ".html":
                if fragment not in Page(resolved).ids:
                    errors.append(f"Missing anchor in {page.path.name}: {target}")
    publications = json.loads((ROOT / "content/publications.json").read_text())
    expected = [p["id"] for p in sorted(publications, key=publication_sort_key)]
    if pages[0].publications != expected:
        errors.append("The homepage publication list does not match the shared source and its order")
    if len(expected) != len(set(expected)):
        errors.append("Publication IDs must be unique")
    orders = [p["order"] for p in publications]
    if len(orders) != len(set(orders)):
        errors.append("Publication order values must be unique")
    for p in publications:
        if p["category"] not in ("conference", "journal", "under_submission"):
            errors.append(f"Unknown publication category: {p['id']}")
        if not p.get("title") or not p.get("authors"):
            errors.append(f"Incomplete publication: {p['id']}")
        if p.get("status") not in (None, "to_appear", "under_submission"):
            errors.append(f"Unknown publication status: {p['id']}")
        if p.get("status") == "under_submission" and p["category"] != "under_submission":
            errors.append(f"Submission badge on a published/accepted entry: {p['id']}")
        if not p.get("year") and (p["category"] != "under_submission" or any(link["label"] == "arXiv" for link in p.get("links", []))):
            errors.append(f"Published, accepted, and arXiv entries need a year: {p['id']}")
        if p.get("blog", {}).get("published") and not p["blog"].get("url"):
            errors.append(f"Published blog needs a URL: {p['id']}")
    css_path = ROOT / "assets/css/refresh.css"
    css = css_path.read_text()
    for target in re.findall(r'url\(["\']?([^\)"\']+)', css):
        if not urlparse(target).scheme and not (css_path.parent / target).resolve().exists():
            errors.append(f"Missing CSS image: {target}")
    profile = json.loads((ROOT / "content/profile.json").read_text())
    for key in ("hero_image", "portrait"):
        if not (ROOT / profile[key]).resolve().exists():
            errors.append(f"Missing profile image: {key}")
    if profile.get("contact_image") and not (ROOT / profile["contact_image"]).resolve().is_file():
        errors.append("Missing profile image: contact_image")
    cv = CV_OUTPUT
    stamp = cv.with_suffix(".json")
    current = hashlib.sha256((ROOT / "content/publications.json").read_bytes()).hexdigest()
    fresh = cv.exists() and stamp.exists() and json.loads(stamp.read_text())["publications_sha256"] == current and json.loads(stamp.read_text()).get("cv_inputs_sha256") == cv_fingerprint()
    if args.cv and not fresh:
        errors.append("PDF is out of date. Run python3 build.py --cv before pushing.")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(pages)} pages, {len(publications)} static publication entries, local links and assets.")
    print("PDF publication data is current." if fresh else "PDF refresh is optional until you prepare to push (--cv).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
