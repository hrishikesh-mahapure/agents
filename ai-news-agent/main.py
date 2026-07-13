from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from news_agent import (
    AgentConfig,
    AINewsAgent,
    ConfigurationError,
    get_timezone,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Terminal-based daily AI and defence business news agent powered by Gemini."
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Generate a report immediately.")
    run_parser.add_argument(
        "--hours",
        type=int,
        default=None,
        help="Only include stories published within this many hours.",
    )
    run_parser.add_argument(
        "--max-per-topic",
        type=int,
        default=None,
        help="Maximum number of articles sent to Gemini per topic.",
    )

    schedule_parser = subparsers.add_parser(
        "schedule", help="Keep the terminal open and generate a report every day."
    )
    schedule_parser.add_argument(
        "--time",
        dest="daily_time",
        default=None,
        help="Daily run time in HH:MM (24-hour format). Defaults to DAILY_RUN_TIME in .env.",
    )
    schedule_parser.add_argument(
        "--run-now",
        action="store_true",
        help="Generate one report immediately before waiting for the next scheduled run.",
    )

    subparsers.add_parser("check", help="Validate configuration without calling Gemini.")
    return parser.parse_args()


def next_run(now: datetime, hour: int, minute: int) -> datetime:
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def parse_daily_time(value: str) -> Tuple[int, int]:
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise ConfigurationError(
            "Daily time must use HH:MM in 24-hour format, for example 08:00."
        ) from exc
    return parsed.hour, parsed.minute


def generate_once(agent: AINewsAgent) -> Path:
    logging.info("Collecting fresh business news...")
    output_path = agent.generate_report()
    print("\nReport saved to: {0}".format(output_path.resolve()))
    return output_path


def run_scheduler(
    agent: AINewsAgent, config: AgentConfig, daily_time: str, run_now: bool
) -> None:
    hour, minute = parse_daily_time(daily_time)
    tz = get_timezone(config.timezone)

    if run_now:
        try:
            generate_once(agent)
        except Exception:
            logging.exception("Immediate report generation failed.")

    print(
        "Scheduler started. A report will be generated daily at {0} ({1}). "
        "Press Ctrl+C to stop.".format(daily_time, config.timezone)
    )

    while True:
        now = datetime.now(tz)
        target = next_run(now, hour, minute)
        wait_seconds = max(1, int((target - now).total_seconds()))
        print("Next run: {0}".format(target.strftime("%Y-%m-%d %H:%M %Z")))

        try:
            time.sleep(wait_seconds)
            generate_once(agent)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            return
        except Exception:
            logging.exception(
                "Scheduled report generation failed. Retrying at the next daily run."
            )


def main() -> int:
    args = parse_args()
    command = args.command or "run"

    try:
        config = AgentConfig.from_env()

        if command == "run":
            hours = getattr(args, "hours", None)
            max_per_topic = getattr(args, "max_per_topic", None)
            if hours is not None:
                config.lookback_hours = hours
            if max_per_topic is not None:
                config.max_articles_per_topic = max_per_topic

        config.validate(require_api_key=command != "check")
        agent = AINewsAgent(config)

        if command == "check":
            print("Configuration looks valid.")
            print("Model: {0}".format(config.gemini_model))
            print("Timezone: {0}".format(config.timezone))
            print("Daily time: {0}".format(config.daily_run_time))
            print("Reports directory: {0}".format(config.reports_dir.resolve()))
            print("Dependencies: Python standard library only")
            return 0

        if command == "schedule":
            daily_time = args.daily_time or config.daily_run_time
            run_scheduler(agent, config, daily_time, args.run_now)
            return 0

        generate_once(agent)
        return 0

    except ConfigurationError as exc:
        print("Configuration error: {0}".format(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.")
        return 130
    except Exception as exc:
        logging.exception("The agent failed.")
        print("Error: {0}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
