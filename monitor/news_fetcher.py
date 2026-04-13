"""Search Google News RSS for recent articles related to a stock move.

Uses requests + stdlib xml.etree.ElementTree to parse RSS — no feedparser
dependency required.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests

from monitor.config import NEWS_MAX_RESULTS
from monitor.logger import setup_logger

logger = setup_logger()

_GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search"
    "?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

# Polite delay between successive news requests (seconds)
_REQUEST_DELAY = 2.0


def _parse_rss(xml_text: str, max_results: int) -> list[dict]:
    """Parse an RSS 2.0 XML string and return article dicts."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("RSS parse error: %s", exc)
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item")[:max_results]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""

        articles.append(
            {
                "title": title,
                "link": link,
                "published": pub_date,
                "source": source,
            }
        )
    return articles


def search_news(company_name: str, symbol: str, max_results: int = NEWS_MAX_RESULTS) -> list[dict]:
    """Return recent news articles for a stock.

    Args:
        company_name: Human-readable company name (e.g. "Reliance Industries Ltd.").
        symbol: NSE ticker (e.g. "RELIANCE") — used as a secondary search term.
        max_results: Maximum number of articles to return.

    Returns:
        List of dicts with keys: title, link, published, source.
    """
    query = quote_plus(f"{company_name} {symbol} stock NSE")
    url = _GOOGLE_NEWS_RSS.format(query=query)

    logger.debug("Fetching news for %s: %s", symbol, url)

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        articles = _parse_rss(resp.text, max_results)
    except requests.RequestException as exc:
        logger.warning("News fetch error for %s: %s", symbol, exc)
        articles = []

    logger.debug("Found %d articles for %s.", len(articles), symbol)
    time.sleep(_REQUEST_DELAY)
    return articles


def format_news_report(symbol: str, company_name: str, pct_change: float, articles: list[dict]) -> str:
    """Return a human-readable block summarising the alert + news."""
    direction = "UP" if pct_change > 0 else "DOWN"
    lines = [
        "",
        f"{'='*70}",
        f"  ALERT: {symbol} ({company_name})",
        f"  Change: {pct_change:+.2f}%  [{direction}]",
        f"{'='*70}",
        f"  Related news ({len(articles)} article{'s' if len(articles) != 1 else ''}):",
    ]
    if articles:
        for i, art in enumerate(articles, 1):
            lines.append(f"  {i}. {art['title']}")
            lines.append(f"     Source: {art['source'] or 'Unknown'}  |  {art['published']}")
            lines.append(f"     {art['link']}")
    else:
        lines.append("  (No news articles found)")
    lines.append("")
    return "\n".join(lines)
