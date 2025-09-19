"""Utilities for persisting and retrieving quote history."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .stock_data import StockQuote


@dataclass(slots=True)
class HistoryRecord:
    """Represents a single day's tracked quote data for a ticker."""

    date: dt.date
    close: float
    change_percent: float
    open: float
    high: float
    low: float
    volume: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "date": self.date.isoformat(),
            "close": self.close,
            "change_percent": self.change_percent,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "HistoryRecord":
        raw_date = payload.get("date")
        if isinstance(raw_date, dt.date):
            record_date = raw_date
        elif isinstance(raw_date, str):
            record_date = dt.date.fromisoformat(raw_date)
        else:
            raise ValueError("History record must contain a valid date field")

        return cls(
            date=record_date,
            close=float(payload.get("close", 0.0)),
            change_percent=float(payload.get("change_percent", 0.0)),
            open=float(payload.get("open", 0.0)),
            high=float(payload.get("high", 0.0)),
            low=float(payload.get("low", 0.0)),
            volume=int(payload.get("volume", 0)),
        )


def _history_path(ticker: str, *, output_dir: Path) -> Path:
    return output_dir / "history" / f"{ticker}.jsonl"


def _write_records(path: Path, records: List[HistoryRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def load_history(
    ticker: str,
    *,
    output_dir: Path,
    limit: Optional[int] = 30,
) -> List[HistoryRecord]:
    """Load historical quote records for ``ticker`` from disk."""

    path = _history_path(ticker, output_dir=output_dir)
    if not path.exists():
        return []

    records: List[HistoryRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            records.append(HistoryRecord.from_dict(data))

    if limit is not None and len(records) > limit:
        records = records[-limit:]
    return records


def append_history_record(
    ticker: str,
    quote: StockQuote,
    *,
    as_of: dt.date,
    output_dir: Path,
    max_records: int = 365,
) -> HistoryRecord:
    """Persist the latest ``quote`` data and return the stored record."""

    existing = load_history(ticker, output_dir=output_dir, limit=None)
    record = HistoryRecord(
        date=as_of,
        close=quote.price,
        change_percent=quote.change_percent,
        open=quote.open,
        high=quote.high,
        low=quote.low,
        volume=quote.volume,
    )

    if existing and existing[-1].date == record.date:
        existing[-1] = record
    else:
        existing.append(record)

    if max_records and len(existing) > max_records:
        existing = existing[-max_records:]

    path = _history_path(ticker, output_dir=output_dir)
    _write_records(path, existing)
    return record


__all__ = ["HistoryRecord", "append_history_record", "load_history"]
