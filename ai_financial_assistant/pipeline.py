"""Coordinated execution pipeline for the AI Financial Assistant."""
from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .analysis import OpenAIAnalyzer, SentimentResult
from .config import AppConfig
from .news_fetcher import NewsArticle, fetch_news_with_content
from .report import DailyReport, ReportNewsEntry, save_report
from .stock_data import StockQuote, fetch_stock_quotes

LOGGER = logging.getLogger(__name__)


def _default_analyzer(config: AppConfig) -> Optional[OpenAIAnalyzer]:
    if not config.openai.enabled:
        return None
    try:
        return OpenAIAnalyzer(config.openai)
    except ValueError:
        LOGGER.warning("OpenAI API key not configured. AI 分析將被停用。")
        return None


def _prepare_news_entries(
    *,
    analyzer: Optional[OpenAIAnalyzer],
    company_name: str,
    articles: List[NewsArticle],
) -> List[ReportNewsEntry]:
    entries: List[ReportNewsEntry] = []
    for article in articles:
        if not article.content:
            LOGGER.debug("Skipping article without content: %s", article.url)
            continue
        if analyzer is None:
            summary = "AI 分析已停用。"
            sentiment = SentimentResult(label="中性", reason="理由：未執行 AI 分析。")
        else:
            try:
                summary = analyzer.summarize(company_name, article.content)
                sentiment = analyzer.analyze_sentiment(company_name, summary)
            except Exception as exc:  # pragma: no cover - OpenAI failure handling
                LOGGER.warning("AI analysis failed for %s: %s", article.url, exc)
                summary = "AI 分析失敗。"
                sentiment = SentimentResult(label="中性", reason="理由：AI 分析失敗。")
        entries.append(
            ReportNewsEntry(
                title=article.title,
                url=article.url,
                summary=summary,
                sentiment=sentiment,
            )
        )
    return entries


def _generate_commentary(
    *,
    analyzer: Optional[OpenAIAnalyzer],
    report_date: dt.date,
    company_name: str,
    ticker: str,
    quote: StockQuote,
    entries: List[ReportNewsEntry],
) -> Optional[str]:
    if analyzer is None:
        return None
    news_items = [
        (
            entry.sentiment.label,
            " ".join(line.strip("- ") for line in entry.summary.splitlines() if line.strip()),
        )
        for entry in entries
    ]
    try:
        return analyzer.generate_commentary(
            date=report_date,
            company_name=company_name,
            ticker=ticker,
            price=quote.price,
            change_percent=quote.change_percent,
            news_items=news_items,
        )
    except Exception as exc:  # pragma: no cover - OpenAI failure handling
        LOGGER.warning("AI commentary generation failed for %s: %s", ticker, exc)
        return None


def run_pipeline(
    config: AppConfig,
    *,
    output_dir: Optional[Path] = None,
    analyzer: Optional[OpenAIAnalyzer] = None,
) -> List[Path]:
    """Execute the end-to-end workflow once and return report paths."""

    if output_dir is None:
        output_dir = Path(config.report.output_dir)

    quotes: Dict[str, StockQuote] = fetch_stock_quotes(config.tickers)
    report_paths: List[Path] = []
    report_date = dt.date.today()

    if analyzer is None:
        analyzer = _default_analyzer(config)

    for ticker in config.tickers:
        quote = quotes.get(ticker)
        if quote is None:
            LOGGER.warning("No quote data for ticker %s, skipping report.", ticker)
            continue

        company_name = config.company_for(ticker)
        articles = fetch_news_with_content(company_name, config.news)
        entries = _prepare_news_entries(
            analyzer=analyzer,
            company_name=company_name,
            articles=articles,
        )

        commentary = None
        if config.report.include_ai_commentary:
            commentary = _generate_commentary(
                analyzer=analyzer,
                report_date=report_date,
                company_name=company_name,
                ticker=ticker,
                quote=quote,
                entries=entries,
            )

        report = DailyReport(
            ticker=ticker,
            company_name=company_name,
            as_of=report_date,
            quote=quote,
            news=entries,
            commentary=commentary,
        )
        report_path = save_report(report, output_dir)
        report_paths.append(report_path)

    return report_paths


__all__ = ["run_pipeline"]
