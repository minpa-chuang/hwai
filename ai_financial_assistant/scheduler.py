"""Scheduling helpers built on top of the schedule package."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

import schedule

from .config import AppConfig
from .pipeline import run_pipeline

LOGGER = logging.getLogger(__name__)


def start_scheduler(
    config: AppConfig,
    *,
    output_dir: Optional[Path] = None,
    job: Optional[Callable[[], None]] = None,
) -> None:
    """Start a blocking scheduler that executes the pipeline daily."""

    if job is None:
        job = lambda: run_pipeline(config, output_dir=output_dir)

    scheduler = schedule.Scheduler()
    scheduler.every().day.at(config.schedule.time).do(job)
    LOGGER.info("Scheduler started. Job will run daily at %s (%s).", config.schedule.time, config.schedule.timezone)

    while True:  # pragma: no cover - blocking loop
        scheduler.run_pending()
        time.sleep(1)


__all__ = ["start_scheduler"]
