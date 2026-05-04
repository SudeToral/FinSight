from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings
from agents.state import AgentState
from tools.search_tool import web_search

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "market_news"
EMBEDDING_MODEL = "nomic-embed-text"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

def news_researcher_node(state: AgentState) -> AgentState:
    """
    Retrieves relevant news from Qdrant and supplements with Live Web Search.
    """
    symbol = state.get("symbol", "AAPL")
    print(f"[News Researcher] Searching news for {symbol}...")
    
    # 1. Search in Qdrant (RAG)
    query_vector = embeddings.embed_query(f"Latest news about {symbol} stock market")
    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter={
            "must": [
                {"key": "symbol", "match": {"value": symbol}}
            ]
        },
        limit=3
    ).points
    
    headlines = [hit.payload["title"] for hit in search_result]
    
    # 2. Supplemental Live Web Search
    # WHY: Qdrant might have stale data. Live search ensures the latest info.
    print(f"[News Researcher] Performing supplemental live web search for {symbol}...")
    web_results = web_search(f"latest {symbol} stock market news today", max_results=2)
    
    # Combine results
    combined_headlines = headlines + web_results
    
    if not combined_headlines:
        print(f"[News Researcher] No news found for {symbol}")
        combined_headlines = ["No recent news available."]
    else:
        print(f"[News Researcher] Found {len(combined_headlines)} news items (RAG + Web).")
        
    return {
        "news_headlines": combined_headlines,
        "news_researched": True
    }
