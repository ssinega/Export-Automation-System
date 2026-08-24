"""
API 3 – EXPORT Automation System
Test Suite

Tests cover:
  - Email validation
  - Duplicate detection
  - CSV upload processing
  - AI classification (local fallback)
  - Dry-run sending
  - Attachment existence and PDF validation
  - CSV Initialization
  - Report Generation
"""

import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from validation.email_validator import is_valid_email, validate_email_list
from extraction.data_extractor import (
    extract_emails_from_text,
    normalize_buyer_record,
    deduplicate_records,
    process_search_results,
    save_buyers,
)
from classifier import _classify_local, load_classified
from outreach.attachment_handler import check_presentation_exists
from outreach.gmail_sender import GmailSender
from reports.report_generator import generate_report
from activity_log.activity_logger import init_csv_files

class TestBase(unittest.TestCase):
    """Base class for system tests that isolates configuration and database paths."""

    def setUp(self):
        # Create temporary data directory
        self.test_dir = tempfile.mkdtemp()
        self.original_data_dir = config.Config.DATA_DIR
        self.original_buyers = config.Config.BUYERS_CSV
        self.original_biz = config.Config.BUSINESS_EMAILS_CSV
        self.original_ind = config.Config.INDIVIDUAL_EMAILS_CSV
        self.original_sent = config.Config.SENT_LOG_CSV
        self.original_presentation = config.Config.PRESENTATION_PATH
        self.original_dry_run = config.Config.DRY_RUN

        # Patch configuration paths
        config.Config.DATA_DIR = self.test_dir
        config.Config.BUYERS_CSV = os.path.join(self.test_dir, "buyers.csv")
        config.Config.BUSINESS_EMAILS_CSV = os.path.join(self.test_dir, "business_emails.csv")
        config.Config.INDIVIDUAL_EMAILS_CSV = os.path.join(self.test_dir, "individual_emails.csv")
        config.Config.SENT_LOG_CSV = os.path.join(self.test_dir, "sent_log.csv")
        config.Config.DRY_RUN = True

        # Write a dummy presentation file
        self.test_pdf = os.path.join(self.test_dir, "test_presentation.pdf")
        with open(self.test_pdf, "wb") as f:
            f.write(b"%PDF-1.4 mock pdf content %%EOF")
        config.Config.PRESENTATION_PATH = self.test_pdf

    def tearDown(self):
        # Restore configuration paths
        config.Config.DATA_DIR = self.original_data_dir
        config.Config.BUYERS_CSV = self.original_buyers
        config.Config.BUSINESS_EMAILS_CSV = self.original_biz
        config.Config.INDIVIDUAL_EMAILS_CSV = self.original_ind
        config.Config.SENT_LOG_CSV = self.original_sent
        config.Config.PRESENTATION_PATH = self.original_presentation
        config.Config.DRY_RUN = self.original_dry_run

        # Remove temporary directory
        try:
            shutil.rmtree(self.test_dir)
        except Exception:
            pass


class TestEmailValidation(TestBase):
    """Test email validation logic."""

    def test_valid_email(self):
        self.assertTrue(is_valid_email("valid@example.org"))

    def test_valid_email_subdomain(self):
        self.assertTrue(is_valid_email("user@mail.company.com"))

    def test_valid_email_dots_in_local(self):
        self.assertTrue(is_valid_email("first.last@domain.com"))

    def test_invalid_missing_at(self):
        self.assertFalse(is_valid_email("invalidemail.com"))

    def test_invalid_missing_domain(self):
        self.assertFalse(is_valid_email("invalid@"))

    def test_invalid_plain_text(self):
        self.assertFalse(is_valid_email("abc"))

    def test_invalid_empty(self):
        self.assertFalse(is_valid_email(""))

    def test_invalid_none(self):
        self.assertFalse(is_valid_email(None))

    def test_invalid_image_extension(self):
        self.assertFalse(is_valid_email("photo@example.png"))

    def test_invalid_too_long(self):
        long_email = "a" * 250 + "@example.com"
        self.assertFalse(is_valid_email(long_email))

    def test_invalid_no_tld(self):
        self.assertFalse(is_valid_email("user@localhost"))

    def test_invalid_short_tld(self):
        self.assertFalse(is_valid_email("user@domain.x"))

    def test_validate_email_list(self):
        emails = [
            "good@example.org",
            "invalid@",
            "abc",
            "another@valid.com",
        ]
        result = validate_email_list(emails)
        self.assertEqual(len(result["valid"]), 2)
        self.assertEqual(len(result["invalid"]), 2)
        self.assertIn("good@example.org", result["valid"])
        self.assertIn("another@valid.com", result["valid"])


class TestEmailExtraction(TestBase):
    """Test email extraction from text."""

    def test_extract_from_text(self):
        text = "Contact us at info@company.com or sales@company.com"
        emails = extract_emails_from_text(text)
        self.assertIn("info@company.com", emails)
        self.assertIn("sales@company.com", emails)

    def test_extract_ignores_images(self):
        text = "Image at banner@site.png and logo@site.jpg"
        emails = extract_emails_from_text(text)
        self.assertEqual(len(emails), 0)

    def test_extract_deduplicates(self):
        text = "test@example.com and Test@Example.com again"
        emails = extract_emails_from_text(text)
        self.assertEqual(len(emails), 1)


