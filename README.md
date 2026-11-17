# AI-Powered Instagram Influencer Research & Email Outreach Automation

A practical, local-first internship assignment implementation for Sankar Group. It provides a Streamlit dashboard, SQLite CRM, Claude-powered qualification and email/reply drafting, Gmail OAuth sending/reply retrieval, and optional Google Sheets export.

## 1. Features mapped to the assignment

| Assignment requirement | Implementation |
|---|---|
| Instagram research | CSV import for manually researched/public business profile data; template download |
| AI filtering | Claude scoring, category, summary and rationale |
| CRM | SQLite database; unique Instagram username; statuses and activity history |
| Cold email | Claude-generated personalized drafts; explicit human approval; Gmail API |
| Follow-ups | Contact date/stage queue and cadence guidance; human review before sending |
| Reply management | Gmail recent-message retrieval; Claude classification and reply draft; human review |
| Final demonstration | Sample CSV, local dashboard, test script and demo guide |

**Important scope and compliance:** Instagram data is supplied through a CSV template so the operator can use public profile details, manual research, or an authorized provider/API. This project does not bypass login, scrape private accounts, harvest private data, or evade platform limits. Only public business contact details or contacts supplied with permission should be used. Gmail sending is user-authorized and each message requires a human approval checkbox. AI replies are drafts only.

## 2. Requirements

- Python 3.10+
- A Claude API key (optional; needed for AI functions)
- A Google Cloud project with Gmail API enabled and OAuth Desktop credentials (needed for Gmail)
- Optional Google service-account credentials and a Google Sheet (for Sheets export; helper module included)

## 3. Installation

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add `ANTHROPIC_API_KEY`. Never commit `.env` or credentials.

## 4. Run

```bash
streamlit run run.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## 5. Demo workflow (10–15 minutes)

1. Start the dashboard.
2. Open **Research import**, upload `sample_data/influencers.csv`, and import.
3. Open **Dashboard & CRM** to show lead records and duplicate prevention.
4. In **AI qualification**, select sample leads and click Analyse (requires Claude API key).
5. In **Email studio**, select a sample contact and generate an initial draft.
6. Review the content and recipient. For a real test, replace sample addresses with a test mailbox you control, configure Gmail OAuth, tick the approval box, and send.
7. In **Replies & follow-ups**, check Gmail for recent replies and classify a reply. Match it to a lead and update CRM. AI reply output remains a draft.
8. Show the follow-up review queue and explain the 3–5 day / additional 5–7 day cadence.

Do not send to the sample `example.com` addresses; they are placeholders.

## 6. Gmail OAuth setup

1. In Google Cloud Console, create/select a project and enable Gmail API.
2. Configure OAuth consent screen for the intended test users.
3. Create an OAuth Client ID of type **Desktop app** and download the JSON.
4. Save it as `credentials.json` in the project root.
5. Run the app and use Gmail send/reply actions. Complete Google's consent flow in the browser.
6. The app creates `token.json`; keep it private and do not commit it.

Scopes requested: `gmail.send` and `gmail.readonly`.

## 7. Google Sheets setup (optional)

1. Create a Google Cloud service account and enable Google Sheets API.
2. Download its JSON key as `service_account.json` in the project root.
3. Share the target Sheet with the service-account email as Editor.
4. Put the Sheet ID in `.env` as `GOOGLE_SHEET_ID`.
5. Call `app.sheets.sync_to_google_sheets()` from a trusted local Python session.

## 8. Data model and statuses

Influencer records include profile identity, niche, follower count, public business email, location, AI score/summary, status, opt-out flag, last contact timestamp and follow-up stage. Username is unique, preventing duplicate records.

Suggested lifecycle: New Lead → Email Available → Email Sent → Follow-up Due → Replied → Interested / Not Interested → Collaboration Confirmed. Opt-outs are excluded from eligible email drafts.

## 9. Follow-up policy

The assignment specifies a first follow-up after 3–5 days and a second after another 5–7 days. This prototype surfaces contacted records for human review rather than silently dispatching automated follow-ups. Before any follow-up, verify there is no reply, decline, or opt-out. Apply reasonable sending limits and applicable anti-spam requirements.

## 10. Testing

```bash
pytest -q
```

The test checks username-based deduplication. For a clean demo database, stop the app and delete `data/outreach.db`; it will be recreated on next launch.

## 11. Limitations / next improvements

- Instagram discovery is an operator-led CSV import. A production deployment should connect only to an authorized Instagram/Meta API or licensed provider that permits the intended use.
- Gmail replies are fetched from a recent-message query and require human matching to a CRM lead; production should correlate Gmail thread IDs and maintain webhook/polling state.
- The follow-up queue is review-based; a production scheduler should use a background worker, suppression checks, rate limits, audit logs and explicit campaign approvals.
- Google Sheets sync helper is provided but is not exposed as a dashboard action yet.
- Deploy behind authentication, use a secrets manager, encrypt sensitive tokens, define retention periods, and add role-based access before multi-user use.

## 12. Troubleshooting

- **Claude error:** check `ANTHROPIC_API_KEY`, account access and model availability.
- **Gmail credentials error:** confirm `credentials.json` is a Desktop OAuth client and Gmail API is enabled.
- **Import error:** ensure CSV includes `username`; optional fields can be blank.
- **Streamlit import error:** run `streamlit run run.py` from the project root.

## 13. Architecture

```text
Public profile research / authorized source
                 |
             CSV import
                 |
        Streamlit application
                 |
        SQLite influencer CRM
          /       |        \\
     Claude AI  Gmail API  Google Sheets
    scoring &   approved    optional
     drafting   sending
                 |
        Gmail reply retrieval
                 |
         Claude classification
                 |
      Human review + CRM update
```
