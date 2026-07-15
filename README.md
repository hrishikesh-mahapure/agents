# AI GRID — AI Platform News Dashboard

<p align="center">
  <img alt="Python 3.8+" src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Google News RSS" src="https://img.shields.io/badge/Google_News-RSS-34A853?style=for-the-badge&logo=rss&logoColor=white">
  <img alt="No dependencies" src="https://img.shields.io/badge/Dependencies-None-111111?style=for-the-badge">
  <img alt="Gemini optional" src="https://img.shields.io/badge/Gemini-Optional-4285F4?style=for-the-badge&logo=google&logoColor=white">
</p>

AI GRID is a responsive news-intelligence dashboard for tracking releases, research, developer tools, funding, regulation, and market moves across leading AI platforms.

It uses public Google News RSS results, does not scrape full articles, and runs entirely with the Python standard library. A Gemini-powered Markdown briefing workflow is also available as an optional CLI feature.

## Features

- Live, UI-based AI news dashboard
- Coverage of OpenAI, Anthropic, Google, Microsoft, Meta, xAI, Mistral, Cohere, Perplexity, and the wider AI industry
- Platform filters, source names, timestamps, summaries, and original article links
- Manual feed refresh without reloading the page
- Responsive BMW-M-inspired dark interface
- Automatic headline deduplication and age filtering
- Automatic fallback when port `8000` is occupied
- Optional Gemini-generated Markdown intelligence reports
- No third-party Python packages

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai_news_agent
```

### 2. Start the dashboard

```bash
python3 web_app.py
```

Open the URL printed in the terminal, normally:

```text
http://127.0.0.1:8000
```

The dashboard does not require a Gemini API key.

If port `8000` is occupied, AI GRID automatically tries ports `8001` through `8009` and prints the selected URL. You can also choose a port explicitly:

```bash
python3 web_app.py --port 9000
```

To make the dashboard available to other devices on your local network:

```bash
python3 web_app.py --host 0.0.0.0 --port 8000
```

## How News Is Fetched

The browser requests `GET /api/news` from the local Python server. The server then:

1. Builds Google News RSS search URLs for leading AI platforms and industry topics.
2. Downloads the public RSS/XML feeds using `urllib.request`.
3. Parses headlines, publisher names, links, dates, and snippets.
4. Excludes stories older than `LOOKBACK_HOURS`.
5. Deduplicates similar headlines and sorts them newest-first.
6. Limits the results using `MAX_ARTICLES_PER_TOPIC`.
7. Returns JSON to the browser, where the cards and filters are rendered.

Example RSS URL:

```text
https://news.google.com/rss/search?q=<search-query>&hl=en-IN&gl=IN&ceid=IN:en
```

AI GRID links readers to the original result for full context. It does not scrape or republish full news articles.

## Coverage

The current searches are grouped into two feeds:

| Feed | Coverage |
|---|---|
| AI Platforms | OpenAI/ChatGPT, Anthropic/Claude, Google Gemini/DeepMind, Microsoft Copilot, Meta/Llama, xAI/Grok, Mistral, Cohere, and Perplexity |
| AI Industry | Agents, developer tools, coding models, chips, data centers, funding, acquisitions, partnerships, enterprise AI, safety, and regulation |

Search queries can be changed in `TOPIC_QUERIES` inside `news_agent.py`.

## Project Structure

```text
ai_news_agent/
├── web/
│   ├── index.html          # Dashboard markup
│   ├── styles.css          # Responsive BMW-M-inspired styling
│   └── app.js              # Feed loading, filtering, and rendering
├── assets/                 # Repository assets
├── main.py                 # Optional report CLI and scheduler
├── news_agent.py           # RSS collection and Gemini report logic
├── web_app.py              # Static web server and JSON API
├── run_daily.sh            # Linux/macOS scheduler launcher
├── run_daily.bat           # Windows scheduler launcher
├── requirements.txt        # No external dependencies
├── .env.example            # Configuration template
├── LICENSE
└── README.md
```

## Web API

| Endpoint | Purpose |
|---|---|
| `GET /` | Serves the dashboard |
| `GET /api/news` | Fetches, processes, and returns current news as JSON |
| `GET /api/health` | Returns a basic server health response |

## Configuration

The dashboard works with defaults. To customize it, copy the example environment file:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---:|---|
| `LOOKBACK_HOURS` | `36` | Maximum age of stories included in the feed |
| `MAX_ARTICLES_PER_TOPIC` | `12` | Maximum stories selected for each feed group |
| `TIMEZONE` | `Asia/Kolkata` | Timezone used by reports and scheduling |
| `GEMINI_API_KEY` | empty | Required only for generated Markdown reports |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model used for reports |
| `DAILY_RUN_TIME` | `08:00` | Scheduled report time in `HH:MM` format |
| `REPORTS_DIR` | `reports` | Generated report directory |
| `LOG_LEVEL` | `INFO` | Application logging level |

Never commit your real `.env` file or API key.

## Optional Gemini Reports

The UI does not use Gemini. Gemini is only needed when generating summarized Markdown briefs from the command line.

Add a key to `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Validate configuration:

```bash
python3 main.py check
```

Generate one report:

```bash
python3 main.py run
```

Change the collection window or result limit:

```bash
python3 main.py run --hours 48 --max-per-topic 15
```

Run the daily scheduler:

```bash
python3 main.py schedule --run-now
```

Use a custom daily time:

```bash
python3 main.py schedule --time 07:30 --run-now
```

## Troubleshooting

### Port already in use

The server normally selects the next available port automatically. To force another port:

```bash
python3 web_app.py --port 9000
```

To inspect or stop a Linux process using port `8000`:

```bash
sudo lsof -i :8000
sudo fuser -k 8000/tcp
```

### Feed is empty or unavailable

- Confirm that the computer has internet access.
- Click **Refresh feed** in the dashboard.
- Increase `LOOKBACK_HOURS` in `.env`.
- Check whether Google News RSS is reachable on the current network.

### Gemini API key error

This only affects CLI report generation. Add a valid `GEMINI_API_KEY` to `.env`; the web dashboard works without it.

### Python timezone issue

Python 3.9+ supports IANA timezone names through `zoneinfo`. The Python 3.8 fallback is limited to `Asia/Kolkata` and `UTC`.

## Privacy and Source Notes

- Raw RSS feeds are processed in memory and are not stored.
- The dashboard displays public RSS metadata and links to source articles.
- Optional Gemini reports send selected RSS metadata and snippets to the Gemini REST API.
- Verify important claims using the linked publisher and relevant primary sources.

## License

Released under the terms in [LICENSE](LICENSE).
