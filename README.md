# AI Content Agent — Module 01: Source Collector

A production-oriented first module for an agentic content pipeline:

**Scheduled GitHub Action → Python Collector → Source Extraction → Normalization → Deduplication → Secure Webhook**

This module intentionally does **not** publish to social media. Its only job is to reliably collect new content and send clean, structured article records to your n8n/Make webhook.

## What this module does

- Runs automatically from GitHub Actions.
- Supports RSS/Atom feeds and normal HTML article/list pages.
- Extracts title, URL, description/content, publication date, author and image where available.
- Normalizes whitespace and HTML.
- Generates deterministic SHA-256 IDs/hashes.
- Performs local deduplication within each run.
- Maintains a lightweight state file between GitHub Action runs.
- Sends one structured JSON payload per new article.
- Supports webhook bearer-token authentication.
- Retries temporary HTTP failures with exponential backoff.
- Uses environment variables/secrets; no credentials are stored in source code.
- Includes unit tests for parsing, normalization and deduplication.
- Produces useful logs for debugging.

## Repository structure

```text
ai-content-agent-module-01/
├── .github/
│   └── workflows/
│       ├── daily_collector.yml
│       └── test.yml
├── config/
│   └── sources.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── scraper.py
│   ├── state.py
│   └── utils.py
├── tests/
│   ├── test_deduplication.py
│   └── test_normalization.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 1. Create the repository

Upload the contents of this ZIP to a new GitHub repository.

Recommended repository name:

`ai-content-agent`

Keep the repository **private** while you are developing/testing if your workflow or source configuration is sensitive.

## 2. Configure sources

Edit:

`config/sources.json`

Example:

```json
{
  "sources": [
    {
      "name": "Example RSS",
      "type": "rss",
      "url": "https://example.com/feed.xml",
      "category": "technology",
      "priority": 10,
      "enabled": true,
      "max_items": 10
    },
    {
      "name": "Example Website",
      "type": "website",
      "url": "https://example.com/news",
      "category": "technology",
      "priority": 8,
      "enabled": true,
      "max_items": 10,
      "selectors": {
        "article": "article",
        "title": "h1",
        "content": "article",
        "date": "time",
        "author": "[rel='author']",
        "image": "article img"
      }
    }
  ]
}
```

### Prefer RSS whenever available

RSS/Atom is more stable and easier to maintain than scraping arbitrary HTML.

For a website without RSS, configure CSS selectors for that site's page structure. Website HTML differs from site to site, so selectors may need adjustment.

## 3. Configure your webhook

The collector expects:

- `WEBHOOK_URL`
- `WEBHOOK_SECRET`

For local testing, create `.env` from `.env.example`.

For GitHub Actions, add repository secrets:

**GitHub → Settings → Secrets and variables → Actions → New repository secret**

Add:

```text
WEBHOOK_URL
WEBHOOK_SECRET
```

Do not put these values into `sources.json`, Python files, README files, commits, screenshots or issue comments.

## 4. Webhook security

The collector sends:

```http
Authorization: Bearer YOUR_WEBHOOK_SECRET
Content-Type: application/json
X-Agent-Name: ai-content-agent
X-Agent-Version: 1.0.0
```

Your n8n/Make webhook should validate the bearer token before processing the payload.

For a stronger production deployment, also put the webhook behind HTTPS and validate the expected JSON structure in the receiving workflow.

## 5. Local setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy:

```text
.env.example → .env
```

Fill in your webhook values.

Then run:

```bash
python -m src.main
```

## 6. Test without GitHub Actions

Run:

```bash
python -m pytest -q
```

Then:

```bash
python -m src.main
```

You should see logs similar to:

```text
Starting collector
Loaded 2 enabled sources
Collected 7 candidate items
7 new items after deduplication
Sent 7/7 items successfully
Collector completed
```

If a source fails, the collector logs the error and continues with other sources.

## 7. GitHub Actions

The scheduled workflow is:

`.github/workflows/daily_collector.yml`

The default schedule is **07:00 UTC**, which is **12:30 PM IST**.

Change the cron expression if you want a different time.

For example, 7:00 AM IST is:

```yaml
- cron: "30 1 * * *"
```

GitHub scheduled workflows use UTC unless a timezone is explicitly configured.

You can also run the workflow manually from:

**GitHub → Actions → Daily Content Collector → Run workflow**

The workflow also supports manual execution through `workflow_dispatch`.

## 8. What the webhook receives

Each article is sent as JSON similar to:

```json
{
  "schema_version": "1.0",
  "event": "content.discovered",
  "article_id": "a_sha256_id",
  "source": {
    "name": "Example RSS",
    "type": "rss",
    "url": "https://example.com/feed.xml",
    "category": "technology",
    "priority": 10
  },
  "article": {
    "title": "Example headline",
    "url": "https://example.com/article",
    "description": "Short description",
    "content": "Clean article content",
    "author": "Author Name",
    "published_at": "2026-09-28T06:30:00+00:00",
    "image_url": "https://example.com/image.jpg"
  },
  "metadata": {
    "collected_at": "2026-09-28T07:00:00+00:00",
    "language": "en",
    "content_hash": "sha256...",
    "source_item_id": "..."
  },
  "pipeline": {
    "agent": "ai-content-agent",
    "module": "01-source-collector",
    "version": "1.0.0"
  }
}
```

This is the **data contract** that Module 2 can consume.

## 9. Deduplication design

The collector uses two IDs:

### Article ID

Based on:

```text
normalized source + normalized article URL
```

This identifies the same URL consistently.

### Content hash

Based on normalized:

```text
title + URL + content
```

This helps identify repeated content.

The state file stores recently processed IDs so the same article is not repeatedly sent on every scheduled run.

## 10. Important production note about GitHub Actions state

The collector writes its state to:

```text
data/state.json
```

The scheduled workflow automatically commits an updated state file back to the repository when it changes.

This is intentionally simple for Module 1.

For a larger production system, Module 2/3 should move persistent state to PostgreSQL/Supabase rather than using Git commits as a database.

## 11. How the architecture will evolve

### Module 01 — Source Collector

```text
GitHub Actions
      ↓
