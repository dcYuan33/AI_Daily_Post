from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    root: Path
    timezone: ZoneInfo
    ai_api_key: str
    ai_base_url: str
    ai_model: str
    telegram_bot_token: str
    telegram_chat_id: str
    gmail_username: str
    gmail_app_password: str
    gmail_to: str
    sources_config: Path
    prompt_file: Path

    @property
    def smtp_server(self) -> str:
        return os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")

    @property
    def smtp_port(self) -> int:
        return int(os.getenv("GMAIL_SMTP_PORT", "465"))


def _path(value: str, default: str) -> Path:
    return (ROOT / (value or default)).resolve()


def load_settings() -> Settings:
    timezone_name = os.getenv("REPORT_TIMEZONE", "Asia/Shanghai")
    return Settings(
        root=ROOT,
        timezone=ZoneInfo(timezone_name),
        ai_api_key=os.getenv("AI_API_KEY", ""),
        ai_base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        ai_model=os.getenv("AI_MODEL", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        gmail_username=os.getenv("GMAIL_USERNAME", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        gmail_to=os.getenv("GMAIL_TO", ""),
        sources_config=_path(os.getenv("SOURCES_CONFIG", "config/sources.yaml"), "config/sources.yaml"),
        prompt_file=_path(os.getenv("PROMPT_FILE", "prompts/ai-daily.md"), "prompts/ai-daily.md"),
    )
