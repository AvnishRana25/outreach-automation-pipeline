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

def sync_draft_states(client=None) -> int:
    """
    Verifies leads in 'Drafted in Gmail' status against Gmail API.
    If the draft was already sent manually by the user, updates status to 'SENT'.
    If the draft was trashed, marks it as 'ARCHIVED'.
    Prevents ghost drafts from falsely blocking research or throwing 400 errors.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, gmail_draft_id FROM leads WHERE LOWER(status) LIKE '%draft%' AND gmail_draft_id IS NOT NULL")
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return 0

    client = client or GmailClient()
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for r in rows:
        did = r["gmail_draft_id"]
        lid = r["id"]
        name = r["name"]
        try:
            draft = client._api_request(f"drafts/{did}")
            msg = draft.get("message", {})
            labels = msg.get("labelIds", [])
            thread_id = msg.get("threadId")

            if "SENT" in labels:
                internal_date = int(msg.get("internalDate", 0)) / 1000
                sent_at = datetime.fromtimestamp(internal_date, tz=timezone.utc).isoformat() if internal_date else now
                cursor.execute(
                    "UPDATE leads SET status = 'SENT', sent_at = ?, gmail_thread_id = ? WHERE id = ?",
                    (sent_at, thread_id, lid)
                )
                updated += 1
                print(f"[Draft Sync] Synced {name} -> SENT (already sent in Gmail)")
            elif "TRASH" in labels:
                cursor.execute("UPDATE leads SET status = 'ARCHIVED' WHERE id = ?", (lid,))
                updated += 1
                print(f"[Draft Sync] Synced {name} -> ARCHIVED (trashed in Gmail)")
        except Exception:
            pass

    if updated > 0:
        conn.commit()
    conn.close()
    return updated

def action_send_batch(region: str = "US", dry_run: bool = False, auto_send: bool = False):
    """
    Processes emails for a given region according to founder local morning hours.
    If auto_send is True, sends them directly via Gmail API with human-like deliverability pacing.
    If auto_send is False, ensures they are drafted in Gmail and alerts mobile.
    """
    print(f"[Batch Engine] Processing batch for region: {region} (auto_send={auto_send})")
    client = GmailClient()
    
    # Sync drafts first to eliminate phantom drafts
    sync_draft_states(client)

    conn = get_db()
    cursor = conn.cursor()
    
    region_clause = db.get_region_sql_filter(region)
    sql = f"SELECT * FROM leads WHERE {region_clause} AND LOWER(status) LIKE '%draft%'"
    cursor.execute(sql)
    leads = cursor.fetchall()
    
    if not leads:
        print(f"[Batch Engine] No pending drafted leads found for region query: {region}")
        conn.close()
        return 0
        
    print(f"[Batch Engine] Found {len(leads)} leads for {region}:")
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
                send_res = None
                if draft_id:
                    try:
                        send_res = client.send_draft(draft_id)
                    except Exception as err:
                        # Check if draft was already sent manually or deleted
                        print(f"   ⚠️ Could not send draft {draft_id}: {err}")
                        try:
                            draft_info = client._api_request(f"drafts/{draft_id}")
                            msg = draft_info.get("message", {})
                            if "SENT" in msg.get("labelIds", []):
                                print(f"   ℹ️ Draft {draft_id} was already sent in Gmail.")
                                thread_id = msg.get("threadId")
                                cursor.execute(
                                    "UPDATE leads SET status = 'SENT', sent_at = ?, gmail_thread_id = ? WHERE id = ?",
                                    (now, thread_id, lead_id)
                                )
                                conn.commit()
                                processed_count += 1
                                continue
                        except Exception:
                            pass
                        # Fallback: direct send
                        print(f"   🚀 Fallback: Sending directly via Gmail API to {email}...")
                        send_res = client.send_message(email, subject, body)
                else:
                    send_res = client.send_message(email, subject, body)
                
                thread_id = send_res.get("threadId") if send_res else None
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
        action_text = "sent automatically to" if auto_send else "queued in Gmail Drafts for"
        notify_user_mobile(
            title="Follow-Up Alert",
            message=f"{fu_count} personalized follow-up emails {action_text} unreplied leads.",
            click_url="https://mail.google.com/mail/u/0/#inbox" if auto_send else "https://mail.google.com/mail/u/0/#drafts"
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

def action_research_and_draft(region: str = None, dry_run: bool = False):
    """Sources new multi-region startups, deduplicates, and drafts them into Gmail."""
    print(f"[Research & Draft Engine] Sourcing new startups (region filter: {region}, dry_run={dry_run})...")
    target_regions = [region] if region and region.upper() != "ALL" else None
    leads = run_multi_region_expansion(target_regions=target_regions, dry_run=dry_run, create_drafts=not dry_run)
    print(f"[Research & Draft Engine] Finished. {len(leads)} new emails drafted in Gmail.")
    return len(leads)

def is_region_in_sending_window(region: str) -> tuple[bool, str]:
    """
    Evaluates whether target region is currently within the local founder morning window (08:30 - 12:30 local time)
    on a business day.
    Timezones:
      - India: UTC+5:30 (IST). Window: 08:30 - 12:30 IST (03:00 - 07:00 UTC). Mon-Fri.
      - Middle East: UTC+3 (AST Riyadh) / UTC+4 (GST Dubai). Window: 08:30 - 12:30 Riyadh time (05:30 - 09:30 UTC). Sun-Thu.
      - Europe: UTC+1 (BST London) / UTC+2 (CEST Paris/Berlin). Window: 08:00 - 12:30 London/CEST (06:30 - 11:30 UTC). Mon-Fri.
      - US: UTC-7 (PDT SF/West Coast). Window: 08:30 - 12:30 PDT (15:30 - 19:30 UTC). Mon-Fri.
    Returns:
      (in_window: bool, status_desc: str)
    """
    now_utc = datetime.now(timezone.utc)
    r_upper = region.upper()
    
    if "INDIA" in r_upper or "IN" in r_upper:
        local_time = now_utc + timedelta(hours=5, minutes=30)
        weekday = local_time.weekday()
        time_decimal = local_time.hour + local_time.minute / 60.0
        time_str = local_time.strftime("%I:%M %p IST")
        is_weekday = weekday in range(0, 5)
        in_hours = 8.5 <= time_decimal <= 12.5
        desc = f"{time_str} ({local_time.strftime('%A')})"
        return (is_weekday and in_hours, desc)
        
    elif "ME" in r_upper or "MIDDLE" in r_upper or "DUBAI" in r_upper or "RIYADH" in r_upper:
        local_time = now_utc + timedelta(hours=3) # Riyadh AST
        weekday = local_time.weekday()
        time_decimal = local_time.hour + local_time.minute / 60.0
        time_str = local_time.strftime("%I:%M %p AST (Riyadh)")
        is_weekday = weekday in [6, 0, 1, 2, 3, 4]
        in_hours = 8.5 <= time_decimal <= 12.5
        desc = f"{time_str} ({local_time.strftime('%A')})"
        return (is_weekday and in_hours, desc)
        
    elif "EU" in r_upper or "UK" in r_upper or "EUROPE" in r_upper:
        local_time = now_utc + timedelta(hours=1) # London BST
        weekday = local_time.weekday()
        time_decimal = local_time.hour + local_time.minute / 60.0
        time_str = local_time.strftime("%I:%M %p BST (London)")
        is_weekday = weekday in range(0, 5)
        in_hours = 8.0 <= time_decimal <= 12.5
        desc = f"{time_str} ({local_time.strftime('%A')})"
        return (is_weekday and in_hours, desc)
        
    elif "US" in r_upper or "AMERICA" in r_upper:
        local_time = now_utc - timedelta(hours=7) # PDT San Francisco
        weekday = local_time.weekday()
        time_decimal = local_time.hour + local_time.minute / 60.0
        time_str = local_time.strftime("%I:%M %p PDT (SF)")
        is_weekday = weekday in range(0, 5)
        in_hours = 8.5 <= time_decimal <= 12.5
        desc = f"{time_str} ({local_time.strftime('%A')})"
        return (is_weekday and in_hours, desc)
        
    return (True, f"{now_utc.strftime('%H:%M UTC')} (Unrestricted)")

def action_tick(dry_run: bool = False, auto_send: bool = True):
    """
    Heartbeat tick designed to be called by any scheduled cron or background runner.
    Completely idempotent and timezone-aware:
    1. Always runs inbox reply detection.
    2. Evaluates each region (India, Middle East, Europe, US):
       - If within local morning sending window AND 0 emails sent today:
         - Dispatches send-batch for that region.
         - If 0 drafts exist in candidate/leads, replenishes via research-and-draft first!
       - If outside window, logs status and avoids sending.
    3. Processes due follow-ups (Day +3, Day +7) during business hours.
    """
    print("=" * 60)
    print("       TIMEZONE-AWARE ORCHESTRATOR HEARTBEAT TICK       ")
    print("=" * 60)
    now_utc = datetime.now(timezone.utc)
    print(f"[Tick Engine] Current UTC Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 1. Sync Draft States with Gmail (eliminates phantom drafts)
    try:
        sync_draft_states()
    except Exception as e:
        print(f"[Tick Engine] Warning syncing draft states: {e}")

    # 2. Reply Detection
    action_check_replies()

    # 3. Autonomous Morning Replenishment (02:00 - 06:00 UTC / 07:30 - 11:30 AM IST)
    # If total drafts across all regions is low (< 8), replenish fresh startups
    time_decimal = now_utc.hour + now_utc.minute / 60.0
    if 2.0 <= time_decimal <= 6.0:
        total_drafts = db.get_pending_draft_count("All")
        if total_drafts < 8:
            print(f"[Tick Engine] 🌅 Morning replenishment window active (total pending drafts={total_drafts} < 8). Replenishing fresh startups...")
            action_research_and_draft(region="All", dry_run=dry_run)
    
    # 4. Regional morning dispatch checks
    regions = ["India", "ME", "EU", "US"]
    for reg in regions:
        in_window, local_desc = is_region_in_sending_window(reg)
        print(f"\n[Timezone Controller] Checking {reg} -> Local: {local_desc}")
        if in_window:
            today_sent = db.get_today_sent_count(reg)
            if today_sent > 0:
                print(f"[Timezone Controller] ⏸️ {reg} is in morning sending window, but {today_sent} emails were already sent today. Skipping duplicate dispatch.")
            else:
                pending_drafts = db.get_pending_draft_count(reg)
                if pending_drafts == 0:
                    print(f"[Timezone Controller] ⚠️ {reg} is in sending window with 0 pending drafts. Replenishing drafts via research-and-draft...")
                    action_research_and_draft(region=reg, dry_run=dry_run)
                    pending_drafts = db.get_pending_draft_count(reg)
                    
                if pending_drafts > 0:
                    print(f"[Timezone Controller] 🚀 {reg} morning window ACTIVE! Dispatching batch of {pending_drafts} drafts...")
                    action_send_batch(region=reg, dry_run=dry_run, auto_send=auto_send)
                else:
                    print(f"[Timezone Controller] No drafts available for {reg}.")
        else:
            print(f"[Timezone Controller] ⏳ {reg} is outside morning sending window (08:30 - 12:30 local). No emails will be sent.")
            
    # 3. Follow-up Engine
    print("\n[Tick Engine] Running Follow-Up verification...")
    action_process_followups(auto_send=auto_send)
    print("=" * 60)
    print("                    HEARTBEAT TICK COMPLETE                     ")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloud Outreach Orchestrator")
    parser.add_argument("--action", choices=["research-and-draft", "send-batch", "check-replies", "followups", "status", "tick"], default="research-and-draft")
    parser.add_argument("--region", default="All", help="Target region (India, Middle East, Europe, US, All)")
    parser.add_argument("--auto-send", action="store_true", help="Send directly instead of creating drafts")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing to Gmail")
    args = parser.parse_args()
    
    if args.action == "tick":
        action_tick(dry_run=args.dry_run, auto_send=args.auto_send)
    elif args.action == "research-and-draft":
        action_research_and_draft(region=args.region, dry_run=args.dry_run)
    elif args.action == "status":
        action_status()
    elif args.action == "check-replies":
        action_check_replies()
    elif args.action == "send-batch":
        action_send_batch(region=args.region, dry_run=args.dry_run, auto_send=args.auto_send)
    elif args.action == "followups":
        action_process_followups(auto_send=args.auto_send)


