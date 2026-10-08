# AI Daily Post

无服务器的 AI 日报：由 GitHub Actions 每天运行，使用 `ai-weekly-briefing` 的 A/B/C 信源规则，Telegram 发送摘要，并通过 GitHub Pages 展示完整日报。

最终交付方式是：**Telegram 只接收摘要，GitHub Pages 展示完整内容**。

## 功能

- 前一天自然日的 AI 新闻采集和中文日报生成；
- A/B/C 信源配置集中在 `config/sources.yaml`；
- RSS 优先，网页栏目作为候选，文章原文作为核验输入；
- 生成 Markdown 和 HTML；
- Telegram：发送自己的日报摘要和 GitHub Pages 完整日报链接；
- GitHub Pages：提供首页、日报归档、日期详情页、搜索和深色模式；
- Python 使用 `uv` 管理；
- GitHub Actions 手动运行时可以指定 `report_date`。

## 首次配置

1. 建议将仓库设为 Private 或 Public；GitHub Pages 对两种仓库都可以使用，但账号方案可能影响可用性。
2. 在 GitHub Repository Settings → Secrets and variables → Actions 中添加：

```text
AI_API_KEY
AI_BASE_URL       # 例如 https://api.openai.com/v1
AI_MODEL
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

3. 在 Repository Settings → Pages 中将部署方式设置为 **GitHub Actions**（第一次运行 Workflow 后也可以在这里确认）。
4. 先使用 `workflow_dispatch` 手动运行，填写 `report_date`，确认 Telegram 和 Pages 后再等待定时任务。

## 本地运行

本项目使用 uv 管理 Python 版本、虚拟环境和依赖，不直接使用 `pip install`。

```bash
uv lock    # 首次或依赖变更时执行；网络可用后提交生成的 uv.lock
uv sync
cp .env.example .env
set -a; source .env; set +a
uv run python -m app --report-date 2026-10-06
```

本地测试只验证纯函数，不需要网络或密钥：

```bash
uv run python -m unittest discover -s tests -v
```

本地生成站点后可以用静态服务器预览：

```bash
uv run python -m http.server 8000 --directory site
```

然后打开 `http://localhost:8000`。

## 运行时间和日期窗口

定时任务使用 `01:17 UTC`，即 `09:17 Asia/Shanghai`。默认报告日期是运行时区的前一天，例如 2026-10-07 早上运行时生成 `2026-10-06` 日报。手动运行可以用 `report_date` 覆盖。

## GitHub Pages 页面结构

```text
site/
├── index.html                 首页和最新日报
├── archive.html               全部日报归档
├── assets/style.css           页面样式
└── issues/YYYY-MM-DD/
    ├── index.html             单期日报详情页
    └── data.json              用于重新构建归档和导航的数据
```

GitHub Pages 使用 Actions 构建并部署 `site/`。每次日报生成后，Workflow 会：

1. 生成 Markdown、HTML 和 Pages 静态文件；
2. 将 `reports/` 和 `site/` 提交回仓库；
3. 上传 `site/` 为 Pages artifact；
4. 部署到 GitHub Pages；
5. Telegram 消息附带当天详情页链接。
