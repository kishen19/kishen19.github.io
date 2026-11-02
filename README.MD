# Kishen N. Gowda's website

The main website is at the repository root. All public assets live in `assets/`;
the original CV sources remain in `CV/`. No script commits, pushes, or deploys.

## Folder guide

| Folder | Purpose |
| --- | --- |
| `assets/css/` | Website styles, including `refresh.css` |
| `assets/js/` | JavaScript, including `refresh.js` and `news.mjs` |
| `assets/img/` | Photos, social-preview image, and favicon |
| `assets/files/` | PDFs/slides and the generated `kishen-gowda-cv.pdf` |
| `CV/` | Original editable LaTeX sources and original PDF |
| **`content/`** | All editable main-site text and structured data |
| `templates/` | HTML page structure, separate from your content |
| `tests/` | Automated checks |
| `experimental/` | Unlinked personal/blog previews and earlier design experiments |

The old root `publications.json` and unused publication-loading script are removed.
There is no longer a main-site `data/`, `output/`, or `_archive/` directory.
Use git history for the original website. Existing user deletions of `old/` and
`projects.html` are preserved. Legacy assets still used by `about.html` are kept.

## Preview

```sh
python3 preview.py --open
```

Open **http://127.0.0.1:4173/**. If that preview is already running, just use its URL.
Keep the terminal open; Ctrl+C stops it. Use `--port 4174` if the port is occupied.
The website only needs Python 3.9+; no package installation is needed.

After editing source, run `python3 build.py` and refresh the browser. The delivered
HTML already contains the publications and news, even without JavaScript.

## Everyday updates

| Update | File to edit |
| --- | --- |
| Research interests | **`content/research.html`** |
| Introductory bio | `content/about.html` |
| Publications, shared with the PDF CV | **`content/publications.json`** |
| Lately / Earlier News | **`content/news.json`** |
| Display email, address, photographs, show/hide news | `content/profile.json` |
| Layout, fixed links, SVG curves, metadata | `templates/index.html` |
| Colors, typography, spacing | `assets/css/refresh.css` |
| Non-publication CV sections | Original `CV/*.tex` files |

Run **`python3 build.py`** after main-site edits. It updates the main `index.html`
and the `publications.html` compatibility redirect. It does not compile the CV or
create CV scratch files. Do not edit generated HTML instead of its source.

### Research interests

Use ordinary `<p>...</p>` paragraphs in `content/research.html`. Optional `<h4>`
headings can separate research areas. The layout grows naturally with longer text;
phones place it before Lately. No fixed height or layout change is needed.

### News

Edit one `items` list in `content/news.json`. Add an object such as this, replacing
the example information before removing `draft` or setting it to `false`:

```json
{
  "id": "my-next-event",
  "date": "2026-11",
  "text": "Will be attending [event] at [place].",
  "draft": true
}
```

- Use a unique hyphenated `id` and `YYYY-MM` date (optionally `YYYY-MM-DD`).
  Display dates look like **Nov 2026**. Future events may display immediately.
- `settings.max_visible` defaults to **3**; `max_age_months` defaults to **18**.
  Use `null` for no age cutoff. Entries sort newest first; same-month entries
  follow file order. Old news never backfills empty recent slots.
- Remaining items go into scrollable **Earlier News**. Nothing is deleted.
  Announcement wording stays unchanged, including future tense in the archive.
- `draft: true` excludes an item from delivered HTML. Legacy year-only items need
  an explicit `date_todo` and remain archived until the month is supplied.
- A small script refreshes the age grouping on page load using America/New_York.
  Without JS, grouping reflects the last build, but all news is still readable.

### Publications: one source for website and CV

Edit **`content/publications.json`**, not files in `experimental/` or the old CV
bibliography. Each record has `id`, `order`, `category`, `title`, and `authors`.

- `category`: `conference` (including workshops), `journal`, or `under_submission`
  (including arXiv). These control the subtle margin marker/color.
