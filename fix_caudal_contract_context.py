#!/usr/bin/env python3
"""
Refines Caudal AI context across all drafts in outreach.db and Gmail:
Clarifies that Caudal AI is an ongoing contract engineering engagement.
Updates both database and live Gmail drafts.
"""

import sqlite3
import time
from gmail_client import GmailClient
import db

REPLACEMENTS = [
    ("When building Caudal AI, our core bottleneck was", "In my current contract role at Caudal AI, our core focus is"),
    ("When building Caudal AI, the biggest hurdle wasn't", "In my current contract role at Caudal AI, our core engineering focus isn't"),
    ("when building Caudal AI", "in my current contract role at Caudal AI"),
    ("while building Caudal AI", "in my contract role at Caudal AI"),
    ("When building Caudal AI and Realty Pandit", "Across my contract role at Caudal AI and building Realty Pandit"),
    ("building Caudal AI and Realty Pandit", "my contract role at Caudal AI and building Realty Pandit"),
    ("At Caudal AI, I also built", "In my current contract role at Caudal AI, I also engineer"),
    ("At Caudal AI, I built", "In my current contract role at Caudal AI, I engineer"),
    ("At Caudal AI, I design", "In my current contract role at Caudal AI, I design"),
    ("At Caudal AI, I designed", "In my current contract role at Caudal AI, I build"),
    ("At Caudal AI, I author", "In my current contract role at Caudal AI, I author"),
    ("At Caudal AI, we saw", "In my contract role at Caudal AI, we saw"),
]

def clean_text(text: str) -> str:
    if not text:
        return text
    new_text = text
    for old, new in REPLACEMENTS:
        new_text = new_text.replace(old, new)
    return new_text

def run_migration():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, founder_email, initial_subject, initial_body, fu1_subject, fu1_body, fu2_subject, fu2_body, gmail_draft_id FROM leads")
    leads = cursor.fetchall()
    
    client = GmailClient()
    updated_db_count = 0
    updated_gmail_count = 0

    print("Starting Caudal AI contract context refinement across all leads...")

    for row in leads:
        lead_id = row["id"]
        company = row["name"]
        email = row["founder_email"]
        draft_id = row["gmail_draft_id"]
        
        orig_init = row["initial_body"]
        orig_fu1 = row["fu1_body"]
        orig_fu2 = row["fu2_body"]
        
        new_init = clean_text(orig_init)
        new_fu1 = clean_text(orig_fu1)
        new_fu2 = clean_text(orig_fu2)
        
        changed = (new_init != orig_init) or (new_fu1 != orig_fu1) or (new_fu2 != orig_fu2)
        
        if changed:
            cursor.execute("""
            UPDATE leads
            SET initial_body = ?, fu1_body = ?, fu2_body = ?
            WHERE id = ?
            """, (new_init, new_fu1, new_fu2, lead_id))
            conn.commit()
            updated_db_count += 1
            
            # Update live draft in Gmail
            if draft_id and email:
                try:
                    client.update_draft(draft_id, email, row["initial_subject"], new_init)
                    updated_gmail_count += 1
                    print(f" ✅ Updated Gmail Draft & DB for: {company} ({email})")
                except Exception as e:
                    print(f" ⚠️ Could not update Gmail draft for {company} ({draft_id}): {e}")
            else:
                print(f" ℹ️ Updated DB for: {company}")

    conn.close()
    print("=" * 60)
    print(f"Refinement complete! Updated {updated_db_count} leads in SQLite, and {updated_gmail_count} live Gmail drafts.")
    print("=" * 60)

if __name__ == "__main__":
    run_migration()
