from pydantic import BaseSettings

class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"  # Local Qdrant; change to cloud URL
    qdrant_api_key: str = ""  # For cloud instances
    elevenlabs_api_key: str
    youtube_api_key: str  # For YouTube Data API
    # Add more keys as needed (e.g., Instagram Graph API)

    class Config:
        env_file = ".env"

settings = Settings()