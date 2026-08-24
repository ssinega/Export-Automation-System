# API 3 – EXPORT Automation System

> **Automated buyer discovery, email validation, AI classification, and Gmail campaign system for a Singing Bowls export business.**

---

## 1. Project Purpose

This system automates the end-to-end export outreach workflow:

```
Buyer Discovery → Email Extraction → Email Validation → Duplicate Check →
AI Classification → Gmail Campaign → Presentation Attachment → Logging → Reporting
```

It is designed for a Singing Bowls export business to discover potential international buyers, classify their contacts, and send personalized email campaigns with product presentations attached.

---

## 2. Architecture

The system is built as a **modular Python application** with two interfaces:

| Interface | File | Description |
|-----------|------|-------------|
| **Web Dashboard** | `app.py` | Flask web application at `http://127.0.0.1:5000` |
| **CLI Pipeline** | `main.py` | Command-line automation pipeline |

### Technology Stack

- **Python 3.10+** – Core language
- **Flask** – Web framework
- **HTML5 / CSS3** – Dashboard UI
- **Pandas** – CSV data processing
- **Requests + BeautifulSoup4** – Web scraping
- **Google Gemini API** – AI email classification
- **Gmail SMTP** – Email sending
- **CSV files** – Local database

---

## 3. Folder Structure

```
export-automation/
│
├── main.py                  # CLI pipeline
├── app.py                   # Flask web application
├── config.py                # Central configuration
├── classifier.py            # AI email classifier
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (secrets)
├── .env.example             # Template for .env
├── .gitignore               # Git ignore rules
├── README.md                # This file
│
├── search/                  # Buyer discovery adapters
│   ├── google_search.py
│   ├── facebook_search.py
│   ├── linkedin_search.py
│   ├── directory_search.py
│   └── website_search.py
│
├── extraction/              # Email extraction
│   └── data_extractor.py
│
├── validation/              # Email validation
│   └── email_validator.py
│
├── outreach/                # Gmail integration
│   ├── gmail_auth.py
│   ├── gmail_sender.py
│   └── attachment_handler.py
│
├── activity_log/            # Activity logging
│   └── activity_logger.py
│
├── reports/                 # Report generation
│   └── report_generator.py
│
├── templates/               # HTML templates
│   ├── index.html
│   ├── upload.html
│   ├── classify.html
│   ├── send.html
│   ├── report.html
│   └── settings.html
│
├── static/                  # CSS & JavaScript
│   ├── css/style.css
│   └── js/script.js
│
├── assets/                  # Attachments
│   └── company_presentation.pdf
│
├── data/                    # CSV databases
│   ├── buyers.csv
│   ├── business_emails.csv
│   ├── individual_emails.csv
│   └── sent_log.csv
│
└── tests/                   # Test suite
    └── test_system.py
```

---

## 4. Quick Start Commands (Windows)

Open a PowerShell prompt and execute:

```powershell
cd "C:\Users\Admin\Downloads\task 1\export-automation"
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

To run the automated tests:

```powershell
python -m pytest tests/ -v
```

To run the CLI pipeline:

```powershell
python main.py
```

---

## 5. Virtual Environment & Dependencies

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

This installs:
- Flask
- requests
- beautifulsoup4
- pandas
- python-dotenv
- validate-email-address
- google-generativeai
- pytest

---

## 7. `.env` Configuration

Copy the example file:

```powershell
copy .env.example .env
```

Edit `.env` with your settings:

```env
# Required for live email sending
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Optional monitoring CC
MONITOR_EMAIL=monitor@gmail.com

# AI classification (optional – fallback works without it)
GEMINI_API_KEY=your-gemini-api-key

# Google Custom Search (optional)
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-cse-id

# Campaign settings
DAILY_SEND_LIMIT=10
SEND_DELAY=5

# CRITICAL: Keep true until ready for live sending
DRY_RUN=true

# Presentation file path
PRESENTATION_PATH=assets/company_presentation.pdf
```

---

## 8. Gmail App Password Setup

Gmail requires an **App Password** instead of your regular password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select **Mail** and **Windows Computer**
5. Click **Generate**
6. Copy the 16-character password
7. Add to `.env`:
   ```env
   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

