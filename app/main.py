import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from .db import init_db, upsert_influencer, all_influencers, update_fields, add_email_log, email_history, stats, due_followups
from .ai import score_influencer, draft_email, classify_reply

load_dotenv()
st.set_page_config(page_title="Influencer Outreach AI",page_icon="📣",layout="wide")
init_db()
st.title("📣 Influencer Outreach Automation")
st.caption("Research • AI qualification • CRM • Human-approved Gmail outreach • Follow-ups • Reply assistant")
st.info("Compliance-first: add only publicly available business contact details or contacts supplied with permission. No private data or unauthorized Instagram scraping. All outbound messages require human approval.")

with st.sidebar:
    st.header("Campaign setup")
    brand=st.text_input("Brand / client", "Demo Brand")
    campaign=st.text_area("Campaign brief", "Explore a potential creator partnership for an upcoming product campaign.")
    sender=st.text_input("Sender name","Campaign Team")
    company=st.text_input("Sender company","Demo Brand")
    st.divider()
    st.caption("Integrations are optional until configured. Add API credentials to .env.")

tab1,tab2,tab3,tab4,tab5=st.tabs(["Dashboard & CRM","Research import","AI qualification","Email studio","Replies & follow-ups"])

with tab1:
    s=stats(); cols=st.columns(4)
    for c,(label,key) in zip(cols,[("Leads","leads"),("Contacted","contacted"),("Replies","replied"),("Interested","interested")]):
        c.metric(label,s[key])
    data=all_influencers()
    if data:
        df=pd.DataFrame(data)
        show=[x for x in ["id","name","username","niche","followers","email","location","score","status"] if x in df]
        edited=st.data_editor(df[show],use_container_width=True,hide_index=True,disabled=["id","username"])
        if st.button("Save CRM edits"):
            for _,r in edited.iterrows(): update_fields(int(r["id"]),status=r["status"])
            st.success("CRM statuses saved.")
        selected=st.selectbox("Open lead",options=[int(x["id"]) for x in data],format_func=lambda x: next((f'@{r["username"]} — {r["name"]}' for r in data if r["id"]==x),str(x)))
        if selected:
            rec=next(r for r in data if r["id"]==selected)
            st.write({k:rec.get(k) for k in ["profile_url","bio","ai_summary","score","notes"]})
            st.write("Email activity")
            st.dataframe(pd.DataFrame(email_history(selected)),use_container_width=True)
    else: st.write("No leads yet. Import sample or researched public profile data in the Research tab.")

with tab2:
    st.subheader("Import public influencer research")
    st.write("Use the CSV template. Research can be collected manually or through an authorized data provider/API.")
    st.download_button("Download CSV template",
       "name,username,profile_url,niche,followers,email,location,bio,brand\nAarav Creator,aarav_demo,https://www.instagram.com/aarav_demo/,Fitness,25000,aarav@example.com,Pune,Public fitness creator profile,Demo Brand\n",
       file_name="influencers_template.csv",mime="text/csv")
    up=st.file_uploader("Upload influencer CSV",type=["csv"])
    if up:
        df=pd.read_csv(up).fillna("")
        st.dataframe(df.head(20),use_container_width=True)
        if st.button("Import leads"):
            added=0
            for row in df.to_dict("records"):
                added += int(upsert_influencer(row))
            st.success(f"Import complete. {added} new leads added; duplicate usernames updated.")
    st.caption("Required field: username. Do not import private, scraped-at-scale, or non-consensual personal data.")

with tab3:
    st.subheader("Claude AI qualification")
    data=all_influencers()
    if not data: st.warning("Import leads first.")
    else:
        options=[r["id"] for r in data]
        chosen=st.multiselect("Select leads to analyse",options,default=options[:min(3,len(options))],
            format_func=lambda x: next(f'@{r["username"]}' for r in data if r["id"]==x))
        if st.button("Analyse selected with Claude"):
            progress=st.progress(0)
            for i,iid in enumerate(chosen):
                p=next(r for r in data if r["id"]==iid)
                try:
                    result=score_influencer(p,brand,campaign)
                    update_fields(iid,score=float(result.get("overall_score",0)),ai_summary=result.get("summary",""))
                    st.write(f'**@{p["username"]} — {result.get("overall_score",0)}/100**')
                    st.write(result.get("summary",""))
                    st.caption(result.get("rationale",""))
                except Exception as e: st.error(str(e))
                progress.progress((i+1)/max(1,len(chosen)))
    st.caption("AI scores are decision support, not verified audience analytics. Review source evidence before outreach.")

