"""
Web search module with Perplexity Sonar (primary) and Serper (fallback) support.
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

try:
    from backend.serper_client import serper_search
except ModuleNotFoundError:
    from serper_client import serper_search

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Initialize Perplexity client if API key is available
perplexity_client = None
if PERPLEXITY_API_KEY:
    perplexity_client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai"
    )


def search_with_perplexity(query: str, max_results: int = 5) -> Optional[List[Dict[str, str]]]:
    """
    Search using Perplexity Sonar model.

    Returns a list of search result snippets or None if unavailable/failed.
    Each snippet contains: title, snippet, link
    """
    if not perplexity_client:
        return None

    try:
        response = perplexity_client.chat.completions.create(
            model="sonar",
            messages=[
                {
                    "role": "system",
                    "content": "You are a search assistant. Provide factual information with citations.",
                },
                {
                    "role": "user",
                    "content": f"Search for: {query}",
                },
            ],
            max_tokens=800,
            temperature=0.2,
        )

        snippets: List[Dict[str, str]] = []

        search_results = getattr(response, "search_results", None)
        if search_results:
            for idx, item in enumerate(search_results[:max_results]):
                if isinstance(item, dict):
                    title = item.get("title") or f"Result {idx + 1}"
                    snippet = item.get("snippet") or ""
                    link = item.get("url") or ""
                else:
                    title = getattr(item, "title", f"Result {idx + 1}")
                    snippet = getattr(item, "snippet", "") or getattr(item, "text", "")
                    link = getattr(item, "url", "") or getattr(item, "link", "")

                if link:
                    snippets.append(
                        {
                            "title": title,
                            "snippet": snippet,
                            "link": link,
                        }
                    )

        if not snippets:
            raw_citations = getattr(response, "citations", None)
            if raw_citations:
                for idx, cit in enumerate(raw_citations[:max_results]):
                    url = cit if isinstance(cit, str) else str(cit)
                    snippets.append(
                        {
                            "title": f"Result {idx + 1}",
                            "snippet": "",
                            "link": url,
                        }
                    )

        if not snippets and response.choices:
            content = response.choices[0].message.content or ""
            if content.strip():
                snippets.append(
                    {
                        "title": f"Search result for: {query}",
                        "snippet": content[:500],
                        "link": "",
                    }
                )

        return snippets or None

    except Exception as e:
        print(f"[Perplexity] Search failed for query '{query}': {e}")
        return None


def search_with_serper(query: str, max_results: int = 5) -> Optional[List[Dict[str, str]]]:
    """
    Search using Serper as fallback.

    Returns a list of search result snippets or None if failed.
    """
    try:
        data = serper_search(query, num=max_results, search_type="search")
        snippets = []

        for item in data.get("organic", []):
            link = item.get("link")
            if not link:
                continue
            snippets.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": link,
            })

        return snippets if snippets else None

    except Exception as e:
        print(f"[Serper] Search failed for query '{query}': {e}")
        return None


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Unified web search function that tries Perplexity first, then falls back to Serper.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of search result dictionaries with 'title', 'snippet', and 'link' keys
    """
    # Try Perplexity first
    results = search_with_perplexity(query, max_results)

    if results:
        print(f"[WebSearch] Using Perplexity for query: {query}")
        return results

    # Fall back to Serper
    print(f"[WebSearch] Falling back to Serper for query: {query}")
    results = search_with_serper(query, max_results)

    if results:
        return results

    # If both fail, return empty list
    print(f"[WebSearch] Both Perplexity and Serper failed for query: {query}")
    return []


def multi_query_search(queries: List[str], max_results: int = 8) -> List[Dict[str, str]]:
    """
    Execute multiple search queries and combine results.

    Args:
        queries: List of search query strings
        max_results: Maximum total results to return (deduplicated)

    Returns:
        Deduplicated list of search results
    """
    all_snippets = []

    for query in queries:
        snippets = web_search(query, max_results=5)
        all_snippets.extend(snippets)

    # Deduplicate by link
    unique_snippets = {}
    for snippet in all_snippets:
        link = snippet.get("link")
        if link and link not in unique_snippets:
            unique_snippets[link] = snippet

    # Return up to max_results
    return list(unique_snippets.values())[:max_results]
