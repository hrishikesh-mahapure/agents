# AI & Defence Business News Agent

![AI & Defence Business News Agent](assets/ai-defence-news-agent-banner.png)

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Gemini" src="https://img.shields.io/badge/Gemini-REST_API-4285F4?style=for-the-badge&logo=google&logoColor=white">
  <img alt="Google News RSS" src="https://img.shields.io/badge/Google_News-RSS-34A853?style=for-the-badge&logo=rss&logoColor=white">
  <img alt="Markdown" src="https://img.shields.io/badge/Output-Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white">
</p>

> A terminal-based news intelligence agent that collects fresh AI and defence business headlines, filters the noise, asks Gemini to write a concise business brief, and saves the final report as Markdown.

## What This Project Does

This project is a small automation tool for people who want a quick daily briefing on:

- AI business news: startups, funding, regulation, enterprise AI, chips, acquisitions, market moves
- Defence business news: contracts, procurement, aerospace, defence tech, manufacturing, funding, exports

Instead of manually checking news sites, the agent pulls recent results from Google News RSS, converts the XML feed into Python article objects, removes repeated stories, sends the selected article metadata to Gemini, and stores a readable report in the `reports/` folder.

## Why It Is Useful

- Saves time by collecting news from multiple Google News searches
- Keeps the focus on business impact, not random headlines
- Uses RSS metadata and snippets instead of scraping full articles
- Produces clean Markdown reports that are easy to read, share, or archive
- Runs once on demand or daily from the terminal
- Uses only the Python standard library, with no Gemini SDK required

## Tech Stack

| Area | Used In This Project |
|---|---|
| Language | Python 3.8+ |
| News Source | Google News RSS |
| Feed Format | XML / RSS |
| XML Parser | `xml.etree.ElementTree` |
| HTTP Client | `urllib.request` |
| AI Model API | Gemini REST API |
| Config | `.env` file loaded by local parser |
| Output Format | Markdown |
| Scheduling | Built-in Python loop with `time.sleep()` |
| Dependencies | Python standard library only |

## How It Works

```text
Terminal command
      |
      v
main.py
      |
      v
AgentConfig loads .env values
      |
      v
AINewsAgent.collect_articles()
      |
      v
Google News RSS search URLs
      |
      v
RSS XML arrives as bytes
      |
      v
XML is parsed into article fields
      |
      v
Article objects are cleaned, filtered, sorted, and deduplicated
      |
      v
Gemini prompt is built from article metadata
      |
      v
Gemini creates the business brief
      |
      v
Markdown report is saved in reports/
```

## Google News RSS Pipeline

The agent does not scrape full news websites. It uses Google News RSS search feeds.

For every topic query, the project builds a URL like this:

```text
https://news.google.com/rss/search?q=<search-query>&hl=en-IN&gl=IN&ceid=IN:en
```

Then the raw XML comes back from Google News:

```xml
<rss>
  <channel>
    <item>
      <title>Example headline</title>
      <link>https://example.com/story</link>
      <source>Publisher</source>
      <pubDate>Mon, 13 Jul 2026 08:30:00 GMT</pubDate>
      <description>Short RSS snippet...</description>
    </item>
  </channel>
</rss>
```

The project converts each `<item>` into an `Article` object:

```python
Article(
    topic="AI Business",
    title="Example headline",
    source="Publisher",
    link="https://example.com/story",
    published=datetime(...),
    snippet="Short RSS snippet..."
)
```

Those articles are then filtered by age, deduplicated by title, sorted newest-first, and passed to Gemini.

## Project Structure

```text
ai_news_agent/
  assets/
    ai-defence-news-agent-banner.png
  reports/
    ai_defence_business_YYYY-MM-DD_HHMMSS.md
  main.py
  news_agent.py
  requirements.txt
  run_daily.sh
  run_daily.bat
  .env.example
  .gitignore
  README.md
```

## Key Files

| File | Purpose |
|---|---|
| `main.py` | Command-line interface for `run`, `schedule`, and `check` |
| `news_agent.py` | Core logic for RSS fetching, XML parsing, Gemini prompting, and report saving |
| `.env.example` | Template for local configuration |
| `requirements.txt` | Notes that no third-party packages are required |
| `run_daily.sh` | Linux/macOS launcher for daily mode |
| `run_daily.bat` | Windows launcher for daily mode |
| `reports/` | Generated Markdown reports |

## Requirements

- Python 3.8 or newer
- Internet access
- Gemini API key from Google AI Studio

## Setup

Clone or open this folder, then create a virtual environment.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

`requirements.txt` contains no third-party packages, so installation should finish immediately.

## Environment Variables

Create a `.env` file from `.env.example` and add your Gemini API key.

```env
GEMINI_API_KEY=paste_your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
TIMEZONE=Asia/Kolkata
DAILY_RUN_TIME=08:00
LOOKBACK_HOURS=36
MAX_ARTICLES_PER_TOPIC=12
REPORTS_DIR=reports
LOG_LEVEL=INFO
```

Do not commit or share your `.env` file.

## Commands

### Check Configuration

```bash
python3 main.py check
```

This validates the setup without calling Gemini.

### Generate One Report

```bash
python3 main.py run
```

Optional overrides:

```bash
python3 main.py run --hours 48 --max-per-topic 15
```

### Run Daily Scheduler

```bash
python3 main.py schedule --run-now
```

Run at a custom time for the current session:

```bash
python3 main.py schedule --time 07:30 --run-now
```

The scheduler keeps the terminal open and runs every day at the configured time. Press `Ctrl+C` to stop it.

## Output Example

Reports are saved as timestamped Markdown files:

```text
reports/ai_defence_business_2026-07-13_163741.md
```

Each report follows this structure:

```text
# Daily AI & Defence Business Brief

## Executive Summary
## AI Business News
## Defence Business News
## Cross-Sector Signals
## Companies & Organizations Mentioned
## Source Notes
```

## Configuration Reference

| Variable | Default | Purpose |
|---|---:|---|
| `GEMINI_API_KEY` | required | Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model used for report generation |
| `TIMEZONE` | `Asia/Kolkata` | Timezone used by the scheduler and filenames |
| `DAILY_RUN_TIME` | `08:00` | Daily run time in `HH:MM` format |
| `LOOKBACK_HOURS` | `36` | Maximum age of stories to include |
| `MAX_ARTICLES_PER_TOPIC` | `12` | Number of stories sent to Gemini per topic |
| `REPORTS_DIR` | `reports` | Output folder for Markdown reports |
| `LOG_LEVEL` | `INFO` | Logging detail |

## Design Notes

- RSS data is kept in memory and is not stored as raw XML files.
- Only the final Gemini-written Markdown report is saved.
- The Gemini API key is sent in the `x-goog-api-key` HTTPS header.
- The generated brief is based on RSS headlines, links, publishers, dates, and snippets.
- Important business decisions should still be verified from original publisher links and primary documents.

## Troubleshooting

### Configuration error about Gemini API key

Update `.env` and set:

```env
GEMINI_API_KEY=your_real_key_here
```

### No articles found

Try increasing the lookback window:

```bash
python3 main.py run --hours 72
```

### Python timezone issue

Python 3.9+ supports IANA timezone names through `zoneinfo`. Python 3.8 fallback support is limited to `Asia/Kolkata` and `UTC`.

## License

This project is released under the license included in [LICENSE](LICENSE).
