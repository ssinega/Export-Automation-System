"""
LinkedIn Search adapter for buyer discovery.

LinkedIn's API requires OAuth 2.0 and approved partner access for
people/company search.  This module provides a placeholder adapter so
the application can run without LinkedIn credentials.

When you have valid OAuth credentials, set LINKEDIN_CLIENT_ID and
LINKEDIN_CLIENT_SECRET in .env and implement the live search.
"""

from config import Config


def search_linkedin(keyword: str = None, max_results: int = 10) -> list[dict]:
    """
    Search LinkedIn for potential buyers.

    Requires LinkedIn API OAuth credentials in .env.
    Returns sample data when credentials are not configured.

    Args:
        keyword: Search term.
        max_results: Maximum results to return.

    Returns:
        List of buyer dicts.
    """
    keyword = keyword or Config.SEARCH_KEYWORD

    print("[LinkedIn Search] OAuth credentials not configured. "
          "Returning sample data for testing.")
    return _sample_results()


def _sample_results() -> list[dict]:
    """Return sample buyer data for local testing."""
    return [
        {
            "buyer_name": "David Lee",
            "company_name": "Mindful Imports Inc.",
            "email": "david@mindfulimports.com",
            "website": "https://linkedin.com/company/mindfulimports",
            "country": "Australia",
            "source_platform": "LinkedIn",
        },
        {
            "buyer_name": "Sophie Martin",
            "company_name": "Bien-Etre Distribution",
            "email": "sophie@bienetredist.fr",
            "website": "https://linkedin.com/company/bienetredist",
            "country": "France",
            "source_platform": "LinkedIn",
        },
    ]
