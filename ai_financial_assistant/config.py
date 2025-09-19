"""Configuration loading utilities for the AI Financial Assistant."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(slots=True)
class NewsConfig:
    """Settings that control how news content is downloaded."""

    per_company: int = 5
    language: str = "zh-TW"
    region: str = "TW"
    max_retries: int = 3
    request_timeout: int = 10
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )


@dataclass(slots=True)
class OpenAIConfig:
    """Configuration for OpenAI-powered analysis."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    enabled: bool = True
    max_retries: int = 3


@dataclass(slots=True)
class GeminiConfig:
    """Configuration for Google Gemini-powered analysis."""

    model: str = "gemini-1.5-pro"
    temperature: float = 0.2
    enabled: bool = False
    max_retries: int = 3


@dataclass(slots=True)
class PerplexityConfig:
    """Configuration for Perplexity API analysis."""

    model: str = "sonar-small-chat"
    temperature: float = 0.2
    enabled: bool = False
    max_retries: int = 3


@dataclass(slots=True)
class AIProvidersConfig:
    """Collection of AI provider configurations."""

    primary: str = "openai"
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    perplexity: PerplexityConfig = field(default_factory=PerplexityConfig)

    def normalized_primary(self) -> str:
        """Return the normalized provider name for the configured primary provider."""

        return self.primary.lower()

    def is_enabled(self, provider: str) -> bool:
        provider = provider.lower()
        if provider == "openai":
            return self.openai.enabled
        if provider == "gemini":
            return self.gemini.enabled
        if provider == "perplexity":
            return self.perplexity.enabled
        return False

    def enabled_providers(self) -> List[str]:
        return [
            name
            for name in ("openai", "gemini", "perplexity")
            if self.is_enabled(name)
        ]


@dataclass(slots=True)
class ReportConfig:
    """Controls how reports are generated and stored."""

    output_dir: str = "reports"
    template: str = "text"
    include_ai_commentary: bool = True


@dataclass(slots=True)
class ScheduleConfig:
    """Scheduling preferences for automated execution."""

    enabled: bool = False
    time: str = "15:00"
    timezone: str = "Asia/Taipei"


@dataclass(slots=True)
class AppConfig:
    """Top-level configuration dataclass for the application."""

    tickers: List[str]
    company_map: Dict[str, str]
    news: NewsConfig = field(default_factory=NewsConfig)
    ai: AIProvidersConfig = field(default_factory=AIProvidersConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)

    def validate(self) -> None:
        """Validate mandatory configuration values."""

        if not self.tickers:
            raise ValueError("Configuration must include at least one ticker symbol.")

        missing_names: List[str] = [t for t in self.tickers if t not in self.company_map]
        if missing_names:
            raise ValueError(
                "Missing company name mapping for tickers: " + ", ".join(missing_names)
            )

        if self.ai.normalized_primary() not in {"openai", "gemini", "perplexity"}:
            raise ValueError(
                f"Unsupported primary AI provider configured: {self.ai.primary}"
            )

    def company_for(self, ticker: str) -> str:
        """Return the human-readable company name for a ticker."""

        return self.company_map[ticker]

    @property
    def openai(self) -> OpenAIConfig:
        """Provide backwards-compatible access to the OpenAI configuration."""

        return self.ai.openai


def _load_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(path: Optional[os.PathLike[str] | str] = None) -> AppConfig:
    """Load an :class:`AppConfig` from a JSON file.

    Parameters
    ----------
    path:
        The JSON file to read. If omitted, ``config/config.json`` relative to the
        project root will be used when available.
    """

    if path is None:
        default_path = Path.cwd() / "config" / "config.json"
        if default_path.exists():
            path = default_path
        else:
            raise FileNotFoundError(
                "No configuration file provided and default config/config.json does not exist."
            )

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = _load_json(config_path)

    tickers = list(raw.get("tickers", []))
    company_map = dict(raw.get("company_map", {}))

    ai_raw = dict(raw.get("ai", {}))
    if "openai" not in ai_raw and "openai" in raw:
        ai_raw["openai"] = dict(raw.get("openai", {}))

    config = AppConfig(
        tickers=tickers,
        company_map=company_map,
        news=NewsConfig(**(raw.get("news", {}))),
        ai=AIProvidersConfig(
            primary=ai_raw.get("primary", "openai"),
            openai=OpenAIConfig(**(ai_raw.get("openai", {}))),
            gemini=GeminiConfig(**(ai_raw.get("gemini", {}))),
            perplexity=PerplexityConfig(**(ai_raw.get("perplexity", {}))),
        ),
        report=ReportConfig(**(raw.get("report", {}))),
        schedule=ScheduleConfig(**(raw.get("schedule", {}))),
    )

    config.validate()
    return config


__all__ = [
    "AppConfig",
    "NewsConfig",
    "OpenAIConfig",
    "GeminiConfig",
    "PerplexityConfig",
    "AIProvidersConfig",
    "ReportConfig",
    "ScheduleConfig",
    "load_config",
]
