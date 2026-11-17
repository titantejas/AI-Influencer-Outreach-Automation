import os, json
from anthropic import Anthropic

def _client():
    key=os.getenv("ANTHROPIC_API_KEY","").strip()
    if not key: raise RuntimeError("Set ANTHROPIC_API_KEY in .env to enable Claude AI.")
    return Anthropic(api_key=key)

def _ask(prompt):
    msg=_client().messages.create(
        model=os.getenv("CLAUDE_MODEL","claude-3-5-haiku-latest"),
        max_tokens=900,
        messages=[{"role":"user","content":prompt}]
    )
    return "".join(b.text for b in msg.content if getattr(b,"type",None)=="text")

def score_influencer(person, brand, campaign):
    prompt=f"""You are an influencer campaign research assistant. Use only supplied public information.
Brand: {brand}
Campaign: {campaign}
Profile: {json.dumps(person, ensure_ascii=False)}
Return JSON only with keys niche_fit (0-100), audience_fit (0-100), brand_safety (0-100),
overall_score (0-100), category, summary (max 60 words), rationale.
Do not invent audience demographics, engagement rates, contact details, or facts.
If evidence is missing, state that in summary/rationale."""
    raw=_ask(prompt)
    try:
        start=raw.find("{"); end=raw.rfind("}")+1
        return json.loads(raw[start:end])
    except Exception:
        return {"overall_score":0,"summary":raw[:500],"rationale":"AI response could not be parsed."}

def draft_email(person, brand, campaign, sender_name, sender_company, kind="initial"):
    prompt=f"""Write a concise, respectful {kind} influencer collaboration email.
Brand: {brand}. Campaign: {campaign}. Sender: {sender_name}, {sender_company}.
Public profile data: {json.dumps(person, ensure_ascii=False)}.
Personalize only using supplied facts. Do not invent prior contact, metrics, payment, or product claims.
Include a clear low-pressure call to action, sender identification, and a simple opt-out sentence.
Return JSON only: {{ "subject": "...", "body": "..." }}."""
    raw=_ask(prompt)
    try:
        start=raw.find("{"); end=raw.rfind("}")+1
        return json.loads(raw[start:end])
    except Exception:
        return {"subject":f"{brand} collaboration enquiry","body":raw}

def classify_reply(text):
    prompt=f"""Classify this email reply. Return JSON only with category one of
Interested, Not Interested, Pricing Enquiry, Collaboration Request, Opt-out, Other;
summary (max 40 words), suggested_action (max 30 words), draft_reply.
Do not send anything. Email:
{text[:5000]}"""
    raw=_ask(prompt)
    try:
        start=raw.find("{"); end=raw.rfind("}")+1
        return json.loads(raw[start:end])
    except Exception:
        return {"category":"Other","summary":raw[:300],"suggested_action":"Review manually","draft_reply":""}
