"""Utilities for retrieving stock market data using yfinance."""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List

import yfinance as yf

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class StockQuote:
    """Represents essential quote information for a single trading day."""

    price: float
    change_percent: float
    open: float
    high: float
    low: float
    volume: int

    def to_dict(self) -> Dict[str, float | int]:
        return asdict(self)


def _calculate_change_percent(close_series: List[float]) -> float:
    if not close_series:
        return 0.0
    if len(close_series) == 1:
        return 0.0
    latest = close_series[-1]
    previous = close_series[-2]
    if previous == 0:
        return 0.0
    return (latest - previous) / previous


def fetch_stock_quotes(tickers: Iterable[str]) -> Dict[str, StockQuote]:
    """Fetch the latest stock quotes for each ticker."""

    results: Dict[str, StockQuote] = {}
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period="5d", interval="1d", actions=False)
            if history.empty:
                LOGGER.warning("No pricing history returned for ticker %s", ticker)
                continue

            latest = history.iloc[-1]
            change_percent = _calculate_change_percent(history["Close"].tolist())
            results[ticker] = StockQuote(
                price=float(latest["Close"]),
                change_percent=float(change_percent),
                open=float(latest["Open"]),
                high=float(latest["High"]),
                low=float(latest["Low"]),
                volume=int(latest.get("Volume", 0)),
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to retrieve quote for %s: %s", ticker, exc)

    return results


__all__ = ["StockQuote", "fetch_stock_quotes"]