- `venue`: normal casing, e.g. `PPoPP`, `NeurIPS`, `VecDB`, `arXiv`.
- `year`: venue/public-posting year; omit only for an unposted submission.
  Undated submissions come first, then **all dated works sort by descending year**.
  Lower `order` values control ordering within a year. Keep IDs/order values unique.
- `status`: omit for published work, or use `to_appear` / `under_submission`.
- `award`: optional text, e.g. `Best Paper Nominee`, shown in the gold margin badge.
- `links`: only real artifacts, e.g. `{"label":"DOI","url":"https://doi.org/..."}`.
  Labels can include `arXiv`, `PDF`, `Code`, `Slides`, `Talk`, `Project`.
  Local paths use `assets/files/...`; empty lists are fine. Never use `#`.
- `cv`: defaults to true; false deliberately omits a work from the generated PDF.
- `blog`: reserved for a real future `{"url":"writing/my-paper.html","published":true}`
  link. Leave absent until the page is ready. Metadata such as `selected`, `tags`,
  `summary`, and `visual` is retained but currently not displayed.

All entries appear on the main page. The old `publications.html` URL redirects
there. Legacy `#home`, `#page-top`, and `#contact1` anchors remain supported.

## PDF CV: refresh only when ready

```sh
python3 build.py --cv
python3 validate.py --cv
```

This copies the non-publication LaTeX sections from `CV/` into disposable
`_build/cv/`, generates its publication section from `content/publications.json`,
and compiles **`assets/files/kishen-gowda-cv.pdf`**. The homepage links to this PDF.
Its companion `.json` file lets validation detect stale publication/CV inputs.
PDF generation needs the existing `latexmk`/TeX installation (e.g. MacTeX).

The original `CV/` directory and `CV/main.pdf` remain unchanged. For other CV
updates, edit the original `CV/*.tex` sections, then run the command above.
Do not compile directly inside `CV/` for the unified version: that would use the
old publication list in `CV/3_publications.tex`. Ordinary builds never compile PDFs.

The generated PDF was **moved, not regenerated**, during folder cleanup; its
contents are unchanged. Its freshness record was migrated after verifying that
the publication data and other CV inputs were unchanged.

## Personal and blog previews (not published)

These stay in `experimental/`, excluded from GitHub Pages and unlinked from the
main website. With the same preview server running:

- Personal corner: http://127.0.0.1:4173/experimental/personal.html
- Writing and course-notes plan: http://127.0.0.1:4173/experimental/writing.html
- Blog template: http://127.0.0.1:4173/experimental/writing/behind-the-paper-template.html

Rebuild them with `python3 experimental/build.py`. The personal page's albums,
music, and books are in `experimental/data/personal.json`. The current albums
reuse existing photos; favorites are intentionally empty until chosen.
Multiple photos in an album form a touch/keyboard-scrollable strip.

The blog body is editable HTML in
`experimental/content/posts/behind-the-paper-template.html`, with metadata in
`experimental/data/posts.json`. It is marked as a **draft template**, not a real
published article. HTML previews need no extra dependency. Optional Markdown
sources need the existing `experimental/requirements.txt` dependency. The course
notes are only a plan in `experimental/data/writing.json`; no scanned notes have
been uploaded or linked. Don't delete `experimental/` until you've kept any drafts
you want: these new drafts are not yet in git history.

## Before your own commit/push

```sh
python3 build.py --cv
python3 validate.py --cv
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/news.test.mjs
node tests/refresh.test.mjs
```

Include sources, generated main HTML, assets (including the CV PDF and its JSON
record), and `_config.yml`. Pages serves checked-in HTML; Python runs locally.
`_config.yml` excludes editable sources, tests, and the workshop from Pages.
`_build/` and Python `__pycache__/` folders are disposable/ignored.

Still to confirm: the existing CV says **May 2027** while the earlier brief said
December 2027; CV and website use different UMD email variants. Neither graduation
date appears on the website. UFO Trees news uses the Feb 2026 conference month,
not a verified nomination-announcement month, and three old news records have
`date_todo` fields. The set-cover journal paper uses its publisher's 2027 issue
year. Source provenance is preserved in the publication/news JSON.
