import yfinance as yf
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_ollama import OllamaEmbeddings
import time
import uuid

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "market_news"
EMBEDDING_MODEL = "nomic-embed-text"

# Initialize components
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

def init_qdrant():
    """Create the collection if it doesn't exist."""
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"Creating Qdrant collection: {COLLECTION_NAME}")
        # nomic-embed-text usually has 768 dimensions
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

def fetch_and_store_news(symbol="AAPL"):
    """Fetch news from yfinance and store in Qdrant."""
    print(f"Fetching news for {symbol}...")
    ticker = yf.Ticker(symbol)
    news = ticker.news
    
    if not news:
        print(f"No news found for {symbol}")
        return

    for item in news[:5]: # Store last 5 news items
        title = item.get('title', '')
        publisher = item.get('publisher', '')
        link = item.get('link', '')
        
        # Create a unique ID for the news item
        point_id = str(uuid.uuid4())
        
        # Generate embedding
        vector = embeddings.embed_query(title)
        
        # Store in Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": point_id,
                "vector": vector,
                "payload": {
                    "symbol": symbol,
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "timestamp": time.time()
                }
            }]
        )
        print(f"Stored: {title[:50]}...")

if __name__ == "__main__":
    init_qdrant()
    symbols = ["AAPL", "MSFT", "GOOGL"]
    for sym in symbols:
        fetch_and_store_news(sym)
    print("News ingestion complete!")
