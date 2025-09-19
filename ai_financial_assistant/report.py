"""Report generation utilities."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .analysis import SentimentResult
from .history import HistoryRecord
from .stock_data import StockQuote

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ReportNewsEntry:
    """Container for AI processed news data."""

    title: str
    url: str
    summary: str
    sentiment: SentimentResult


@dataclass(slots=True)
class DailyReport:
    """Aggregate structure for a single ticker report."""

    ticker: str
    company_name: str
    as_of: dt.date
    quote: StockQuote
    news: List[ReportNewsEntry]
    commentary: Optional[str] = None

    def to_markdown(self) -> str:
        change_percent = self.quote.change_percent * 100
        lines: List[str] = [
            "=" * 40,
            f"**{self.company_name} ({self.ticker}) - {self.as_of.isoformat()} 每日戰情速報**",
            "=" * 40,
            "",
            "**【股市表現】**",
            f"- 收盤價：${self.quote.price:,.2f}",
            f"- 漲跌幅：{change_percent:+.2f}%",
            f"- 開盤價：${self.quote.open:,.2f}",
            f"- 最高價：${self.quote.high:,.2f}",
            f"- 最低價：${self.quote.low:,.2f}",
            f"- 成交量：{self.quote.volume:,}",
            "",
        ]

        if self.commentary:
            lines.extend(
                [
                    "**【AI 綜合點評】**",
                    self.commentary.strip(),
                    "",
                ]
            )

        lines.append("**【本日新聞焦點】**")
        if not self.news:
            lines.append("(無可用新聞資料)")
        else:
            for idx, entry in enumerate(self.news, start=1):
                lines.extend(
                    [
                        "---",
                        f"{idx}. **標題:** {entry.title}",
                        f"   - **連結:** {entry.url}",
                        "   - **AI 摘要:**",
                    ]
                )
                summary_lines = [
                    f"     - {line.strip()}"
                    for line in entry.summary.splitlines()
                    if line.strip()
                ]
                if not summary_lines:
                    summary_lines = ["     - 無法生成摘要。"]
                lines.extend(summary_lines)
                lines.extend(
                    [
                        f"   - **情緒分析:** {entry.sentiment.label} ({entry.sentiment.reason})",
                    ]
                )
            lines.append("---")
        lines.append("")
        return "\n".join(lines)


@dataclass(slots=True)
class OverviewTickerSnapshot:
    """Summary data used to build the portfolio overview."""

    ticker: str
    company_name: str
    quote: StockQuote
    history: List[HistoryRecord]
    latest_sentiment: Optional[SentimentResult] = None
    report_path: Optional[Path] = None


_PROVIDER_DISPLAY_NAMES = {
    "openai": "ChatGPT (OpenAI)",
    "gemini": "Gemini (Google)",
    "perplexity": "Perplexity AI",
}


@dataclass(slots=True)
class PortfolioOverview:
    """Aggregated view of all tracked tickers for the day."""

    as_of: dt.date
    snapshots: List[OverviewTickerSnapshot]
    consultations: Dict[str, str]

    def to_markdown(self) -> str:
        lines: List[str] = [
            "=" * 60,
            f"**投資組合概覽 - {self.as_of.isoformat()}**",
            "=" * 60,
            "",
        ]

        if not self.snapshots:
            lines.append("目前沒有任何已追蹤的標的。")
            return "\n".join(lines)

        lines.extend(
            [
                "## 監控總覽",
                "",
                "| 股票 | 收盤價 | 漲跌幅 | 最新情緒 | 每日報告 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )

        for snapshot in self.snapshots:
            change_percent = snapshot.quote.change_percent * 100
            if snapshot.latest_sentiment:
                sentiment_text = (
                    f"{snapshot.latest_sentiment.label}（{snapshot.latest_sentiment.reason}）"
                )
            else:
                sentiment_text = "尚無資料"
            sentiment_text = sentiment_text.replace("\n", "<br>").replace("|", "\\|")
            report_link = "-"
            if snapshot.report_path:
                report_link = f"[連結]({snapshot.report_path.name})"

            lines.append(
                "| {company} ({ticker}) | ${price:,.2f} | {change:+.2f}% | {sentiment} | {link} |".format(
                    company=snapshot.company_name,
                    ticker=snapshot.ticker,
                    price=snapshot.quote.price,
                    change=change_percent,
                    sentiment=sentiment_text,
                    link=report_link,
                )
            )

        lines.extend(["", "## 個股趨勢", ""])

        for snapshot in self.snapshots:
            lines.append(f"### {snapshot.company_name} ({snapshot.ticker})")
            if snapshot.history:
                recent = snapshot.history[-5:]
                trend = "、".join(
                    f"{record.date.strftime('%m/%d')}：${record.close:,.2f} ({record.change_percent * 100:+.2f}%)"
                    for record in recent
                )
                lines.append(f"- 近期走勢：{trend}")
            else:
                lines.append("- 近期走勢：尚無歷史資料。")

            if snapshot.latest_sentiment:
                lines.append(
                    f"- 最新情緒：{snapshot.latest_sentiment.label}（{snapshot.latest_sentiment.reason}）"
                )
            else:
                lines.append("- 最新情緒：尚無情緒分析資料。")

            if snapshot.report_path:
                lines.append(f"- 詳細報告：[每日戰情]({snapshot.report_path.name})")

            lines.append("")

        if self.consultations:
            lines.extend(["## AI 專業諮詢", ""])
            for provider in sorted(self.consultations):
                content = self.consultations[provider]
                display_name = _PROVIDER_DISPLAY_NAMES.get(provider, provider.title())
                lines.append(f"### {display_name}")
                lines.append(content.strip())
                lines.append("")

        return "\n".join(lines)


def save_report(report: DailyReport, output_dir: Path) -> Path:
    """Write the report to a Markdown file and return the path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{report.ticker}_{report.as_of.isoformat()}.md"
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        handle.write(report.to_markdown())
    LOGGER.info("Report written to %s", path)
    return path


def save_overview_report(overview: PortfolioOverview, output_dir: Path) -> Path:
    """Persist the portfolio overview report and return the resulting path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"overview_{overview.as_of.isoformat()}.md"
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        handle.write(overview.to_markdown())
    LOGGER.info("Overview report written to %s", path)
    return path


__all__ = [
    "DailyReport",
    "OverviewTickerSnapshot",
    "PortfolioOverview",
    "ReportNewsEntry",
    "save_overview_report",
    "save_report",
]
