#!/usr/bin/env python3
"""Refresh pending drafts while preserving their tracking headers and threads."""
import sys
import db
from gmail_client import GmailClient
from cloud_orchestrator import locked, rows, get_attempt, finish


@locked
def refresh(dry_run=False):
    client=None if dry_run else GmailClient()
    count=failures=0
    for lead in rows():
        if lead['status'] not in (*db.PENDING,'INITIAL_QUEUED','FU1_QUEUED','FU2_QUEUED'): continue
        stage='fu1' if lead['status']=='FU1_QUEUED' else 'fu2' if lead['status']=='FU2_QUEUED' else 'initial'
        attempt=get_attempt(lead['id'],stage)
        draft_id=attempt['draft_id'] if attempt else lead.get('gmail_draft_id') if stage=='initial' else None
        if not draft_id: continue
        if dry_run:
            count+=1;continue
        try:
            draft=client.get_draft(draft_id)
            if not draft: continue  # Reconciliation, not a formatting operation, handles manually sent drafts.
            message_id=client.headers(draft['message']).get('x-outreach-id') or client.headers(draft['message']).get('message-id')
            if not message_id: raise ValueError('Draft tracking header is unavailable')
            client.update_draft(draft_id,lead['founder_email'],lead['initial_subject'],lead[stage+'_body'],thread_id=lead.get('gmail_thread_id') if stage!='initial' else None,message_id=message_id)
            count+=1
        except Exception as exc:
            print(f"Draft refresh failed for {lead['name']}: {type(exc).__name__}",file=sys.stderr);failures+=1
    return finish(count,failures,dry_run,'Drafts refreshed')


if __name__=='__main__':
    refresh(dry_run='--dry-run' in sys.argv)
