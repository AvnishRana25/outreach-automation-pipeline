#!/usr/bin/env python3
"""Offline regressions: temporary state, fake Gmail, blocked external network."""
import base64
import contextlib
import csv
import http.client
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.error
from datetime import datetime, timezone, timedelta
from email import message_from_bytes
from unittest.mock import patch

import db
import cloud_orchestrator as co
import research_and_generate as research
import generate_outreach as cli
import notify_mobile as mobile
import setup_github_cloud as setup
from gmail_client import GmailClient
from build_dashboard import build_dashboard
from serve_dashboard import Handler


class FakeGmail:
    def __init__(self):
        self.drafts={};self.sent={};self.sent_calls=0;self.created=0
        self.reply=False;self.lose_response=False;self.delivery_delayed=False;self.fail_create=False
    @staticmethod
    def headers(message): return message['headers']
    def create_draft(self,email,subject,body,thread_id=None,message_id=None):
        if self.fail_create: raise TimeoutError('Draft creation unavailable')
        self.created+=1;identity=f'draft-{self.created}'
        result={'id':identity,'message':{'id':f'msg-{self.created}','threadId':thread_id or f'thread-{self.created}','headers':{'message-id':message_id or f'<legacy-{self.created}@example.invalid>'},'subject':subject,'body':body}}
        self.drafts[identity]=result;return result
    def get_draft(self,identity): return self.drafts.get(identity)
    def find_delivery(self,message_id,created_at=None):
        if self.delivery_delayed:return None
        if message_id in self.sent:return {'state':'SENT','message':self.sent[message_id]}
        for draft in self.drafts.values():
            if self.headers(draft['message'])['message-id']==message_id:return {'state':'DRAFTED','draft':draft}
        return None
    def find_legacy_sent(self,email,subject,created_at):
        found=[m for m in self.sent.values() if m['subject']==subject]
        if len(found)>1:raise RuntimeError('Ambiguous legacy send')
        return found[0] if found else None
    def send_draft(self,identity):
        self.sent_calls+=1
        draft=self.drafts.pop(identity)
        message={**draft['message'],'internalDate':str(int(datetime.now(timezone.utc).timestamp()*1000)),'labelIds':['SENT']}
        self.sent[message['headers']['message-id']]=message
        if self.lose_response:raise TimeoutError('Accepted, but response lost')
        return message
    def check_recipient_replied(self,*args,**kwargs):return self.reply
    def delete_draft(self,identity):self.drafts.pop(identity,None)
    def update_draft(self,*args,**kwargs):return {}


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.fake=FakeGmail()
        self.patches=[patch.object(db,'DB_PATH',str(self.root/'outreach.db')),
                      patch.dict(os.environ,{'OUTREACH_CLOUD':'','OUTREACH_ALLOW_LOCAL_SEND':'1','OUTREACH_SEND_DELAY':'0'}),
                      patch('urllib.request.urlopen',side_effect=AssertionError('External network forbidden')),
                      patch.object(co,'GmailClient',return_value=self.fake),patch.object(research,'GmailClient',return_value=self.fake),
                      patch.object(co,'notify_user_mobile',return_value=True),patch.object(research,'notify_user_mobile',return_value=True)]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.addCleanup(self.temp.cleanup)
        self.out=contextlib.redirect_stdout(io.StringIO());self.out.__enter__();self.addCleanup(self.out.__exit__,None,None,None)
        self.err=contextlib.redirect_stderr(io.StringIO());self.err.__enter__();self.addCleanup(self.err.__exit__,None,None,None)
        db.init_db()
    def lead(self,name='Example',location='San Francisco, US',verified=True):
        lead={'company_name':name,'domain':name.lower().replace(' ','')+'.invalid','founder_name':'Founder','verified_email':name.lower().replace(' ','')+'@example.invalid','location':location,'initial_subject':f'Hello {name}','initial_body':'Hi\n\nUseful body\n\nBest,\nAvnish Rana','fu1_body':'First followup','fu2_body':'Final followup'}
        if verified:lead.update(email_verified_at='2026-01-01T00:00:00+00:00',email_verification_source='User-verified contact list')
        db.insert_or_update_lead(lead)
        return co.rows()[-1]
    def aged_sent(self,days=4):
        lead=self.lead();co.action_send_batch(auto_send=True)
        co.update_lead(lead['id'],sent_at=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat())
        return co.rows()[-1]
    def client(self):return GmailClient(client_id='test',client_secret='test',refresh_token='test')

    def test_bootstrap_and_idempotent_schema(self):
        db.init_db();db.init_db()
        with db.connection() as conn:self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_validation_at_import_and_mime_boundaries(self):
        for changes in ({'verified_email':'a@example.invalid\nBcc: victim@example.invalid'},{'domain':''},{'initial_body':''},{'location':'Australia'},{'recipient_timezone':'Unknown/Zone'},{'initial_subject':'hello\nBcc: other'}):
            lead={'company_name':'Bad','domain':'bad.invalid','verified_email':'a@example.invalid','location':'London, UK','initial_subject':'Hello','initial_body':'a','fu1_body':'b','fu2_body':'c',**changes}
            with self.assertRaises(Exception):db.insert_or_update_lead(lead)
        with self.assertRaises(ValueError):self.client()._build_mime_message('a@example.invalid','x\r\nBcc: y','Body')
    def test_dedup_preserves_sent_history_and_copy(self):
        lead=self.aged_sent();before=co.rows()[0]
        changed={'company_name':'Renamed','domain':lead['domain'],'verified_email':lead['founder_email'],'location':'London, UK','initial_subject':'Replacement','initial_body':'Replacement','fu1_body':'b','fu2_body':'c'}
        self.assertFalse(db.insert_or_update_lead(changed));after=co.rows()[0]
        for key in ('status','sent_at','initial_body','founder_email','region'):self.assertEqual(before[key],after[key])
    def test_region_aliases_and_injection_rejected(self):
        self.assertEqual(db.normalize_region('Middle East'),'ME');self.assertEqual(db.normalize_region('UK'),'EU')
        for value in ('Berlin','Australia',"%' OR 1=1 --"):
            with self.assertRaises(ValueError):co.action_send_batch(value,dry_run=True)
        self.assertEqual(db.region_for_location('Berlin, Germany'),'EU')
        self.assertEqual(db.region_for_location('Bengaluru & US'),'India')
    def test_dst_and_weekend_dispatch_windows(self):
        lead={'recipient_timezone':'America/Los_Angeles'}
        self.assertTrue(db.in_send_window(lead,datetime(2026,7,6,16,30,tzinfo=timezone.utc)))
        self.assertTrue(db.in_send_window(lead,datetime(2026,12,7,17,30,tzinfo=timezone.utc)))
        self.assertFalse(db.in_send_window(lead,datetime(2026,7,5,16,30,tzinfo=timezone.utc)))
        self.assertFalse(db.in_send_window(lead,datetime(2026,12,7,15,30,tzinfo=timezone.utc)))
    def test_all_cli_dry_runs_have_no_side_effects(self):
        self.lead();before=Path(db.DB_PATH).read_bytes()
        for action in ('send-batch','followups','research-and-draft','check-replies','reconcile','status','tick','notify-test'):
            co.main(['--action',action,'--dry-run','--auto-send'])
        self.assertEqual(before,Path(db.DB_PATH).read_bytes());self.assertEqual(self.fake.created,0);self.assertEqual(self.fake.sent_calls,0)
        co.notify_user_mobile.assert_not_called()
    def test_mobile_acceptance_action_reports_success_and_failure(self):
        co.main(['--action','notify-test']);co.notify_user_mobile.assert_called_once()
        with patch.object(co,'notify_user_mobile',return_value=False):
            with self.assertRaises(RuntimeError):co.main(['--action','notify-test'])
        self.assertEqual(co.rows(),[]);self.assertEqual(self.fake.sent_calls,0)
    def test_positional_dry_run_skips_schema_and_checkpoint(self):
        self.lead()
        with patch.object(db,'init_db') as schema, patch.object(db,'checkpoint') as save:
            co.action_send_batch('All',True,True)
            co.action_process_followups(True,True)
            schema.assert_not_called();save.assert_not_called()
    def test_retired_migrations_do_not_touch_database_or_gmail(self):
        import clean_all_placeholders as old_clean
        import fix_caudal_contract_context as old_context
        self.lead();before=Path(db.DB_PATH).read_bytes()
        old_clean.clean_placeholders();old_context.run_migration()
        self.assertEqual(before,Path(db.DB_PATH).read_bytes());self.assertEqual(self.fake.created,0)
    def test_reply_cancellation_failure_retries_without_followup_send(self):
        self.aged_sent();co.action_process_followups();self.fake.reply=True
        with patch.object(self.fake,'delete_draft',side_effect=TimeoutError('Unavailable')):
            with self.assertRaises(RuntimeError):co.action_check_replies()
        self.assertEqual(co.rows()[0]['status'],'REPLIED')
        co.action_check_replies()
        self.assertEqual(co.get_attempt(1,'fu1')['state'],'CANCELLED')
        self.assertEqual(self.fake.sent_calls,1)
    def test_persistence_failure_after_successful_send_recovers_without_resend(self):
        self.lead();original=co.update_attempt
        def failing_save(lead_id,stage,**fields):
            if fields.get('state')=='SENT':raise co.PersistenceError('Push unavailable')
            return original(lead_id,stage,**fields)
        with patch.object(co,'update_attempt',side_effect=failing_save):
            with self.assertRaises(co.PersistenceError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.sent_calls,1)
        co.action_check_replies();co.action_send_batch(auto_send=True)
        self.assertEqual(co.rows()[0]['status'],'SENT');self.assertEqual(self.fake.sent_calls,1)
    def test_initial_draft_then_send_once(self):
        self.lead();self.assertEqual(co.action_send_batch(),1)
        self.assertEqual(co.rows()[0]['status'],'INITIAL_QUEUED')
        self.assertEqual(co.action_send_batch(),0)
        self.assertEqual(co.action_send_batch(auto_send=True),1)
        self.assertEqual(co.action_send_batch(auto_send=True),0)
        self.assertEqual(self.fake.sent_calls,1);self.assertIsNone(co.rows()[0]['gmail_draft_id'])
    def test_unverified_initial_send_is_held(self):
        self.lead(verified=False)
        with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.sent_calls,0);self.assertEqual(self.fake.created,0)
    def test_local_auto_send_requires_exclusive_opt_in(self):
        self.lead()
        with patch.dict(os.environ,{'OUTREACH_ALLOW_LOCAL_SEND':''}):
            with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.sent_calls,0)
    def test_manual_initial_send_reconciles_and_never_resends(self):
        self.lead();co.action_send_batch()
        self.fake.send_draft(co.get_attempt(1,'initial')['draft_id'])
        co.action_check_replies();self.assertEqual(co.rows()[0]['status'],'SENT')
        co.action_send_batch(auto_send=True);self.assertEqual(self.fake.sent_calls,1)
    def test_legacy_manual_send_recovery(self):
        lead=self.lead();draft=self.fake.create_draft(lead['founder_email'],lead['initial_subject'],lead['initial_body'])
        co.update_lead(lead['id'],gmail_draft_id=draft['id']);self.fake.send_draft(draft['id'])
        co.action_check_replies();self.assertEqual(co.rows()[0]['status'],'SENT')
    def test_missing_legacy_draft_is_held_without_creating_another(self):
        self.lead();co.update_lead(1,gmail_draft_id='deleted')
        with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.created,0);self.assertEqual(self.fake.sent_calls,0)
    def test_timeout_after_accepted_send_recovers_without_resend(self):
        self.lead();self.fake.lose_response=True
        with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.assertEqual(co.get_attempt(1,'initial')['state'],'UNKNOWN')
        self.fake.lose_response=False;co.action_check_replies()
        self.assertEqual(co.rows()[0]['status'],'SENT');co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.sent_calls,1)
    def test_delayed_search_never_retries_uncertain_send(self):
        self.lead();self.fake.lose_response=True
        with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.fake.delivery_delayed=True
        with self.assertRaises(RuntimeError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.sent_calls,1)
    def test_failed_checkpoint_stops_before_gmail_write(self):
        self.lead()
        with patch.object(db,'checkpoint',side_effect=RuntimeError('Push rejected')):
            with self.assertRaises(co.PersistenceError):co.action_send_batch(auto_send=True)
        self.assertEqual(self.fake.created,0);self.assertEqual(self.fake.sent_calls,0)
    def test_crash_between_attempt_and_lead_update_is_healed(self):
        self.lead();co.action_send_batch();attempt=co.get_attempt(1,'initial');message=self.fake.send_draft(attempt['draft_id'])
        co.update_attempt(1,'initial',state='SENT',gmail_message_id=message['id'],thread_id=message['threadId'],sent_at=db.utcnow())
        co.action_check_replies();self.assertEqual(co.rows()[0]['status'],'SENT');self.assertEqual(self.fake.sent_calls,1)
    def test_followup_draft_manual_send_then_fu2(self):
        self.aged_sent(8);original=co.rows()[0]['sent_at'];co.action_process_followups()
        self.assertEqual(co.rows()[0]['status'],'FU1_QUEUED');attempt=co.get_attempt(1,'fu1');self.assertTrue(attempt['draft_id'])
        self.fake.send_draft(attempt['draft_id']);co.action_check_replies()
        self.assertEqual(co.rows()[0]['status'],'FU1_SENT');self.assertEqual(co.rows()[0]['sent_at'],original)
        self.assertEqual(co.action_process_followups(auto_send=True),0)
        co.update_lead(1,fu1_sent_at=(datetime.now(timezone.utc)-timedelta(days=2)).isoformat())
        self.assertEqual(co.action_process_followups(auto_send=True),1);self.assertEqual(co.rows()[0]['status'],'FU2_SENT')
        self.assertEqual(co.action_process_followups(auto_send=True),0)
    def test_reply_cancels_queued_draft_and_notifies_once(self):
        self.aged_sent();co.action_process_followups();draft=co.get_attempt(1,'fu1')['draft_id'];self.fake.reply=True
        co.notify_user_mobile.reset_mock();co.action_check_replies();co.action_check_replies()
        self.assertEqual(co.rows()[0]['status'],'REPLIED');self.assertNotIn(draft,self.fake.drafts)
        self.assertEqual(co.notify_user_mobile.call_count,1);self.assertEqual(co.action_process_followups(auto_send=True),0)
    def test_followup_reply_uses_same_notification_path(self):
        self.aged_sent();self.fake.reply=True;co.notify_user_mobile.reset_mock();co.action_process_followups(auto_send=True)
        self.assertEqual(co.rows()[0]['status'],'REPLIED');co.notify_user_mobile.assert_called_once()
    def test_failed_reply_notification_retries_without_sending(self):
        self.aged_sent();self.fake.reply=True
        with patch.object(co,'notify_user_mobile',return_value=False):co.action_check_replies()
        self.assertIsNone(co.rows()[0]['reply_notified_at']);co.notify_user_mobile.reset_mock();co.action_check_replies()
        co.notify_user_mobile.assert_called_once();self.assertEqual(self.fake.sent_calls,1)
    def test_bad_timestamp_does_not_stop_other_leads(self):
        self.lead('First');self.lead('Second');co.action_send_batch(auto_send=True)
        for lead in co.rows():co.update_lead(lead['id'],sent_at='broken' if lead['id']==1 else (datetime.now(timezone.utc)-timedelta(days=4)).isoformat())
        with self.assertRaises(RuntimeError):co.action_process_followups(auto_send=True)
        self.assertEqual(co.rows()[1]['status'],'FU1_SENT');self.assertTrue(co.rows()[0]['last_error'])
    def test_naive_timestamp_is_normalized(self):
        self.aged_sent();co.update_lead(1,sent_at=(datetime.now(timezone.utc)-timedelta(days=4)).replace(tzinfo=None).isoformat())
        self.assertEqual(co.action_process_followups(auto_send=True),1)
    def test_draft_creation_failure_is_reported_and_not_retried(self):
        self.lead();self.fake.fail_create=True
        with self.assertRaises(RuntimeError):co.action_send_batch()
        self.fake.fail_create=False
        with self.assertRaises(RuntimeError):co.action_send_batch()
        self.assertEqual(self.fake.created,0)
    def test_verified_json_import_and_region_filter(self):
        records=[]
        for name,location in [('Gulf','Dubai, UAE'),('Euro','Berlin, Germany'),('Mercor','San Francisco, US')]:
            records.append({'company':name,'domain':name.lower()+'.invalid','founder':'Person','email':name.lower()+'@example.invalid','region':location,'category':'AI Agents','hook':'Tool reliability','email_verified_at':'2026-01-01T00:00:00Z','email_verification_source':'User-verified'})
        file=self.root/'import.json';file.write_text(json.dumps(records))
        added=research.run_multi_region_expansion(['ME'],create_drafts=False,leads_file=file)
        self.assertEqual([lead['company_name'] for lead in added],['Gulf'])
        added=research.run_multi_region_expansion(['EU'],create_drafts=False,leads_file=file)
        self.assertEqual([lead['company_name'] for lead in added],['Euro'])
        self.assertEqual(research.run_multi_region_expansion(['ME'],create_drafts=False,leads_file=file),[])
        records[0].pop('email_verified_at');file.write_text(json.dumps(records))
        with self.assertRaises(ValueError):research.run_multi_region_expansion(leads_file=file)
    def test_verification_import_updates_existing_lead_without_rewriting_copy(self):
        lead=self.lead(verified=False);data=dict(db.campaign_leads()[0]);data.update(initial_body='New body',email_verified_at='2026-01-01T00:00:00Z',email_verification_source='User checked')
        file=self.root/'verified.json';file.write_text(json.dumps([data]));research.run_multi_region_expansion(create_drafts=False,leads_file=file)
        self.assertEqual(co.rows()[0]['initial_body'],lead['initial_body']);self.assertEqual(co.action_send_batch(auto_send=True),1)
    def test_csv_atomic_export_and_extra_fields(self):
        self.aged_sent();destination=self.root/'tracker.csv';destination.write_text('old tracker')
        with patch.object(cli,'TRACKER_CSV',str(destination)):cli.export_to_csv()
        records=list(csv.DictReader(io.StringIO(destination.read_text())));self.assertEqual(len(records),1);self.assertEqual(records[0]['status'],'SENT')
        original=destination.read_text()
        def broken_writer(handle):handle.write('broken');raise ValueError('Bad record')
        with self.assertRaises(ValueError):db.atomic_write(destination,broken_writer)
        self.assertEqual(destination.read_text(),original)
    def test_cli_views_and_dashboard_are_from_current_state(self):
        self.aged_sent();cli.show_draft(1);cli.list_leads();cli.show_schedule()
        page=build_dashboard(self.root/'index.html');self.assertIn('SENT',page);self.assertNotIn('MX & SMTP Verified',page);self.assertNotIn('cdn.',page)
        self.assertNotIn('metadata',db.campaign_leads()[0]);self.assertEqual(db.campaign_leads()[0]['status'],'SENT')
        self.assertLess(page.index('id="toast"'),page.index('</dialog>'))
    def test_missing_verified_import_never_uses_seed_addresses(self):
        with patch.object(db,'ROOT',self.root):
            with self.assertRaises(ValueError):research.run_multi_region_expansion()
            self.assertEqual(research.run_multi_region_expansion(dry_run=True),[])
        self.assertEqual(co.rows(),[]);self.assertEqual(self.fake.created,0)
    def test_dashboard_escapes_script_terminator(self):
        self.lead();leads=db.campaign_leads();leads[0]['company_name']='</script><img src=x onerror=alert(1)>'
        page=build_dashboard(self.root/'index.html',leads)
        self.assertNotIn('</script><img',page);self.assertIn('\\u003c/script',page);self.assertIn('textContent',page)
    def test_html_preserves_content_and_tracking_mime(self):
        client=self.client();body='I am Avnish Rana\n\nKeep <img src=x onerror=alert(1)> & this paragraph.\n\nBest,\nAvnish Rana'
        content=client.format_email_html(body);self.assertIn('Keep &lt;img',content);self.assertIn('I am Avnish Rana',content)
        with patch.object(client,'get_thread_message_id',return_value='<original@example.invalid>'):
            payload=client._build_mime_message('a@example.invalid','Original subject',body,'thread','<tracking@example.invalid>')
        message=message_from_bytes(base64.urlsafe_b64decode(payload['raw']))
        self.assertEqual(message['Message-ID'],'<tracking@example.invalid>');self.assertEqual(message['In-Reply-To'],'<original@example.invalid>');self.assertEqual(payload['threadId'],'thread')
    def test_reply_detection_is_thread_time_and_automatic_response_aware(self):
        client=self.client();sent='2026-01-01T00:00:00+00:00';since=int(db.parse_time(sent).timestamp()*1000)
        def message(timestamp,headers,labels=[]):return {'internalDate':str(timestamp),'labelIds':labels,'payload':{'headers':[{'name':key,'value':value} for key,value in headers.items()]}}
        automatic=message(since+1000,{'From':'founder@example.invalid','Auto-Submitted':'auto-replied'})
        old=message(since-1000,{'From':'founder@example.invalid'})
        own=message(since+1000,{'From':'me@example.invalid'},['SENT'])
        colleague=message(since+2000,{'From':'Colleague <colleague@example.invalid>'})
        with patch.object(client,'get_thread',return_value={'messages':[automatic,old,own]}):self.assertFalse(client.check_recipient_replied('founder@example.invalid','thread',sent))
        with patch.object(client,'get_thread',return_value={'messages':[colleague]}):self.assertTrue(client.check_recipient_replied('founder@example.invalid','thread',sent))
        with self.assertRaises(ValueError):client.check_recipient_replied('founder@example.invalid')
    def test_missing_thread_header_fails_closed(self):
        client=self.client()
        with patch.object(client,'get_thread',return_value={'messages':[]}):
            with self.assertRaises(ValueError):client._build_mime_message('a@example.invalid','Subject','Body','thread')
    def test_rewritten_message_id_recovers_using_custom_tracking_header(self):
        client=self.client();tracking='<outreach.unique@outreach.local>'
        for label in ('SENT','DRAFT'):
            message={'id':'tracked','labelIds':[label],'payload':{'headers':[{'name':'Message-ID','value':'<rewritten@gmail.com>'},{'name':'X-Outreach-ID','value':tracking}]}}
            def listing(endpoint,key,query=''):
                if endpoint=='drafts':return [{'id':'stable-draft','message':{'id':'tracked'}}]
                return [] if 'rfc822msgid:' in query else [{'id':'tracked'},{'id':'unrelated'}]
            def metadata(endpoint):
                return message if 'tracked?' in endpoint else {'id':'unrelated','labelIds':['SENT'],'payload':{'headers':[]}}
            with patch.object(client,'list_all',side_effect=listing),patch.object(client,'_api_request',side_effect=metadata),patch.object(client,'get_draft',return_value={'id':'stable-draft','message':message}):
                found=client.find_delivery(tracking,db.utcnow())
                self.assertEqual(found['state'],'SENT' if label=='SENT' else 'DRAFTED')
        payload=client._build_mime_message('a@example.invalid','Subject','Body',message_id='<plus+equals=test@gmail.com>')
        message=message_from_bytes(base64.urlsafe_b64decode(payload['raw']))
        self.assertEqual(message['X-Outreach-ID'],'<plus+equals=test@gmail.com>')
    def test_gmail_pagination_and_auth_refresh(self):
        client=self.client()
        with patch.object(client,'_api_request',side_effect=[{'messages':[{'id':'1'}],'nextPageToken':'next'},{'messages':[{'id':'2'}]}]) as api:
            self.assertEqual(len(client.list_all('messages','messages','in:sent')),2);self.assertIn('pageToken=next',api.call_args.args[0])
        client.access_token='old';response=unittest.mock.MagicMock();response.__enter__.return_value=response;response.read.return_value=b'{"ok":true}'
        error=urllib.error.HTTPError('https://gmail.googleapis.com',401,'Unauthorized',{},None)
        with patch('urllib.request.urlopen',side_effect=[error,response]),patch.object(client,'refresh_access_token',side_effect=lambda:setattr(client,'access_token','new')) as refresh:
            self.assertTrue(client._api_request('profile')['ok']);refresh.assert_called_once()
    def test_private_notifications_and_credential_redaction(self):
        with patch.dict(os.environ,{},clear=True),patch('urllib.request.urlopen') as network:
            self.assertFalse(mobile.notify_user_mobile('Title','Message'));network.assert_not_called()
        with patch.dict(os.environ,{'NTFY_TOPIC':'avnish-outreach-alert-797','NTFY_TOKEN':'secret'},clear=True),patch('urllib.request.urlopen') as network:
            self.assertFalse(mobile.send_ntfy_notification('Title','Message'));network.assert_not_called()
        response=unittest.mock.MagicMock();response.__enter__.return_value=response;response.status=200;response.read.return_value=b'{"ok":true}'
        with patch.dict(os.environ,{'NTFY_TOPIC':'private-new','NTFY_TOKEN':'secret'},clear=True),patch('urllib.request.urlopen',return_value=response) as network:
            self.assertTrue(mobile.send_ntfy_notification('Title\nInjected','Message'));self.assertEqual(network.call_args.args[0].get_header('Authorization'),'Bearer secret')
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'do-not-log-me','TELEGRAM_CHAT_ID':'1'},clear=True),patch('urllib.request.urlopen',return_value=response):
            self.assertTrue(mobile.send_telegram_notification('a_[','b_*'))
        output=io.StringIO()
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'do-not-log-me','TELEGRAM_CHAT_ID':'1'},clear=True),patch('urllib.request.urlopen',side_effect=RuntimeError('do-not-log-me')),contextlib.redirect_stderr(output):
            self.assertFalse(mobile.send_telegram_notification('a','b'))
        self.assertNotIn('do-not-log-me',output.getvalue())
    def test_cloud_setup_checks_failure_results(self):
        result=subprocess.CompletedProcess(['gh'],7,'','secret-bearing error')
        with patch('subprocess.run',return_value=result):
            self.assertFalse(setup.run_cmd(['gh','repo','view'],check=False)[0])
            with self.assertRaises(RuntimeError):setup.run_cmd(['gh','repo','view'])
    def test_cloud_setup_refuses_public_repo_and_wrong_origin(self):
        credentials=self.root/'credentials.json'
        credentials.write_text(json.dumps({'client_id':'test','client_secret':'test','refresh_token':'test'}))
        for visibility,origin in [('PUBLIC',f'https://github.com/{setup.REPO_NAME}.git'),('PRIVATE',f'https://other.invalid/{setup.REPO_NAME}.git')]:
            def fake_command(args,**kwargs):
                if args[:3]==['git','rev-parse','--show-toplevel']:return True,str(db.ROOT)
                if args[:3]==['git','branch','--show-current']:return True,'main'
                if '--json' in args:return True,json.dumps({'visibility':visibility})
                if args[:3]==['git','remote','get-url']:return True,origin
                return True,'{}'
            with patch.object(setup,'CREDS_FILE',credentials),patch.object(setup,'run_cmd',side_effect=fake_command) as command:
                with self.assertRaises(ValueError):setup.setup()
                self.assertFalse(any(call.args[0][:2]==['gh','secret'] or call.args[0][:2]==['git','push'] for call in command.call_args_list))
    def test_process_lock_rejects_parallel_local_sender(self):
        script='import db; db.DB_PATH='+repr(db.DB_PATH)+';\nwith db.campaign_lock(): print("unexpected")'
        with db.campaign_lock():
            result=subprocess.run([sys.executable,'-B','-c',script],cwd=db.ROOT,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('Another campaign action',result.stderr)
    def test_preview_exposes_only_dashboard(self):
        with patch.object(db,'ROOT',self.root):
            (self.root/'index.html').write_text('dashboard')
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                connection=http.client.HTTPConnection(*server.server_address)
                for path,expected in [('/',200),('/index.html?x=1',200),('/outreach.db',404),('/.git/config',404),('/../outreach.db',404),('/%2e%2e/outreach.db',404)]:
                    connection.request('GET',path);response=connection.getresponse();self.assertEqual(response.status,expected);response.read()
                connection.close()
            finally:server.shutdown();server.server_close();thread.join()
    def test_tick_continues_independent_actions_but_surfaces_failure(self):
        with patch.object(co,'action_check_replies',side_effect=RuntimeError('Failure')),patch.object(co,'action_send_batch') as batch,patch.object(co,'action_process_followups') as follow:
            with self.assertRaises(RuntimeError):co.action_tick()
            batch.assert_called_once();follow.assert_called_once()
    def test_cloud_checkpoint_pushes_to_local_bare_remote(self):
        if not shutil.which('git'):self.skipTest('git unavailable')
        repo=self.root/'repo';repo.mkdir();bare=self.root/'remote.git'
        def git(*args):return subprocess.run(['git',*args],cwd=repo,check=True,capture_output=True,text=True)
        git('init','-b','main');git('config','user.email','test@example.invalid');git('config','user.name','Test')
        subprocess.run(['git','init','--bare',str(bare)],check=True,capture_output=True)
        git('remote','add','origin',str(bare));(repo/'outreach.db').write_bytes(b'first');git('add','.');git('commit','-m','Initial');git('push','-u','origin','main')
        (repo/'outreach.db').write_bytes(b'checkpoint')
        with patch.object(db,'ROOT',repo),patch.object(db,'DB_PATH',str(repo/'outreach.db')),patch.dict(os.environ,{'OUTREACH_CLOUD':'1'}):db.checkpoint()
        result=subprocess.run(['git','--git-dir',str(bare),'show','main:outreach.db'],capture_output=True,check=True)
        self.assertEqual(result.stdout,b'checkpoint')
    def test_workflow_is_serialized_and_has_failure_recovery(self):
        source=(db.ROOT/'.github/workflows/outreach_pipeline.yml').read_text()
        self.assertIn('cancel-in-progress: false',source);self.assertIn('git pull --ff-only',source);self.assertIn('always()',source);self.assertIn('upload-artifact@v4',source);self.assertNotIn('date -u',source);self.assertNotIn('|| true',source);self.assertNotIn("secrets.NTFY_TOPIC ||",source)


# Imported late to keep sys available in subprocess regression above.
import sys
if __name__=='__main__':unittest.main()
