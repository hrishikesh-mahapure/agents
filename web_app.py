from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from news_agent import AINewsAgent, AgentConfig


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "web"


class NewsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/news":
            self.send_news()
            return
        if path == "/api/health":
            self.send_json({"status": "ok"})
            return

        relative = "index.html" if path == "/" else path.lstrip("/")
        file_path = (PUBLIC / relative).resolve()
        if PUBLIC.resolve() not in file_path.parents or not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_news(self) -> None:
        try:
            config = AgentConfig.from_env()
            config.validate(require_api_key=False)
            articles = AINewsAgent(config).collect_articles()
            payload = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "lookback_hours": config.lookback_hours,
                "articles": [
                    {
                        "topic": article.topic,
                        "title": article.title,
                        "source": article.source,
                        "url": article.link,
                        "published": article.published.isoformat() if article.published else None,
                        "snippet": article.snippet,
                    }
                    for article in articles
                ],
            }
            self.send_json(payload)
        except Exception as exc:
            self.send_json({"error": str(exc), "articles": []}, status=502)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print("[web] " + fmt % args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI GRID web dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def create_server(host: str, requested_port: int) -> ThreadingHTTPServer:
    """Use the requested port, or the next available one when it is occupied."""
    for port in range(requested_port, requested_port + 10):
        try:
            return ThreadingHTTPServer((host, port), NewsHandler)
        except OSError as exc:
            if exc.errno not in (98, 48, 10048):
                raise
    raise OSError(
        "Ports {0}-{1} are already in use. Try --port 9000.".format(
            requested_port, requested_port + 9
        )
    )


def main() -> None:
    args = parse_args()
    server = create_server(args.host, args.port)
    actual_port = server.server_address[1]
    if actual_port != args.port:
        print("Port {0} is busy; using {1} instead.".format(args.port, actual_port))
    print("AI GRID running at http://{0}:{1}".format(args.host, actual_port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAI GRID stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
