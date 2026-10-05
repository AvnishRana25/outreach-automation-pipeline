#!/usr/bin/env python3
"""Serialized, checkpointed Gmail outreach with conservative recovery."""
import argparse
import functools
import inspect
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import db
from gmail_client import GmailClient
from notify_mobile import notify_user_mobile


class PersistenceError(RuntimeError):
    pass


def checkpoint():
    try:
        db.checkpoint()
    except Exception as exc:
        raise PersistenceError('State checkpoint failed; Gmail writes stopped') from exc


def locked(function):
    signature = inspect.signature(function)
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        with db.campaign_lock():
            if not signature.bind_partial(*args, **kwargs).arguments.get('dry_run', False):
                db.init_db()
                checkpoint()
            return function(*args, **kwargs)
    return wrapper


def rows():
    if not Path(db.DB_PATH).exists(): return []
    with db.connection(readonly=True) as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM leads ORDER BY id')]


def update_lead(lead_id, **fields):
    with db.connection() as conn:
        conn.execute('UPDATE leads SET ' + ','.join(f'{k}=?' for k in fields) + ' WHERE id=?', (*fields.values(),lead_id))
    checkpoint()


def update_attempt(lead_id,stage,**fields):
    with db.connection() as conn:
        conn.execute('UPDATE attempts SET '+','.join(f'{k}=?' for k in fields)+' WHERE lead_id=? AND stage=?',(*fields.values(),lead_id,stage))
    checkpoint()


def get_attempt(lead_id,stage):
    with db.connection() as conn:
        row=conn.execute('SELECT * FROM attempts WHERE lead_id=? AND stage=?',(lead_id,stage)).fetchone()
    return dict(row) if row else None


def complete(lead,stage,message):
    if not message.get('id') or not message.get('threadId'): raise ValueError('Incomplete Gmail send response')
    stamp=datetime.fromtimestamp(int(message['internalDate'])/1000,timezone.utc).isoformat() if message.get('internalDate') else db.utcnow()
    attempt=get_attempt(lead['id'],stage)
    if attempt and attempt['thread_id'] and message['threadId'] != attempt['thread_id']:
        raise RuntimeError('Gmail returned a different follow-up thread; review required')
    update_attempt(lead['id'],stage,state='SENT',sent_at=stamp,gmail_message_id=message['id'],thread_id=message['threadId'],draft_id=None,error=None)
    fields={'status':{'initial':'SENT','fu1':'FU1_SENT','fu2':'FU2_SENT'}[stage],'gmail_thread_id':message['threadId'],'last_error':None}
    fields['sent_at' if stage=='initial' else stage+'_sent_at']=stamp
    if stage=='initial': fields['gmail_draft_id']=None
    update_lead(lead['id'],**fields)
    lead.update(fields)


def reconcile_attempt(lead,stage,client):
    attempt=get_attempt(lead['id'],stage)
    if not attempt: return None
    if attempt['state']=='SENT':
        # Heal a crash between saving the attempt and updating the lead.
        ranks = {'DRAFTED':0,'Drafted in Gmail':0,'Ready to Send':0,'INITIAL_QUEUED':0,'INITIAL_UNCERTAIN':0,'SENT':1,'FU1_QUEUED':1,'FU1_UNCERTAIN':1,'FU1_SENT':2,'FU2_QUEUED':2,'FU2_UNCERTAIN':2,'FU2_SENT':3,'REPLIED':99}
        if ranks.get(lead['status'],99) < {'initial':1,'fu1':2,'fu2':3}[stage]:
            complete(lead,stage,{'id':attempt['gmail_message_id'],'threadId':attempt['thread_id'],'internalDate':str(int(db.parse_time(attempt['sent_at']).timestamp()*1000))})
        return get_attempt(lead['id'],stage)
    found=client.find_delivery(attempt['message_id'],attempt['created_at'])
    if found and found['state']=='SENT':
        complete(lead,stage,found['message'])
    elif found and found['state']=='DRAFTED' and attempt['state'] in ('PREPARING','DRAFTED'):
        update_attempt(lead['id'],stage,state='DRAFTED',draft_id=found['draft']['id'],error=None)
        if stage=='initial': update_lead(lead['id'],gmail_draft_id=found['draft']['id'])
    elif attempt['state'] != 'DRAFTED':
        raise RuntimeError(f'{stage} outcome is uncertain; reconciliation will retry, sending is held')
    return get_attempt(lead['id'],stage)


