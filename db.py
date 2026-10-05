#!/usr/bin/env python3
"""SQLite campaign state, validated imports, atomic exports and durable checkpoints."""
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import tempfile
from contextlib import contextmanager, closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DB_PATH = str(ROOT / 'outreach.db')
PENDING = ('DRAFTED', 'Drafted in Gmail', 'Ready to Send')
ALIASES = {'all':'All', 'us':'US', 'usa':'US', 'america':'US', 'india':'India', 'in':'India', 'me':'ME', 'middle east':'ME', 'gulf':'ME', 'eu':'EU', 'uk':'EU', 'europe':'EU'}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def parse_time(value):
    if not value:
        raise ValueError('Missing send timestamp')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp.astimezone(timezone.utc)


def normalize_region(value='All'):
    try:
        return ALIASES[value.strip().lower()]
    except (KeyError, AttributeError):
        raise ValueError('Region must be All, US, India, ME or EU') from None


def region_for_location(location):
    text = (location or '').lower()
    for code, words in [('India',r'\b(india|bengaluru|bangalore|mumbai|gurgaon|gurugram|delhi)\b'), ('ME',r'\b(riyadh|dubai|saudi|uae|abu dhabi|middle east)\b'), ('EU',r'\b(london|uk|europe|paris|berlin|stockholm|amsterdam|france|germany)\b'), ('US',r'\b(us|usa|sf|san francisco|california|new york|nyc|silicon valley)\b')]:
        if re.search(words,text):
            return code
    raise ValueError(f'Unsupported lead location: {location!r}')


def timezone_for_location(location):
    region = region_for_location(location)
    text = location.lower()
    if region == 'India': return 'Asia/Kolkata'
    if region == 'ME': return 'Asia/Dubai' if 'dubai' in text or 'uae' in text else 'Asia/Riyadh'
    if region == 'US': return 'America/New_York' if 'new york' in text or 'nyc' in text else 'America/Los_Angeles'
    return 'Europe/Paris' if 'paris' in text or 'france' in text else 'Europe/Berlin' if 'berlin' in text else 'Europe/London'


def in_send_window(lead, now=None):
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(lead['recipient_timezone']))
    return local.weekday() < 5 and 9 <= local.hour < 11


