import concurrent.futures
from duckduckgo_search import DDGS

def _do_search(query: str, max_results: int):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(f"{r['title']} - {r['body']}")
    return results

def web_search(query: str, max_results: int = 3):
    """
    Performs a live web search using DuckDuckGo with a timeout.
    """
    print(f"[Web Search] Searching for: {query}")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_search, query, max_results)
            # Timeout after 5 seconds to prevent hanging
            return future.result(timeout=5.0)
    except concurrent.futures.TimeoutError:
        print("[Web Search] Error: Search timed out after 5 seconds.")
        return ["Search timed out."]
    except Exception as e:
        print(f"[Web Search] Error: {e}")
        return ["Search failed."]
