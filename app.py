"""
API 3 – EXPORT Automation System
Flask Web Application

Routes:
  /               – Dashboard
  /upload         – CSV upload
  /classify       – AI classification
  /send           – Email campaign
  /report         – Campaign report
  /settings       – Configuration
  /download-report – CSV report download
"""

import os
import io

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, Response, jsonify,
)
import pandas as pd

from config import Config
from activity_log.activity_logger import init_csv_files, count_by_status
from extraction.data_extractor import (
    process_search_results, save_buyers, load_buyers,
)
from validation.email_validator import is_valid_email
from classifier import classify_emails, load_classified
from outreach.gmail_sender import GmailSender
from outreach.attachment_handler import check_presentation_exists
from reports.report_generator import (
    generate_report, generate_csv_report, get_sent_log_data,
)

# ──────────────────────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_SIZE

# Ensure CSV files exist on startup
init_csv_files()


# ──────────────────────────────────────────────────────────────
# Helper: safe filename check
# ──────────────────────────────────────────────────────────────

def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Dashboard – overview of buyers, classifications, and campaign stats."""
    report = generate_report()
    warnings = Config.validate()
    presentation = check_presentation_exists()
    return render_template(
        "index.html",
        report=report,
        warnings=warnings,
        presentation=presentation,
        dry_run=Config.DRY_RUN,
    )


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload CSV of buyer records."""
    if request.method == "POST":
        # Check file presence
        if "file" not in request.files:
            flash("No file selected.", "error")
            return redirect(url_for("upload"))

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("upload"))

        if not _allowed_file(file.filename):
            flash("Only CSV files are allowed.", "error")
            return redirect(url_for("upload"))

        try:
            # Read CSV
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            df = pd.read_csv(stream)

            # Validate required columns
            required = set(Config.BUYER_HEADERS)
            if not required.issubset(set(df.columns)):
                missing = required - set(df.columns)
                flash(f"Missing columns: {', '.join(missing)}", "error")
                return redirect(url_for("upload"))

            # Validate emails and filter
            records = df.to_dict("records")
            valid_records = []
            invalid_count = 0

            for record in records:
                email = str(record.get("email", "")).strip().lower()
                record["email"] = email
                if is_valid_email(email):
                    valid_records.append(record)
                else:
                    invalid_count += 1

            # Process and save
            processed = process_search_results(valid_records)
            saved = save_buyers(processed)

            flash(
                f"Uploaded successfully! {saved} new buyers added. "
                f"{invalid_count} invalid emails rejected.",
                "success",
            )

        except Exception as exc:
            flash(f"Error processing file: {exc}", "error")

        return redirect(url_for("upload"))

    # GET
    buyers = load_buyers()
    return render_template("upload.html", buyers=buyers)


@app.route("/classify", methods=["GET", "POST"])
def classify():
    """Run AI classification on buyer records."""
    business_count = 0
    individual_count = 0
    total = 0
    classified = False

    if request.method == "POST":
        buyers = load_buyers()
        if buyers.empty:
            flash("No buyers to classify. Upload data first.", "error")
            return redirect(url_for("classify"))

        records = buyers.to_dict("records")
        result = classify_emails(records)

        business_count = len(result["business"])
        individual_count = len(result["individual"])
        total = business_count + individual_count
        classified = True

        flash(
            f"Classification complete! {business_count} business, "
            f"{individual_count} individual.",
            "success",
        )

    # Load current classified counts
    biz = load_classified("business")
    ind = load_classified("individual")

    return render_template(
        "classify.html",
        business_count=len(biz),
        individual_count=len(ind),
        total=len(biz) + len(ind),
        classified=classified,
    )


