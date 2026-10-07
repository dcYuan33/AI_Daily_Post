from __future__ import annotations

import requests

from .models import DailyReport

TELEGRAM_LIMIT = 3800


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


def report_telegram_summary(report: DailyReport, site_url: str = "") -> str:
    lines = [f"🤖 {report.title}", ""]
    if not report.items:
        lines.append("今日暂未发现足够可靠的重要 AI 新进展。")
    for index, item in enumerate(report.items[:8], 1):
        lines.append(f"{index}. {item.title}")
        lines.append(item.summary)
        if item.sources:
            lines.append(item.sources[0]["url"])
        lines.append("")
    if site_url:
        lines.append(f"完整日报：{site_url}")
    return "\n".join(lines).strip()
