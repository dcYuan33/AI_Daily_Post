from __future__ import annotations

import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

from .models import Candidate

USER_AGENT = "ai-daily/0.1 (+https://github.com/)"
TIMEOUT = 10


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


def _page_date(soup: BeautifulSoup) -> datetime | None:
    for selector in (
        "meta[property='article:published_time']",
        "meta[property='og:published_time']",
        "meta[name='date']",
        "meta[name='pubdate']",
        "time[datetime]",
    ):
        node = soup.select_one(selector)
        if node:
            value = node.get("content") or node.get("datetime") or node.get_text(" ", strip=True)
            parsed = _parse_datetime(value)
            if parsed:
                return parsed
    return None


def fetch_page(url: str) -> tuple[str, str, datetime | None]:
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return response.url, _article_text(soup), _page_date(soup)
    except requests.RequestException:
        return url, "", None


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


def enrich_candidates(candidates: list[Candidate], max_articles: int = 60) -> list[Candidate]:
    # Landing pages can expose many links. Bound and parallelize article requests so a
    # single slow source cannot consume the whole GitHub Actions job.
    selected = candidates[:max_articles]
    enriched: list[Candidate] = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_page, candidate.url): candidate for candidate in selected}
        for future in as_completed(futures):
            candidate = futures[future]
            try:
                final_url, content, published_at = future.result()
            except Exception:
                final_url, content, published_at = candidate.url, "", None
            candidate.url = final_url
            candidate.content = content
            candidate.published_at = candidate.published_at or published_at
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
