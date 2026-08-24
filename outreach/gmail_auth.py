"""
Gmail Authentication – Handles SMTP connection with Gmail.

Uses App Password authentication over SSL (port 465).
Credentials are loaded from environment variables and never hard-coded.
"""

import smtplib
from config import Config


class GmailAuth:
    """Manages Gmail SMTP authentication and connection lifecycle."""

    def __init__(self):
        self.server = None
        self.email = Config.GMAIL_EMAIL
        self.password = Config.GMAIL_APP_PASSWORD
        self.host = Config.SMTP_HOST
        self.port = Config.SMTP_SSL_PORT

    def is_configured(self) -> bool:
        """Check if Gmail credentials are present in configuration."""
        return bool(self.email and self.password)

    def connect(self) -> smtplib.SMTP_SSL:
        """
        Establish an authenticated SMTP_SSL connection to Gmail.

        Returns:
            The authenticated SMTP_SSL server object.

        Raises:
            ValueError: If credentials are not configured.
            smtplib.SMTPAuthenticationError: If login fails.
        """
        if not self.is_configured():
            raise ValueError(
                "Gmail credentials not configured. "
                "Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
            )

        self.server = smtplib.SMTP_SSL(self.host, self.port)
        self.server.login(self.email, self.password)
        print(f"[Gmail Auth] Connected as {self.email}")
        return self.server

    def reconnect(self) -> smtplib.SMTP_SSL:
        """
        Disconnect (if connected) and establish a fresh connection.

        Returns:
            The newly authenticated SMTP_SSL server object.
        """
        self.disconnect()
        return self.connect()

    def disconnect(self):
        """Close the SMTP connection gracefully."""
        if self.server:
            try:
                self.server.quit()
            except smtplib.SMTPServerDisconnected:
                pass
            finally:
                self.server = None
                print("[Gmail Auth] Disconnected.")

    def get_server(self) -> smtplib.SMTP_SSL:
        """
        Return the current SMTP server, reconnecting if necessary.

        Returns:
            Active SMTP_SSL server object.
        """
        if self.server is None:
            return self.connect()
        return self.server
