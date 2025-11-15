import openai
import numpy as np
from ..config import settings

openai.api_key = settings.openai_api_key

def get_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return response['data'][0]['embedding']

def score_validity(content: str) -> tuple[float, str]:
    # Use GPT to score and summarize
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Score the legitimacy of this content on a scale of 0-1 and provide a summary. Check for fraud indicators like undisclosed sponsorships."},
            {"role": "user", "content": content}
        ]
    )
    # Parse response (simplified; add parsing logic)
    score = 0.8  # Placeholder
    summary = "This appears legitimate based on analysis."
    return score, summary

def score_and_embed(content: str) -> tuple[float, str, List[float]]:
    score, summary = score_validity(content)
    embedding = get_embedding(content)
    return score, summary, embedding

def transcribe_video(video_url: str) -> str:
    # Use Whisper for transcription (assume video file; adapt for URL)
    # Placeholder: In reality, download video and transcribe
    return "Transcribed text from video."

def score_and_embed_transcription(transcription: str, profile_check: dict) -> tuple[float, List[float]]:
    # Combine for scoring
    prompt = f"Transcription: {transcription}\nProfile: {profile_check}\nScore legitimacy 0-1."
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    score = 0.75  # Placeholder
    combined_text = transcription + str(profile_check)
    embedding = get_embedding(combined_text)
    return score, embedding