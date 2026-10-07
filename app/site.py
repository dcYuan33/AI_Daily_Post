from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path

from .models import DailyReport, ReportItem


def report_to_dict(report: DailyReport) -> dict:
    return asdict(report)


def report_from_dict(data: dict) -> DailyReport:
    return DailyReport(
        title=data["title"],
        report_date=data["report_date"],
        generated_at=data.get("generated_at", ""),
        items=[ReportItem(**item) for item in data.get("items", [])],
    )


def _css() -> str:
    return r'''
:root{--bg:#f6f7f9;--surface:#fff;--soft:#f0f2f5;--text:#17191c;--muted:#707781;--line:#e4e7eb;--accent:#1c7df2;--accent2:#0d5dcc;--shadow:0 12px 36px rgba(21,32,52,.07)}
[data-theme=dark]{--bg:#111315;--surface:#1a1d20;--soft:#22262a;--text:#f2f4f7;--muted:#a5adb7;--line:#333940;--accent:#72aefc;--accent2:#9bc5ff;--shadow:0 14px 38px rgba(0,0,0,.2)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.75}a{color:inherit;text-decoration:none}a:hover{color:var(--accent2)}.shell{width:min(1120px,calc(100% - 36px));margin:0 auto}.topbar{height:68px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{display:flex;gap:12px;align-items:center;font-weight:800;letter-spacing:-.02em}.brand-mark{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,#2b8cff,#8057e8);box-shadow:0 8px 20px rgba(42,128,244,.25)}.brand small{display:block;color:var(--muted);font-size:11px;font-weight:500;letter-spacing:.03em}.nav{display:flex;align-items:center;gap:18px;color:var(--muted);font-size:14px}.nav a:hover{color:var(--text)}.theme{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:999px;padding:6px 11px;cursor:pointer}.hero{padding:58px 0 32px;display:grid;grid-template-columns:1fr auto;gap:28px;align-items:end}.eyebrow{color:var(--accent);font-weight:700;font-size:13px;letter-spacing:.08em;text-transform:uppercase}h1{margin:10px 0 8px;font-size:clamp(32px,5vw,54px);line-height:1.13;letter-spacing:-.045em}.lead{max-width:620px;margin:0;color:var(--muted);font-size:16px}.date-block{text-align:right;color:var(--muted);font-size:13px}.date-block strong{display:block;color:var(--text);font-size:24px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 0 22px}.toolbar h2{margin:0;font-size:21px;letter-spacing:-.02em}.search{width:min(280px,48vw);border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:10px;padding:10px 13px;outline:none}.search:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(28,125,242,.12)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;padding-bottom:52px}.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px;box-shadow:var(--shadow);transition:transform .18s ease,border-color .18s ease}.card:hover{transform:translateY(-2px);border-color:rgba(28,125,242,.45)}.card-meta{display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:12px}.card h3{margin:12px 0 8px;font-size:20px;line-height:1.45;letter-spacing:-.02em}.card p{margin:0;color:var(--muted);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.tag{display:inline-flex;align-items:center;border-radius:999px;padding:3px 9px;background:var(--soft);color:var(--accent2);font-size:12px;white-space:nowrap}.empty{grid-column:1/-1;padding:48px 24px;background:var(--surface);border:1px dashed var(--line);border-radius:16px;color:var(--muted);text-align:center}.issue-head{padding:56px 0 34px;max-width:850px}.issue-head h1{font-size:clamp(30px,5vw,50px)}.issue-meta{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:13px}.issue-layout{display:grid;grid-template-columns:minmax(0,1fr) 240px;gap:28px;align-items:start;padding-bottom:60px}.article{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:clamp(22px,4vw,42px);box-shadow:var(--shadow)}.article-item{padding:0 0 32px;margin:0 0 32px;border-bottom:1px solid var(--line)}.article-item:last-child{border-bottom:0;padding-bottom:0;margin-bottom:0}.article-item h2{margin:10px 0 12px;font-size:clamp(21px,3vw,28px);line-height:1.4;letter-spacing:-.025em}.article-item .summary{font-size:16px}.comment{margin-top:16px;padding:13px 16px;background:var(--soft);border-left:3px solid var(--accent);color:var(--muted);border-radius:0 9px 9px 0}.sources{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.source{color:var(--accent2);font-size:13px;border:1px solid var(--line);padding:4px 9px;border-radius:7px}.side{position:sticky;top:20px;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px}.side h3{margin:0 0 12px;font-size:14px}.side a{display:block;padding:8px 0;color:var(--muted);font-size:13px;border-bottom:1px solid var(--line)}.side a:last-child{border-bottom:0}.pager{display:flex;justify-content:space-between;gap:10px;margin-top:22px}.button{display:inline-flex;align-items:center;gap:6px;padding:9px 13px;background:var(--surface);border:1px solid var(--line);border-radius:9px;color:var(--muted);font-size:13px}footer{border-top:1px solid var(--line);color:var(--muted);font-size:12px;padding:24px 0 40px}@media(max-width:760px){.shell{width:min(100% - 24px,1120px)}.topbar{height:60px}.brand small{display:none}.nav{gap:10px}.hero{display:block;padding-top:38px}.date-block{text-align:left;margin-top:20px}.grid{grid-template-columns:1fr}.toolbar{align-items:flex-start;flex-direction:column}.search{width:100%}.issue-layout{grid-template-columns:1fr}.side{position:static;order:-1}.article{padding:22px}.nav a:nth-child(1){display:none}}
'''


