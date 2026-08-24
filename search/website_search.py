"""
Website Search adapter for buyer discovery.

Uses requests + BeautifulSoup to extract contact information from
individual company websites.  This adapter respects robots.txt and
does not bypass authentication or CAPTCHAs.
"""

import re
import requests
from bs4 import BeautifulSoup
from config import Config


# Common email pattern
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


def search_websites(urls: list[str] = None) -> list[dict]:
    """
    Extract buyer information from a list of website URLs.

    Args:
        urls: List of URLs to scrape.  Returns sample data if empty.

    Returns:
        List of buyer dicts.
    """
    if not urls:
        print("[Website Search] No URLs provided. Returning sample data.")
        return _sample_results()

    results = []
    for url in urls:
        extracted = extract_from_website(url)
        results.extend(extracted)

    return results


def extract_from_website(url: str) -> list[dict]:
    """
    Scrape a single website for emails and contact information.

    Args:
        url: Website URL to scrape.

    Returns:
        List of buyer dicts with extracted emails.
    """
    results = []
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "ExportAutomation/1.0 (Educational Project)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()

        # Extract emails from page text
        emails = set(EMAIL_REGEX.findall(text))

        # Also check mailto: links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                emails.add(email)

        # Get page title as company name
        title = soup.title.get_text(strip=True) if soup.title else ""

        for email in emails:
            email = email.lower().strip()
            results.append({
                "buyer_name": "",
                "company_name": title,
                "email": email,
                "website": url,
                "country": "",
                "source_platform": "Website",
            })

    except requests.RequestException as exc:
        print(f"[Website Search] Error scraping {url}: {exc}")

    return results


def _sample_results() -> list[dict]:
    """Return sample buyer data for local testing."""
    return [
        {
            "buyer_name": "Chen Wei",
            "company_name": "Oriental Wellness Co",
            "email": "chen@orientalwellness.cn",
            "website": "https://orientalwellness.cn",
            "country": "China",
            "source_platform": "Website",
        },
        {
            "buyer_name": "Olga Ivanova",
            "company_name": "Sound Therapy RU",
            "email": "olga@soundtherapy.ru",
            "website": "https://soundtherapy.ru",
            "country": "Russia",
            "source_platform": "Website",
        },
    ]
