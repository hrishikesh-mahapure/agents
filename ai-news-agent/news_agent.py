from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, quote_plus
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:  # pragma: no cover - used on Python 3.8
    ZoneInfo = None  # type: ignore


class ConfigurationError(ValueError):
    """Raised when environment configuration is missing or invalid."""


@dataclass
class Article:
    topic: str
    title: str
    source: str
    link: str
    published: Optional[datetime]
    snippet: str

    @property
    def fingerprint(self) -> str:
        normalized = re.sub(r"[^a-z0-9]+", " ", self.title.lower()).strip()
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    def as_prompt_text(self, index: int) -> str:
        published = (
            self.published.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            if self.published
            else "Unknown"
        )
        return (
            "Article {index}\n"
            "Topic: {topic}\n"
            "Title: {title}\n"
            "Source: {source}\n"
            "Published: {published}\n"
            "URL: {link}\n"
            "RSS snippet: {snippet}\n"
        ).format(
            index=index,
            topic=self.topic,
            title=self.title,
            source=self.source,
            published=published,
            link=self.link,
            snippet=self.snippet or "No snippet available.",
        )


@dataclass
class AgentConfig:
    gemini_api_key: str
    gemini_model: str
    timezone: str
    daily_run_time: str
    lookback_hours: int
    max_articles_per_topic: int
    reports_dir: Path
    log_level: str

    @classmethod
    def from_env(cls) -> "AgentConfig":
        project_dir = Path(__file__).resolve().parent
        _load_env_file(project_dir / ".env")

        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
            timezone=os.getenv("TIMEZONE", "Asia/Kolkata").strip(),
            daily_run_time=os.getenv("DAILY_RUN_TIME", "08:00").strip(),
            lookback_hours=_env_int("LOOKBACK_HOURS", 36),
            max_articles_per_topic=_env_int("MAX_ARTICLES_PER_TOPIC", 12),
            reports_dir=project_dir / os.getenv("REPORTS_DIR", "reports").strip(),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )

    def validate(self, require_api_key: bool = True) -> None:
        if require_api_key and (
            not self.gemini_api_key or "paste" in self.gemini_api_key.lower()
        ):
            raise ConfigurationError(
                "Add your Gemini API key to GEMINI_API_KEY in the .env file."
            )
        if not self.gemini_model:
            raise ConfigurationError("GEMINI_MODEL cannot be empty.")
        if self.lookback_hours < 1:
            raise ConfigurationError("LOOKBACK_HOURS must be at least 1.")
        if not 1 <= self.max_articles_per_topic <= 50:
            raise ConfigurationError(
                "MAX_ARTICLES_PER_TOPIC must be between 1 and 50."
            )
        get_timezone(self.timezone)
        try:
            datetime.strptime(self.daily_run_time, "%H:%M")
        except ValueError as exc:
            raise ConfigurationError(
                "DAILY_RUN_TIME must use HH:MM in 24-hour format."
            ) from exc


TOPIC_QUERIES: Dict[str, List[str]] = {
    "AI Business": [
        "artificial intelligence business OR AI startup funding OR AI acquisition",
        "generative AI enterprise earnings investment chip business",
        "AI regulation company market business deal",
    ],
    "Defence Business": [
        "defence business contract procurement company OR defense business contract procurement company",
        "military technology startup funding acquisition contract",
        "aerospace defense industry order earnings deal",
    ],
}