def get_connection(readonly=False):
    if readonly:
        conn = sqlite3.connect(Path(DB_PATH).resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    else:
        conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection(readonly=False):
    with closing(get_connection(readonly)) as conn:
        with conn:
            yield conn


@contextmanager
def campaign_lock():
    # ponytail: one campaign-wide process lock; distributed state requires one authoritative cloud runner.
    with open(str(DB_PATH) + '.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another campaign action is running') from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def init_db():
    with connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, domain TEXT UNIQUE,
            founder_name TEXT, founder_email TEXT, founder_role TEXT, region TEXT,
            status TEXT DEFAULT 'DRAFTED', initial_subject TEXT, initial_body TEXT,
            fu1_subject TEXT, fu1_body TEXT, fu2_subject TEXT, fu2_body TEXT,
            gmail_draft_id TEXT, gmail_thread_id TEXT, created_at TEXT, sent_at TEXT,
            last_checked_reply_at TEXT, replied_at TEXT)''')
        columns = {r['name'] for r in conn.execute('PRAGMA table_info(leads)')}
        for name, kind in {'region_code':'TEXT', 'recipient_timezone':'TEXT', 'metadata':'TEXT', 'fu1_sent_at':'TEXT', 'fu2_sent_at':'TEXT', 'last_error':'TEXT', 'reply_notified_at':'TEXT'}.items():
            if name not in columns:
                conn.execute(f'ALTER TABLE leads ADD COLUMN {name} {kind}')
        conn.execute('''CREATE TABLE IF NOT EXISTS attempts (
            lead_id INTEGER NOT NULL REFERENCES leads(id), stage TEXT NOT NULL,
            message_id TEXT NOT NULL UNIQUE, draft_id TEXT, gmail_message_id TEXT,
            thread_id TEXT, state TEXT NOT NULL, created_at TEXT NOT NULL,
            sent_at TEXT, error TEXT, PRIMARY KEY(lead_id, stage))''')
        for row in conn.execute('SELECT id,region FROM leads WHERE region_code IS NULL').fetchall():
            try:
                code, zone = region_for_location(row['region']), timezone_for_location(row['region'])
                conn.execute('UPDATE leads SET region_code=?,recipient_timezone=? WHERE id=?',(code,zone,row['id']))
            except ValueError:
                conn.execute('UPDATE leads SET last_error=? WHERE id=?',('Set a supported region and recipient timezone before sending',row['id']))
        conn.execute("UPDATE leads SET status='DRAFTED' WHERE status IN ('Drafted in Gmail','Ready to Send')")
        conn.execute("UPDATE leads SET gmail_draft_id=NULL WHERE sent_at IS NOT NULL")


def validate_lead(data):
    lead = dict(data)
    mappings = {'company_name':'company', 'founder_name':'founder', 'verified_email':'email', 'founder_role':'role', 'location':'region'}
    for key, alias in mappings.items():
        lead[key] = (lead.get(key) or lead.get(alias) or '').strip()
    domain = (lead.get('domain') or '').strip().lower()
    if '://' in domain: domain = urlparse(domain).hostname or ''
    lead['domain'] = domain.removeprefix('www.').rstrip('.')
    if not lead['company_name'] or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}', lead['domain']):
        raise ValueError('Lead requires a company name and valid domain')
    if not re.fullmatch(r'[^\s<>@,;\r\n]+@[^\s<>@,;\r\n]+\.[^\s<>@,;\r\n]+', lead['verified_email']):
        raise ValueError('Lead requires one valid recipient email')
    lead['region_code'] = normalize_region(lead.get('region_code')) if lead.get('region_code') else region_for_location(lead['location'])
    if lead['region_code'] == 'All': raise ValueError('A lead must have a specific region')
    lead['recipient_timezone'] = lead.get('recipient_timezone') or timezone_for_location(lead['location'])
    ZoneInfo(lead['recipient_timezone'])
    for key in ('initial_subject','initial_body','fu1_body','fu2_body'):
        if not isinstance(lead.get(key),str) or not lead[key].strip(): raise ValueError(f'Missing {key}')
    for key in ('initial_subject','fu1_subject','fu2_subject'):
        if '\r' in (lead.get(key) or '') or '\n' in (lead.get(key) or ''): raise ValueError('Subject cannot contain newlines')
    if lead.get('email_verified_at'):
        if parse_time(lead['email_verified_at']) > datetime.now(timezone.utc) or not lead.get('email_verification_source'):
            raise ValueError('Email verification requires a source and a nonfuture timestamp')
    lead['status'] = 'DRAFTED'
    return lead


def is_company_contacted(domain, name=None):
    with connection() as conn:
        return conn.execute('SELECT id FROM leads WHERE domain=? OR name=? COLLATE NOCASE', (domain.strip().lower().removeprefix('www.').rstrip('.'),name)).fetchone() is not None


def insert_or_update_lead(data):
    """Insert once. A duplicate import never rewrites an active campaign's copy or history."""
    lead = validate_lead(data)
    with connection() as conn:
        existing = conn.execute('SELECT * FROM leads WHERE domain=? OR name=? COLLATE NOCASE',(lead['domain'],lead['company_name'])).fetchone()
        if existing:
            if existing['founder_email'].lower() != lead['verified_email'].lower():
                raise ValueError('Duplicate company has a different recipient; explicit campaign review required')
            metadata = json.loads(existing['metadata'] or '{}')
            metadata.update({k:lead[k] for k in ('email_verified_at','email_verification_source','target_role','batch_or_stage','hook_angle') if lead.get(k)})
            conn.execute('UPDATE leads SET metadata=? WHERE id=?',(json.dumps(metadata),existing['id']))
            return False
        fields = {'name':lead['company_name'],'domain':lead['domain'],'founder_name':lead['founder_name'], 'founder_email':lead['verified_email'],'founder_role':lead['founder_role'] or 'Founder','region':lead['location'],'region_code':lead['region_code'],'recipient_timezone':lead['recipient_timezone'],'status':'DRAFTED','created_at':utcnow(),'metadata':json.dumps(lead),'gmail_draft_id':lead.get('gmail_draft_id')}
        fields.update({k:lead.get(k) for k in ('initial_subject','initial_body','fu1_subject','fu1_body','fu2_subject','fu2_body')})
        conn.execute(f"INSERT INTO leads ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",tuple(fields.values()))
    return True


def seed_from_curated_leads():
    path = ROOT / 'curated_leads.json'
    if not path.exists(): return 0
    data = json.loads(path.read_text())
    return sum(insert_or_update_lead(lead) for lead in (data if isinstance(data,list) else data['leads']))


def campaign_leads():
    if not Path(DB_PATH).exists(): return []
    with connection(readonly=True) as conn:
        rows = conn.execute("SELECT * FROM leads WHERE domain != 'mock-test.internal' ORDER BY id").fetchall()
    result = []
    for row in rows:
        data = json.loads(row['metadata'] or '{}') if 'metadata' in row.keys() else {}
        data.update({key:row[key] for key in row.keys() if key != 'metadata'})
        data.update(company_name=row['name'],verified_email=row['founder_email'],location=row['region'])
        data['target_role'] = data.get('target_role') or 'AI / Automation Engineer'
        data['batch_or_stage'] = data.get('batch_or_stage') or 'Not recorded'
        data['hook_angle'] = data.get('hook_angle') or 'Agent reliability and business automation'
        zone = data.get('recipient_timezone') or timezone_for_location(data['location'])
        data['recommended_send_time_ist'] = '09:00–11:00 recipient local time'
        data['founder_local_window'] = zone
        result.append(data)
    return result


def atomic_write(path, writer):
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',dir=path.parent,delete=False) as handle:
            temp = handle.name
            writer(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp,path)
    finally:
        if temp and os.path.exists(temp): os.unlink(temp)


def checkpoint():
    """Cloud writes must reach the authoritative branch BEFORE a Gmail send is allowed."""
    if os.getenv('OUTREACH_CLOUD') != '1': return
    def git(*args):
        return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,text=True,timeout=60)
    git('add','--',Path(DB_PATH).name)
    dirty = subprocess.run(['git','diff','--cached','--quiet','--',Path(DB_PATH).name],cwd=ROOT).returncode
    if dirty not in (0,1): raise RuntimeError('Cannot inspect campaign checkpoint')
    if dirty: git('commit','-m','Checkpoint outreach state [skip ci]','--',Path(DB_PATH).name)
    # Also retry pushing an already-created checkpoint if the preceding push failed.
    git('push','origin','HEAD:main')


if __name__ == '__main__':
    with campaign_lock():
        init_db()
        print(f'Imported {seed_from_curated_leads()} new leads')
        checkpoint()
