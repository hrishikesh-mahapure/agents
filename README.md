# Agents

A growing collection of small AI agent projects and experiments.

## Projects

### Gemini Chat API

Folder: [`gemini-chat-api`](gemini-chat-api/)

A Python terminal chatbot powered by the Gemini API. It supports:

- interactive chat
- model fallback
- local persistent memory
- `/clear` memory reset
- safe `.env` based API key loading

Start here if you want to understand the basic building blocks of an agentic AI application: API calls, state, memory, and command handling.

### AI & Defence Business News Agent

Folder: [`ai-news-agent`](ai-news-agent/)

A terminal-based news intelligence agent powered by Google News RSS and the Gemini REST API. It supports:

- AI and defence business news collection
- RSS XML parsing
- headline filtering and deduplication
- Gemini-generated Markdown briefings
- one-time report generation
- daily scheduled terminal runs

Use this project if you want to understand how an agent can gather structured web feed data, convert it into clean context, and produce a useful business report.

## Repository Structure

```text
agents/
+-- README.md
+-- ai-news-agent/
    +-- assets/
    +-- main.py
    +-- news_agent.py
    +-- README.md
    +-- requirements.txt
+-- gemini-chat-api/
    +-- app.py
    +-- README.md
    +-- requirements.txt
    +-- assets/
```

## Safety Notes

Private files are intentionally ignored:

- `.env`
- `chat_history.json`
- generated reports
- `__pycache__/`

This keeps API keys, local chat history, generated reports, and cache files out of GitHub.