class AINewsAgent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        logging.basicConfig(
            level=getattr(logging, config.log_level, logging.INFO),
            format="%(asctime)s | %(levelname)s | %(message)s",
        )

    def generate_report(self) -> Path:
        articles = self.collect_articles()
        if not articles:
            raise RuntimeError(
                "No recent articles were found. Check your internet connection or increase LOOKBACK_HOURS."
            )

        prompt = self._build_prompt(articles)
        report = self._ask_gemini(prompt)
        return self._save_report(report)

    def collect_articles(self) -> List[Article]:
        all_articles = []  # type: List[Article]
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=self.config.lookback_hours
        )

        for topic, queries in TOPIC_QUERIES.items():
            topic_articles = []  # type: List[Article]
            for query_text in queries:
                url = self._google_news_rss_url(query_text)
                payload = self._fetch_feed(url, query_text)
                if payload is None:
                    continue

                for article in self._parse_feed(topic, payload):
                    if article.published and article.published < cutoff:
                        continue
                    topic_articles.append(article)

            topic_articles = self._deduplicate(topic_articles)
            topic_articles.sort(
                key=lambda article: article.published
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            selected = topic_articles[: self.config.max_articles_per_topic]
            logging.info("Selected %d %s articles.", len(selected), topic)
            all_articles.extend(selected)

        return all_articles

    def _google_news_rss_url(self, query_text: str) -> str:
        days = max(1, (self.config.lookback_hours + 23) // 24)
        return (
            "https://news.google.com/rss/search?"
            "q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        ).format(query=quote_plus(query_text + " when:{0}d".format(days)))

    @staticmethod
    def _fetch_feed(url: str, query_text: str) -> Optional[bytes]:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AI-News-Agent/1.1; RSS reader)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
                "Accept-Encoding": "identity",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            logging.warning("Could not fetch RSS for %s: %s", query_text, exc)
            return None

    @staticmethod
    def _parse_feed(topic: str, payload: bytes) -> List[Article]:
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            logging.warning("Could not parse an RSS feed: %s", exc)
            return []

        articles = []  # type: List[Article]
        for item in root.iter():
            if _local_name(item.tag) != "item":
                continue

            title = _clean_text(_child_text(item, "title") or "Untitled")
            link = (_child_text(item, "link") or "").strip()
            source = _clean_text(_child_text(item, "source") or "Unknown source")
            snippet = _clean_text(
                _child_text(item, "description")
                or _child_text(item, "summary")
                or ""
            )[:700]
            published = _parse_date_text(
                _child_text(item, "pubDate") or _child_text(item, "updated")
            )
            articles.append(
                Article(topic, title, source, link, published, snippet)
            )
        return articles

    @staticmethod
    def _deduplicate(articles: Iterable[Article]) -> List[Article]:
        seen = set()
        unique = []  # type: List[Article]
        for article in articles:
            if article.fingerprint in seen:
                continue
            seen.add(article.fingerprint)
            unique.append(article)
        return unique

    def _build_prompt(self, articles: List[Article]) -> str:
        article_text = "\n---\n".join(
            article.as_prompt_text(index)
            for index, article in enumerate(articles, start=1)
        )
        report_date = datetime.now(get_timezone(self.config.timezone)).strftime(
            "%Y-%m-%d"
        )
        return """
You are a careful business-news intelligence analyst. Create a concise daily report dated {report_date}
using ONLY the supplied RSS article metadata and snippets. Do not invent facts. When a snippet does not
support a conclusion, say that details are limited. Preserve the supplied URLs so the reader can verify each item.

Audience: a business reader interested in artificial intelligence and the defence/defense industry.

Required Markdown structure:
# Daily AI & Defence Business Brief — {report_date}

## Executive Summary
- 5 to 8 bullets covering the most consequential developments across both sectors.

## AI Business News
For the most important AI-business stories, provide:
### Headline
- **What happened:** 1-2 factual sentences.
- **Business significance:** 1-2 sentences focused on companies, capital, revenue, competition, regulation, supply chains, or market impact.
- **Watch next:** one concrete issue to monitor.
- **Source:** [Publisher](URL) — published time if available.

## Defence Business News
Use the same format. Focus on contracts, procurement, company strategy, funding, manufacturing capacity,
exports, acquisitions, aerospace/space defence, dual-use technology, and regulation.

## Cross-Sector Signals
- 3 to 5 bullets on links between AI and defence business, clearly labeling any inference as "Inference".

## Companies & Organizations Mentioned
A compact comma-separated list with no duplicates.

## Source Notes
State that this report is based on RSS headlines/snippets and readers should open primary sources for full context.

Rules:
- Select quality over quantity; omit weak, repetitive, purely political, or unrelated stories.
- Do not provide operational military guidance, sensitive targeting information, or speculation about classified activity.
- Never fabricate financial figures, contract values, quotations, dates, or company names.
- Keep the report under approximately 1,800 words.

SUPPLIED ARTICLES
=================
{article_text}
""".strip().format(report_date=report_date, article_text=article_text)

    def _ask_gemini(self, prompt: str) -> str:
        if not self.config.gemini_api_key:
            raise ConfigurationError(
                "Gemini API key is unavailable because GEMINI_API_KEY is missing."
            )

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "{model}:generateContent"
        ).format(model=quote(self.config.gemini_model, safe=""))
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
            },
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.config.gemini_api_key,
                "User-Agent": "AI-News-Agent/1.1",
            },
            method="POST",
        )

        logging.info(
            "Sending %d characters of news context to Gemini model %s.",
            len(prompt),
            self.config.gemini_model,
        )
        try:
            with urlopen(request, timeout=120) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = _http_error_detail(exc)
            raise RuntimeError(
                "Gemini request failed with HTTP {0}: {1}".format(exc.code, detail)
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                "Gemini request could not connect: {0}".format(exc.reason)
            ) from exc
        except (TimeoutError, OSError) as exc:
            raise RuntimeError("Gemini request timed out or lost connection.") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Gemini returned an unreadable response.") from exc

        text_parts = []  # type: List[str]
        for candidate in response_data.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if text:
                    text_parts.append(str(text))

        report = "\n".join(text_parts).strip()
        if not report:
            feedback = response_data.get("promptFeedback", {})
            block_reason = feedback.get("blockReason")
            if block_reason:
                raise RuntimeError(
                    "Gemini blocked the request: {0}".format(block_reason)
                )
            raise RuntimeError("Gemini returned an empty response.")
        return report

    def _save_report(self, report: str) -> Path:
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(get_timezone(self.config.timezone))
        output_path = self.config.reports_dir / (
            "ai_defence_business_{0}.md".format(now.strftime("%Y-%m-%d_%H%M%S"))
        )
        output_path.write_text(report + "\n", encoding="utf-8")
        return output_path


def get_timezone(name: str):
    """Return a timezone object with a Python 3.8 fallback for India and UTC."""
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception as exc:
            raise ConfigurationError("Unknown timezone: {0}".format(name)) from exc

    normalized = name.strip().lower()
    if normalized in ("asia/kolkata", "asia/calcutta", "ist"):
        return timezone(timedelta(hours=5, minutes=30), name="IST")
    if normalized in ("utc", "etc/utc", "gmt"):
        return timezone.utc
    raise ConfigurationError(
        "Python 3.8 fallback supports TIMEZONE=Asia/Kolkata or UTC. "
        "Use Python 3.9+ for other IANA timezones."
    )


def _load_env_file(path: Path) -> None:
    """Load a simple KEY=VALUE .env file without an external package."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0:1] == value[-1:] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError("{0} must be an integer.".format(name)) from exc


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, child_name: str) -> Optional[str]:
    for child in list(element):
        if _local_name(child.tag) == child_name:
            return "".join(child.itertext())
    return None


def _parse_date_text(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _http_error_detail(exc: HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        message = data.get("error", {}).get("message")
        if message:
            return str(message)
        return raw[:500] or exc.reason
    except Exception:
        return str(exc.reason)
