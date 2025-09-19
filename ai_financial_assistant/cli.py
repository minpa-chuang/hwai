"""Command line interface for the AI Financial Assistant."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from .config import AppConfig, load_config
from .pipeline import run_pipeline
from .scheduler import start_scheduler


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Financial Assistant CLI")
    parser.add_argument("--config", default=None, help="Path to configuration JSON file.")
    parser.add_argument("--output-dir", default=None, help="Directory to store generated reports.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, ...)")
    parser.add_argument(
        "--disable-ai",
        action="store_true",
        help="Disable OpenAI-powered analysis for this run.",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run continuously according to the schedule defined in the configuration.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    _setup_logging(args.log_level)

    config: AppConfig = load_config(args.config)
    if args.disable_ai:
        config.openai.enabled = False
    if args.output_dir:
        config.report.output_dir = args.output_dir

    output_path = Path(config.report.output_dir)
    if args.schedule or config.schedule.enabled:
        start_scheduler(config, output_dir=output_path)
    else:
        paths = run_pipeline(config, output_dir=output_path)
        for path in paths:
            print(path)


if __name__ == "__main__":  # pragma: no cover
    main()
