# kishen19.github.io
Go to my [Personal Website](https://kishen19.github.io/)

## Updating news

Edit the single `items` list in `content/news.json`. Use `YYYY-MM` dates;
the newest entries appear first. `settings.max_visible` controls the number
shown under Lately, and `max_age_months` moves older entries into Earlier News.
Set `"draft": true` on an entry to hide it.

Add links directly inside `text`, using `[words to link](URL)`, for example:

```json
"text": "I will present [MV-IVF](#mv-ivf) at the [VecDB workshop](https://vecdb-ws.github.io/vldb2026/papers.html)."
```

Use `#publication-id` for a publication on this page, a local path for a PDF,
or a full `https://…` URL. Multiple links in one announcement are supported.
No separate `links` list or HTML is needed; `sources` remains private editing
context and is not displayed. External links open in a new tab.

Run `python3 build.py` after editing to refresh `index.html`, then preview with
`python3 preview.py`. News links are included in the generated HTML and work
without JavaScript. The normal build does not regenerate the CV.
