#!/usr/bin/env python3
"""
Cloud Outreach Orchestrator
Designed to run in GitHub Actions (or locally) without user interaction.
Executes timezone dispatches, reply detection, follow-up queues, and mobile phone alerts.
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
import sqlite3

from gmail_client import GmailClient
from notify_mobile import notify_user_mobile
import db

def get_db():
    return db.get_connection()

def action_check_replies():
    """Checks Gmail inbox to detect if any prospect has replied."""
    print("[Reply Engine] Checking Gmail inbox for prospect replies...")
    client = GmailClient()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, founder_name, founder_email, status FROM leads WHERE status IN ('SENT', 'FU1_SENT', 'FU2_SENT')")
    contacted_leads = cursor.fetchall()
    
    replied_count = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for row in contacted_leads:
        lead_id = row["id"]
        company = row["name"]
        founder = row["founder_name"]
        email = row["founder_email"]
        
        if not email or "@" not in email:
            continue
            
        try:
            has_replied = client.check_recipient_replied(email)
            if has_replied:
                print(f"🔥 FOUNDER REPLIED: {founder} at {company} ({email})")
                cursor.execute(
                    "UPDATE leads SET status = 'REPLIED', replied_at = ?, last_checked_reply_at = ? WHERE id = ?",
                    (now, now, lead_id)
                )
                conn.commit()
                replied_count += 1
                
                # High priority phone notification!
                notify_user_mobile(
                    title=f"🔥 REPLIED: {company}",
                    message=f"{founder} responded to your email! Open Gmail to reply.",
                    click_url="https://mail.google.com/mail/u/0/#inbox"
                )
            else:
                cursor.execute("UPDATE leads SET last_checked_reply_at = ? WHERE id = ?", (now, lead_id))
                conn.commit()
        except Exception as e:
            print(f"[Reply Engine] Error checking {email}: {e}")
            
    conn.close()
    print(f"[Reply Engine] Completed reply check. {replied_count} new replies detected.")
    return replied_count

import time
import random

def action_send_batch(region: str = "US", dry_run: bool = False, auto_send: bool = False):
    """
    Processes emails for a given region according to founder local morning hours.
    If auto_send is True, sends them directly via Gmail API with human-like deliverability pacing.
    If auto_send is False, ensures they are drafted in Gmail and alerts mobile.
    """
    print(f"[Batch Engine] Processing batch for region: {region} (auto_send={auto_send})")
    conn = get_db()
    cursor = conn.cursor()
    
    # Flexible keyword mapping for regions with strict disambiguation
    region_upper = region.upper()
    if "US" in region_upper or "AMERICA" in region_upper:
        # Exclude Indian and Middle East hybrid profiles from US batch so they send at local morning
        region_clause = "((region LIKE '%US%' OR region LIKE '%SF%' OR region LIKE '%San Francisco%' OR region LIKE '%California%') AND region NOT LIKE '%Bengaluru%' AND region NOT LIKE '%Mumbai%' AND region NOT LIKE '%India%' AND region NOT LIKE '%Riyadh%' AND region NOT LIKE '%Dubai%')"
    elif "INDIA" in region_upper or "IN" in region_upper:
        region_clause = "(region LIKE '%Bengaluru%' OR region LIKE '%Mumbai%' OR region LIKE '%India%')"
    elif "ME" in region_upper or "MIDDLE" in region_upper or "DUBAI" in region_upper or "RIYADH" in region_upper:
        region_clause = "(region LIKE '%Riyadh%' OR region LIKE '%Dubai%' OR region LIKE '%Saudi%' OR region LIKE '%Middle East%')"
    elif "EU" in region_upper or "UK" in region_upper or "EUROPE" in region_upper or "LONDON" in region_upper:
        region_clause = "(region LIKE '%London%' OR region LIKE '%UK%' OR region LIKE '%Europe%' OR region LIKE '%Paris%')"
    elif "ALL" in region_upper:
        region_clause = "1=1"
    else:
        region_clause = f"region LIKE '%{region}%'"

    sql = f"SELECT * FROM leads WHERE {region_clause} AND LOWER(status) LIKE '%draft%'"
    cursor.execute(sql)
    leads = cursor.fetchall()
    
    if not leads:
        print(f"[Batch Engine] No pending drafted leads found for region query: {region}")
        conn.close()
        return 0
        
    print(f"[Batch Engine] Found {len(leads)} leads for {region}:")
    client = GmailClient()
    processed_count = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for row in leads:
        company = row["name"]
        founder = row["founder_name"]
        email = row["founder_email"]
        subject = row["initial_subject"]
        body = row["initial_body"]
        draft_id = row["gmail_draft_id"]
        lead_id = row["id"]
        
        print(f" -> {company} ({founder} <{email}>)")
        
        if dry_run:
            processed_count += 1
            continue
            
        try:
            if auto_send:
                if draft_id:
                    send_res = client.send_draft(draft_id)
                else:
                    send_res = client.send_message(email, subject, body)
                thread_id = send_res.get("threadId")
                cursor.execute(
                    "UPDATE leads SET status = 'SENT', sent_at = ?, gmail_thread_id = ? WHERE id = ?",
                    (now, thread_id, lead_id)
                )
                conn.commit()
                processed_count += 1
                print(f"   🚀 Sent automatically to {email}")
                # Rate limit & deliverability delay (2.5 - 4.5s random jitter)
                time.sleep(random.uniform(2.5, 4.5))
            else:
                # If not drafted yet in Gmail, create draft
                if not draft_id:
                    draft_res = client.create_draft(email, subject, body)
                    new_draft_id = draft_res.get("id")
                    thread_id = draft_res.get("message", {}).get("threadId")
                    cursor.execute(
                        "UPDATE leads SET gmail_draft_id = ?, gmail_thread_id = ? WHERE id = ?",
                        (new_draft_id, thread_id, lead_id)
                    )
                    conn.commit()
                processed_count += 1
        except Exception as e:
            print(f"[Batch Engine] Error processing {company}: {e}")
            
    conn.close()
    
    # Send mobile push alert
    status_text = "sent automatically" if auto_send else "ready in Gmail Drafts"
    notify_user_mobile(
        title=f"Outreach Alert: {region} Batch",
        message=f"{processed_count} emails for {region} startups are {status_text}.",
        click_url="https://mail.google.com/mail/u/0/#drafts"
    )
    
    return processed_count

def action_process_followups(auto_send: bool = False):
    """
    Finds sent leads that are 3+ days old with no reply and creates Follow-Up 1,
    or 7+ days old for Follow-Up 2.
    """
    print("[Follow-Up Engine] Evaluating sent leads for scheduled follow-ups...")
    conn = get_db()
    cursor = conn.cursor()
    client = GmailClient()
    
    now = datetime.now(timezone.utc)
    cursor.execute("SELECT * FROM leads WHERE status IN ('SENT', 'FU1_SENT')")
    leads = cursor.fetchall()
    
    fu_count = 0
    for row in leads:
        lead_id = row["id"]
        company = row["name"]
        founder = row["founder_name"]
        email = row["founder_email"]
        status = row["status"]
        sent_at_str = row["sent_at"]
        thread_id = row["gmail_thread_id"]
        
        if not sent_at_str:
            continue
            
        sent_at = datetime.fromisoformat(sent_at_str)
        days_passed = (now - sent_at).days
        
        # Follow-Up 1 (Day +3)
        if status == "SENT" and days_passed >= 3:
            # First verify they haven't replied
            if client.check_recipient_replied(email):
                cursor.execute("UPDATE leads SET status = 'REPLIED', replied_at = ? WHERE id = ?", (now.isoformat(), lead_id))
                conn.commit()
                continue
                
            subject = row["fu1_subject"] or f"Re: {row['initial_subject']}"
            body = row["fu1_body"]
            
            if auto_send:
                client.send_message(email, subject, body, thread_id=thread_id)
                cursor.execute("UPDATE leads SET status = 'FU1_SENT', sent_at = ? WHERE id = ?", (now.isoformat(), lead_id))
            else:
                draft_res = client.create_draft(email, subject, body, thread_id=thread_id)
                cursor.execute("UPDATE leads SET status = 'FU1_QUEUED' WHERE id = ?", (lead_id,))
                
            conn.commit()
            fu_count += 1
            print(f"[Follow-Up Engine] Queued FU1 for {company} ({founder})")
            
        # Follow-Up 2 (Day +7)
        elif status == "FU1_SENT" and days_passed >= 4:
            if client.check_recipient_replied(email):
                cursor.execute("UPDATE leads SET status = 'REPLIED', replied_at = ? WHERE id = ?", (now.isoformat(), lead_id))
                conn.commit()
                continue
                
            subject = row["fu2_subject"] or f"Re: {row['initial_subject']}"
            body = row["fu2_body"]
            
            if auto_send:
                client.send_message(email, subject, body, thread_id=thread_id)
                cursor.execute("UPDATE leads SET status = 'FU2_SENT', sent_at = ? WHERE id = ?", (now.isoformat(), lead_id))
            else:
                draft_res = client.create_draft(email, subject, body, thread_id=thread_id)
                cursor.execute("UPDATE leads SET status = 'FU2_QUEUED' WHERE id = ?", (lead_id,))
                
            conn.commit()
            fu_count += 1
            print(f"[Follow-Up Engine] Queued FU2 for {company} ({founder})")
            
    conn.close()
    
    if fu_count > 0:
        notify_user_mobile(
            title="Follow-Up Alert",
            message=f"{fu_count} personalized follow-up emails queued in Gmail for unreplied leads.",
            click_url="https://mail.google.com/mail/u/0/#drafts"
        )
    return fu_count

def action_status():
    """Prints campaign state breakdown."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
    rows = cursor.fetchall()
    print("=" * 45)
    print("           OUTREACH PIPELINE STATUS          ")
    print("=" * 45)
    total = 0
    for r in rows:
        print(f"  {r['status']:<18}: {r['count']}")
        total += r['count']
    print("-" * 45)
    print(f"  {'TOTAL LEADS':<18}: {total}")
    print("=" * 45)
    conn.close()

