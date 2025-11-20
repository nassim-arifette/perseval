"""Backward-compatible configuration module."""

from backend.app.core.settings import Settings, get_settings

settings = get_settings()
API_TITLE = settings.api_title
MISTRAL_API_KEY = settings.mistral_api_key

__all__ = ["Settings", "get_settings", "settings", "API_TITLE", "MISTRAL_API_KEY"]
