"""AI-powered analysis helpers using multiple providers."""
from __future__ import annotations

import datetime as dt
import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import requests

from .config import AIProvidersConfig, GeminiConfig, OpenAIConfig, PerplexityConfig

try:  # pragma: no cover - optional import path for new SDK
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover - fallback to legacy SDK
    OpenAI = None

try:  # pragma: no cover - optional dependency for Gemini
    import google.generativeai as genai
except ImportError:  # pragma: no cover - Gemini support disabled when package missing
    genai = None

LOGGER = logging.getLogger(__name__)

_SUMMARY_SYSTEM_PROMPT = "你是一位專業的財經分析師。"
_SENTIMENT_SYSTEM_PROMPT = "你是一位市場情緒分析專家。"
_COMMENTARY_SYSTEM_PROMPT = "你是一位資深投資顧問。"
_PORTFOLIO_SYSTEM_PROMPT = (
    "你是一位投資組合顧問，需整合多家公司的行情、新聞與情緒資訊，"
    "提供風險、機會與建議的專業分析。"
)


@dataclass(slots=True)
class SentimentResult:
    """Represents the outcome of a sentiment analysis request."""

    label: str
    reason: str


class AnalyzerProtocol(Protocol):
    """Common interface implemented by all analyzer implementations."""

    def summarize(self, company_name: str, article_content: str) -> str:
        ...

    def analyze_sentiment(self, company_name: str, content: str) -> SentimentResult:
        ...

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
        ...

    def consult_portfolio(self, prompt: str) -> str:
        ...


# Prompt builders -----------------------------------------------------------------