@app.route("/send", methods=["GET", "POST"])
def send():
    """Send email campaign."""
    if request.method == "POST":
        audience = request.form.get("audience", "all")
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not subject:
            flash("Email subject is required.", "error")
            return redirect(url_for("send"))

        if not body:
            flash("Email body is required.", "error")
            return redirect(url_for("send"))

        # Check presentation
        presentation = check_presentation_exists()
        if not presentation["exists"]:
            flash(
                f"⚠ {presentation['error']}. Campaign stopped.",
                "error",
            )
            return redirect(url_for("send"))

        # Load recipients
        recipients = load_classified(audience)
        if not recipients:
            flash("No recipients found. Classify emails first.", "error")
            return redirect(url_for("send"))

        # Send campaign
        sender = GmailSender()
        results = sender.send_campaign(recipients, subject, body, attach=True)

        if "error" in results:
            flash(f"⚠ {results['error']}", "error")
        else:
            mode = "DRY RUN" if Config.DRY_RUN else "LIVE"
            flash(
                f"Campaign complete [{mode}]! "
                f"Sent: {results.get('sent', 0)}, "
                f"Dry-run: {results.get('dry_run', 0)}, "
                f"Failed: {results.get('failed', 0)}, "
                f"Duplicates skipped: {results.get('skipped_duplicate', 0)}",
                "success",
            )

        return redirect(url_for("send"))

    # GET
    presentation = check_presentation_exists()
    biz = load_classified("business")
    ind = load_classified("individual")

    return render_template(
        "send.html",
        business_count=len(biz),
        individual_count=len(ind),
        dry_run=Config.DRY_RUN,
        presentation=presentation,
        gmail_configured=bool(Config.GMAIL_EMAIL and Config.GMAIL_APP_PASSWORD),
        default_subject=Config.DEFAULT_SUBJECT,
        default_body=Config.DEFAULT_BODY,
    )


@app.route("/report")
def report():
    """Campaign report dashboard."""
    report_data = generate_report()
    log_data = get_sent_log_data()
    return render_template(
        "report.html",
        report=report_data,
        log=log_data,
    )


@app.route("/download-report")
def download_report():
    """Download campaign report as CSV."""
    csv_content = generate_csv_report()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=campaign_report.csv"},
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Application settings page."""
    if request.method == "POST":
        new_settings = {
            "SEARCH_KEYWORD": request.form.get("search_keyword", Config.SEARCH_KEYWORD).strip(),
            "DAILY_SEND_LIMIT": request.form.get("daily_limit", str(Config.DAILY_SEND_LIMIT)).strip(),
            "SEND_DELAY": request.form.get("send_delay", str(Config.SEND_DELAY)).strip(),
            "DEFAULT_SUBJECT": request.form.get("default_subject", Config.DEFAULT_SUBJECT).strip(),
            "DEFAULT_BODY": request.form.get("default_body", Config.DEFAULT_BODY),
            "CLASSIFICATION_PREFERENCE": request.form.get("classification_preference", Config.CLASSIFICATION_PREFERENCE).strip(),
        }
        
        try:
            new_settings["DAILY_SEND_LIMIT"] = int(new_settings["DAILY_SEND_LIMIT"])
            new_settings["SEND_DELAY"] = int(new_settings["SEND_DELAY"])
        except ValueError:
            flash("Daily send limit and delay must be valid integers.", "error")
            return redirect(url_for("settings"))
            
        success = Config.save_custom_settings(new_settings)
        if success:
            flash("Settings updated successfully!", "success")
        else:
            flash("Failed to update settings.", "error")
            
        return redirect(url_for("settings"))

    return render_template(
        "settings.html",
        config={
            "gmail_email": Config.GMAIL_EMAIL or "(not configured)",
            "daily_limit": Config.DAILY_SEND_LIMIT,
            "send_delay": Config.SEND_DELAY,
            "dry_run": Config.DRY_RUN,
            "search_keyword": Config.SEARCH_KEYWORD,
            "presentation_path": Config.PRESENTATION_PATH,
            "default_subject": Config.DEFAULT_SUBJECT,
            "default_body": Config.DEFAULT_BODY,
            "classification_preference": Config.CLASSIFICATION_PREFERENCE,
            "gemini_configured": bool(Config.GEMINI_API_KEY),
            "gmail_configured": bool(Config.GMAIL_EMAIL and Config.GMAIL_APP_PASSWORD),
        },
        warnings=Config.validate(),
    )


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════╗")
    print("║   API 3 – EXPORT Automation System          ║")
    print("║   http://127.0.0.1:5000                     ║")
    print("╚══════════════════════════════════════════════╝\n")

    warnings = Config.validate()
    if warnings:
        print("⚠  Configuration warnings:")
        for w in warnings:
            print(f"   • {w}")
        print()

    if Config.DRY_RUN:
        print("🔒 DRY RUN mode is active – no emails will be sent.\n")

    app.run(debug=Config.DEBUG, host="127.0.0.1", port=5000)