⚠️ **Never** share or commit this password.

---

## 9. Gemini API Setup

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key
3. Add to `.env`:
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```

If no Gemini key is configured, the system uses a **local fallback classifier** based on domain analysis (free provider = Individual, custom domain = Business).

---

## 10. Google Custom Search API Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable **Custom Search API**
3. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/) and create a search engine
4. Add to `.env`:
   ```env
   GOOGLE_API_KEY=your-api-key
   GOOGLE_CSE_ID=your-search-engine-id
   ```

If not configured, the system uses **sample data** for buyer discovery.

---

## 11. Dry-Run Testing

The application defaults to `DRY_RUN=true`:

```env
DRY_RUN=true
```

In this mode:
- No actual emails are sent
- All operations are logged as `dry-run`
- The console shows `[DRY RUN] Would send to ...`
- The full pipeline can be tested safely

**Always test with dry-run first!**

---

## 12. CSV Upload Testing

1. Start Flask (see section 13)
2. Go to `http://127.0.0.1:5000/upload`
3. Upload a CSV with these columns:
   ```csv
   buyer_name,company_name,email,website,country,source_platform
   Test User,Test Co,test@testco.com,https://testco.com,USA,Manual
   ```
4. The system validates emails and adds valid records to the database

---

## 13. Starting Flask

```powershell
python app.py
```

Then open:

```
http://127.0.0.1:5000
```

### Available Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard with overview statistics |
| `/upload` | Upload CSV buyer data |
| `/classify` | Run AI email classification |
| `/send` | Send email campaign |
| `/report` | Campaign analytics & send log |
| `/settings` | View current configuration |
| `/download-report` | Download report as CSV |

---

## 14. Running `main.py`

For command-line pipeline execution:

```powershell
python main.py
```

This runs the full automation pipeline:
1. Loads configuration
2. Searches all configured sources
3. Extracts and validates buyer records
4. Saves to CSV
5. Runs AI classification
6. Checks presentation file
7. Sends email campaign (dry-run by default)
8. Generates report

---

## 15. Real Email Sending

When you're ready for live sending:

1. ✅ Configure Gmail credentials in `.env`
2. ✅ Replace `assets/company_presentation.pdf` with your real PDF
3. ✅ Test thoroughly with `DRY_RUN=true`
4. ✅ Review all recipients in the dashboard
5. Change `.env`:
   ```env
   DRY_RUN=false
   ```
6. Restart Flask
7. Go to `/send` and run the campaign

The system will:
- Check for duplicates before each send
- Respect the daily send limit
- Add configurable delays between emails
- Retry on SMTP disconnection
- Log every send attempt

---

## 16. Running Tests

```powershell
python -m pytest tests/ -v
```

Or with unittest:

```powershell
python -m unittest tests.test_system -v
```

Tests cover:
- Email validation (valid, invalid, edge cases)
- Duplicate detection
- Record normalization
- Classification (business vs individual)
- Attachment checking
- Dry-run mode verification

---

## 17. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate venv: `.venv\Scripts\activate` |
| Flask won't start | Check `pip install -r requirements.txt` |
| CSV files missing | They are auto-created on first run |
| Gmail auth fails | Check App Password, not regular password |
| Classification always uses fallback | Add `GEMINI_API_KEY` to `.env` |
| Presentation not found | Add PDF to `assets/` folder |
| Emails not sending | Check `DRY_RUN=false` in `.env` |
| SMTP timeout | Check internet connection and Gmail settings |
| Daily limit reached | Wait 24 hours or increase `DAILY_SEND_LIMIT` |

---

## 18. Security Precautions

- ✅ All credentials stored in `.env` (never hard-coded)
- ✅ `.env` is listed in `.gitignore`
- ✅ Gmail App Password never displayed in web UI
- ✅ Uploaded file size limited to 5 MB
- ✅ Only CSV files accepted for upload
- ✅ Email addresses validated before processing
- ✅ No bypassing of website authentication or CAPTCHA
- ✅ Dry-run mode enabled by default

---

## License

This project is created for educational/demonstration purposes as a final-year CSE project.
