from __future__ import annotations

import argparse
import logging
import os
from datetime import date, datetime, timedelta

from .config import load_settings

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
    from .collect import collect_candidates
    from .llm import generate_report
    from .notify import report_telegram_summary, send_telegram
    from .render import save_report
    from .site import build_site

    settings = load_settings()
    target_date = resolve_report_date(settings, args.report_date)
    logger.info("Generating AI daily report for %s", target_date)

    candidates = collect_candidates(settings.sources_config, target_date)
    logger.info("Collected %d candidates", len(candidates))
    report = generate_report(settings, target_date, candidates)
    logger.info("Generated %d report items for %s", len(report.items), target_date)
    markdown_path, html_path = save_report(report, settings.root)
    build_site(report, settings.root)
    logger.info("Saved %s and %s", markdown_path, html_path)

    site_url = os.getenv("SITE_URL", "").rstrip("/")
    issue_url = f"{site_url}/issues/{report.report_date}/" if site_url else ""
    send_telegram(settings, report_telegram_summary(report, issue_url))
    logger.info("Sent report summary to Telegram")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
