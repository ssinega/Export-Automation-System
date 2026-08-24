"""
Report Generator – Produces campaign statistics and downloadable reports.

Generates:
  - Total emails
  - Successful sends
  - Failed sends
  - Duplicates skipped
  - Success rate
"""

import os
import io

import pandas as pd

from config import Config


def generate_report() -> dict:
    """
    Generate a campaign statistics report.

    Returns:
        Dict with all report metrics.
    """
    # Buyer counts
    total_buyers = 0
    business_count = 0
    individual_count = 0

    if os.path.exists(Config.BUYERS_CSV):
        buyers_df = pd.read_csv(Config.BUYERS_CSV)
        total_buyers = len(buyers_df)

    if os.path.exists(Config.BUSINESS_EMAILS_CSV):
        biz_df = pd.read_csv(Config.BUSINESS_EMAILS_CSV)
        business_count = len(biz_df)

    if os.path.exists(Config.INDIVIDUAL_EMAILS_CSV):
        ind_df = pd.read_csv(Config.INDIVIDUAL_EMAILS_CSV)
        individual_count = len(ind_df)

    # Send log analysis
    sent_count = 0
    failed_count = 0
    dry_run_count = 0
    duplicates_skipped = 0

    if os.path.exists(Config.SENT_LOG_CSV):
        try:
            log_df = pd.read_csv(Config.SENT_LOG_CSV)
            total_emails = len(log_df)

            status_counts = log_df["status"].value_counts().to_dict()
            sent_count = status_counts.get("sent", 0)
            failed_count = status_counts.get("failed", 0)
            dry_run_count = status_counts.get("dry-run", 0)
        except Exception as exc:
            print(f"[Report Generator] Error reading sent log: {exc}")
            total_emails = 0
    else:
        total_emails = 0

    # Calculate duplicates skipped: buyers whose emails are already in sent_log.csv
    if os.path.exists(Config.BUYERS_CSV) and os.path.exists(Config.SENT_LOG_CSV):
        try:
            buyers_df = pd.read_csv(Config.BUYERS_CSV)
            log_df = pd.read_csv(Config.SENT_LOG_CSV)
            if not buyers_df.empty and not log_df.empty and "email" in buyers_df.columns and "email" in log_df.columns:
                contacted_emails = set(
                    log_df[log_df["status"].isin(["sent", "dry-run"])]["email"]
                    .astype(str).str.lower().str.strip()
                )
                buyer_emails = buyers_df["email"].astype(str).str.lower().str.strip()
                duplicates_skipped = int(buyer_emails.isin(contacted_emails).sum())
        except Exception as exc:
            print(f"[Report Generator] Error calculating duplicates: {exc}")

    # Success rate
    attempted = sent_count + failed_count
    success_rate = (
        round((sent_count / attempted) * 100, 1) if attempted > 0 else 0
    )

    return {
        "total_buyers": total_buyers,
        "business_contacts": business_count,
        "individual_contacts": individual_count,
        "total_emails": total_emails,
        "successful": sent_count,
        "failed": failed_count,
        "dry_run": dry_run_count,
        "duplicates_skipped": duplicates_skipped,
        "success_rate": success_rate,
    }


def generate_csv_report() -> str:
    """
    Generate a CSV string of the campaign report.

    Returns:
        CSV-formatted string suitable for download.
    """
    report = generate_report()

    rows = [
        {"Metric": "Total Buyers", "Value": report["total_buyers"]},
        {"Metric": "Business Contacts", "Value": report["business_contacts"]},
        {"Metric": "Individual Contacts", "Value": report["individual_contacts"]},
        {"Metric": "Total Emails Processed", "Value": report["total_emails"]},
        {"Metric": "Successful Sends", "Value": report["successful"]},
        {"Metric": "Failed Sends", "Value": report["failed"]},
        {"Metric": "Dry Run Sends", "Value": report["dry_run"]},
        {"Metric": "Duplicates Skipped", "Value": report["duplicates_skipped"]},
        {"Metric": "Success Rate (%)", "Value": report["success_rate"]},
    ]

    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def get_sent_log_data() -> list[dict]:
    """
    Return the full sent log as a list of dicts for display.

    Returns:
        List of log entry dicts.
    """
    filepath = Config.SENT_LOG_CSV
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        return df.to_dict("records")
    return []