class TestDuplicateDetection(TestBase):
    """Test duplicate buyer record detection."""

    def test_dedup_removes_duplicates(self):
        records = [
            {"email": "test@example.com", "buyer_name": "A"},
            {"email": "test@example.com", "buyer_name": "B"},
            {"email": "other@example.com", "buyer_name": "C"},
        ]
        result = deduplicate_records(records)
        self.assertEqual(len(result), 2)

    def test_dedup_case_insensitive(self):
        records = [
            {"email": "Test@Example.com", "buyer_name": "A"},
            {"email": "test@example.com", "buyer_name": "B"},
        ]
        result = deduplicate_records(records)
        self.assertEqual(len(result), 1)

    def test_dedup_empty_emails_skipped(self):
        records = [
            {"email": "", "buyer_name": "A"},
            {"email": "", "buyer_name": "B"},
            {"email": "valid@example.com", "buyer_name": "C"},
        ]
        result = deduplicate_records(records)
        self.assertEqual(len(result), 1)


class TestNormalization(TestBase):
    """Test buyer record normalization."""

    def test_normalize_fills_missing(self):
        record = {"email": "Test@Example.COM"}
        result = normalize_buyer_record(record)
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["buyer_name"], "")
        self.assertEqual(result["company_name"], "")
        self.assertEqual(result["source_platform"], "")

    def test_normalize_strips_whitespace(self):
        record = {
            "buyer_name": "  John  ",
            "email": " john@example.com ",
        }
        result = normalize_buyer_record(record)
        self.assertEqual(result["buyer_name"], "John")
        self.assertEqual(result["email"], "john@example.com")


class TestProcessSearchResults(TestBase):
    """Test the full processing pipeline."""

    def test_process_removes_invalid_and_dupes(self):
        results = [
            {"email": "valid@example.com", "buyer_name": "A"},
            {"email": "valid@example.com", "buyer_name": "B"},  # duplicate
            {"email": "", "buyer_name": "C"},  # no email
            {"email": "another@company.org", "buyer_name": "D"},
        ]
        processed = process_search_results(results)
        emails = [r["email"] for r in processed]
        self.assertEqual(len(processed), 2)
        self.assertIn("valid@example.com", emails)
        self.assertIn("another@company.org", emails)


class TestClassification(TestBase):
    """Test local fallback classifier."""

    def test_business_email(self):
        buyers = [
            {"email": "john@abcwellness.com", "buyer_name": "John",
             "company_name": "ABC", "website": "", "country": "", "source_platform": ""},
        ]
        result = _classify_local(buyers)
        self.assertEqual(len(result["business"]), 1)
        self.assertEqual(len(result["individual"]), 0)

    def test_individual_email(self):
        buyers = [
            {"email": "person@gmail.com", "buyer_name": "Person",
             "company_name": "", "website": "", "country": "", "source_platform": ""},
        ]
        result = _classify_local(buyers)
        self.assertEqual(len(result["individual"]), 1)
        self.assertEqual(len(result["business"]), 0)

    def test_mixed_classification(self):
        buyers = [
            {"email": "biz@company.com", "buyer_name": "Biz",
             "company_name": "Co", "website": "", "country": "", "source_platform": ""},
            {"email": "person@yahoo.com", "buyer_name": "Person",
             "company_name": "", "website": "", "country": "", "source_platform": ""},
            {"email": "another@outlook.com", "buyer_name": "Another",
             "company_name": "", "website": "", "country": "", "source_platform": ""},
        ]
        result = _classify_local(buyers)
        self.assertEqual(len(result["business"]), 1)
        self.assertEqual(len(result["individual"]), 2)


class TestAttachment(TestBase):
    """Test presentation attachment checking and PDF validation."""

    def test_existing_presentation(self):
        result = check_presentation_exists()
        self.assertTrue(result["exists"])
        self.assertIsNone(result["error"])

    def test_missing_presentation(self):
        config.Config.PRESENTATION_PATH = os.path.join(self.test_dir, "nonexistent.pdf")
        result = check_presentation_exists()
        self.assertFalse(result["exists"])
        self.assertIsNotNone(result["error"])

    def test_invalid_pdf_magic_bytes(self):
        bad_pdf = os.path.join(self.test_dir, "invalid.pdf")
        with open(bad_pdf, "wb") as f:
            f.write(b"NOT A PDF content text")
        config.Config.PRESENTATION_PATH = bad_pdf

        result = check_presentation_exists()
        self.assertFalse(result["exists"])
        self.assertIn("magic bytes", result["error"])


