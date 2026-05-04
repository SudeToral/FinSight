from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 3):
    """
    Performs a live web search using DuckDuckGo.
    """
    print(f"[Web Search] Searching for: {query}")
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"{r['title']} - {r['body']}")
        return results
    except Exception as e:
        print(f"[Web Search] Error: {e}")
        return ["Search failed."]
