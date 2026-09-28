# Automated AI Sales Prospecting & CRM Pipeline

An end-to-end sales outreach pipeline designed to extract lead data, validate it through strict schemas, and facilitate human-in-the-loop review before pushing directly to HubSpot. The system bypasses repetitive manual login flows by injecting saved browser states, and uses a local MongoDB instance to manage lead statuses.

---

## Architecture & File Structure

| File | Role | Description |
|------|------|-------------|
| `file1.py` | Authentication Node | A Playwright automation script that launches a visible browser for manual login to target platforms (e.g., LinkedIn). It captures the authenticated session cookies and local storage, saving them to `auth.json`. |
| `parser.py` / `main.py` | Data Enforcement | Uses Pydantic (`ProspectProfile`) to enforce strict type-checking and validation on scraped lead data, ensuring fields like `current_role` and `recent_achievements` meet the required schema before processing. |
| `app1.py` | Review & Sync Dashboard | A Streamlit web app connected to a local MongoDB (`sales_agent`). It surfaces profiles with a `drafted` status, lets operators edit the generated outreach emails, and makes REST API calls to create contacts in HubSpot upon approval. |
| `leads.csv` | Flat-file storage | Raw input data or exported pipeline backups. |
| `auth.json` | Session storage | Git-ignored file that lets headless scrapers bypass authentication walls. |

---

## Prerequisites

Ensure the following are installed on your local host:

- Python 3.10+
- **MongoDB:** running locally on port `27017`
- **Playwright:** browsers installed via `playwright install`
- **HubSpot account:** a valid Private App Access Token with `crm.objects.contacts.write` permissions

---

## Local Setup Guide

### 1. Clone and Configure Environment

```bash
# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install streamlit pymongo requests pydantic playwright
playwright install chromium
```

### 2. Secure Your API Keys

> **Crucial security step:** Never hardcode your HubSpot Access Token directly into `app1.py`. Doing so will trigger GitHub's Push Protection and block your commits.

Instead, export the values in your terminal or use a `.env` file:

```bash
export HUBSPOT_ACCESS_TOKEN="your_private_app_token_here"
export HUBSPOT_API_URL="https://api.hubapi.com/crm/v3/objects/contacts"
```

---

## Execution Flow

### Step 1: Generate Authentication State

Run the Playwright login script. A browser window will open. Log into your target directory manually, and once fully logged in, press `Enter` in your terminal to save your session to `auth.json`.

```bash
python3 file1.py
```

### Step 2: Database Staging

Run your scraping and generation scripts here. Ensure your processed `ProspectProfile` data is pushed to the local MongoDB instance (`sales_agent` → `prospects` collection) with the `status` field set to `"drafted"`.

### Step 3: Human-in-the-Loop Review

Launch the Streamlit dashboard to review the pending queue:

```bash
python3 -m streamlit run app1.py
```

From the web interface, you can expand each prospect's profile, edit the finalized email copy, and click **Approve & Push**. The system will automatically call the HubSpot API, create the contact, and update the MongoDB document status to `"approved"`.

---

## Maintainer

Maintained by Shubankar Rai
