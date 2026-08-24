"""
Email Validator – Validates email addresses before they enter the sending queue.

Checks format, structure, domain, length, and rejects obviously invalid
addresses or image/file extensions.
"""

import os
import re

# Strict email regex
_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9]"                     # Must start with alphanumeric
    r"[a-zA-Z0-9._%+\-]*"               # Local part body
    r"@"                                 # @ symbol
    r"[a-zA-Z0-9]"                       # Domain must start with alphanumeric
    r"[a-zA-Z0-9.\-]*"                   # Domain body
    r"\."                                # Dot before TLD
    r"[a-zA-Z]{2,}$"                     # TLD (min 2 chars)
)

# Maximum email length (RFC 5321)
MAX_EMAIL_LENGTH = 254

# File / image extensions to reject
INVALID_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar",
    ".mp3", ".mp4", ".avi", ".mov", ".exe", ".bat",
}

# Obviously invalid local parts
INVALID_LOCAL_PARTS = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer-daemon", "postmaster", "abuse", "spam",
    "example", "test", "info@info", "admin@admin",
}

# Obviously invalid domains
INVALID_DOMAINS = {
    "example.com", "test.com", "localhost", "invalid.com",
    "sentry.io", "wixpress.com",
}


def is_valid_email(email: str) -> bool:
    """
    Validate an email address.

    Checks:
        - Non-empty string
        - Maximum length
        - Contains exactly one @
        - Matches email regex pattern
        - Local part is not empty
        - Domain has at least one dot
        - Domain extension is at least 2 characters
        - Does not end with an image/file extension
        - Is not an obviously invalid address

    Args:
        email: The email address to validate.

    Returns:
        True if the email is valid, False otherwise.
    """
    try:
        if not email or not isinstance(email, str):
            return False

        email = email.strip().lower()

        # Length check
        if len(email) > MAX_EMAIL_LENGTH:
            return False

        # Must contain exactly one @
        if email.count("@") != 1:
            return False

        local_part, domain = email.split("@")

        # Local part checks
        if not local_part:
            return False
        if len(local_part) > 64:
            return False

        # Domain checks
        if not domain:
            return False
        if "." not in domain:
            return False

        # Domain extension
        tld = domain.split(".")[-1]
        if len(tld) < 2:
            return False

        # Regex check
        if not _EMAIL_PATTERN.match(email):
            return False

        # Reject file/image extensions
        _, ext = os.path.splitext(email)
        if ext.lower() in INVALID_EXTENSIONS:
            return False

        # Reject obviously invalid local parts
        if local_part in INVALID_LOCAL_PARTS:
            return False

        # Reject known invalid domains
        if domain in INVALID_DOMAINS:
            return False

        # Optional: check using imported validate_email if installed
        try:
            from validate_email_address import validate_email
            if not validate_email(email):
                return False
        except ImportError:
            pass

        return True
    except Exception as exc:
        print(f"[Email Validator] Error validating email '{email}': {exc}")
        return False


def validate_email_list(emails: list[str]) -> dict:
    """
    Validate a list of email addresses.

    Args:
        emails: List of email strings.

    Returns:
        Dict with 'valid' and 'invalid' lists.
    """
    valid = []
    invalid = []
    for email in emails:
        if is_valid_email(email):
            valid.append(email.strip().lower())
        else:
            invalid.append(email)
    return {"valid": valid, "invalid": invalid}
