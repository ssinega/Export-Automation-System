"""
Google Search adapter for buyer discovery.

Uses Google Custom Search JSON API when GOOGLE_API_KEY and GOOGLE_CSE_ID
are configured.  Falls back to a safe placeholder when credentials are
unavailable so the rest of the application can still be tested.
"""

import requests
from config import Config


def search_google(keyword: str = None, max_results: int = 10) -> list[dict]:
    """
    Search Google for potential buyers using the Custom Search API.

    Args:
        keyword: Search term (defaults to Config.SEARCH_KEYWORD).
        max_results: Maximum number of results to return.

    Returns:
        List of dicts with keys: buyer_name, company_name, email,
        website, country, source_platform.
    """
    keyword = keyword or Config.SEARCH_KEYWORD
    results = []

    api_key = Config.GOOGLE_API_KEY
    cse_id = Config.GOOGLE_CSE_ID

    if not api_key or not cse_id:
        print("[Google Search] API key or CSE ID not configured. "
              "Returning sample data for testing.")
        return _sample_results()

    queries = Config.SEARCH_QUERIES
    for query in queries:
        full_query = f"{keyword} {query}"
        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": api_key,
                    "cx": cse_id,
                    "q": full_query,
                    "num": min(max_results, 10),
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                results.append({
                    "buyer_name": "",
                    "company_name": item.get("title", ""),
                    "email": "",
                    "website": item.get("link", ""),
                    "country": "",
                    "source_platform": "Google",
                })
        except requests.RequestException as exc:
            print(f"[Google Search] Error searching '{full_query}': {exc}")
            continue

    return results


def _sample_results() -> list[dict]:
    """Return sample buyer data for local testing."""
    return [
        {
            "buyer_name": "John Smith",
            "company_name": "ABC Wellness Store",
            "email": "john@abcwellness.com",
            "website": "https://abcwellness.com",
            "country": "USA",
            "source_platform": "Google",
        },
        {
            "buyer_name": "Maria Garcia",
            "company_name": "Zen Imports EU",
            "email": "maria@zenimports.eu",
            "website": "https://zenimports.eu",
            "country": "Germany",
            "source_platform": "Google",
        },
        {
            "buyer_name": "Akira Tanaka",
            "company_name": "Harmony Sound Co",
            "email": "akira@harmonysound.co.jp",
            "website": "https://harmonysound.co.jp",
            "country": "Japan",
            "source_platform": "Google",
        },
        {
            "buyer_name": "Sarah Johnson",
            "company_name": "Meditation Hub",
            "email": "sarah@meditationhub.com",
            "website": "https://meditationhub.com",
            "country": "UK",
            "source_platform": "Google",
        },
        {
            "buyer_name": "Lucas Fernandes",
            "company_name": "Spirit World Dist.",
            "email": "lucas@spiritworld.com.br",
            "website": "https://spiritworld.com.br",
            "country": "Brazil",
            "source_platform": "Google",
        },
    ]
