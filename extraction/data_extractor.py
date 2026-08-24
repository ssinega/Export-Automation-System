"""
Data Extractor – Extracts, normalizes, and deduplicates buyer records.

Processes raw search results from all adapters into a unified schema
and persists them to buyers.csv.
"""

import os
import re
import pandas as pd
from config import Config

# Regex for email extraction from raw text / HTML
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# File extensions to reject (image / binary files masquerading as email)
INVALID_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar",
}


def extract_emails_from_text(text: str) -> list[str]:
    """
    Extract email addresses from raw text using regex.

    Args:
        text: Raw text content.

    Returns:
        List of normalised, unique email addresses.
    """
    raw_emails = EMAIL_REGEX.findall(text)
    cleaned = set()
    for email in raw_emails:
        email = email.lower().strip()
        # Skip emails that end with image/file extensions
        _, ext = os.path.splitext(email)
        if ext.lower() in INVALID_EXTENSIONS:
            continue
        cleaned.add(email)
    return list(cleaned)


def normalize_buyer_record(record: dict) -> dict:
    """
    Normalize a single buyer record to the standard schema.

    Args:
        record: Dict with buyer data (may have missing keys).

    Returns:
        Normalized dict with all required keys.
    """
    return {
        "buyer_name": str(record.get("buyer_name", "")).strip(),
        "company_name": str(record.get("company_name", "")).strip(),
        "email": str(record.get("email", "")).strip().lower(),
        "website": str(record.get("website", "")).strip(),
        "country": str(record.get("country", "")).strip(),
        "source_platform": str(record.get("source_platform", "")).strip(),
    }


def deduplicate_records(records: list[dict]) -> list[dict]:
    """
    Remove duplicate records based on email address.

    Args:
        records: List of buyer dicts.

    Returns:
        Deduplicated list.
    """
    seen_emails = set()
    unique = []
    for record in records:
        email = record.get("email", "").lower().strip()
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique.append(record)
    return unique


def process_search_results(raw_results: list[dict]) -> list[dict]:
    """
    Full extraction pipeline: normalize → deduplicate → filter empty emails.

    Args:
        raw_results: Combined results from all search adapters.

    Returns:
        Clean, deduplicated list of buyer records.
    """
    normalized = [normalize_buyer_record(r) for r in raw_results]
    # Remove records without email
    with_email = [r for r in normalized if r["email"]]
    # Deduplicate
    unique = deduplicate_records(with_email)
    return unique


def save_buyers(records: list[dict], append: bool = True) -> int:
    """
    Save buyer records to buyers.csv.

    Args:
        records: List of buyer dicts.
        append: If True, append to existing file; otherwise overwrite.

    Returns:
        Number of new records saved.
    """
    try:
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        filepath = Config.BUYERS_CSV

        if append and os.path.exists(filepath):
            existing_df = pd.read_csv(filepath)
            existing_emails = set(existing_df["email"].str.lower().str.strip())
            new_records = [r for r in records if r["email"] not in existing_emails]
        else:
            new_records = records

        if not new_records:
            return 0

        new_df = pd.DataFrame(new_records, columns=Config.BUYER_HEADERS)

        if append and os.path.exists(filepath):
            new_df.to_csv(filepath, mode="a", header=False, index=False)
        else:
            new_df.to_csv(filepath, index=False)

        return len(new_records)
    except (PermissionError, OSError) as exc:
        print(f"[Extractor] Warning: Could not save buyers to CSV (read-only filesystem): {exc}")
        return 0
    except Exception as exc:
        print(f"[Extractor] Error saving buyers: {exc}")
        return 0


def load_buyers() -> pd.DataFrame:
    """
    Load buyers from CSV.

    Returns:
        DataFrame with buyer records.
    """
    filepath = Config.BUYERS_CSV
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame(columns=Config.BUYER_HEADERS)
