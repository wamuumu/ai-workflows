import requests

from bs4 import BeautifulSoup
from ddgs import DDGS
from tools.decorator import tool

@tool(
    name="search_web",
    description="Search the web for a given query and return relevant results.",
    category="web"
)
def search_web(query: str, num_results: int = 5) -> dict:
    try:
        results = DDGS().text(query, max_results=num_results)
        
        return {
            "query": query,
            "results": results,
        }
    except Exception as e:
        return {"error": str(e)}
    
@tool(
    name="scrape_web",
    description="Scrape content from a given URL.",
    category="web",
)
def scrape_web(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'noscript']):
            tag.extract()
        text = soup.get_text(separator=' ')
        return " ".join(text.split())
    except requests.RequestException as e:
        return f"Error fetching URL {url}: {str(e)}"