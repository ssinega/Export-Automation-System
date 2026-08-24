"""
Attachment Handler – Attaches the company presentation PDF to outgoing emails.

The presentation path is configured via PRESENTATION_PATH in .env.
"""

import os
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

from config import Config


def check_presentation_exists() -> dict:
    """
    Verify that the company presentation file exists and is a valid PDF.

    Returns:
        Dict with 'exists' (bool), 'path' (str), 'is_placeholder' (bool), and 'error' (str).
    """
    path = Config.PRESENTATION_PATH
    if not os.path.isfile(path):
        return {
            "exists": False,
            "path": path,
            "is_placeholder": False,
            "error": f"Presentation file not found: {path}",
        }

    try:
        with open(path, "rb") as f:
            header = f.read(1024)
        if not header.startswith(b"%PDF-"):
            return {
                "exists": False,
                "path": path,
                "is_placeholder": False,
                "error": f"Invalid PDF file: {path} (missing %PDF- magic bytes)",
            }
        
        is_placeholder = b"Export Company Presentation" in header or b"mock pdf" in header
        return {
            "exists": True,
            "path": path,
            "is_placeholder": is_placeholder,
            "error": "Note: Using the placeholder company presentation. Replace it with the real one before live campaigns." if is_placeholder else None,
        }
    except Exception as exc:
        return {
            "exists": False,
            "path": path,
            "is_placeholder": False,
            "error": f"Error reading presentation file: {exc}",
        }


def attach_presentation(msg: MIMEMultipart, path: str = None) -> MIMEMultipart:
    """
    Attach the company presentation PDF to an email message.

    Args:
        msg: The MIMEMultipart message to attach to.
        path: Optional override for presentation file path.

    Returns:
        The message with attachment added.

    Raises:
        FileNotFoundError: If the presentation file does not exist.
    """
    path = path or Config.PRESENTATION_PATH

    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Presentation file not found: {path}. "
            "Add the file or update PRESENTATION_PATH in .env."
        )

    filename = os.path.basename(path)

    with open(path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={filename}",
    )
    msg.attach(part)

    return msg
