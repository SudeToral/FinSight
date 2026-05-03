from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings
from agents.state import AgentState

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "market_news"
EMBEDDING_MODEL = "nomic-embed-text"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

def news_researcher_node(state: AgentState) -> AgentState:
    """
    Retrieves relevant news for the symbol from Qdrant.
    """
    symbol = state.get("symbol", "AAPL")
    print(f"[News Researcher] Searching news for {symbol}...")
    
    # Query vector
    query_vector = embeddings.embed_query(f"Latest news about {symbol} stock market")
    
    # Search in Qdrant
    # Filter by symbol for precision
    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter={
            "must": [
                {"key": "symbol", "match": {"value": symbol}}
            ]
        },
        limit=3
    )
    
    headlines = [hit.payload["title"] for hit in search_result]
    
    if not headlines:
        print(f"[News Researcher] No news found in DB for {symbol}")
        headlines = ["No recent news available."]
    else:
        print(f"[News Researcher] Found {len(headlines)} relevant headlines.")
        
    return {"news_headlines": headlines}
