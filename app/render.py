from __future__ import annotations

import html
from pathlib import Path

try:
    import markdown
except ImportError:  # Keeps date/config unit tests runnable before dependencies are installed.
    markdown = None

from .models import DailyReport


def render_markdown(report: DailyReport) -> str:
    lines = [
        f"# {report.title}",
        "",
        f"- 生成时间：{report.generated_at}",
        f"- 收集日期：{report.report_date}（Asia/Shanghai）",
        "",
        "## 重点动态",
        "",
    ]
    if not report.items:
        lines.append("这一天内暂未发现足够可靠的重要 AI 新进展。")
    for index, item in enumerate(report.items, 1):
        lines.extend([
            f"### {index}. {item.title}",
            f"- 时间：{item.time}",
            f"- 分类：{item.category}",
            f"- 新闻：{item.summary}",
        ])
        if item.comment:
            lines.append(f"- 简评：{item.comment}")
        source_text = "; ".join(
            f"[{source['name']}（{source['tier']}）]({source['url']})" for source in item.sources
        )
        lines.extend([f"- 来源：{source_text}", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_html(report: DailyReport) -> str:
    md = render_markdown(report)
    if markdown is not None:
        body = markdown.markdown(md, extensions=["extra", "sane_lists"])
    else:
        body = "<pre>" + html.escape(md) + "</pre>"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{html.escape(report.title)}</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.7;max-width:860px;margin:32px auto;padding:0 20px;color:#222}}h1{{border-bottom:1px solid #ddd;padding-bottom:12px}}h2{{margin-top:32px}}h3{{margin-top:26px}}a{{color:#1769aa}}li{{margin:8px 0}}</style>
</head><body>{body}</body></html>"""


def save_report(report: DailyReport, root: Path) -> tuple[Path, Path]:
    folder = root / "reports" / report.report_date[:4] / report.report_date[5:7]
    folder.mkdir(parents=True, exist_ok=True)
    stem = folder / f"ai-daily-{report.report_date}"
    md_path, html_path = stem.with_suffix(".md"), stem.with_suffix(".html")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    return md_path, html_path