def prepare(lead,stage,client):
    attempt=get_attempt(lead['id'],stage)
    if attempt: return reconcile_attempt(lead,stage,client)
    legacy=client.get_draft(lead['gmail_draft_id']) if stage=='initial' and lead.get('gmail_draft_id') else None
    if stage=='initial' and lead.get('gmail_draft_id') and not legacy:
        sent=client.find_legacy_sent(lead['founder_email'],lead['initial_subject'],lead['created_at'])
        if not sent: raise RuntimeError('Existing draft disappeared and no unique sent message was found; review required')
        message_id=client.headers(sent).get('message-id')
        if not message_id: raise ValueError('Legacy sent email has no Message-ID')
    else:
        sent=None
        message_id=client.headers(legacy['message']).get('message-id') if legacy else f'<outreach.{uuid.uuid4().hex}@outreach.local>'
        if not message_id: raise ValueError('Existing draft has no Message-ID; review required')
    with db.connection() as conn:
        conn.execute('INSERT INTO attempts(lead_id,stage,message_id,draft_id,thread_id,state,created_at) VALUES(?,?,?,?,?,?,?)',
                     (lead['id'],stage,message_id,lead.get('gmail_draft_id') if legacy else None,lead.get('gmail_thread_id') if stage!='initial' else None,'DRAFTED' if legacy else 'PREPARING',db.utcnow()))
    checkpoint()
    if sent:
        complete(lead,stage,sent)
    elif not legacy:
        subject=lead['initial_subject']
        body=lead[stage+'_body']
        try:
            result=client.create_draft(lead['founder_email'],subject,body,thread_id=lead.get('gmail_thread_id') if stage!='initial' else None,message_id=message_id)
            if not result.get('id'): raise ValueError('Gmail did not return a draft ID')
            update_attempt(lead['id'],stage,state='DRAFTED',draft_id=result['id'])
            if stage=='initial': update_lead(lead['id'],gmail_draft_id=result['id'],gmail_thread_id=result.get('message',{}).get('threadId'))
        except PersistenceError:
            raise
        except Exception as exc:
            update_attempt(lead['id'],stage,error=type(exc).__name__)
            raise
    return get_attempt(lead['id'],stage)


def deliver(lead,stage,client,auto_send):
    if not lead.get('region_code') or not lead.get('recipient_timezone'): raise ValueError('Set a region and recipient timezone')
    if stage=='initial' and auto_send:
        metadata=json.loads(lead.get('metadata') or '{}')
        if not metadata.get('email_verified_at') or not metadata.get('email_verification_source'):
            raise ValueError('Recipient verification is not recorded; import verified JSON before automatic sending')
        if db.parse_time(metadata['email_verified_at']) > datetime.now(timezone.utc): raise ValueError('Invalid email verification date')
    attempt=prepare(lead,stage,client)
    if attempt['state']=='SENT': return False
    if not auto_send:
        if lead['status'] == ('INITIAL_QUEUED' if stage=='initial' else stage.upper()+'_QUEUED'): return False
        update_lead(lead['id'],status='INITIAL_QUEUED' if stage=='initial' else stage.upper()+'_QUEUED')
        return True
    if attempt['state']!='DRAFTED' or not attempt['draft_id']: raise RuntimeError('No confirmed draft available; sending held')
    # Durable intent is pushed before the only send request. Unknown outcomes never get an automatic second send.
    update_attempt(lead['id'],stage,state='SENDING')
    update_lead(lead['id'],status=stage.upper()+'_UNCERTAIN')
    try:
        message=client.send_draft(attempt['draft_id'])
        complete(lead,stage,message)
    except PersistenceError:
        raise
    except Exception as exc:
        update_attempt(lead['id'],stage,state='UNKNOWN',error=type(exc).__name__)
        raise
    time.sleep(float(os.getenv('OUTREACH_SEND_DELAY','3')))
    return True


