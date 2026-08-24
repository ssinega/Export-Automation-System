"""
Directory Search adapter for buyer discovery.

Searches online business directories for potential buyers of
Singing Bowls and related products.  Uses requests + BeautifulSoup
for public directory pages.

This adapter provides sample data by default so the application
can run locally without depending on third-party directory sites.
"""

import requests
from bs4 import BeautifulSoup
from config import Config


def search_directories(keyword: str = None, max_results: int = 10) -> list[dict]:
    """
    Search online business directories for potential buyers.

    Args:
        keyword: Search term (defaults to Config.SEARCH_KEYWORD).
        max_results: Maximum results to return.

    Returns:
        List of buyer dicts.
    """
    keyword = keyword or Config.SEARCH_KEYWORD

    # In a production deployment you would iterate over a list of
    # directory URLs and scrape them with BeautifulSoup.
    # For local testing we return sample data.
    print("[Directory Search] Using sample data for testing.")
    return _sample_results()


def scrape_directory_page(url: str) -> list[dict]:
    """
    Scrape a single directory page for buyer information.

    Args:
        url: The URL of the directory page.

    Returns:
        List of extracted buyer dicts.
    """
    results = []
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "ExportAutomation/1.0 (Educational Project)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Generic extraction – adapt selectors per directory site
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("http") and "contact" in href.lower():
                results.append({
                    "buyer_name": "",
                    "company_name": link.get_text(strip=True),
                    "email": "",
                    "website": href,
                    "country": "",
                    "source_platform": "Directory",
                })
    except requests.RequestException as exc:
        print(f"[Directory Search] Error scraping {url}: {exc}")

    return results


def _sample_results() -> list[dict]:
    """Return sample buyer data for local testing."""
    return [
        {
            "buyer_name": "James Brown",
            "company_name": "Holistic Products Ltd",
            "email": "james@holisticproducts.co.uk",
            "website": "https://holisticproducts.co.uk",
            "country": "UK",
            "source_platform": "Directory",
        },
        {
            "buyer_name": "Anna Kowalski",
            "company_name": "Zen Market Europe",
            "email": "anna@zenmarket.eu",
            "website": "https://zenmarket.eu",
            "country": "Poland",
            "source_platform": "Directory",
        },
    ]
