from qdrant_client import QdrantClient
import numpy as np

client = QdrantClient(host="localhost", port=6333)
print(f"Client type: {type(client)}")
print(f"Has search attribute: {hasattr(client, 'search')}")
print(f"Attributes: {[a for a in dir(client) if not a.startswith('_')]}")
