from fastapi import FastAPI
from .routers import analysis, transcription
from .qdrant_client import create_collections

# Create Qdrant collections on startup
create_collections()

app = FastAPI(title="Influencer Trust SaaS", version="1.0.0")

app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(transcription.router, prefix="/api/v1", tags=["transcription"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Influencer Trust SaaS"}