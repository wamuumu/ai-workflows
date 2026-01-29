"""
Web Tools Module
================

This module provides web-related tools for searching the internet
and scraping content from web pages.

Main Responsibilities:
    - Perform web searches via DuckDuckGo
    - Scrape and extract text content from URLs

Key Dependencies:
    - requests: For HTTP requests
    - ddgs: DuckDuckGo Search API wrapper
    - bs4: BeautifulSoup for HTML parsing
    - tools.decorator: For @tool registration

External APIs:
    - DuckDuckGo Search: Web search results
"""

import requests

from typing import TypedDict, List
from ddgs import DDGS
from bs4 import BeautifulSoup
from tools.decorator import tool


class WebSearchOutput(TypedDict):
    """
    Structured output for web search results.
    
    Attributes:
        query: The search query that was executed.
        results: List of search result dictionaries.
    """
    query: str
    results: List[dict]


class ScrapeWebOutput(TypedDict):
    """
    Structured output for web scraping.
    
    Attributes:
        url: The URL that was scraped.
        content: Extracted text content from the page.
    """
    url: str
    content: str


@tool(
    name="search_web",
    description="Search the web for a given query and return relevant results.",
    category="web"
)
def search_web(query: str, num_results: int = 5) -> WebSearchOutput:
    """
    Search the web using DuckDuckGo.
    
    Performs a text search and returns the top results including
    titles, snippets, and URLs.
    
    Args:
        query: The search query string.
        num_results: Maximum results to return (default: 5).
        
    Returns:
        WebSearchOutput with query and list of result dictionaries.
        Returns error dict if search fails.
    """
    try:
        results = DDGS().text(query, max_results=num_results)
        return WebSearchOutput(query=query, results=list(results))
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="scrape_web",
    description="Scrape content from a given URL.",
    category="web",
)
def scrape_web(url: str) -> ScrapeWebOutput:
    """
    Scrape and extract text content from a web page.
    
    Fetches the page HTML, removes script/style elements,
    and extracts clean text content.
    
    Args:
        url: The URL to scrape.
        
    Returns:
        ScrapeWebOutput with URL and extracted text content.
        Returns error string if request fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove non-content elements
        for tag in soup(['script', 'style', 'noscript']):
            tag.extract()
        
        # Extract text with space separation
        text = soup.get_text(separator=' ')
        return ScrapeWebOutput(url=url, content=text)
    except requests.RequestException as e:
        return f"Error fetching URL {url}: {str(e)}"