"""Helpers for building search queries used across trust computations."""

from typing import List, Optional

from backend.web_search import multi_query_search


def fetch_snippets_from_queries(queries: List[str], max_results: int = 8) -> List[dict]:
    """Query Perplexity/Serper via the shared helper for a set of search phrases."""
    return multi_query_search(queries, max_results=max_results)


def get_company_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" reviews',
        f'"{name}" scam',
        f'"{name}" lawsuit',
        f'"{name}" complaints',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_product_snippets(name: str, max_results: int = 8) -> List[dict]:
    queries = [
        f'"{name}" product reviews',
        f'"{name}" complaints',
        f'"{name}" scam',
        f'"{name}" safety issues',
    ]
    return fetch_snippets_from_queries(queries, max_results)


def get_influencer_snippets(
    handle: str,
    full_name: Optional[str],
    max_results: int = 8,
) -> List[dict]:
    normalized_handle = handle.lstrip("@")
    queries = [
        f'"{normalized_handle}" scam',
        f'"{normalized_handle}" controversy',
        f'"{normalized_handle}" lawsuit',
    ]
    if full_name:
        queries += [
            f'"{full_name}" scam',
            f'"{full_name}" controversy',
        ]
    return fetch_snippets_from_queries(queries, max_results)

