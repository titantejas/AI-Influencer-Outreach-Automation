import os
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from .db import all_influencers

def sync_to_google_sheets():
    keyfile=Path(__file__).resolve().parent.parent/"service_account.json"
    sheet_id=os.getenv("GOOGLE_SHEET_ID","").strip()
    if not keyfile.exists() or not sheet_id:
        raise RuntimeError("Add service_account.json and GOOGLE_SHEET_ID to .env.")
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
    creds=Credentials.from_service_account_file(str(keyfile),scopes=scopes)
    gc=gspread.authorize(creds)
    ws=gc.open_by_key(sheet_id).sheet1
    rows=all_influencers()
    headers=["id","name","username","profile_url","niche","followers","email","location","brand","score","status","ai_summary"]
    ws.clear()
    ws.append_row(headers)
    for r in rows:
        ws.append_row([r.get(k,"") for k in headers])
    return len(rows)