class TestCSVInitialization(TestBase):
    """Test automatic creation of CSV files with correct headers."""

    def test_csv_init_creates_files(self):
        for filepath in [config.Config.BUYERS_CSV, config.Config.BUSINESS_EMAILS_CSV,
                         config.Config.INDIVIDUAL_EMAILS_CSV, config.Config.SENT_LOG_CSV]:
            if os.path.exists(filepath):
                os.remove(filepath)

        init_csv_files()

        self.assertTrue(os.path.exists(config.Config.BUYERS_CSV))
        self.assertTrue(os.path.exists(config.Config.BUSINESS_EMAILS_CSV))
        self.assertTrue(os.path.exists(config.Config.INDIVIDUAL_EMAILS_CSV))
        self.assertTrue(os.path.exists(config.Config.SENT_LOG_CSV))

        buyers_df = pd.read_csv(config.Config.BUYERS_CSV)
        self.assertEqual(list(buyers_df.columns), config.Config.BUYER_HEADERS)

        biz_df = pd.read_csv(config.Config.BUSINESS_EMAILS_CSV)
        self.assertEqual(list(biz_df.columns), ["email_address"])

        ind_df = pd.read_csv(config.Config.INDIVIDUAL_EMAILS_CSV)
        self.assertEqual(list(ind_df.columns), ["email_address"])

        sent_df = pd.read_csv(config.Config.SENT_LOG_CSV)
        self.assertEqual(list(sent_df.columns), config.Config.SENT_LOG_HEADERS)


class TestDryRunMode(TestBase):
    """Test dry-run campaign outreach execution."""

    def test_sender_respects_dry_run(self):
        self.assertTrue(config.Config.DRY_RUN)
        sender = GmailSender()
        self.assertTrue(sender.dry_run)

    def test_dry_run_sending(self):
        init_csv_files()
        
        buyers = [
            {"email": "buyer1@company.com", "buyer_name": "Buyer One", "company_name": "Company One",
             "website": "www.co1.com", "country": "USA", "source_platform": "Google"},
            {"email": "buyer2@gmail.com", "buyer_name": "Buyer Two", "company_name": "Company Two",
             "website": "www.co2.com", "country": "Canada", "source_platform": "Website"},
        ]
        save_buyers(buyers)
        
        _classify_local(buyers)
        
        recipients = load_classified("all")
        self.assertEqual(len(recipients), 2)

        sender = GmailSender()
        results = sender.send_campaign(
            recipients=recipients,
            subject="Test Subject for {{company}}",
            body_template="Hello {{name}}, welcome to our test.",
            attach=True
        )

        self.assertEqual(results["dry_run"], 2)
        self.assertEqual(results["sent"], 0)
        self.assertEqual(results["failed"], 0)

        sent_df = pd.read_csv(config.Config.SENT_LOG_CSV)
        self.assertEqual(len(sent_df), 2)
        self.assertEqual(list(sent_df["status"]), ["dry-run", "dry-run"])
        self.assertIn("buyer1@company.com", list(sent_df["email"]))


class TestReportGeneration(TestBase):
    """Test dynamic campaign report metrics generation."""

    def test_report_empty_databases(self):
        init_csv_files()
        report = generate_report()
        self.assertEqual(report["total_buyers"], 0)
        self.assertEqual(report["business_contacts"], 0)
        self.assertEqual(report["individual_contacts"], 0)
        self.assertEqual(report["total_emails"], 0)
        self.assertEqual(report["duplicates_skipped"], 0)
        self.assertEqual(report["success_rate"], 0.0)

    def test_report_filled_databases(self):
        init_csv_files()
        
        buyers = [
            {"email": "biz1@company.com", "buyer_name": "B1", "company_name": "C1",
             "website": "", "country": "", "source_platform": ""},
            {"email": "ind1@gmail.com", "buyer_name": "I1", "company_name": "",
             "website": "", "country": "", "source_platform": ""},
            {"email": "ind2@yahoo.com", "buyer_name": "I2", "company_name": "",
             "website": "", "country": "", "source_platform": ""},
        ]
        save_buyers(buyers)
        
        _classify_local(buyers)

        log_records = [
            {"email": "ind1@gmail.com", "timestamp": "2026-08-24T12:00:00", "status": "sent", "subject": "Sub"},
            {"email": "ind2@yahoo.com", "timestamp": "2026-08-24T12:01:00", "status": "failed", "subject": "Sub"},
            {"email": "biz1@company.com", "timestamp": "2026-08-24T11:00:00", "status": "sent", "subject": "Prev Sub"},
        ]
        pd.DataFrame(log_records).to_csv(config.Config.SENT_LOG_CSV, index=False)

        report = generate_report()

        self.assertEqual(report["total_buyers"], 3)
        self.assertEqual(report["business_contacts"], 1)
        self.assertEqual(report["individual_contacts"], 2)
        
        self.assertEqual(report["total_emails"], 3)
        self.assertEqual(report["successful"], 2)
        self.assertEqual(report["failed"], 1)
        
        self.assertEqual(report["duplicates_skipped"], 2)
        self.assertEqual(report["success_rate"], 66.7)


if __name__ == "__main__":
    unittest.main()
