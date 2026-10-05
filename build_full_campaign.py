#!/usr/bin/env python3
"""Export current campaign state; never reset it from historical templates."""
import json
import db


def main():
    leads=db.campaign_leads()
    db.atomic_write(db.ROOT/'curated_leads.json',lambda handle:json.dump(leads,handle,indent=2,ensure_ascii=False))
    print(f'Exported {len(leads)} campaign leads from SQLite')


if __name__=='__main__': main()
