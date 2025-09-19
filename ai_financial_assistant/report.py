"""Report generation utilities."""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .analysis import SentimentResult
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


def save_report(report: DailyReport, output_dir: Path) -> Path:
    """Write the report to a Markdown file and return the path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{report.ticker}_{report.as_of.isoformat()}.md"
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        handle.write(report.to_markdown())
    LOGGER.info("Report written to %s", path)
    return path


__all__ = ["DailyReport", "ReportNewsEntry", "save_report"]
