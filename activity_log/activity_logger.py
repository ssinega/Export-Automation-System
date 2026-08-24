"""
Activity Logger – Maintains CSV logs for all automation activities.

Handles:
  - Initializing CSV files with proper headers on first run
  - Appending send log records
  - Reading log data for reporting
"""

import os
from datetime import datetime

import pandas as pd

from config import Config


def init_csv_files():
    """
    Create all required CSV files with proper headers if they don't exist.

    This should be called at application startup to prevent crashes
    from missing files.
    """
    os.makedirs(Config.DATA_DIR, exist_ok=True)

    csv_files = {
        Config.BUYERS_CSV: Config.BUYER_HEADERS,
        Config.BUSINESS_EMAILS_CSV: ["email_address"],
        Config.INDIVIDUAL_EMAILS_CSV: ["email_address"],
        Config.SENT_LOG_CSV: Config.SENT_LOG_HEADERS,
    }

    for filepath, headers in csv_files.items():
        if not os.path.exists(filepath):
            df = pd.DataFrame(columns=headers)
            df.to_csv(filepath, index=False)
            print(f"[Logger] Created {filepath}")


def log_activity(email: str, status: str, subject: str = ""):
    """
    Append a record to the sent log.

    Args:
        email: Recipient email address.
        status: One of 'sent', 'failed', 'dry-run'.
        subject: Email subject line.
    """
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    filepath = Config.SENT_LOG_CSV

    record = pd.DataFrame([{
        "email": email.lower().strip(),
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "subject": subject,
    }])

    if os.path.exists(filepath):
        record.to_csv(filepath, mode="a", header=False, index=False)
    else:
        record.to_csv(filepath, index=False)


def get_sent_log() -> pd.DataFrame:
    """
    Load the complete sent log.

    Returns:
        DataFrame with columns: email, timestamp, status, subject.
    """
    filepath = Config.SENT_LOG_CSV
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return pd.DataFrame(columns=Config.SENT_LOG_HEADERS)


def get_sent_emails() -> set:
    """
    Return a set of all emails that have been sent to.

    Returns:
        Set of lowercase email strings.
    """
    log = get_sent_log()
    if log.empty:
        return set()
    return set(log["email"].str.lower().str.strip())


def count_by_status() -> dict:
    """
    Count log entries grouped by status.

    Returns:
        Dict mapping status → count (e.g. {'sent': 5, 'failed': 1}).
    """
    log = get_sent_log()
    if log.empty:
        return {"sent": 0, "failed": 0, "dry-run": 0}

    counts = log["status"].value_counts().to_dict()
    return {
        "sent": counts.get("sent", 0),
        "failed": counts.get("failed", 0),
        "dry-run": counts.get("dry-run", 0),
    }
