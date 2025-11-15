from fastapi import APIRouter, Depends, HTTPException
from ..models import AnalysisRequest, AnalysisResponse
from ..services import llm_service, validation_service, vector_service
from ..qdrant_client import qdrant, ANALYSIS_COLLECTION

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_content(request: AnalysisRequest):
    # Fetch content from URL (placeholder; use httpx for real fetching)
    content = "Sample content from URL"  # Replace with actual fetch
    
    # LLM scoring and embedding
    score, summary, embedding = llm_service.score_and_embed(content)
    is_legit = "legit" if score > 0.7 else "not legit"
    
    # Validation checks (e.g., profiles)
    links = validation_service.get_related_links(request.url)
    
    # Store in Qdrant
    vector_service.store_analysis(request.url, score, is_legit, summary, links, embedding)
    
    # Search for similar cases (RAG)
    similar_cases = vector_service.search_similar(embedding, ANALYSIS_COLLECTION, limit=3)
    
    return AnalysisResponse(
        validity_score=score, is_legit=is_legit, summary=summary, links=links, similar_cases=similar_cases
    )