"""Shared configuration helpers for the backend."""

import os

from dotenv import load_dotenv

load_dotenv()

API_TITLE = "Scam Checker API"

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise RuntimeError("Missing MISTRAL_API_KEY in .env")

