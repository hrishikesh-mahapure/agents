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

## Repository Structure

```text
agents/
+-- README.md
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
- `__pycache__/`

This keeps API keys and local chat history out of GitHub.