from research_and_generate import run_multi_region_expansion

def action_research_and_draft(region: str = None):
    """Sources new multi-region startups, deduplicates, and drafts them into Gmail."""
    print(f"[Research & Draft Engine] Sourcing new startups (region filter: {region})...")
    target_regions = [region] if region and region.upper() != "ALL" else None
    leads = run_multi_region_expansion(target_regions=target_regions, dry_run=False, create_drafts=True)
    print(f"[Research & Draft Engine] Finished. {len(leads)} new emails drafted in Gmail.")
    return len(leads)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Outreach Orchestrator")
    parser.add_argument("--action", choices=["research-and-draft", "send-batch", "check-replies", "followups", "status"], default="research-and-draft")
    parser.add_argument("--region", default="All", help="Target region (India, Middle East, Europe, US, All)")
    parser.add_argument("--auto-send", action="store_true", help="Send directly instead of creating drafts")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing to Gmail")
    args = parser.parse_args()
    
    if args.action == "research-and-draft":
        action_research_and_draft(region=args.region)
    elif args.action == "status":
        action_status()
    elif args.action == "check-replies":
        action_check_replies()
    elif args.action == "send-batch":
        action_send_batch(region=args.region, dry_run=args.dry_run, auto_send=args.auto_send)
    elif args.action == "followups":
        action_process_followups(auto_send=args.auto_send)

