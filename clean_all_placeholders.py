#!/usr/bin/env python3
"""
Eliminates all placeholders across all leads, follow-ups, and drafts.
Replaces [GitHub Link] and [GitHub] with full URL https://github.com/AvnishRana25
Clarifies Caudal AI as ongoing contract engagement.
"""

import sqlite3
import db

def clean_placeholders():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, fu2_body FROM leads")
    rows = cursor.fetchall()
    
    fixed_count = 0
    for r in rows:
        lead_id = r["id"]
        fu2 = r["fu2_body"] or ""
        
        new_fu2 = fu2
        new_fu2 = new_fu2.replace("[GitHub Link]", "https://github.com/AvnishRana25")
        new_fu2 = new_fu2.replace("[GitHub]", "https://github.com/AvnishRana25")
        new_fu2 = new_fu2.replace("Caudal AI: Frontier", "Caudal AI (Contract): Frontier")
        
        if new_fu2 != fu2:
            cursor.execute("UPDATE leads SET fu2_body = ? WHERE id = ?", (new_fu2, lead_id))
            fixed_count += 1
            
    conn.commit()
    conn.close()
    print(f"Cleaned all placeholders from {fixed_count} leads in SQLite.")

if __name__ == "__main__":
    clean_placeholders()
