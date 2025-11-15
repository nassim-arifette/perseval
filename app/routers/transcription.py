from fastapi import APIRouter, Depends, HTTPException
from ..models import TranscriptionRequest, TranscriptionResponse
from ..services import llm_service, api_service, validation_service, vector_service
from ..qdrant_client import qdrant, TRANSCRIPTION_COLLECTION

router = APIRouter()

@router.post("/transcribe", response_model=TranscriptionResponse)
def transcribe_video(request: TranscriptionRequest):
    # Get video metadata via API
    metadata = api_service.get_video_metadata(request.video_url)
    
    # Transcribe using LLM/Whisper
    transcription = llm_service.transcribe_video(request.video_url)
    
    # Profile/partner checks
    profile_check = validation_service.check_profile(metadata["channel_id"])
    
    # Score and embed based on transcription and checks
    score, embedding = llm_service.score_and_embed_transcription(transcription, profile_check)
    
    # Store in Qdrant
    vector_service.store_transcription(request.video_url, transcription, profile_check, score, embedding)
    
    # Search for similar cases
    similar_cases = vector_service.search_similar(embedding, TRANSCRIPTION_COLLECTION, limit=3)
    
    return TranscriptionResponse(
        transcription=transcription, profile_check=profile_check, validity_score=score, similar_cases=similar_cases
    )