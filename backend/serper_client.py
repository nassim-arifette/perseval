"""
Thin Serper.dev client used for web reputation lookups.
"""

from __future__ import annotations

import os
from typing import Dict, Literal, TypedDict

import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

SERPER_ENDPOINTS = {
    "search": "https://google.serper.dev/search",
    "news": "https://google.serper.dev/news",
}


class SerperResult(TypedDict, total=False):
    title: str
    snippet: str
    link: str


def serper_search(
    query: str,
    num: int = 10,
    *,
    search_type: Literal["search", "news"] = "search",
) -> Dict:
    """
    Execute a Serper query and return the JSON payload.
    This helper keeps the rest of the app decoupled from raw HTTP bits.
    """
    if not SERPER_API_KEY:
        raise RuntimeError("Missing SERPER_API_KEY in .env (required for web reputation lookups).")

    endpoint = SERPER_ENDPOINTS.get(search_type, SERPER_ENDPOINTS["search"])
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "q": query,
        "num": num,
        "gl": "us",
        "hl": "en",
    }
    resp = requests.post(endpoint, headers=headers, json=body, timeout=20)
    resp.raise_for_status()
    return resp.json()