def _scripts() -> str:
    return '''<script>(()=>{const saved=localStorage.getItem('ai-daily-theme');if(saved)document.documentElement.dataset.theme=saved;const b=document.querySelector('[data-theme-toggle]');if(b)b.onclick=()=>{const n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;localStorage.setItem('ai-daily-theme',n)};const s=document.querySelector('[data-search]');if(s)s.oninput=()=>{const k=s.value.trim().toLowerCase();document.querySelectorAll('[data-search-card]').forEach(c=>c.hidden=!!k&&!c.textContent.toLowerCase().includes(k))}})()</script>'''


def _page(title: str, content: str, css_path: str = "assets/style.css", root_path: str = "./") -> str:
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f6f7f9"><title>{html.escape(title)}</title><link rel="stylesheet" href="{css_path}"></head><body><header class="shell topbar"><a class="brand" href="{root_path}index.html"><span class="brand-mark">✦</span><span>AI Daily<small>每日 AI 情报</small></span></a><nav class="nav"><a href="{root_path}index.html">首页</a><a href="{root_path}archive.html">归档</a><button class="theme" data-theme-toggle aria-label="切换主题">◐</button></nav></header>{content}<footer class="shell">AI Daily · 基于可核验来源的每日 AI 新闻简报</footer>{_scripts()}</body></html>'''


def _card(report: DailyReport, link: str) -> str:
    first = report.items[0] if report.items else None
    excerpt = first.summary if first else "这一天内暂未发现足够可靠的重要 AI 新进展。"
    category = first.category if first else "日报"
    return f'<a class="card" data-search-card href="{link}"><div class="card-meta"><span>{html.escape(report.report_date)}</span><span class="tag">{html.escape(category)}</span></div><h3>{html.escape(report.title)}</h3><p>{html.escape(excerpt)}</p><div class="card-meta" style="margin-top:18px"><span>{len(report.items)} 条重点动态</span><span>阅读 →</span></div></a>'


def _article_item(index: int, item: ReportItem) -> str:
    sources = "".join(f'<a class="source" href="{html.escape(s["url"], quote=True)}" target="_blank" rel="noreferrer">{html.escape(s["name"])} · {html.escape(s["tier"])}</a>' for s in item.sources)
    comment = f'<div class="comment"><strong>简评：</strong>{html.escape(item.comment)}</div>' if item.comment else ""
    return f'<article class="article-item" id="item-{index}"><div class="card-meta"><span>#{index:02d} · {html.escape(item.time)}</span><span class="tag">{html.escape(item.category)}</span></div><h2>{html.escape(item.title)}</h2><div class="summary">{html.escape(item.summary)}</div>{comment}<div class="sources">{sources}</div></article>'


