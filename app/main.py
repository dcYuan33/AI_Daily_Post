from __future__ import annotations

import argparse
import logging
import os
from datetime import date, datetime, timedelta

from .collect import collect_candidates
from .config import load_settings
from .llm import generate_report
from .notify import fetch_juya_latest, juya_telegram_summary, report_telegram_summary, send_gmail, send_telegram
from .render import save_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def resolve_report_date(settings, explicit: str | None) -> date:
    value = explicit or os.getenv("REPORT_DATE", "").strip()
    if value:
        return date.fromisoformat(value)
    return (datetime.now(settings.timezone) - timedelta(days=1)).date()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-date", help="YYYY-MM-DD; defaults to previous day in REPORT_TIMEZONE")
    args = parser.parse_args()
    settings = load_settings()
    target_date = resolve_report_date(settings, args.report_date)
    logger.info("Generating AI daily report for %s", target_date)

    candidates = collect_candidates(settings.sources_config, target_date)
    logger.info("Collected %d candidates", len(candidates))
    report = generate_report(settings, target_date, candidates)
    markdown_path, html_path = save_report(report, settings.root)
    logger.info("Saved %s and %s", markdown_path, html_path)

    # Each notification is isolated so a temporary failure in one channel does not suppress the others.
    try:
        send_telegram(settings, report_telegram_summary(report))
        logger.info("Sent own report summary to Telegram")
    except Exception:
        logger.exception("Failed to send own report to Telegram")

    juya_url = None
    try:
        issue = fetch_juya_latest()
        if issue:
            juya_url = issue["url"]
            send_telegram(settings, juya_telegram_summary(issue))
            logger.info("Sent Juya issue to Telegram")
        else:
            logger.warning("No Juya RSS issue found")
    except Exception:
        logger.exception("Failed to fetch/send Juya issue")

    try:
        send_gmail(settings, report, html_path, markdown_path, juya_url)
        logger.info("Sent full report to Gmail")
    except Exception:
        logger.exception("Failed to send full report to Gmail")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