def check_reply(lead,client):
    if not lead.get('sent_at') or not lead.get('gmail_thread_id'): return False
    replied=client.check_recipient_replied(lead['founder_email'],thread_id=lead['gmail_thread_id'],sent_at=lead['sent_at'])
    update_lead(lead['id'],last_checked_reply_at=db.utcnow())
    if replied:
        update_lead(lead['id'],status='REPLIED',replied_at=lead.get('replied_at') or db.utcnow())
        lead['status']='REPLIED'
        for stage in ('fu1','fu2'):
            attempt=get_attempt(lead['id'],stage)
            if attempt and attempt['state']=='DRAFTED' and attempt['draft_id']:
                client.delete_draft(attempt['draft_id'])
                update_attempt(lead['id'],stage,state='CANCELLED',draft_id=None)
        notify_reply(lead)
    return replied


def notify_reply(lead):
    if lead.get('reply_notified_at'): return
    if notify_user_mobile(title=f"Reply: {lead['name']}",message=f"{lead['founder_name']} replied. Open Gmail to respond.",click_url='https://mail.google.com/mail/u/0/#inbox'):
        update_lead(lead['id'],reply_notified_at=db.utcnow())


def reconcile(lead,client):
    if lead['status']=='REPLIED':
        # Retry queued-draft cancellation/notification after a transient failure.
        for stage in ('fu1','fu2'):
            attempt=get_attempt(lead['id'],stage)
            if attempt and attempt['state']=='DRAFTED' and attempt['draft_id']:
                client.delete_draft(attempt['draft_id'])
                update_attempt(lead['id'],stage,state='CANCELLED',draft_id=None)
        notify_reply(lead)
        return
    for stage in ('initial','fu1','fu2'):
        if get_attempt(lead['id'],stage): reconcile_attempt(lead,stage,client)
    if lead['status'] in db.PENDING or lead['status']=='INITIAL_QUEUED':
        if lead.get('gmail_draft_id') and not get_attempt(lead['id'],'initial'): prepare(lead,'initial',client)


def fail(lead,exc):
    if isinstance(exc,PersistenceError): raise exc
    update_lead(lead['id'],last_error=f'{type(exc).__name__}: '+str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__)
    print(f"Failed {lead['name']}: {type(exc).__name__}",file=sys.stderr)


def finish(count,failures,dry_run=False,label='Processed'):
    print(f'{label}: {count}; failed: {failures}' + (' (dry run)' if dry_run else ''))
    if failures: raise RuntimeError(f'{failures} lead(s) need attention; successful progress was saved')
    return count


def require_sender(auto_send,dry_run):
    if auto_send and not dry_run and os.getenv('OUTREACH_CLOUD')!='1' and os.getenv('OUTREACH_ALLOW_LOCAL_SEND')!='1':
        raise RuntimeError('Cloud is the authoritative sender. For exclusive local operation, disable cloud dispatch and set OUTREACH_ALLOW_LOCAL_SEND=1')


@locked
def action_check_replies(dry_run=False):
    client=None if dry_run else GmailClient()
    count=failures=0
    for lead in rows():
        if dry_run:
            print(f"Would reconcile/check {lead['name']}");continue
        try:
            if check_reply(lead,client):
                count+=1;continue
            reconcile(lead,client)
            if lead['status']=='REPLIED': continue
            if check_reply(lead,client): count+=1
        except Exception as exc:
            fail(lead,exc);failures+=1
    return finish(count,failures,dry_run,'Replies')


@locked
def action_send_batch(region='All',dry_run=False,auto_send=False,respect_window=False):
    region=db.normalize_region(region)
    require_sender(auto_send,dry_run)
    client=None if dry_run else GmailClient()
    count=failures=0
    for lead in rows():
        if region!='All' and lead.get('region_code')!=region: continue
        if lead['status'] not in (*db.PENDING,'INITIAL_QUEUED','INITIAL_UNCERTAIN'): continue
        try:
            if respect_window and not db.in_send_window(lead): continue
            if dry_run:
                print(f"Would {'send' if auto_send else 'draft'} {lead['name']}");count+=1;continue
            reconcile(lead,client)
            if lead['status'] not in (*db.PENDING,'INITIAL_QUEUED','INITIAL_UNCERTAIN'): continue
            count+=int(deliver(lead,'initial',client,auto_send))
        except Exception as exc:
            fail(lead,exc);failures+=1
    if count and not dry_run:
        notify_user_mobile(title='Outreach batch',message=f"{count} initial emails {'sent' if auto_send else 'drafted'}; {failures} failed.")
    return finish(count,failures,dry_run)


