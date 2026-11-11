"""Dated news from one list, with static HTML and a small client-side age refresh."""
from __future__ import annotations

from datetime import date, datetime
from html import escape
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

MONTHS = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
INLINE_LINK = re.compile(r"\[([^\[\]\n]+)\]\(((?:[^\s()<>]|\([^\s()<>]*\))+)\)")


def news_text(text):
    """Support only [linked words](URL); escape all other text, including HTML."""
    parts, end = [], 0
    for match in INLINE_LINK.finditer(text):
        label, url = match.groups()
        try:
            parsed = urlsplit(url)
            external = parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc)
            local = not parsed.scheme and not parsed.netloc and not url.startswith("//")
            valid = (external or local) and "\\" not in url and not any(ord(c) < 32 or ord(c) == 127 for c in url)
        except ValueError:
            valid = False
        parts.append(escape(text[end:match.start()]))
        if valid:
            attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
            parts.append(f'<a href="{escape(url, quote=True)}"{attrs}>{escape(label)}</a>')
        else:
            parts.append(escape(match.group()))
        end = match.end()
    parts.append(escape(text[end:]))
    return "".join(parts)


def news_date(value):
    """Return year, optional month, label, and an HTML datetime value."""
    if not isinstance(value, str):
        raise ValueError("News date must be YYYY-MM (or YYYY-MM-DD)")
    if re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value):
        parsed = date.fromisoformat(value if len(value) == 10 else value + "-01")
        return parsed.year, parsed.month, f"{MONTHS[parsed.month]} {parsed.year}", value
    if re.fullmatch(r"\d{4}(?:–\d{4})?", value):
        years = [int(part) for part in value.split("–")]
        if not all(1 <= year <= 9999 for year in years) or years != sorted(years):
            raise ValueError(f"Invalid legacy news date: {value}")
        return years[-1], None, value, value if len(years) == 1 else None
    raise ValueError(f"Invalid news date: {value}; use YYYY-MM")


def news_records(config):
    if not isinstance(config, dict) or not isinstance(config.get("items"), list):
        raise ValueError("news.json needs settings and a single items list")
    settings = config.get("settings", {})
    if not isinstance(settings, dict):
        raise ValueError("News settings must be an object")
    limit = settings.get("max_visible", 3)
    age = settings.get("max_age_months", 18)
    if type(limit) is not int or limit < 1:
        raise ValueError("News max_visible must be a positive integer")
    if age is not None and (type(age) is not int or age < 1):
        raise ValueError("News max_age_months must be a positive integer or null")
    records, ids = [], set()
    for index, item in enumerate(config["items"]):
        if not isinstance(item, dict):
            raise ValueError("Each news item must be an object")
        identifier = item.get("id", "")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) or identifier in ids:
            raise ValueError(f"News IDs must be unique slugs: {identifier!r}")
        ids.add(identifier)
        if type(item.get("draft", False)) is not bool:
            raise ValueError(f"News draft flag must be true/false: {identifier}")
        if item.get("draft"):
            continue
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError(f"News entry needs text: {identifier}")
        year, month, label, machine_date = news_date(item.get("date"))
        if month is None and not item.get("date_todo"):
            raise ValueError(f"News entry needs a month or an explicit date_todo: {identifier}")
        records.append({**item, "year": year, "month": month, "label": label, "datetime": machine_date, "index": index})
    records.sort(key=lambda item: (-item["year"], -(item["month"] or 0), item["index"]))
    return records, {"max_visible": limit, "max_age_months": age}


def news_groups(config, today=None):
    records, settings = news_records(config)
    today = today or datetime.now(ZoneInfo("America/New_York")).date()
    current = today.year * 12 + today.month
    recent, archive = [], []
    for item in records:
        age = current - (item["year"] * 12 + (item["month"] or 0))
        eligible = item["month"] is not None and (settings["max_age_months"] is None or age < settings["max_age_months"])
        (recent if eligible and len(recent) < settings["max_visible"] else archive).append(item)
    return recent, archive, settings


def render_news(config, today=None):
    recent, archive, settings = news_groups(config, today)
    if not recent and not archive:
        return ""

    def row(item):
        machine = f' datetime="{escape(item["datetime"], quote=True)}"' if item["datetime"] else ""
        tag = "time" if item["datetime"] else "span"
        month = item["month"] or ""
        return f'<li id="news-{item["id"]}" data-news-year="{item["year"]}" data-news-month="{month}" data-news-order="{item["index"]}"><{tag} class="news-date"{machine}>{escape(item["label"])}</{tag}><p>{news_text(item["text"])}</p></li>'

    age = settings["max_age_months"] if settings["max_age_months"] is not None else ""
    return f'''<aside class="lately" aria-labelledby="lately-title" data-news-limit="{settings['max_visible']}" data-news-max-age-months="{age}">
  <h3 id="lately-title">Lately</h3>
  <ul class="news-recent"{' hidden' if not recent else ''}>{''.join(row(item) for item in recent)}</ul>
  <details class="news-history"{' hidden' if not archive else ''}>
    <summary id="earlier-news-label">Earlier News</summary>
    <div class="news-archive" role="region" aria-labelledby="earlier-news-label" tabindex="0"><ul>{''.join(row(item) for item in archive)}</ul></div>
  </details>
</aside>'''
