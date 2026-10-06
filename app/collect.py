from __future__ import annotations

import html
import re
from datetime import date, datetime, time, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

from .models import Candidate

USER_AGENT = "ai-daily/0.1 (+https://github.com/)"
TIMEOUT = 20


def load_sources(path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle).get("sources", [])


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, time):
        return datetime.combine(date.today(), value)
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError, OverflowError):
        return None


def _clean_text(value: str) -> str:
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()


def _article_text(soup: BeautifulSoup) -> str:
    for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        node.decompose()
    article = soup.find("article") or soup.find("main") or soup.body
    if not article:
        return ""
    paragraphs = [_clean_text(p.get_text(" ", strip=True)) for p in article.find_all(["p", "li"])]
    return "\n".join(p for p in paragraphs if len(p) >= 30)[:12000]


def fetch_page(url: str) -> tuple[str, str]:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return response.url, _article_text(soup)
    except requests.RequestException:
        return url, ""


def _rss_candidates(source: dict, target_date: date, limit: int = 40) -> list[Candidate]:
    parsed = feedparser.parse(source["rss"])
    result: list[Candidate] = []
    for entry in parsed.entries[:limit]:
        published = _parse_datetime(entry.get("published") or entry.get("updated"))
        if published and published.date() != target_date:
            continue
        url = entry.get("link") or source["url"]
        result.append(
            Candidate(
                source_name=source["name"],
                tier=source["tier"],
                source_url=source["url"],
                title=_clean_text(entry.get("title", "")),
                url=url,
                published_at=published,
                summary=_clean_text(entry.get("summary", "") or entry.get("description", "")),
                topics=source.get("topics", []),
            )
        )
    return result


def _webpage_candidates(source: dict, target_date: date, limit: int = 20) -> list[Candidate]:
    try:
        response = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        title = _clean_text(link.get_text(" ", strip=True))
        url = urljoin(response.url, link["href"])
        if not title or len(title) < 12 or url in seen or url.startswith(("javascript:", "mailto:", "#")):
            continue
        # Section landing pages rarely expose reliable dates. Keep candidates and let article verification/LLM decide.
        seen.add(url)
        candidates.append(
            Candidate(
                source_name=source["name"],
                tier=source["tier"],
                source_url=source["url"],
                title=title,
                url=url,
                summary="",
                topics=source.get("topics", []),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def enrich_candidates(candidates: list[Candidate], max_articles: int = 50) -> list[Candidate]:
    enriched: list[Candidate] = []
    for candidate in candidates[:max_articles]:
        final_url, content = fetch_page(candidate.url)
        candidate.url = final_url
        candidate.content = content
        enriched.append(candidate)
    return enriched


def collect_candidates(sources_path, target_date: date) -> list[Candidate]:
    candidates: list[Candidate] = []
    for source in load_sources(sources_path):
        if source.get("rss"):
            candidates.extend(_rss_candidates(source, target_date))
        else:
            candidates.extend(_webpage_candidates(source, target_date))
    # URL/title de-duplication before expensive article fetches.
    unique: dict[str, Candidate] = {}
    for item in candidates:
        key = re.sub(r"\W+", " ", item.url.lower()).strip() or re.sub(r"\W+", " ", item.title.lower()).strip()
        unique.setdefault(key, item)
    return enrich_candidates(list(unique.values()))
