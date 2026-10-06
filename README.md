# AI Daily Briefing

无服务器的 AI 日报：由 GitHub Actions 每天运行，使用 `ai-weekly-briefing` 的 A/B/C 信源规则，Telegram 发送摘要，Gmail 发送完整 HTML 日报，同时把橘鸦 AI 日报单独推送到 Telegram。

## 功能

- 前一天自然日的 AI 新闻采集和中文日报生成；
- A/B/C 信源配置集中在 `config/sources.yaml`；
- RSS 优先，网页栏目作为候选，文章原文作为核验输入；
- 生成 Markdown 和 HTML；
- Telegram：自己的日报摘要 + 橘鸦最新日报摘要/链接；
- Gmail：自己的完整 HTML 日报和 Markdown 附件；
- GitHub Actions 手动运行时可以指定 `report_date`；
- 使用 `pyproject.toml` 和 uv 管理 GitHub Actions 与本地依赖。

## 首次配置

1. 建议将仓库设为 Private。
2. 在 GitHub Repository Settings → Secrets and variables → Actions 中添加：

```text
AI_API_KEY
AI_BASE_URL       # 例如 https://api.openai.com/v1；兼容 OpenAI API 的服务也可以
AI_MODEL
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
GMAIL_USERNAME
GMAIL_APP_PASSWORD
GMAIL_TO
```

Gmail 推荐使用开启两步验证后的 App Password，不要使用主密码。

3. 启用 `.github/workflows/daily.yml`。
4. 先使用 `workflow_dispatch` 手动运行，填写 `report_date`，确认 Telegram 和 Gmail 后再等待定时任务。

## 本地运行

本项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 版本、虚拟环境和依赖，不直接使用 `pip install`。

```bash
uv sync
cp .env.example .env
set -a; source .env; set +a
uv run python -m app --report-date 2026-10-05
```

本地测试只验证纯函数，不需要网络或密钥：

```bash
uv run python -m unittest discover -s tests -v
```

## 运行时间和日期窗口

定时任务使用 `01:17 UTC`，即 `09:17 Asia/Shanghai`。默认报告日期是运行时区的前一天，例如 2026-10-07 早上运行时生成 `2026-10-06` 日报。手动运行可以用 `report_date` 覆盖。

## TrendRadar 的参考边界

本项目只参考 TrendRadar 的 RSS 配置、Telegram 通知分批、HTML 报告、环境变量和 GitHub Actions 思路，不依赖 TrendRadar 的热点榜单排序或主报告 Prompt。

## 目录

```text
app/                    Python 代码
config/sources.yaml     A/B/C 信源
prompts/ai-daily.md     日报生成约束
reports/                生成的 Markdown/HTML
.github/workflows/       GitHub Actions
```
