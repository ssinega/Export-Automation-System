"""
API 3 – EXPORT Automation System
Main Pipeline (CLI)

Orchestrates the full automation workflow:
  Load Config → Search → Extract → Validate → Save →
  Deduplicate → Classify → Queue → Auth Gmail →
  Attach → Personalize → Send → Log → Report
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from activity_log.activity_logger import init_csv_files
from search.google_search import search_google
from search.facebook_search import search_facebook
from search.linkedin_search import search_linkedin
from search.directory_search import search_directories
from search.website_search import search_websites
from extraction.data_extractor import process_search_results, save_buyers, load_buyers
from validation.email_validator import is_valid_email
from classifier import classify_emails, load_classified
from outreach.gmail_sender import GmailSender
from outreach.attachment_handler import check_presentation_exists
from reports.report_generator import generate_report


def main():
    """Execute the full export automation pipeline."""

    print("\n" + "=" * 56)
    print("   API 3 – EXPORT Automation System – CLI Pipeline")
    print("=" * 56 + "\n")

    # ── Step 1: Load configuration ────────────────────────
    print("[1/10] Loading configuration...")
    warnings = Config.validate()
    for w in warnings:
        print(f"  ⚠ {w}")

    if Config.DRY_RUN:
        print("  🔒 DRY RUN mode is active – no emails will be sent.")

    # ── Step 2: Initialize CSV files ──────────────────────
    print("\n[2/10] Initializing data files...")
    init_csv_files()

    # ── Step 3: Search configured sources ─────────────────
    print("\n[3/10] Searching for buyers...")
    all_results = []

    try:
        print("  → Google Search...")
        all_results.extend(search_google())
    except Exception as exc:
        print(f"  ✗ Google Search failed: {exc}")

    try:
        print("  → Facebook Search...")
        all_results.extend(search_facebook())
    except Exception as exc:
        print(f"  ✗ Facebook Search failed: {exc}")

    try:
        print("  → LinkedIn Search...")
        all_results.extend(search_linkedin())
    except Exception as exc:
        print(f"  ✗ LinkedIn Search failed: {exc}")

    try:
        print("  → Directory Search...")
        all_results.extend(search_directories())
    except Exception as exc:
        print(f"  ✗ Directory Search failed: {exc}")

    try:
        print("  → Website Search...")
        all_results.extend(search_websites())
    except Exception as exc:
        print(f"  ✗ Website Search failed: {exc}")

    print(f"  Found {len(all_results)} raw results.")

    # ── Step 4: Extract & validate ────────────────────────
    print("\n[4/10] Extracting and validating buyer records...")
    processed = process_search_results(all_results)

    # Validate emails
    valid_records = []
    invalid_count = 0
    for record in processed:
        if is_valid_email(record.get("email", "")):
            valid_records.append(record)
        else:
            invalid_count += 1

    print(f"  Valid: {len(valid_records)}, Invalid: {invalid_count}")

    # ── Step 5: Save to buyers.csv ────────────────────────
    print("\n[5/10] Saving buyers to CSV...")
    saved = save_buyers(valid_records)
    print(f"  {saved} new buyers saved.")

    # ── Step 6: AI Classification ─────────────────────────
    print("\n[6/10] Running AI classification...")
    buyers = load_buyers()
    if buyers.empty:
        print("  No buyers to classify.")
    else:
        records = buyers.to_dict("records")
        result = classify_emails(records)
        print(f"  Business: {len(result['business'])}")
        print(f"  Individual: {len(result['individual'])}")

    # ── Step 7: Check presentation ────────────────────────
    print("\n[7/10] Checking presentation attachment...")
    pres = check_presentation_exists()
    if pres["exists"]:
        print(f"  ✓ Found: {pres['path']}")
    else:
        print(f"  ✗ {pres['error']}")
        print("  Campaign cannot proceed without presentation.")
        if not Config.DRY_RUN:
            print("\nPipeline stopped. Add the presentation file and re-run.")
            return

    # ── Step 8: Select audience & create queue ────────────
    print("\n[8/10] Building outreach queue...")
    recipients = load_classified("all")
    print(f"  Queue size: {len(recipients)}")

    if not recipients:
        print("  No recipients in queue. Pipeline complete.")
        _print_report()
        return

    # ── Step 9: Send campaign ─────────────────────────────
    print("\n[9/10] Sending email campaign...")

    subject = "Singing Bowls – Export Partnership Opportunity"
    body = (
        "Hello {{name}},\n\n"
        "We are an export supplier of high-quality Singing Bowls "
        "from Nepal.\n\n"
        "We would like to explore whether our products may be "
        "relevant to {{company}}.\n\n"
        "Please find our company presentation attached.\n\n"
        "Regards,\n"
        "Export Sales Team"
    )

    sender = GmailSender()
    results = sender.send_campaign(recipients, subject, body, attach=pres["exists"])

    if "error" in results:
        print(f"  ✗ {results['error']}")
    else:
        print(f"  Sent: {results.get('sent', 0)}")
        print(f"  Dry-run: {results.get('dry_run', 0)}")
        print(f"  Failed: {results.get('failed', 0)}")
        print(f"  Duplicates skipped: {results.get('skipped_duplicate', 0)}")

    # ── Step 10: Generate report ──────────────────────────
    _print_report()

    print("\n✓ Pipeline complete.\n")


def _print_report():
    """Print campaign report summary."""
    print("\n[10/10] Campaign Report:")
    report = generate_report()
    print(f"  Total Buyers:       {report['total_buyers']}")
    print(f"  Business Contacts:  {report['business_contacts']}")
    print(f"  Individual Contacts:{report['individual_contacts']}")
    print(f"  Emails Processed:   {report['total_emails']}")
    print(f"  Successful:         {report['successful']}")
    print(f"  Failed:             {report['failed']}")
    print(f"  Dry-run:            {report['dry_run']}")
    print(f"  Success Rate:       {report['success_rate']}%")


if __name__ == "__main__":
    main()
