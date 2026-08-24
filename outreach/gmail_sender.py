"""
Gmail Sender – Sends personalized emails with attachment support.

Handles:
  - Dry-run mode (no actual sending)
  - Duplicate prevention via sent_log.csv
  - Configurable daily send limit and inter-email delay
  - SMTP disconnect recovery with automatic reconnect
  - Per-recipient exception handling
  - CC to monitor email
"""

import os
import time
import smtplib
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from config import Config
from outreach.gmail_auth import GmailAuth
from outreach.attachment_handler import attach_presentation


class GmailSender:
    """Orchestrates email campaign sending."""

    def __init__(self):
        self.auth = GmailAuth()
        self.dry_run = Config.DRY_RUN
        self.daily_limit = Config.DAILY_SEND_LIMIT
        self.send_delay = Config.SEND_DELAY
        self.sent_today = 0
        self.results = {
            "sent": 0,
            "failed": 0,
            "skipped_duplicate": 0,
            "skipped_limit": 0,
            "dry_run": 0,
            "details": [],
        }

    # ------------------------------------------------------------------
    # Duplicate prevention
    # ------------------------------------------------------------------

    def _load_sent_log(self) -> set:
        """Load set of already-sent email addresses from sent_log.csv."""
        import pandas as pd  # lazy import
        filepath = Config.SENT_LOG_CSV
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            return set(df["email"].str.lower().str.strip())
        return set()

    def _log_send(self, email: str, status: str, subject: str):
        """Append a send record to sent_log.csv."""
        import pandas as pd  # lazy import
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

    def _count_sent_today(self) -> int:
        """Count how many emails were sent (status=sent) today."""
        import pandas as pd  # lazy import
        filepath = Config.SENT_LOG_CSV
        if not os.path.exists(filepath):
            return 0
        df = pd.read_csv(filepath)
        today_str = date.today().isoformat()
        today_sends = df[
            (df["status"] == "sent") &
            (df["timestamp"].str.startswith(today_str))
        ]
        return len(today_sends)

    # ------------------------------------------------------------------
    # Personalization
    # ------------------------------------------------------------------

    @staticmethod
    def personalize(template: str, buyer: dict) -> str:
        """
        Replace {{name}} and {{company}} placeholders in the template.

        Args:
            template: Email body template.
            buyer: Buyer dict with buyer_name and company_name.

        Returns:
            Personalized string.
        """
        result = template.replace("{{name}}", buyer.get("buyer_name", ""))
        result = result.replace("{{company}}", buyer.get("company_name", ""))
        return result

    # ------------------------------------------------------------------
    # Campaign execution
    # ------------------------------------------------------------------

    def send_campaign(
        self,
        recipients: list[dict],
        subject: str,
        body_template: str,
        attach: bool = True,
    ) -> dict:
        """
        Send personalized emails to a list of recipients.

        Args:
            recipients: List of buyer dicts.
            subject: Email subject line.
            body_template: Email body with {{name}}/{{company}} placeholders.
            attach: Whether to attach the company presentation.

        Returns:
            Campaign results dict.
        """
        # Validate presentation if attachment is requested
        if attach and not os.path.exists(Config.PRESENTATION_PATH):
            return {
                "error": (
                    f"Presentation file not found: {Config.PRESENTATION_PATH}. "
                    "Please add the file or update PRESENTATION_PATH in .env."
                )
            }

        sent_log = self._load_sent_log()
        self.sent_today = self._count_sent_today()
        server = None

        # Connect SMTP (unless dry run)
        if not self.dry_run:
            if not self.auth.is_configured():
                return {"error": "Gmail credentials not configured in .env"}
            try:
                server = self.auth.connect()
            except Exception as exc:
                return {"error": f"SMTP connection failed: {exc}"}

        for buyer in recipients:
            email = buyer.get("email", "").lower().strip()
            if not email:
                continue

            # Duplicate check
            if email in sent_log:
                self.results["skipped_duplicate"] += 1
                self.results["details"].append({
                    "email": email,
                    "status": "skipped-duplicate",
                })
                continue

            # Daily limit check
            if self.sent_today >= self.daily_limit:
                self.results["skipped_limit"] += 1
                self.results["details"].append({
                    "email": email,
                    "status": "skipped-limit",
                })
                continue

            # Personalize
            personalized_body = self.personalize(body_template, buyer)
            personalized_subject = self.personalize(subject, buyer)

            # Dry-run mode
            if self.dry_run:
                print(f"[DRY RUN] Would send to {email}")
                self._log_send(email, "dry-run", personalized_subject)
                self.results["dry_run"] += 1
                self.results["details"].append({
                    "email": email,
                    "status": "dry-run",
                })
                sent_log.add(email)
                time.sleep(0.1)  # Small delay for dry run
                continue

            # Build message
            msg = MIMEMultipart()
            msg["From"] = Config.GMAIL_EMAIL
            msg["To"] = email
            msg["Subject"] = personalized_subject

            # CC monitor
            if Config.MONITOR_EMAIL:
                msg["Cc"] = Config.MONITOR_EMAIL

            msg.attach(MIMEText(personalized_body, "plain"))

            # Attach presentation
            if attach:
                attach_presentation(msg)

            # Send with retry on disconnect
            try:
                all_recipients = [email]
                if Config.MONITOR_EMAIL:
                    all_recipients.append(Config.MONITOR_EMAIL)

                server.sendmail(Config.GMAIL_EMAIL, all_recipients, msg.as_string())
                self._log_send(email, "sent", personalized_subject)
                self.results["sent"] += 1
                self.sent_today += 1
                self.results["details"].append({
                    "email": email,
                    "status": "sent",
                })
                sent_log.add(email)
                print(f"[Sent] {email}")

            except smtplib.SMTPServerDisconnected:
                # Reconnect and retry
                print(f"[SMTP] Disconnected – reconnecting for {email}...")
                try:
                    server = self.auth.reconnect()
                    server.sendmail(Config.GMAIL_EMAIL, all_recipients, msg.as_string())
                    self._log_send(email, "sent", personalized_subject)
                    self.results["sent"] += 1
                    self.sent_today += 1
                    self.results["details"].append({
                        "email": email,
                        "status": "sent",
                    })
                    sent_log.add(email)
                    print(f"[Sent after reconnect] {email}")
                except Exception as retry_exc:
                    self._log_send(email, "failed", personalized_subject)
                    self.results["failed"] += 1
                    self.results["details"].append({
                        "email": email,
                        "status": "failed",
                        "error": str(retry_exc),
                    })
                    print(f"[Failed after retry] {email}: {retry_exc}")

            except Exception as exc:
                self._log_send(email, "failed", personalized_subject)
                self.results["failed"] += 1
                self.results["details"].append({
                    "email": email,
                    "status": "failed",
                    "error": str(exc),
                })
                print(f"[Failed] {email}: {exc}")

            # Delay between sends
            time.sleep(self.send_delay)

        # Disconnect
        if not self.dry_run:
            self.auth.disconnect()

        return self.results
