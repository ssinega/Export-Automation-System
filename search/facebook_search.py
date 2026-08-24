"""
Facebook Search adapter for buyer discovery.

Facebook requires a valid Graph API access token and approved app
permissions to search pages or business profiles.  This module
provides a placeholder adapter so the application can run without
Facebook credentials.

When you have a valid access token, set FACEBOOK_ACCESS_TOKEN in .env
and uncomment the live implementation.
"""

from config import Config


def search_facebook(keyword: str = None, max_results: int = 10) -> list[dict]:
    """
    Search Facebook for potential buyers.

    Requires FACEBOOK_ACCESS_TOKEN in .env.
    Returns sample data when credentials are not configured.

    Args:
        keyword: Search term.
        max_results: Maximum results to return.

    Returns:
        List of buyer dicts.
    """
    keyword = keyword or Config.SEARCH_KEYWORD

    # Facebook Graph API requires approved app permissions.
    # Placeholder implementation for local testing.
    print("[Facebook Search] Access token not configured. "
          "Returning sample data for testing.")
    return _sample_results()


def _sample_results() -> list[dict]:
    """Return sample buyer data for local testing."""
    return [
        {
            "buyer_name": "Emma Wilson",
            "company_name": "Healing Vibes Shop",
            "email": "emma@healingvibes.com",
            "website": "https://facebook.com/healingvibes",
            "country": "Canada",
            "source_platform": "Facebook",
        },
        {
            "buyer_name": "Ravi Patel",
            "company_name": "Sound Bath Studio",
            "email": "ravi@soundbathstudio.in",
            "website": "https://facebook.com/soundbathstudio",
            "country": "India",
            "source_platform": "Facebook",
        },
    ]
