"""
Central configuration module for the Export Automation System.
All settings are loaded from environment variables via .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Application configuration loaded from environment variables."""

    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # --- Search ---
    SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD", "Singing Bowls")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

    # --- Gemini AI ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # --- Gmail SMTP ---
    GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    MONITOR_EMAIL = os.getenv("MONITOR_EMAIL", "")
    SMTP_HOST = "smtp.gmail.com"
    SMTP_SSL_PORT = 465
    SMTP_STARTTLS_PORT = 587

    # --- Campaign ---
    DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "10"))
    SEND_DELAY = int(os.getenv("SEND_DELAY", "5"))
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

    # --- Presentation ---
    PRESENTATION_PATH = os.getenv("PRESENTATION_PATH", str(BASE_DIR / "assets" / "company_presentation.pdf"))

    # --- Safe Customize Defaults ---
    DEFAULT_SUBJECT = "Singing Bowls – Export Partnership Opportunity"
    DEFAULT_BODY = (
        "Hello {{name}},\n\n"
        "We are an export supplier of high-quality Singing Bowls from Nepal.\n\n"
        "We would like to explore whether our products may be relevant to {{company}}.\n\n"
        "Please find our company presentation attached.\n\n"
        "Regards,\n"
        "Export Sales Team"
    )
    CLASSIFICATION_PREFERENCE = "gemini"

    # --- File Paths ---
    DATA_DIR = str(BASE_DIR / "data")
    BUYERS_CSV = os.path.join(DATA_DIR, "buyers.csv")
    BUSINESS_EMAILS_CSV = os.path.join(DATA_DIR, "business_emails.csv")
    INDIVIDUAL_EMAILS_CSV = os.path.join(DATA_DIR, "individual_emails.csv")
    SENT_LOG_CSV = os.path.join(DATA_DIR, "sent_log.csv")

    # --- CSV Headers ---
    BUYER_HEADERS = ["buyer_name", "company_name", "email", "website", "country", "source_platform"]
    SENT_LOG_HEADERS = ["email", "timestamp", "status", "subject"]

    # --- Upload ---
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"csv"}

    # --- Search Keywords ---
    SEARCH_QUERIES = [
        "Singing Bowls buyers",
        "Singing Bowl importers",
        "Singing Bowl distributors",
        "Singing Bowl wholesalers",
        "Meditation product stores",
        "Wellness stores",
        "Spiritual product businesses",
        "Sound healing businesses",
    ]

    @classmethod
    def validate(cls):
        """Check critical configuration and return list of warnings."""
        warnings = []
        if not cls.GMAIL_EMAIL:
            warnings.append("GMAIL_EMAIL is not configured in .env")
        if not cls.GMAIL_APP_PASSWORD:
            warnings.append("GMAIL_APP_PASSWORD is not configured in .env")
        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY is not configured – local fallback classifier will be used")
        return warnings

    @classmethod
    def load_custom_settings(cls):
        """Load safe settings from data/settings.json if it exists."""
        import json
        settings_path = os.path.join(cls.DATA_DIR, "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "SEARCH_KEYWORD" in data:
                    cls.SEARCH_KEYWORD = str(data["SEARCH_KEYWORD"])
                if "DAILY_SEND_LIMIT" in data:
                    cls.DAILY_SEND_LIMIT = int(data["DAILY_SEND_LIMIT"])
                if "SEND_DELAY" in data:
                    cls.SEND_DELAY = int(data["SEND_DELAY"])
                if "DEFAULT_SUBJECT" in data:
                    cls.DEFAULT_SUBJECT = str(data["DEFAULT_SUBJECT"])
                if "DEFAULT_BODY" in data:
                    cls.DEFAULT_BODY = str(data["DEFAULT_BODY"])
                if "CLASSIFICATION_PREFERENCE" in data:
                    cls.CLASSIFICATION_PREFERENCE = str(data["CLASSIFICATION_PREFERENCE"])
            except Exception as exc:
                print(f"[Config] Error loading settings.json: {exc}")

    @classmethod
    def save_custom_settings(cls, settings: dict):
        """Save safe settings to data/settings.json and update Config class."""
        import json
        allowed_keys = {
            "SEARCH_KEYWORD", "DAILY_SEND_LIMIT", "SEND_DELAY",
            "DEFAULT_SUBJECT", "DEFAULT_BODY", "CLASSIFICATION_PREFERENCE"
        }
        
        existing = {}
        settings_path = os.path.join(cls.DATA_DIR, "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass
                
        for k, v in settings.items():
            if k in allowed_keys:
                if k == "DAILY_SEND_LIMIT":
                    existing[k] = int(v)
                elif k == "SEND_DELAY":
                    existing[k] = int(v)
                else:
                    existing[k] = str(v)
                    
        try:
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=4)
            cls.load_custom_settings()
            return True
        except Exception as exc:
            print(f"[Config] Error saving settings.json: {exc}")
            return False

# Load custom settings immediately on import
Config.load_custom_settings()