def _load_reports(site_root: Path) -> list[DailyReport]:
    result = []
    for path in sorted((site_root / "issues").glob("*/data.json"), reverse=True):
        try:
            result.append(report_from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            pass
    return sorted(result, key=lambda r: r.report_date, reverse=True)


def _home(site_root: Path, reports: list[DailyReport]) -> None:
    cards = "".join(_card(r, f"./issues/{r.report_date}/index.html") for r in reports)
    latest = reports[0].report_date if reports else "尚未生成"
    content = f'''<main class="shell"><section class="hero"><div><div class="eyebrow">Daily intelligence</div><h1>每天几分钟，<br>掌握 AI 世界。</h1><p class="lead">从模型研究、产品工具到政策与开源生态，整理值得阅读的 AI 动态，并保留每条新闻的原始来源。</p></div><div class="date-block">最新一期<strong>{html.escape(latest)}</strong>Asia/Shanghai</div></section><div class="toolbar"><h2>最新日报</h2><input class="search" data-search placeholder="搜索日报标题或内容…" aria-label="搜索日报"></div><section class="grid">{cards or '<div class="empty">日报还没有生成，下一次 GitHub Actions 运行后会出现在这里。</div>'}</section></main>'''
    (site_root / "index.html").write_text(_page("AI Daily · 每日 AI 情报", content), encoding="utf-8")


def _archive(site_root: Path, reports: list[DailyReport]) -> None:
    cards = "".join(_card(r, f"./issues/{r.report_date}/index.html") for r in reports)
    content = f'''<main class="shell"><section class="hero"><div><div class="eyebrow">Archive</div><h1>日报归档</h1><p class="lead">按日期浏览历史 AI 日报。</p></div><div class="date-block"><strong>{len(reports)}</strong>期日报</div></section><div class="toolbar"><h2>全部内容</h2><input class="search" data-search placeholder="搜索标题或摘要…" aria-label="搜索归档"></div><section class="grid">{cards or '<div class="empty">暂无归档。</div>'}</section></main>'''
    (site_root / "archive.html").write_text(_page("日报归档 · AI Daily", content), encoding="utf-8")


def _issue(site_root: Path, reports: list[DailyReport], report: DailyReport) -> None:
    index = next(i for i, r in enumerate(reports) if r.report_date == report.report_date)
    older = reports[index + 1] if index + 1 < len(reports) else None
    newer = reports[index - 1] if index > 0 else None
    articles = "".join(_article_item(i, item) for i, item in enumerate(report.items, 1)) or '<div class="empty">这一天内暂未发现足够可靠的重要 AI 新进展。</div>'
    toc = "".join(f'<a href="#item-{i}">{html.escape(item.title)}</a>' for i, item in enumerate(report.items, 1))
    prev_link = f'<a class="button" href="../../issues/{older.report_date}/index.html">← {older.report_date}</a>' if older else '<span></span>'
    next_link = f'<a class="button" href="../../issues/{newer.report_date}/index.html">{newer.report_date} →</a>' if newer else '<span></span>'
    content = f'''<main class="shell"><section class="issue-head"><div class="eyebrow">AI Daily · Issue</div><h1>{html.escape(report.title)}</h1><div class="issue-meta"><span>收集日期：{html.escape(report.report_date)}</span><span>生成时间：{html.escape(report.generated_at)}</span><span>{len(report.items)} 条重点动态</span></div></section><section class="issue-layout"><article class="article">{articles}<div class="pager">{prev_link}{next_link}</div></article><aside class="side"><h3>本期目录</h3>{toc or '<span style="color:var(--muted);font-size:13px">暂无条目</span>'}<a href="../../archive.html">查看全部归档 →</a></aside></section></main>'''
    issue_dir = site_root / "issues" / report.report_date
    issue_dir.mkdir(parents=True, exist_ok=True)
    (issue_dir / "index.html").write_text(_page(report.title, content, "../../assets/style.css", "../../"), encoding="utf-8")


def build_site(report: DailyReport, root: Path) -> Path:
    site_root = root / "site"
    (site_root / "assets").mkdir(parents=True, exist_ok=True)
    (site_root / "assets" / "style.css").write_text(_css(), encoding="utf-8")
    issue_dir = site_root / "issues" / report.report_date
    issue_dir.mkdir(parents=True, exist_ok=True)
    (issue_dir / "data.json").write_text(json.dumps(report_to_dict(report), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    reports = _load_reports(site_root)
    _home(site_root, reports)
    _archive(site_root, reports)
    for current in reports:
        _issue(site_root, reports, current)
    (site_root / "404.html").write_text(_page("页面不存在 · AI Daily", '<main class="shell"><section class="hero"><div><div class="eyebrow">404</div><h1>页面不存在</h1><p class="lead">返回首页继续浏览 AI 日报。</p><a class="button" href="./index.html">回到首页 →</a></div></section></main>'), encoding="utf-8")
    return site_root
