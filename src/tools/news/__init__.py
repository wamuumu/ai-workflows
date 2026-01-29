"""
News Tools Module
=================

This module provides tools for retrieving news articles from
various sources including DuckDuckGo News and RSS feeds.

Main Responsibilities:
    - Fetch latest news via DuckDuckGo News API
    - Search RSS feeds for relevant articles

Key Dependencies:
    - feedparser: RSS/Atom feed parsing
    - ddgs: DuckDuckGo Search API wrapper
    - tools.decorator: For @tool registration

External APIs:
    - DuckDuckGo News: News article retrieval
    - Google News RSS: Default RSS feed source
"""

import feedparser

from ddgs import DDGS
from typing import TypedDict, List
from tools.decorator import tool


class NewsOutput(TypedDict):
    """
    Structured output for news retrieval.
    
    Attributes:
        news: List of news article dictionaries.
    """
    news: List[dict]


@tool(
    name="get_news",
    description="Fetch the latest news articles based on a query using DuckDuckGo News.",
    category="news",
)
def get_news(query: str, max_results: int = 5) -> NewsOutput:
    """
    Fetch news articles using DuckDuckGo News.
    
    Searches for recent news articles matching the query string
    via the DuckDuckGo News API.
    
    Args:
        query: Search query for news articles.
        max_results: Maximum articles to return (default: 5).
        
    Returns:
        NewsOutput with list of news article dictionaries.
        Returns error dict if search fails.
    """
    try:
        results = DDGS().news(query, max_results=max_results)
        return NewsOutput(news=results)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="search_news",
    description="Search for news articles using a query and RSS feed URL.",
    category="news",
)
def search_news(query: str, feed_url: str = "https://news.google.com/rss", max_results: int = 5) -> NewsOutput:
    """
    Search RSS feed for news matching a query.
    
    Parses the specified RSS feed and filters entries that contain
    the query string in their title or summary.
    
    Args:
        query: Search string to match in titles/summaries.
        feed_url: URL of RSS feed (default: Google News).
        max_results: Maximum articles to return (default: 5).
        
    Returns:
        NewsOutput with matching news articles.
    """
    feed = feedparser.parse(feed_url)
    results = []
    
    # Filter entries matching query in title or summary
    for entry in feed.entries:
        if query.lower() in entry.title.lower() or query.lower() in entry.summary.lower():
            results.append({"title": entry.title, "link": entry.link, "summary": entry.summary})
    
    return NewsOutput(news=results[:max_results])