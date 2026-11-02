#!/usr/bin/env python3
"""Render the main website. Add --cv to refresh its PDF CV before pushing."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlparse

from news import render_news

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://kishen19.github.io/"
SELF = "Kishen N Gowda"
CV_OUTPUT = ROOT / "assets/files/kishen-gowda-cv.pdf"
CV_SOURCE = ROOT / "_build/cv"


def data(name):
    return json.loads((ROOT / "content" / name).read_text(encoding="utf-8"))


def safe(value):
    return html.escape(str(value), quote=True)


def anchor(url, label, class_name=""):
    if not url or url == "#":
        raise ValueError(f"Missing destination for {label}")
    attrs = ' target="_blank" rel="noopener noreferrer"' if url.startswith("https://") else ""
    return f'<a href="{safe(url)}" class="{class_name}"{attrs}>{safe(label)}</a>'


def publication_sort_key(pub):
    # Unposted submissions first; then all dated works share the same chronology.
    unposted = pub["category"] == "under_submission" and not pub.get("year")
    return (0 if unposted else 1, -(pub.get("year") or 0), pub.get("order", 10000), pub["id"])


def ordered_publications(publications=None):
    return sorted(data("publications.json") if publications is None else publications, key=publication_sort_key)


def publication(pub, number=None):
    category = pub["category"]
    kind = {"conference": "Conference or workshop", "journal": "Journal", "under_submission": "Work in progress"}[category]
    venue = pub.get("venue") or "Under Submission"
    year = f' <span class="pub-year">{pub["year"]}</span>' if pub.get("year") else ""
    status = ' <span class="pub-status">to appear</span>' if pub.get("status") == "to_appear" else ""
    if pub.get("status") == "under_submission":
        status = '<p class="pub-submission">Under Submission</p>'
    names = ", ".join(f'<strong>{safe(n)}</strong>' if n == SELF else safe(n) for n in pub["authors"])
    links = [anchor(link["url"], link["label"]) for link in pub.get("links", []) if link.get("url")]
    blog = pub.get("blog")
    if blog and blog.get("published"):
        links.append(anchor(blog["url"], "Behind the paper", "paper-story"))
    award = f'<p class="pub-award">{safe(pub["award"])}</p>' if pub.get("award") else ""
    return f'''<li class="publication {category}" id="{safe(pub['id'])}">
  <div class="pub-meta"><div class="pub-venue-line"><span class="sr-only">{kind}: </span><span class="pub-venue"><span class="kind-marker" aria-hidden="true"></span>{safe(venue)}</span>{year}</div>{status}{award}</div>
  <div class="pub-copy"><h3>{safe(pub['title'])}</h3><p class="pub-authors">{names}</p><div class="pub-resources">{' '.join(links)}</div></div>
</li>'''


def render(template, target, replacements):
    text = (ROOT / "templates" / template).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("@@" + key + "@@", value)
    if re.search(r"@@[A-Z_]+@@", text):
        raise ValueError(f"Unfilled template token in {template}")
    (ROOT / target).write_text(text, encoding="utf-8")


def tex_escape(text):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "Ł": r"\L{}", "ą": r"\k{a}", "ü": r'\"{u}', "–": "--", "—": "---", "’": "'"}
    return "".join(replacements.get(c, c) for c in str(text))


def cv_publications(publications):
    lines = ["% Generated from content/publications.json. Edit that file instead.", r"\makerubrichead{Publications}", r"\begingroup\small", r"\begin{enumerate}", r"\setlength{\itemsep}{1.05ex}", r"\setlength{\parskip}{0pt}"]
    for pub in publications:
        if pub.get("cv", True) is False:
            continue
        resources = pub.get("links", [])
        destination = next((link["url"] for link in resources if link["label"] == "DOI"), next((link["url"] for link in resources if link["label"] == "arXiv"), None))
        if not destination and resources:
            destination = resources[0]["url"]
        if destination and not urlparse(destination).scheme:
            destination = SITE_URL + (ROOT / destination).resolve().relative_to(ROOT).as_posix()
        title = tex_escape(pub["title"])
        if destination:
            title = r"\href{" + destination.replace("%", r"\%") + "}{" + title + "}"
        venue = tex_escape(pub.get("venue") or "Under Submission")
        year = " " + str(pub["year"]) if pub.get("year") else ""
        status = {"to_appear": " (to appear)", "under_submission": " (Under Submission)"}.get(pub.get("status"), "")
        names = ", ".join(r"\textcolor{SwishLineColour}{\textbf{" + tex_escape(name) + "}}" if name == SELF else tex_escape(name) for name in pub["authors"])
        lines.extend([r"\item \textbf{" + title + r"}\par\nopagebreak", names + r"\par\nopagebreak", r"{\footnotesize\emph{" + venue + year + status + "}}"])
        if pub.get("award"):
            lines.append(r"\quad\textcolor{SwishLineColour}{\textbf{" + tex_escape(pub["award"]) + "}}")
    lines.extend([r"\end{enumerate}", r"\endgroup"])
    return "\n".join(lines) + "\n"


def generate_cv_source(publications):
    """Copy original non-publication sections; never overwrite anything in CV/."""
    CV_SOURCE.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "CV").iterdir():
        if source.suffix in (".tex", ".sty", ".bbx", ".cbx", ".bib") and source.name != "3_publications.tex":
            shutil.copy2(source, CV_SOURCE / source.name)
    (CV_SOURCE / "3_publications.tex").write_text(cv_publications(publications), encoding="utf-8")
    return CV_SOURCE


def cv_fingerprint():
    digest = hashlib.sha256(cv_publications(ordered_publications()).encode())
    for source in sorted((ROOT / "CV").iterdir()):
        if source.suffix in (".tex", ".sty", ".bbx", ".cbx", ".bib") and source.name != "3_publications.tex":
            digest.update(source.name.encode())
            digest.update(source.read_bytes())
    return digest.hexdigest()


def build_cv(source):
    engine = shutil.which("latexmk")
    if not engine and Path("/Library/TeX/texbin/latexmk").is_file():
        engine = "/Library/TeX/texbin/latexmk"
    if not engine:
        raise RuntimeError("PDF generation needs latexmk and a TeX distribution (e.g. MacTeX). Normal website builds do not need them.")
    result = subprocess.run([engine, "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=source, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("CV compilation failed; see _build/cv/main.log.\n" + result.stdout[-2500:])
    CV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "main.pdf", CV_OUTPUT)
    stamp = {"publications_sha256": hashlib.sha256((ROOT / "content/publications.json").read_bytes()).hexdigest(), "cv_inputs_sha256": cv_fingerprint(), "entries": len([pub for pub in ordered_publications() if pub.get("cv", True)])}
    CV_OUTPUT.with_suffix(".json").write_text(json.dumps(stamp, indent=2) + "\n", encoding="utf-8")
    print(f"Refreshed PDF: {CV_OUTPUT.relative_to(ROOT)} (original CV/ files unchanged)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cv", action="store_true", help="also compile the shared-data PDF; never overwrites CV/main.pdf")
    args = parser.parse_args()
    profile = data("profile.json")
    pubs = ordered_publications()
    if args.cv:
        build_cv(generate_cv_source(pubs))
    replacements = {
        "ABOUT": (ROOT / "content/about.html").read_text(encoding="utf-8"),
        "INTERESTS": (ROOT / "content/research.html").read_text(encoding="utf-8"),
        "PUBLICATIONS": "\n".join(publication(pub) for pub in pubs),
        "NEWS": render_news(data("news.json")) if profile.get("show_news") else "",
        "PORTRAIT": safe(profile["portrait"]),
        "HERO_IMAGE": safe(profile["hero_image"]),
        "CONTACT_IMAGE": safe(profile.get("contact_image") or profile["hero_image"]),
        "EMAIL_DISPLAY": safe(profile["email_display"]),
        "ADDRESS": "<br>".join(safe(line) for line in profile["address_lines"]),
        "CV_URL": CV_OUTPUT.relative_to(ROOT).as_posix() if CV_OUTPUT.exists() else "CV/main.pdf",
    }
    render("index.html", "index.html", replacements)
    render("publications-redirect.html", "publications.html", {})
    print(f"Rendered {len(pubs)} publications and news. PDF compilation only with --cv. No git or deployment actions.")


if __name__ == "__main__":
    main()
