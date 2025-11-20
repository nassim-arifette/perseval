"""Helpers for building search queries used across trust computations."""

from typing import List, Optional

from backend.app.services.web_search import multi_query_search


def fetch_snippets_from_queries(queries: List[str], max_results: int = 8) -> List[dict]:
    """Query Perplexity/Serper via the shared helper for a set of search phrases."""
    return multi_query_search(queries, max_results=max_results)


def get_company_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" reviews',
        f'"{name}" scam lawsuit complaints',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_product_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" product reviews',
        f'"{name}" complaints scam safety issues',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_influencer_snippets(
    handle: str,
    full_name: Optional[str],
    max_results: int = 8,
) -> List[dict]:
    """
    Fetch comprehensive web snippets about an influencer's reputation.
    Uses Perplexity (preferred) or Serper for web searches.
    """
    normalized_handle = handle.lstrip("@")
    queries = [
        f'"{normalized_handle}" influencer scam controversy',
        f'"{normalized_handle}" sponsored posts disclosure',
    ]

    # Add full name search if available for better context
    if full_name and full_name.strip():
        queries.append(f'"{full_name}" influencer reputation reviews')

    return fetch_snippets_from_queries(queries, max_results)