@locked
def action_process_followups(auto_send=False,dry_run=False,region='All',respect_window=False):
    region=db.normalize_region(region)
    require_sender(auto_send,dry_run)
    client=None if dry_run else GmailClient()
    count=failures=0
    for lead in rows():
        if region!='All' and lead.get('region_code')!=region: continue
        if lead['status'] not in ('SENT','FU1_SENT','FU1_QUEUED','FU2_QUEUED','FU1_UNCERTAIN','FU2_UNCERTAIN'): continue
        try:
            if respect_window and not db.in_send_window(lead): continue
            if not dry_run:
                if check_reply(lead,client): continue
                reconcile(lead,client)
                if lead['status']=='REPLIED': continue
            now=datetime.now(timezone.utc)
            initial=db.parse_time(lead['sent_at'])
            stage=None
            if lead['status'] in ('SENT','FU1_QUEUED','FU1_UNCERTAIN') and now-initial>=timedelta(days=3): stage='fu1'
            if lead['status'] in ('FU1_SENT','FU2_QUEUED','FU2_UNCERTAIN'):
                # Day +7 from initial, and never less than 24 hours after FU1 when its processing was delayed.
                due=max(initial+timedelta(days=7),db.parse_time(lead['fu1_sent_at'])+timedelta(days=1))
                if now>=due: stage='fu2'
            if not stage: continue
            if dry_run:
                print(f"Would {'send' if auto_send else 'draft'} {stage} for {lead['name']}");count+=1
            else: count+=int(deliver(lead,stage,client,auto_send))
        except Exception as exc:
            if not dry_run: fail(lead,exc)
            failures+=1
    if count and not dry_run:
        notify_user_mobile(title='Follow-ups',message=f"{count} follow-ups {'sent' if auto_send else 'drafted'}; {failures} failed.")
    return finish(count,failures,dry_run)


def action_status(dry_run=False):
    counts={}
    for lead in rows(): counts[lead['status']]=counts.get(lead['status'],0)+1
    for status,count in sorted(counts.items()): print(f'{status}: {count}')
    print(f'TOTAL: {sum(counts.values())}')
    return counts


def action_research_and_draft(region='All',dry_run=False,leads_file=None):
    from research_and_generate import run_multi_region_expansion
    return len(run_multi_region_expansion(target_regions=[db.normalize_region(region)],dry_run=dry_run,create_drafts=True,leads_file=leads_file))


def action_tick():
    failures=[]
    for fn,kwargs in [(action_check_replies,{}),(action_send_batch,{'auto_send':True,'respect_window':True}),(action_process_followups,{'auto_send':True,'respect_window':True})]:
        try: fn(**kwargs)
        except Exception as exc:
            if isinstance(exc,PersistenceError): raise
            failures.append(type(exc).__name__)
    if failures: raise RuntimeError(f'{len(failures)} scheduled action(s) failed')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=['research-and-draft','send-batch','check-replies','reconcile','followups','status','tick','notify-test'],default='status')
    parser.add_argument('--region',default='All',type=db.normalize_region)
    parser.add_argument('--auto-send',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--leads-file',help='Verified JSON import; defaults to verified_leads.json')
    args=parser.parse_args(argv)
    if args.action=='notify-test':
        if args.dry_run: print('Would send one configured private mobile test alert')
        elif not notify_user_mobile('Outreach acceptance test','Private mobile delivery test. Confirm receipt in Codex.'):
            raise RuntimeError('Private notification delivery failed or is not configured')
    elif args.action=='tick':
        if args.dry_run:
            action_check_replies(dry_run=True)
            action_send_batch(dry_run=True,auto_send=True,respect_window=True)
            action_process_followups(dry_run=True,auto_send=True,respect_window=True)
        else: action_tick()
    elif args.action in ('check-replies','reconcile'): action_check_replies(dry_run=args.dry_run)
    elif args.action=='send-batch': action_send_batch(region=args.region,dry_run=args.dry_run,auto_send=args.auto_send)
    elif args.action=='followups': action_process_followups(region=args.region,dry_run=args.dry_run,auto_send=args.auto_send)
    elif args.action=='research-and-draft': action_research_and_draft(region=args.region,dry_run=args.dry_run,leads_file=args.leads_file)
    else: action_status(dry_run=args.dry_run)


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'Pipeline failed: {type(exc).__name__}: {exc}' if isinstance(exc,(ValueError,RuntimeError)) else f'Pipeline failed: {type(exc).__name__}',file=sys.stderr)
        sys.exit(1)