Python
      ↓
RSS / Websites
      ↓
Normalize
      ↓
Deduplicate
      ↓
Webhook
```

### Module 02 — Intelligence

```text
Webhook
   ↓
Validate
   ↓
Store
   ↓
AI Research
   ↓
Classification
   ↓
Relevance
   ↓
Novelty
```

### Module 03 — Editorial Agent

```text
Analysis
   ↓
Should we publish?
   ↓
What angle?
   ↓
Which platform?
   ↓
Human approval
```

### Module 04 — Content Creation

```text
Approved story
   ├── LinkedIn
   ├── Instagram
   └── Facebook
```

### Module 05 — Analytics + Memory

```text
Published posts
      ↓
Performance
      ↓
Memory
      ↓
Future editorial decisions
```

## Troubleshooting

### `401 Unauthorized`

Check:

- `WEBHOOK_SECRET`
- n8n/Make expected header
- HTTPS webhook URL
- GitHub repository secret spelling

### `No items found`

Check the RSS URL in a browser or use an RSS validator. If using a website source, inspect the site's HTML and adjust CSS selectors.

### Duplicate posts

Delete/reset:

```text
data/state.json
```

Only do this during testing; it will cause previously seen articles to be treated as new.

### GitHub Action cannot update state

The workflow needs repository write permission. The included workflow sets:

```yaml
permissions:
  contents: write
```

If your organization restricts GitHub Actions permissions, enable the required repository setting or switch to database-backed state later.

## Design principle

**Module 01 should be boring and reliable.**

Do not put AI generation, social posting or complicated agent logic into the scraper. The collector's job is to produce clean, trustworthy, structured input for the intelligence layer.
