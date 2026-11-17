import os, base64
from email.mime.text import MIMEText
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES=["https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/gmail.readonly"]
ROOT=Path(__file__).resolve().parent.parent

def gmail_service():
    creds=None
    token=ROOT/"token.json"
    client=ROOT/"credentials.json"
    if token.exists(): creds=Credentials.from_authorized_user_file(str(token),SCOPES)
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    if not creds or not creds.valid:
        if not client.exists():
            raise RuntimeError("Add Google OAuth Desktop credentials.json to the project root.")
        flow=InstalledAppFlow.from_client_secrets_file(str(client),SCOPES)
        creds=flow.run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("gmail","v1",credentials=creds)

def send_email(to, subject, body):
    service=gmail_service()
    msg=MIMEText(body)
    msg["to"]=to; msg["subject"]=subject
    raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent=service.users().messages().send(userId="me",body={"raw":raw}).execute()
    return sent

def recent_replies(query="newer_than:30d -from:me"):
    service=gmail_service()
    result=service.users().messages().list(userId="me",q=query,maxResults=50).execute()
    output=[]
    for item in result.get("messages",[]):
        msg=service.users().messages().get(userId="me",id=item["id"],format="full").execute()
        headers={h["name"].lower():h["value"] for h in msg.get("payload",{}).get("headers",[])}
        body=""
        def walk(part):
            nonlocal body
            data=part.get("body",{}).get("data")
            if data and part.get("mimeType") in ("text/plain","text/html") and not body:
                try: body=base64.urlsafe_b64decode(data+"==").decode(errors="ignore")
                except Exception: pass
            for child in part.get("parts",[]): walk(child)
        walk(msg.get("payload",{}))
        output.append({"id":msg["id"],"thread_id":msg.get("threadId"),"from":headers.get("from",""),
                       "subject":headers.get("subject",""),"body":body[:5000]})
    return output
