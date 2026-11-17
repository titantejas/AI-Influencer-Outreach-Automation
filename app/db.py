import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "outreach.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS influencers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT, username TEXT NOT NULL UNIQUE, profile_url TEXT,
          niche TEXT, followers INTEGER DEFAULT 0, email TEXT, location TEXT,
          bio TEXT, brand TEXT, ai_summary TEXT, score REAL DEFAULT 0,
          status TEXT DEFAULT 'New Lead', notes TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          last_contacted_at TEXT, followup_stage INTEGER DEFAULT 0,
          gmail_thread_id TEXT, last_message_id TEXT, opted_out INTEGER DEFAULT 0
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS email_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT, influencer_id INTEGER,
          kind TEXT, subject TEXT, body TEXT, sent_at TEXT,
          gmail_message_id TEXT, outcome TEXT DEFAULT 'Draft',
          FOREIGN KEY(influencer_id) REFERENCES influencers(id)
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS settings (
          key TEXT PRIMARY KEY, value TEXT
        )""")

def upsert_influencer(row):
    username = str(row.get("username","")).strip().lstrip("@")
    if not username: return False
    with connect() as con:
        old = con.execute("SELECT id FROM influencers WHERE username=?", (username,)).fetchone()
        vals = (row.get("name",""), username, row.get("profile_url", f"https://www.instagram.com/{username}/"),
                row.get("niche",""), int(row.get("followers") or 0), row.get("email",""),
                row.get("location",""), row.get("bio",""), row.get("brand",""))
        if old:
            con.execute("""UPDATE influencers SET name=?, profile_url=?, niche=?, followers=?,
                email=?, location=?, bio=?, brand=?, updated_at=CURRENT_TIMESTAMP WHERE username=?""",
                (vals[0], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], vals[8], username))
            return False
        con.execute("""INSERT INTO influencers(name,username,profile_url,niche,followers,email,location,bio,brand)
            VALUES(?,?,?,?,?,?,?,?,?)""", vals)
        return True

def all_influencers():
    with connect() as con:
        return [dict(x) for x in con.execute("SELECT * FROM influencers ORDER BY score DESC, created_at DESC")]

def update_fields(iid, **kwargs):
    allowed = {"ai_summary","score","status","notes","email","opted_out","followup_stage","last_contacted_at","gmail_thread_id","last_message_id"}
    kwargs = {k:v for k,v in kwargs.items() if k in allowed}
    if not kwargs: return
    sql = ", ".join(f"{k}=?" for k in kwargs)
    with connect() as con: con.execute(f"UPDATE influencers SET {sql}, updated_at=CURRENT_TIMESTAMP WHERE id=?", (*kwargs.values(), iid))

def add_email_log(iid, kind, subject, body, sent_at=None, message_id=None, outcome="Draft"):
    with connect() as con:
        con.execute("""INSERT INTO email_log(influencer_id,kind,subject,body,sent_at,gmail_message_id,outcome)
                       VALUES(?,?,?,?,?,?,?)""", (iid,kind,subject,body,sent_at,message_id,outcome))

def email_history(iid):
    with connect() as con:
        return [dict(x) for x in con.execute("SELECT * FROM email_log WHERE influencer_id=? ORDER BY id DESC",(iid,))]

def save_setting(key, value):
    with connect() as con: con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))

def get_setting(key, default=""):
    with connect() as con:
        row=con.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
        return row["value"] if row else default

def due_followups():
    with connect() as con:
        return [dict(x) for x in con.execute("""
          SELECT * FROM influencers WHERE email!='' AND opted_out=0
          AND status IN ('Email Sent','Follow-up Due')
          AND last_contacted_at IS NOT NULL ORDER BY last_contacted_at
        """)]

def stats():
    with connect() as con:
        total=con.execute("SELECT COUNT(*) n FROM influencers").fetchone()["n"]
        sent=con.execute("SELECT COUNT(*) n FROM influencers WHERE status IN ('Email Sent','Follow-up Due','Replied','Interested','Collaboration Confirmed')").fetchone()["n"]
        replied=con.execute("SELECT COUNT(*) n FROM influencers WHERE status IN ('Replied','Interested','Not Interested','Collaboration Confirmed')").fetchone()["n"]
        interested=con.execute("SELECT COUNT(*) n FROM influencers WHERE status IN ('Interested','Collaboration Confirmed')").fetchone()["n"]
        return {"leads":total,"contacted":sent,"replied":replied,"interested":interested}
