from qdrant_client.http.models import PointStruct
from ..qdrant_client import qdrant
from ..models import AnalysisPayload, TranscriptionPayload
import uuid

def store_analysis(url: str, score: float, is_legit: str, summary: str, links: List[str], embedding: List[float]):
    payload = AnalysisPayload(url=url, validity_score=score, is_legit=is_legit, summary=summary, links=links)
    point = PointStruct(id=str(uuid.uuid4()), vector=embedding, payload=payload.dict())
    qdrant.upsert(collection_name="analysis_results", points=[point])

def store_transcription(video_url: str, transcription: str, profile_check: Dict, score: float, embedding: List[float]):
    payload = TranscriptionPayload(video_url=video_url, transcription=transcription, profile_check=profile_check, validity_score=score)
    point = PointStruct(id=str(uuid.uuid4()), vector=embedding, payload=payload.dict())
    qdrant.upsert(collection_name="transcription_results", points=[point])

def search_similar(embedding: List[float], collection: str, limit: int = 5) -> List[Dict]:
    results = qdrant.search(collection_name=collection, query_vector=embedding, limit=limit)
    return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]