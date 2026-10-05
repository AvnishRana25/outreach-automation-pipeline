#!/usr/bin/env python3
"""
Outreach Database Manager (SQLite)
Guarantees deduplication, state tracking across follow-ups, and thread history.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "outreach.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        domain TEXT UNIQUE,
        founder_name TEXT,
        founder_email TEXT,
        founder_role TEXT,
        region TEXT,
        status TEXT DEFAULT 'DRAFTED',
        initial_subject TEXT,
        initial_body TEXT,
        fu1_subject TEXT,
        fu1_body TEXT,
        fu2_subject TEXT,
        fu2_body TEXT,
        gmail_draft_id TEXT,
        gmail_thread_id TEXT,
        created_at TEXT,
        sent_at TEXT,
        last_checked_reply_at TEXT,
        replied_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def is_company_contacted(domain: str, name: str = None) -> bool:
    """Checks if company has ever been queued or contacted."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM leads WHERE domain = ? OR name = ?", (domain.lower(), name))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def insert_or_update_lead(lead_dict: dict):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO leads (
        name, domain, founder_name, founder_email, founder_role, region,
        status, initial_subject, initial_body, fu1_subject, fu1_body,
        fu2_subject, fu2_body, gmail_draft_id, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
        founder_email = excluded.founder_email,
        initial_subject = excluded.initial_subject,
        initial_body = excluded.initial_body,
        fu1_subject = excluded.fu1_subject,
        fu1_body = excluded.fu1_body,
        fu2_subject = excluded.fu2_subject,
        fu2_body = excluded.fu2_body,
        gmail_draft_id = COALESCE(excluded.gmail_draft_id, leads.gmail_draft_id)
    """, (
        lead_dict.get("company_name") or lead_dict.get("company"),
        (lead_dict.get("domain") or "").lower(),
        lead_dict.get("founder_name") or lead_dict.get("founder"),
        lead_dict.get("verified_email") or lead_dict.get("email"),
        lead_dict.get("founder_role") or lead_dict.get("role", "Founder"),
        lead_dict.get("location") or lead_dict.get("region"),
        lead_dict.get("status", "DRAFTED"),
        lead_dict.get("initial_subject"),
        lead_dict.get("initial_body"),
        lead_dict.get("fu1_subject"),
        lead_dict.get("fu1_body"),
        lead_dict.get("fu2_subject"),
        lead_dict.get("fu2_body"),
        lead_dict.get("gmail_draft_id"),
        now
    ))
    conn.commit()
    conn.close()

def seed_from_curated_leads():
    curated_path = os.path.join(os.path.dirname(__file__), "curated_leads.json")
    if not os.path.exists(curated_path):
        return
    with open(curated_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    leads = data if isinstance(data, list) else data.get("leads", [])
    for lead in leads:
        insert_or_update_lead(lead)
    print(f"Seeded {len(leads)} leads into SQLite database ({DB_PATH})")

if __name__ == "__main__":
    init_db()
    seed_from_curated_leads()
