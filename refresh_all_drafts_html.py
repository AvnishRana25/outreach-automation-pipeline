#!/usr/bin/env python3
"""
Refreshes all 52 drafts in Gmail to use the clean, beautiful HTML typography:
- Eliminates ugly raw 100-character Google Drive / GitHub / LinkedIn URLs
- Embeds clean clickable hyperlinks: Resume • GitHub • LinkedIn • Phone
- Removes jagged hard line wraps so sentences flow fluidly
"""

import sqlite3
import time
from gmail_client import GmailClient
import db

def refresh():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, founder_email, initial_subject, initial_body, gmail_draft_id FROM leads WHERE gmail_draft_id IS NOT NULL")
    leads = cursor.fetchall()
    
    client = GmailClient()
    updated = 0
    print(f"Refreshing {len(leads)} drafts in Gmail with clean HTML typography and embedded links...")

    for row in leads:
        lead_id = row["id"]
        company = row["name"]
        email = row["founder_email"]
        subject = row["initial_subject"]
        body = row["initial_body"]
        draft_id = row["gmail_draft_id"]

        try:
            client.update_draft(draft_id, email, subject, body)
            updated += 1
            print(f" ✨ Draft upgraded to clean HTML for: {company} ({email})")
            time.sleep(0.3)
        except Exception as e:
            print(f" ⚠️ Could not update draft for {company}: {e}")

    conn.close()
    print("=" * 60)
    print(f"Upgraded {updated} drafts in Gmail to beautiful rich HTML format!")
    print("=" * 60)

if __name__ == "__main__":
    refresh()
