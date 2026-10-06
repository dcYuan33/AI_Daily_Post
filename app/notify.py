from __future__ import annotations

import html
import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

import feedparser
import requests

from .models import DailyReport
from .render import render_markdown

TELEGRAM_LIMIT = 3800
JUYA_RSS_URL = "https://daily.juya.uk/rss.xml"


def _chunks(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    chunks = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < 1000:
            split_at = remaining.rfind(" ", 0, limit)
        if split_at < 1000:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return chunks


def send_telegram(settings, text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
    endpoint = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    for chunk in _chunks(text):
        response = requests.post(
            endpoint,
            data={"chat_id": settings.telegram_chat_id, "text": chunk, "disable_web_page_preview": "true"},
            timeout=30,
        )
        response.raise_for_status()


def report_telegram_summary(report: DailyReport) -> str:
    lines = [f"🤖 {report.title}", ""]
    if not report.items:
        lines.append("今日暂未发现足够可靠的重要 AI 新进展。")
    for index, item in enumerate(report.items[:8], 1):
        lines.append(f"{index}. {item.title}")
        lines.append(item.summary)
        if item.sources:
            lines.append(item.sources[0]["url"])
        lines.append("")
    lines.append("完整日报已发送至 Gmail。")
    return "\n".join(lines).strip()


def fetch_juya_latest() -> dict | None:
    parsed = feedparser.parse(JUYA_RSS_URL)
    if not parsed.entries:
        return None
    entry = parsed.entries[0]
    return {
        "title": entry.get("title", "橘鸦 AI 日报"),
        "summary": entry.get("summary", ""),
        "url": entry.get("link", "https://daily.juya.uk/"),
    }


def juya_telegram_summary(issue: dict) -> str:
    summary = issue.get("summary", "")
    # RSS summaries are HTML fragments; keep a compact readable excerpt.
    from bs4 import BeautifulSoup
    plain = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)
    if len(plain) > 1200:
        plain = plain[:1200].rstrip() + "…"
    return f"🟣 橘鸦 AI 日报\n\n{issue['title']}\n\n{plain}\n\n阅读全文：{issue['url']}"


def send_gmail(settings, report: DailyReport, html_path: Path, markdown_path: Path, juya_url: str | None = None) -> None:
    required = [settings.gmail_username, settings.gmail_app_password, settings.gmail_to]
    if not all(required):
        raise RuntimeError("GMAIL_USERNAME, GMAIL_APP_PASSWORD and GMAIL_TO are required")
    message = EmailMessage()
    message["Subject"] = f"[AI日报] {report.report_date}"
    message["From"] = settings.gmail_username
    message["To"] = settings.gmail_to
    html_body = html_path.read_text(encoding="utf-8")
    if juya_url:
        html_body = html_body.replace("</body>", f'<hr><p>橘鸦 AI 日报：<a href="{html.escape(juya_url)}">阅读全文</a></p></body>')
    message.set_content(render_markdown(report))
    message.add_alternative(html_body, subtype="html")
    message.add_attachment(
        markdown_path.read_bytes(),
        maintype="text",
        subtype="markdown",
        filename=markdown_path.name,
    )
    with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port, timeout=30) as smtp:
        smtp.login(settings.gmail_username, settings.gmail_app_password)
        smtp.send_message(message)
