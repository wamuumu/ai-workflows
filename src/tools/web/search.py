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