def _summary_messages(company_name: str, article_content: str) -> List[dict[str, str]]:
    user_content = (
        "請根據以下這篇關於\n"
        f"「{company_name}」的財經新聞，用繁體中文總結出 3 個最重要的市場重點，"
        "並以條列式呈現。\n\n"
        "新聞內文：\n" + article_content.strip()
    )
    return [
        {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _sentiment_messages(company_name: str, content: str) -> List[dict[str, str]]:
    user_content = (
        "請根據以下新聞內容，判斷市場對"
        f"「{company_name}」的情緒是「正面」、「負面」還是「中性」。請在第一行直接給出標籤，"
        "並在第二行用不超過 30 字的繁體中文簡要說明你的判斷理由。\n\n"
        "格式範例：\n正面\n理由：營收超出預期，法人看好未來季度的成長動能。\n\n"
        "新聞內容：\n" + content.strip()
    )
    return [
        {"role": "system", "content": _SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _commentary_messages(
    *,
    date: dt.date,
    company_name: str,
    ticker: str,
    price: float,
    change_percent: float,
    news_items: Sequence[Tuple[str, str]],
) -> List[dict[str, str]]:
    if news_items:
        news_lines = [
            f"{idx}. 情緒：{sentiment}，摘要：{summary}"
            for idx, (sentiment, summary) in enumerate(news_items, start=1)
        ]
        news_block = "\n".join(news_lines)
    else:
        news_block = "無可用新聞摘要。"

    user_content = (
        "今天是 "
        f"{date.isoformat()}，請根據以下關於「{company_name}」({ticker}) 的市場數據和新聞分析，"
        "撰寫一段約 50 字的繁體中文綜合點評。\n\n"
        f"- 今日股價：{price:.2f}，漲跌幅：{change_percent * 100:+.2f}%。\n"
        "- 新聞分析：\n"
        f"{news_block}"
    )

    return [
        {"role": "system", "content": _COMMENTARY_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _portfolio_messages(prompt: str) -> List[dict[str, str]]:
    return [
        {"role": "system", "content": _PORTFOLIO_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def _parse_sentiment_response(response: str) -> SentimentResult:
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Sentiment response was empty")
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


def _messages_to_prompt(messages: Sequence[dict[str, str]]) -> str:
    """Concatenate chat messages into a single prompt string for Gemini."""

    parts: List[str] = []
    for message in messages:
        role = message.get("role", "user")
        prefix = "指令" if role == "system" else "輸入"
        parts.append(f"{prefix}：\n{message.get('content', '').strip()}")
    return "\n\n".join(parts)


# Analyzer implementations ---------------------------------------------------------


class OpenAIAnalyzer(AnalyzerProtocol):
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
            raise ValueError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY or pass api_key."
            )

        if OpenAI is not None:
            self._client = OpenAI(api_key=key)
            self._mode = "client"
        else:
            import openai  # type: ignore

            openai.api_key = key
            self._client = openai
            self._mode = "legacy"

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

    def summarize(self, company_name: str, article_content: str) -> str:
        messages = _summary_messages(company_name, article_content)
        return self._chat_completion(messages)

    def analyze_sentiment(self, company_name: str, content: str) -> SentimentResult:
        messages = _sentiment_messages(company_name, content)
        response = self._chat_completion(messages)
        return _parse_sentiment_response(response)

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
        messages = _commentary_messages(
            date=date,
            company_name=company_name,
            ticker=ticker,
            price=price,
            change_percent=change_percent,
            news_items=news_items,
        )
        return self._chat_completion(messages)

    def consult_portfolio(self, prompt: str) -> str:
        messages = _portfolio_messages(prompt)
        return self._chat_completion(messages)


class GeminiAnalyzer(AnalyzerProtocol):
    """Analyzer implementation using Google Gemini."""

    def __init__(
        self,
        config: GeminiConfig,
        *,
        api_key: Optional[str] = None,
        model: Optional[object] = None,
    ) -> None:
        if model is not None:
            self._model = model
        else:
            key = api_key or os.environ.get("GEMINI_API_KEY")
            if not key:
                raise ValueError(
                    "Gemini API key is not configured. Set GEMINI_API_KEY or pass api_key."
                )
            if genai is None:
                raise ImportError(
                    "google-generativeai package is required for Gemini integration."
                )
            genai.configure(api_key=key)
            self._model = genai.GenerativeModel(model=config.model)
        self.config = config

    def _generate(self, prompt: str) -> str:
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self._model.generate_content(  # type: ignore[union-attr]
                    prompt,
                    generation_config={"temperature": self.config.temperature},
                )
                text = getattr(response, "text", None)
                if not text and hasattr(response, "candidates"):
                    for candidate in getattr(response, "candidates", []):
                        parts = getattr(getattr(candidate, "content", None), "parts", [])
                        text = "".join(getattr(part, "text", "") for part in parts).strip()
                        if text:
                            break
                if not text and hasattr(response, "parts"):
                    text = "".join(getattr(part, "text", "") for part in response.parts)
                if not text:
                    raise ValueError("Empty response from Gemini API")
                return str(text).strip()
            except Exception as exc:  # pragma: no cover - network retry
                if attempt == self.config.max_retries:
                    raise
                wait_seconds = 2 ** (attempt - 1)
                LOGGER.warning(
                    "Gemini request failed (attempt %s/%s): %s. Retrying in %s seconds...",
                    attempt,
                    self.config.max_retries,
                    exc,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
        raise RuntimeError("Gemini generate_content failed after retries")

    def summarize(self, company_name: str, article_content: str) -> str:
        prompt = _messages_to_prompt(_summary_messages(company_name, article_content))
        return self._generate(prompt)

    def analyze_sentiment(self, company_name: str, content: str) -> SentimentResult:
        prompt = _messages_to_prompt(_sentiment_messages(company_name, content))
        response = self._generate(prompt)
        return _parse_sentiment_response(response)

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
        prompt = _messages_to_prompt(
            _commentary_messages(
                date=date,
                company_name=company_name,
                ticker=ticker,
                price=price,
                change_percent=change_percent,
                news_items=news_items,
            )
        )
        return self._generate(prompt)

    def consult_portfolio(self, prompt: str) -> str:
        prompt_text = _messages_to_prompt(_portfolio_messages(prompt))
        return self._generate(prompt_text)


class PerplexityAnalyzer(AnalyzerProtocol):
    """Analyzer implementation using the Perplexity API."""

    _ENDPOINT = "https://api.perplexity.ai/chat/completions"

    def __init__(
        self,
        config: PerplexityConfig,
        *,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not key:
            raise ValueError(
                "Perplexity API key is not configured. Set PERPLEXITY_API_KEY or pass api_key."
            )
        self.config = config
        self._session = session or requests.Session()
        self._headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _chat_completion(self, messages: List[dict[str, str]]) -> str:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self._session.post(
                    self._ENDPOINT,
                    json=payload,
                    headers=self._headers,
                    timeout=60,
                )
                if response.status_code >= 400:
                    raise RuntimeError(
                        f"Perplexity API returned status {response.status_code}: {response.text}"
                    )
                data = response.json()
                choices = data.get("choices")
                if not choices:
                    raise ValueError("Empty response from Perplexity API")
                content = choices[0]["message"]["content"]
                if not content:
                    raise ValueError("Empty content from Perplexity API")
                return str(content).strip()
            except Exception as exc:  # pragma: no cover - network retry
                if attempt == self.config.max_retries:
                    raise
                wait_seconds = 2 ** (attempt - 1)
                LOGGER.warning(
                    "Perplexity request failed (attempt %s/%s): %s. Retrying in %s seconds...",
                    attempt,
                    self.config.max_retries,
                    exc,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
        raise RuntimeError("Perplexity chat completion failed after retries")

    def summarize(self, company_name: str, article_content: str) -> str:
        messages = _summary_messages(company_name, article_content)
        return self._chat_completion(messages)

    def analyze_sentiment(self, company_name: str, content: str) -> SentimentResult:
        messages = _sentiment_messages(company_name, content)
        response = self._chat_completion(messages)
        return _parse_sentiment_response(response)

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
        messages = _commentary_messages(
            date=date,
            company_name=company_name,
            ticker=ticker,
            price=price,
            change_percent=change_percent,
            news_items=news_items,
        )
        return self._chat_completion(messages)

    def consult_portfolio(self, prompt: str) -> str:
        messages = _portfolio_messages(prompt)
        return self._chat_completion(messages)


# Factory helpers -----------------------------------------------------------------


def create_enabled_analyzers(config: AIProvidersConfig) -> Dict[str, AnalyzerProtocol]:
    """Instantiate analyzers for all enabled providers, skipping unavailable ones."""

    analyzers: Dict[str, AnalyzerProtocol] = {}

    if config.openai.enabled:
        try:
            analyzers["openai"] = OpenAIAnalyzer(config.openai)
        except Exception as exc:  # pragma: no cover - configuration issues
            LOGGER.warning("OpenAI analyzer unavailable: %s", exc)

    if config.gemini.enabled:
        try:
            analyzers["gemini"] = GeminiAnalyzer(config.gemini)
        except Exception as exc:  # pragma: no cover - configuration issues
            LOGGER.warning("Gemini analyzer unavailable: %s", exc)

    if config.perplexity.enabled:
        try:
            analyzers["perplexity"] = PerplexityAnalyzer(config.perplexity)
        except Exception as exc:  # pragma: no cover - configuration issues
            LOGGER.warning("Perplexity analyzer unavailable: %s", exc)

    return analyzers


__all__ = [
    "AnalyzerProtocol",
    "AIProvidersConfig",
    "GeminiAnalyzer",
    "OpenAIAnalyzer",
    "PerplexityAnalyzer",
    "SentimentResult",
    "create_enabled_analyzers",
]
