"""News retrieval helpers for the AI Financial Assistant."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .config import NewsConfig

LOGGER = logging.getLogger(__name__)
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


@dataclass(slots=True)
class NewsArticle:
    """Lightweight representation of a news article."""

    title: str
    url: str
    published: Optional[datetime] = None
    source: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


def _build_search_url(company_name: str, config: NewsConfig) -> str:
    query = quote_plus(company_name)
    return (
        f"{GOOGLE_NEWS_RSS}?q={query}&hl={config.language}&gl={config.region}"
        f"&ceid={config.region}:{config.language}"
    )


def fetch_company_news(company_name: str, config: NewsConfig) -> List[NewsArticle]:
    """Return a list of recent news article metadata for the company."""

    url = _build_search_url(company_name, config)
    headers = {"User-Agent": config.user_agent}
    articles: List[NewsArticle] = []

    try:
        response = requests.get(url, headers=headers, timeout=config.request_timeout)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network error logging
        LOGGER.exception("Failed to fetch Google News RSS for %s: %s", company_name, exc)
        return articles

    soup = BeautifulSoup(response.text, "xml")
    for item in soup.find_all("item")[: config.per_company]:
        title = item.title.text if item.title else ""
        link = item.link.text if item.link else ""
        source = item.source.text if item.source else None
        published = None
        if item.pubDate and item.pubDate.text:
            try:
                published = parsedate_to_datetime(item.pubDate.text)
            except (TypeError, ValueError):
                LOGGER.debug("Unable to parse publication date: %s", item.pubDate.text)
        if not link:
            continue
        articles.append(
            NewsArticle(
                title=title.strip(),
                url=link.strip(),
                published=published,
                source=source.strip() if source else None,
            )
        )

    return articles


def download_article_content(article: NewsArticle, config: NewsConfig) -> Optional[str]:
    """Download and parse a full article body, returning the extracted text."""

    headers = {"User-Agent": config.user_agent}
    try:
        response = requests.get(article.url, headers=headers, timeout=config.request_timeout)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network error logging
        LOGGER.warning("Failed to download article %s: %s", article.url, exc)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if p.get_text(strip=True)
    ]

    if not paragraphs:
        LOGGER.debug("No paragraph content extracted for %s", article.url)
        return None

    article.content = "\n".join(paragraphs)
    return article.content


def fetch_news_with_content(company_name: str, config: NewsConfig) -> List[NewsArticle]:
    """Fetch article metadata and inline content for a given company."""

    articles = fetch_company_news(company_name, config)
    for article in articles:
        if not article.content:
            download_article_content(article, config)
    return articles


__all__ = [
    "NewsArticle",
    "fetch_company_news",
    "download_article_content",
    "fetch_news_with_content",
]
