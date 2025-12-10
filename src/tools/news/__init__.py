import feedparser
from ddgs import DDGS
from tools.decorator import tool

@tool(
    name="get_news",
    description="Fetch the latest news articles based on a query using DuckDuckGo News.",
    category="news",
)
def get_news(query: str, max_results: int = 5) -> list:
    try:
        results = DDGS().news(query, max_results=max_results)
        return results[:max_results]
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="search_news",
    description="Search for news articles using a query and RSS feed URL.",
    category="news",
)
def search_news(query: str, feed_url: str = "https://news.google.com/rss", max_results: int = 5) -> list:
    feed = feedparser.parse(feed_url)
    results = []
    for entry in feed.entries:
        if query.lower() in entry.title.lower() or query.lower() in entry.summary.lower():
            results.append({"title": entry.title, "link": entry.link, "summary": entry.summary})
    return results[:max_results]