with tab4:
    st.subheader("Personalized email studio")
    data=all_influencers()
    eligible=[r for r in data if r.get("email") and not r.get("opted_out")]
    if not eligible: st.warning("No leads with a public business email. Add verified business emails in the CRM.")
    else:
        iid=st.selectbox("Choose influencer", [r["id"] for r in eligible],
                         format_func=lambda x: next(f'@{r["username"]} ({r["email"]})' for r in eligible if r["id"]==x))
        person=next(r for r in eligible if r["id"]==iid)
        kind=st.selectbox("Email type",["initial","follow-up 1","follow-up 2"])
        if st.button("Generate personalized draft"):
            try:
                d=draft_email(person,brand,campaign,sender,company,kind)
                st.session_state["draft"]={"id":iid,"kind":kind,"subject":d["subject"],"body":d["body"]}
            except Exception as e: st.error(str(e))
        if "draft" in st.session_state and st.session_state["draft"]["id"]==iid:
            draft=st.session_state["draft"]
            subject=st.text_input("Subject",draft["subject"])
            body=st.text_area("Body",draft["body"],height=240)
            st.warning("Review recipient, claims, sender identity and opt-out wording. Sending is a manual, explicit action.")
            confirm=st.checkbox("I reviewed this message and approve sending it to this business contact.")
            if st.button("Send approved email through Gmail",disabled=not confirm):
                try:
                    from .gmail_service import send_email
                    sent=send_email(person["email"],subject,body)
                    now=datetime.now(timezone.utc).isoformat()
                    add_email_log(iid,draft["kind"],subject,body,now,sent.get("id"),"Sent")
                    update_fields(iid,status="Email Sent",last_contacted_at=now,followup_stage=0,
                                  gmail_thread_id=sent.get("threadId"),last_message_id=sent.get("id"))
                    st.success("Email sent. Gmail message ID recorded.")
                except Exception as e: st.error(f"Gmail send failed: {e}")
    st.caption("Configure Gmail OAuth Desktop credentials.json. First use opens Google's consent flow.")

with tab5:
    st.subheader("Reply detection and AI reply drafting")
    col1,col2=st.columns(2)
    with col1:
        if st.button("Check Gmail for recent replies"):
            try:
                from .gmail_service import recent_replies
                msgs=recent_replies()
                st.session_state["replies"]=msgs
                st.success(f"Loaded {len(msgs)} recent messages. Match them to CRM leads before updating statuses.")
            except Exception as e: st.error(str(e))
    with col2:
        st.write("Follow-up queue")
        due=due_followups()
        st.write(f"{len(due)} contacted leads eligible for review.")
        st.caption("The app intentionally queues follow-ups for review; it does not silently send automated emails.")
    msgs=st.session_state.get("replies",[])
    if msgs:
        for idx,m in enumerate(msgs):
            with st.expander(f'{m["subject"]} — {m["from"]}'):
                st.text(m["body"][:2500])
                if st.button("Classify and draft reply",key=f"classify{idx}"):
                    try:
                        result=classify_reply(m["body"])
                        st.session_state[f"reply_result_{idx}"]=result
                    except Exception as e: st.error(str(e))
                result=st.session_state.get(f"reply_result_{idx}")
                if result:
                    st.write(result)
                    leads=all_influencers()
                    match=st.selectbox("Match this reply to lead",[""]+[r["id"] for r in leads],
                       format_func=lambda x: "Select lead" if x=="" else next(f'@{r["username"]}' for r in leads if r["id"]==x),key=f"match{idx}")
                    if match:
                        if st.button("Update CRM status",key=f"update{idx}"):
                            category=result.get("category","Other")
                            status="Interested" if category in ("Interested","Collaboration Request","Pricing Enquiry") else ("Not Interested" if category=="Not Interested" else "Replied")
                            if category=="Opt-out": status="Not Interested"; update_fields(int(match),opted_out=1)
                            update_fields(int(match),status=status)
                            st.success(f"CRM updated: {status}")
                    st.text_area("AI reply draft — review before sending",result.get("draft_reply",""),key=f"replydraft{idx}")
    st.divider()
    st.subheader("Follow-up review queue")
    due=due_followups()
    if due:
        st.dataframe(pd.DataFrame(due)[["id","username","email","last_contacted_at","followup_stage","status"]],use_container_width=True)
        st.caption("Suggested cadence from the assignment: first follow-up after 3–5 days; second after another 5–7 days. Check replies/opt-outs before preparing a follow-up.")
    else: st.write("No follow-up candidates currently.")

st.divider()
st.caption("Prototype note: use real Gmail/Google credentials only in a private local environment. Keep API keys out of source control.")
