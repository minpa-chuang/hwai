"""AI-powered analysis helpers using the OpenAI API."""
from __future__ import annotations

import datetime as dt
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .config import OpenAIConfig

try:  # pragma: no cover - optional import path for new SDK
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - fallback to legacy SDK
    OpenAI = None

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SentimentResult:
    """Represents the outcome of a sentiment analysis request."""

    label: str
    reason: str


class OpenAIAnalyzer:
    """Wrapper around OpenAI chat completions for summaries and sentiment."""

    def __init__(
        self,
        config: OpenAIConfig,
        *,
        api_key: Optional[str] = None,
        client: Optional[object] = None,
    ) -> None:
        self.config = config
        self._mode = "custom" if client is not None else "auto"

        if client is not None:
            self._client = client
            return

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key is not configured. Set OPENAI_API_KEY or pass api_key.")

        if OpenAI is not None:
            self._client = OpenAI(api_key=key)
            self._mode = "client"
        else:
            import openai  # type: ignore

            openai.api_key = key
            self._client = openai
            self._mode = "legacy"

    # Prompt templates -------------------------------------------------
    @staticmethod
    def _summary_prompt(company_name: str, article_content: str) -> List[dict[str, str]]:
        user_content = (
            "你是一位專業的財經分析師。請根據以下這篇關於\n"
            f"「{company_name}」的財經新聞，用繁體中文總結出 3 個最重要的市場重點，"
            "並以條列式呈現。\n\n"
            "新聞內文：\n" + article_content.strip()
        )
        return [
            {"role": "system", "content": "你是一位專業的財經分析師。"},
            {"role": "user", "content": user_content},
        ]

    @staticmethod
    def _sentiment_prompt(company_name: str, content: str) -> List[dict[str, str]]:
        user_content = (
            "你是一位市場情緒分析專家。請根據以下新聞內容，判斷市場對"
            f"「{company_name}」的情緒是「正面」、「負面」還是「中性」。請在第一行直接給出標籤，"
            "並在第二行用不超過 30 字的繁體中文簡要說明你的判斷理由。\n\n"
            "格式範例：\n正面\n理由：營收超出預期，法人看好未來季度的成長動能。\n\n"
            "新聞內容：\n" + content.strip()
        )
        return [
            {"role": "system", "content": "你是一位市場情緒分析專家。"},
            {"role": "user", "content": user_content},
        ]

    # OpenAI invocation -------------------------------------------------
    def _chat_completion(self, messages: List[dict[str, str]]) -> str:
        for attempt in range(1, self.config.max_retries + 1):
            try:
                if self._mode == "client":
                    response = self._client.chat.completions.create(  # type: ignore[union-attr]
                        model=self.config.model,
                        messages=messages,
                        temperature=self.config.temperature,
                    )
                    content = response.choices[0].message.content
                elif self._mode == "legacy":
                    response = self._client.ChatCompletion.create(  # type: ignore[union-attr]
                        model=self.config.model,
                        messages=messages,
                        temperature=self.config.temperature,
                    )
                    content = response["choices"][0]["message"]["content"]
                else:  # custom client
                    content = self._client.create_chat_completion(  # type: ignore[attr-defined]
                        model=self.config.model,
                        messages=messages,
                        temperature=self.config.temperature,
                    )
                if not content:
                    raise ValueError("Empty response from OpenAI API")
                return str(content).strip()
            except Exception as exc:  # pragma: no cover - network retry
                if attempt == self.config.max_retries:
                    raise
                wait_seconds = 2 ** (attempt - 1)
                LOGGER.warning(
                    "OpenAI request failed (attempt %s/%s): %s. Retrying in %s seconds...",
                    attempt,
                    self.config.max_retries,
                    exc,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
        raise RuntimeError("OpenAI chat completion failed after retries")

    # Public API --------------------------------------------------------
    def summarize(self, company_name: str, article_content: str) -> str:
        messages = self._summary_prompt(company_name, article_content)
        return self._chat_completion(messages)

    def analyze_sentiment(self, company_name: str, content: str) -> SentimentResult:
        messages = self._sentiment_prompt(company_name, content)
        response = self._chat_completion(messages)
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        if not lines:
            raise ValueError("OpenAI sentiment response was empty")
        label = lines[0]
        reason = ""
        for line in lines[1:]:
            if line.startswith("理由："):
                reason = line
                break
        if not reason and len(lines) > 1:
            reason = lines[1]
        if not reason:
            reason = "理由：模型未提供具體說明。"
        if not reason.startswith("理由："):
            reason = "理由：" + reason
        return SentimentResult(label=label, reason=reason)

    def generate_commentary(
        self,
        *,
        date: dt.date,
        company_name: str,
        ticker: str,
        price: float,
        change_percent: float,
        news_items: Sequence[Tuple[str, str]],
    ) -> str:
        """Generate a concise daily commentary."""

        if news_items:
            news_lines = [
                f"{idx}. 情緒：{sentiment}，摘要：{summary}"
                for idx, (sentiment, summary) in enumerate(news_items, start=1)
            ]
            news_block = "\n".join(news_lines)
        else:
            news_block = "無可用新聞摘要。"

        user_content = (
            "你是一位資深投資顧問。今天是 "
            f"{date.isoformat()}，請根據以下關於「{company_name}」({ticker}) 的市場數據和新聞分析，"
            "撰寫一段約 50 字的繁體中文綜合點評。\n\n"
            f"- 今日股價：{price:.2f}，漲跌幅：{change_percent * 100:+.2f}%。\n"
            "- 新聞分析：\n"
            f"{news_block}"
        )

        messages = [
            {"role": "system", "content": "你是一位資深投資顧問。"},
            {"role": "user", "content": user_content},
        ]
        return self._chat_completion(messages)


__all__ = ["OpenAIAnalyzer", "SentimentResult"]
