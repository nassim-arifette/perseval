from qdrant_client import QdrantClient
from .config import settings

# Initialize Qdrant client
qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)

# Collection names
ANALYSIS_COLLECTION = "analysis_results"
TRANSCRIPTION_COLLECTION = "transcription_results"

def create_collections():
    # Create collections if they don't exist (vector size: 1536 for OpenAI embeddings)
    qdrant.recreate_collection(
        collection_name=ANALYSIS_COLLECTION,
        vectors_config={"size": 1536, "distance": "Cosine"}
    )
    qdrant.recreate_collection(
        collection_name=TRANSCRIPTION_COLLECTION,
        vectors_config={"size": 1536, "distance": "Cosine"}
    )