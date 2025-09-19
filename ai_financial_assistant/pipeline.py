"""Coordinated execution pipeline for the AI Financial Assistant."""
from __future__ import annotations

import datetime as dt
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .analysis import AnalyzerProtocol, SentimentResult, create_enabled_analyzers
from .config import AppConfig
from .history import append_history_record, load_history
from .news_fetcher import NewsArticle, fetch_news_with_content
from .report import (
    DailyReport,
    OverviewTickerSnapshot,
    PortfolioOverview,
    ReportNewsEntry,
    save_overview_report,
    save_report,
)
from .stock_data import StockQuote, fetch_stock_quotes

LOGGER = logging.getLogger(__name__)


def _initialize_analyzers(
    config: AppConfig,
    override: Optional[AnalyzerProtocol],
) -> Tuple[Optional[AnalyzerProtocol], Dict[str, AnalyzerProtocol]]:
    """Create analyzers and determine which provider should be primary."""

    analyzers = create_enabled_analyzers(config.ai)
    if override is not None:
        analyzers = {"custom": override, **analyzers}
        return override, analyzers

    if not analyzers:
        return None, {}

    preferred = config.ai.normalized_primary()
    if preferred in analyzers:
        return analyzers[preferred], analyzers

    fallback_name = next(iter(analyzers))
    LOGGER.info(
        "Primary AI provider %s unavailable, falling back to %s.",
        config.ai.primary,
        fallback_name,
    )
    return analyzers[fallback_name], analyzers


def _prepare_news_entries(
    *,
    analyzer: Optional[AnalyzerProtocol],
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
            except Exception as exc:  # pragma: no cover - AI failure handling
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
    analyzer: Optional[AnalyzerProtocol],
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
    except Exception as exc:  # pragma: no cover - AI failure handling
        LOGGER.warning("AI commentary generation failed for %s: %s", ticker, exc)
        return None


def _aggregate_sentiment(entries: Sequence[ReportNewsEntry]) -> Optional[SentimentResult]:
    if not entries:
        return None
    counts = Counter(entry.sentiment.label for entry in entries)
    label, _ = counts.most_common(1)[0]
    matching_reasons = [
        entry.sentiment.reason for entry in entries if entry.sentiment.label == label
    ]
    reason = matching_reasons[0] if matching_reasons else entries[0].sentiment.reason
    return SentimentResult(label=label, reason=reason)


def _build_portfolio_prompt(
    report_date: dt.date,
    snapshots: Sequence[OverviewTickerSnapshot],
) -> str:
    lines: List[str] = [
        f"請綜合評估以下投資組合於 {report_date.isoformat()} 的整體現況，提出市場趨勢、風險與建議：",
        "",
    ]
    for snapshot in snapshots:
        change_percent = snapshot.quote.change_percent * 100
        lines.append(
            f"- {snapshot.company_name} ({snapshot.ticker})：收盤 {snapshot.quote.price:.2f}，漲跌幅 {change_percent:+.2f}%。"
        )
        if snapshot.latest_sentiment:
            lines.append(
                f"  最新情緒：{snapshot.latest_sentiment.label}，{snapshot.latest_sentiment.reason}."
            )
        if snapshot.history:
            recent = snapshot.history[-3:]
            trend = ", ".join(
                f"{record.date.strftime('%m/%d')} 收盤 {record.close:.2f}" for record in recent
            )
            lines.append(f"  近期走勢：{trend}。")
    lines.append("請以條列方式整理：(1) 整體投資組合觀察 (2) 主要風險 (3) 建議行動。")
    return "\n".join(lines)


def run_pipeline(
    config: AppConfig,
    *,
    output_dir: Optional[Path] = None,
    analyzer: Optional[AnalyzerProtocol] = None,
) -> List[Path]:
    """Execute the end-to-end workflow once and return report paths."""

    if output_dir is None:
        resolved_output = Path(config.report.output_dir)
    else:
        resolved_output = Path(output_dir)

    quotes: Dict[str, StockQuote] = fetch_stock_quotes(config.tickers)
    report_paths: List[Path] = []
    report_date = dt.date.today()

    primary_analyzer, analyzer_map = _initialize_analyzers(config, analyzer)

    overview_snapshots: List[OverviewTickerSnapshot] = []

    for ticker in config.tickers:
        quote = quotes.get(ticker)
        if quote is None:
            LOGGER.warning("No quote data for ticker %s, skipping report.", ticker)
            continue

        company_name = config.company_for(ticker)
        articles = fetch_news_with_content(company_name, config.news)
        entries = _prepare_news_entries(
            analyzer=primary_analyzer,
            company_name=company_name,
            articles=articles,
        )

        commentary = None
        if config.report.include_ai_commentary:
            commentary = _generate_commentary(
                analyzer=primary_analyzer,
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
        report_path = save_report(report, resolved_output)
        report_paths.append(report_path)

        append_history_record(
            ticker,
            quote,
            as_of=report_date,
            output_dir=resolved_output,
        )
        history_records = load_history(ticker, output_dir=resolved_output, limit=30)
        aggregated_sentiment = _aggregate_sentiment(entries)
        overview_snapshots.append(
            OverviewTickerSnapshot(
                ticker=ticker,
                company_name=company_name,
                quote=quote,
                history=history_records,
                latest_sentiment=aggregated_sentiment,
                report_path=report_path,
            )
        )

    if overview_snapshots:
        consultations: Dict[str, str] = {}
        if analyzer_map:
            prompt = _build_portfolio_prompt(report_date, overview_snapshots)
            for name, provider in analyzer_map.items():
                try:
                    consultations[name] = provider.consult_portfolio(prompt)
                except Exception as exc:  # pragma: no cover - AI failure handling
                    LOGGER.warning(
                        "Portfolio consultation failed for provider %s: %s", name, exc
                    )
        overview = PortfolioOverview(
            as_of=report_date,
            snapshots=overview_snapshots,
            consultations=consultations,
        )
        overview_path = save_overview_report(overview, resolved_output)
        report_paths.append(overview_path)

    return report_paths


__all__ = ["run_pipeline"]
