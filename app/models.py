from pydantic import BaseModel
from typing import List, Dict, Optional
from qdrant_client.http.models import PointStruct

# Pydantic Models for API
class AnalysisRequest(BaseModel):
    url: str

class AnalysisResponse(BaseModel):
    validity_score: float
    is_legit: str
    summary: str
    links: List[str]
    similar_cases: Optional[List[Dict]]  # From vector search

class TranscriptionRequest(BaseModel):
    video_url: str

class TranscriptionResponse(BaseModel):
    transcription: str
    profile_check: Dict
    validity_score: float
    similar_cases: Optional[List[Dict]]  # From vector search

# Qdrant Payload Schemas (for metadata)
class AnalysisPayload(BaseModel):
    url: str
    validity_score: float
    is_legit: str
    summary: str
    links: List[str]

class TranscriptionPayload(BaseModel):
    video_url: str
    transcription: str
    profile_check: Dict
    validity_score: float