#!/usr/bin/env python3
"""
Cold Outreach Automation & Management CLI for Avnish Rana
Managing campaign state for AI startups for Junior FDE, AI Evals, and AI Automation contracts.
"""

import csv
import sys
import os
import db

LEADS_FILE = os.path.join(os.path.dirname(__file__), "curated_leads.json")
TRACKER_CSV = os.path.join(os.path.dirname(__file__), "leads_tracker.csv")

def load_leads():
    return db.campaign_leads()

def export_to_csv():
    leads = load_leads()
    fieldnames = [
        "id",
        "company_name",
        "batch_or_stage",
        "location",
        "domain",
        "founder_name",
        "founder_role",
        "verified_email",
        "target_role",
        "status",
        "hook_angle",
        "recommended_send_time_ist",
        "founder_local_window",
        "resume_link",
        "github_link",
        "linkedin_link",
        "scheduled_initial",
        "initial_subject",
        "initial_body",
        "scheduled_fu1",
        "fu1_subject",
        "fu1_body",
        "scheduled_fu2",
        "fu2_subject",
        "fu2_body", "gmail_thread_id", "sent_at", "fu1_sent_at", "fu2_sent_at",
        "replied_at", "last_error", "region_code", "recipient_timezone",
        "email_verified_at", "email_verification_source"
    ]

    def write(f):
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        for lead in leads:
            writer.writerow({key:lead.get(key, "") for key in fieldnames})
    db.atomic_write(TRACKER_CSV, write)

    print(f"✅ Exported all {len(leads)} leads to {TRACKER_CSV}")

def list_leads():
    leads = load_leads()
    print("\n" + "="*110)
    print(f"🎯 OUTREACH CAMPAIGNS ({len(leads)} Total)")
    print("="*110)
    print(f"{'#':<3} | {'Company':<15} | {'Founder':<20} | {'Email':<26} | {'Best Send Time (IST)':<22} | {'Status'}")
    print("-" * 110)
    for lead in leads:
        print(f"[{lead['id']:>2}] {lead['company_name']:<15} | {lead['founder_name']:<20} | {lead['verified_email']:<26} | {lead.get('recommended_send_time_ist', '9:30 PM IST'):<22} | {lead['status']}")
    print("-" * 110)
    print("\nTip: Run 'python3 generate_outreach.py view <num>' to view full initial email + follow-ups.")
    print("     Run 'python3 generate_outreach.py schedule' to view sending windows by timezone.")

def show_draft(index):
    leads = load_leads()
    if index < 1 or index > len(leads):
        print(f"Error: Invalid index. Choose between 1 and {len(leads)}")
        return

    lead = leads[index - 1]
    print("\n" + "="*90)
    print(f"🏢 COMPANY: {lead['company_name']} ({lead['batch_or_stage']}) — {lead['location']}")
    print(f"👤 RECIPIENT: {lead['founder_name']} ({lead['founder_role']}) <{lead['verified_email']}>")
    print(f"🎯 TARGET ROLE: {lead['target_role']}")
    print(f"⏰ RECOMMENDED SEND TIME: {lead.get('recommended_send_time_ist')} ({lead.get('founder_local_window')})")
    print(f"💡 HOOK: {lead['hook_angle']}")
    print("="*90)

    print(f"\n📩 [STEP 1: INITIAL EMAIL]")
    print(f"Subject: {lead['initial_subject']}\n")
    print(lead['initial_body'])

    print("\n" + "-"*90)
    print(f"🔁 [STEP 2: FOLLOW-UP 1 (+3 Days)]")
    print(f"Subject: {lead['fu1_subject']}\n")
    print(lead['fu1_body'])

    print("\n" + "-"*90)
    print(f"👋 [STEP 3: FOLLOW-UP 2 / BREAK-UP (+7 Days)]")
    print(f"Subject: {lead['fu2_subject']}\n")
    print(lead['fu2_body'])
    print("="*90 + "\n")

def show_schedule():
    leads = load_leads()
    print("\n" + "="*95)
    print("⏰ RECOMMENDED SENDING WINDOWS (BY GEOGRAPHY & TIMEZONE)")
    print("="*95)

    groups = {}
    for l in leads:
        t = l.get("recommended_send_time_ist", "9:30 PM IST")
        groups.setdefault(t, []).append(l)

    for time_slot, group in sorted(groups.items()):
        print(f"\n🕒 {time_slot} — Founder Local Window: {group[0].get('founder_local_window')}")
        print(f"   Batch of {len(group)} companies:")
        for l in group:
            print(f"     • #{l['id']} {l['company_name']} -> {l['founder_name']} <{l['verified_email']}>")
    print("="*95 + "\n")

def main():
    if len(sys.argv) < 2:
        list_leads()
        print("\nAvailable Commands:")
        print("  python3 generate_outreach.py list          -> List campaign leads")
        print("  python3 generate_outreach.py view <num>    -> View complete 3-step sequence for lead #")
        print("  python3 generate_outreach.py schedule      -> View recommended send times by timezone")
        print("  python3 generate_outreach.py sync          -> Export SQLite campaign state to leads_tracker.csv")
    elif sys.argv[1] == "list":
        list_leads()
    elif sys.argv[1] == "sync":
        export_to_csv()
    elif sys.argv[1] == "schedule":
        show_schedule()
    elif sys.argv[1] == "view" and len(sys.argv) > 2:
        try:
            show_draft(int(sys.argv[2]))
        except ValueError:
            print("Please provide a valid integer index within the displayed lead count.")
    else:
        print("Unknown command. Run with no arguments to see available options.")

if __name__ == "__main__":
    main()
