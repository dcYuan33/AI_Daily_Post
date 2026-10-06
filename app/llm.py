from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime

from .models import Candidate, DailyReport, ReportItem


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("LLM response did not contain a JSON object")
    return json.loads(text[start : end + 1])


def generate_report(settings, target_date: date, candidates: list[Candidate]) -> DailyReport:
    if not settings.ai_api_key or not settings.ai_model:
        raise RuntimeError("AI_API_KEY and AI_MODEL are required")
    prompt = settings.prompt_file.read_text(encoding="utf-8")
    payload = {
        "target_date": target_date.isoformat(),
        "candidates": [candidate.as_prompt_dict() for candidate in candidates],
    }
    body = {
        "model": settings.ai_model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    }
    request = urllib.request.Request(
        f"{settings.ai_base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))
    content = result["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    items = []
    for raw in parsed.get("items", []):
        sources = [
            {
                "name": str(source.get("name", "来源")),
                "tier": str(source.get("tier", "C")),
                "url": str(source.get("url", "")),
            }
            for source in raw.get("sources", [])
            if source.get("url")
        ]
        if not raw.get("title") or not raw.get("summary") or not sources:
            continue
        items.append(
            ReportItem(
                title=str(raw["title"]),
                time=str(raw.get("time") or target_date.isoformat()),
                category=str(raw.get("category") or "其他"),
                summary=str(raw["summary"]),
                comment=str(raw.get("comment") or ""),
                sources=sources,
            )
        )
    return DailyReport(
        title=str(parsed.get("title") or f"AI 日报｜{target_date.isoformat()}"),
        report_date=target_date.isoformat(),
        generated_at=datetime.now(settings.timezone).isoformat(),
        items=items,
    )
