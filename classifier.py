"""
AI Email Classifier – Classifies emails as BUSINESS or INDIVIDUAL.

Uses Google Gemini API when GEMINI_API_KEY is configured.
Falls back to a deterministic local classifier when credentials
are unavailable, so the application can still be tested end-to-end.
"""

import os
import pandas as pd
from config import Config


def classify_emails(buyers: list[dict], batch_size: int = 10) -> dict:
    """
    Classify a list of buyer records into BUSINESS and INDIVIDUAL.

    Args:
        buyers: List of buyer dicts with email, buyer_name, company_name, etc.
        batch_size: Number of emails to process per Gemini API call.

    Returns:
        Dict with 'business' and 'individual' lists of buyer dicts.
    """
    if Config.GEMINI_API_KEY:
        return _classify_with_gemini(buyers, batch_size)
    else:
        print("[Classifier] Gemini API key not configured – using local fallback.")
        return _classify_local(buyers)


def _classify_with_gemini(buyers: list[dict], batch_size: int) -> dict:
    """
    Classify emails using Gemini API.

    Sends batches of emails to Gemini and parses the response.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        print("[Classifier] google-generativeai not installed – using local fallback.")
        return _classify_local(buyers)

    genai.configure(api_key=Config.GEMINI_API_KEY)

    business = []
    individual = []

    # Process in batches
    for i in range(0, len(buyers), batch_size):
        batch = buyers[i:i + batch_size]

        prompt_lines = [
            "Classify each of the following email addresses as either "
            "'BUSINESS' or 'INDIVIDUAL'. A BUSINESS email uses a company "
            "domain (not gmail, yahoo, hotmail, outlook, aol, etc). "
            "An INDIVIDUAL email uses a free email provider.\n\n"
            "Respond with ONLY a numbered list in the format:\n"
            "1. BUSINESS\n2. INDIVIDUAL\n\nEmails:"
        ]
        for idx, buyer in enumerate(batch, 1):
            email = buyer.get("email", "")
            company = buyer.get("company_name", "")
            prompt_lines.append(f"{idx}. {email} (Company: {company})")

        prompt = "\n".join(prompt_lines)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Parse response
            lines = text.strip().split("\n")
            for idx, buyer in enumerate(batch):
                classification = "INDIVIDUAL"  # Safe default
                if idx < len(lines):
                    line = lines[idx].upper()
                    if "BUSINESS" in line:
                        classification = "BUSINESS"
                    elif "INDIVIDUAL" in line:
                        classification = "INDIVIDUAL"

                if classification == "BUSINESS":
                    business.append(buyer)
                else:
                    individual.append(buyer)

        except Exception as exc:
            print(f"[Classifier] Gemini API error: {exc}. "
                  "Falling back to local classifier for this batch.")
            local_result = _classify_local(batch)
            business.extend(local_result["business"])
            individual.extend(local_result["individual"])

    _save_classified(business, individual)
    return {"business": business, "individual": individual}


def _classify_local(buyers: list[dict]) -> dict:
    """
    Local fallback classifier using domain-based heuristics.

    Rules:
        - Free email providers (gmail, yahoo, hotmail, outlook, aol, etc.)
          → INDIVIDUAL
        - Company/custom domains → BUSINESS
    """
    FREE_PROVIDERS = {
        "gmail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com",
        "outlook.com", "aol.com", "icloud.com", "mail.com",
        "protonmail.com", "live.com", "msn.com", "yandex.com",
        "gmx.com", "zoho.com", "fastmail.com", "tutanota.com",
        "mail.ru", "inbox.com", "rediffmail.com",
    }

    business = []
    individual = []

    for buyer in buyers:
        email = buyer.get("email", "").lower().strip()
        if "@" not in email:
            individual.append(buyer)
            continue

        domain = email.split("@")[1]
        if domain in FREE_PROVIDERS:
            individual.append(buyer)
        else:
            business.append(buyer)

    _save_classified(business, individual)
    return {"business": business, "individual": individual}


def _save_classified(business: list[dict], individual: list[dict]):
    """Save classified records to their respective CSV files."""
    try:
        os.makedirs(Config.DATA_DIR, exist_ok=True)

        if business:
            df = pd.DataFrame([b.get("email", "").lower().strip() for b in business], columns=["email_address"])
            df.to_csv(Config.BUSINESS_EMAILS_CSV, index=False)

        if individual:
            df = pd.DataFrame([i.get("email", "").lower().strip() for i in individual], columns=["email_address"])
            df.to_csv(Config.INDIVIDUAL_EMAILS_CSV, index=False)

        print(f"[Classifier] Classified: {len(business)} business, "
              f"{len(individual)} individual.")
    except (PermissionError, OSError) as exc:
        print(f"[Classifier] Warning: Could not save classified CSVs (read-only filesystem): {exc}")
    except Exception as exc:
        print(f"[Classifier] Error saving classified CSVs: {exc}")


def load_classified(audience: str = "all") -> list[dict]:
    """
    Load classified buyer records.
    Loads the list of email addresses from the chosen audience CSV,
    and joins it with the full details from buyers.csv to return complete dicts.

    Args:
        audience: 'business', 'individual', or 'all'.

    Returns:
        List of buyer dicts.
    """
    if not os.path.exists(Config.BUYERS_CSV):
        return []

    try:
        buyers_df = pd.read_csv(Config.BUYERS_CSV)
    except Exception as exc:
        print(f"[Classifier] Error reading buyers.csv: {exc}")
        return []

    for col in Config.BUYER_HEADERS:
        if col not in buyers_df.columns:
            buyers_df[col] = ""

    buyers_df["email_norm"] = buyers_df["email"].astype(str).str.lower().str.strip()
    allowed_emails = set()

    if audience in ("business", "all"):
        if os.path.exists(Config.BUSINESS_EMAILS_CSV):
            try:
                biz_df = pd.read_csv(Config.BUSINESS_EMAILS_CSV)
                if not biz_df.empty and "email_address" in biz_df.columns:
                    allowed_emails.update(biz_df["email_address"].astype(str).str.lower().str.strip().tolist())
            except Exception as exc:
                print(f"[Classifier] Error loading business_emails.csv: {exc}")

    if audience in ("individual", "all"):
        if os.path.exists(Config.INDIVIDUAL_EMAILS_CSV):
            try:
                ind_df = pd.read_csv(Config.INDIVIDUAL_EMAILS_CSV)
                if not ind_df.empty and "email_address" in ind_df.columns:
                    allowed_emails.update(ind_df["email_address"].astype(str).str.lower().str.strip().tolist())
            except Exception as exc:
                print(f"[Classifier] Error loading individual_emails.csv: {exc}")

    matched_df = buyers_df[buyers_df["email_norm"].isin(allowed_emails)]
    matched_df = matched_df.drop(columns=["email_norm"])

    records = matched_df.to_dict("records")
    seen_emails = set()
    unique_records = []
    for r in records:
        email = r.get("email", "").lower().strip()
        if email not in seen_emails:
            seen_emails.add(email)
            unique_records.append(r)

    return unique_records
