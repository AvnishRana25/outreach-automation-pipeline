#!/usr/bin/env python3
"""
Gmail REST API Client (Zero external dependencies - standard Python 3 urllib)
Handles authentication via refresh token, draft creation, message sending,
thread search, and reply detection.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.parse
import urllib.error
import html
import re
from email.utils import getaddresses
import db
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailClient:
    def __init__(self, client_id=None, client_secret=None, refresh_token=None):
        self.client_id = client_id or os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("GMAIL_REFRESH_TOKEN")
        
        # Fallback to local credential file if running on Avnish's mac
        if not (self.client_id and self.client_secret and self.refresh_token):
            local_path = os.path.expanduser("~/.google_workspace_mcp/credentials/avnishrana797@gmail.com.json")
            if os.path.exists(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.client_id = self.client_id or data.get("client_id")
                        self.client_secret = self.client_secret or data.get("client_secret")
                        self.refresh_token = self.refresh_token or data.get("refresh_token")
                except Exception as e:
                    print(f"[GmailClient] Warning reading local credentials: {e}", file=sys.stderr)
        
        self.access_token = None

    def refresh_access_token(self):
        """Exchanges refresh token for a short-lived access token."""
        if not (self.client_id and self.client_secret and self.refresh_token):
            raise ValueError("Missing Gmail credentials (client_id, client_secret, or refresh_token).")

        data = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as res:
            resp_data = json.loads(res.read().decode("utf-8"))
            self.access_token = resp_data.get("access_token")
            return self.access_token

    def _api_request(self, endpoint, method="GET", payload=None):
        """Sends an authenticated request to the Gmail REST API."""
        if not self.access_token:
            self.refresh_access_token()

        url = f"https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                content = res.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            if e.code == 401:  # Token expired, retry once
                self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=20) as res2:
                    content2 = res2.read().decode("utf-8")
                    return json.loads(content2) if content2 else {}
            raise

    def get_thread(self, thread_id):
        return self._api_request(f"threads/{urllib.parse.quote(thread_id, safe='')}?format=metadata")

    @staticmethod
    def headers(message):
        return {h['name'].lower(): h['value'] for h in message.get('payload', {}).get('headers', [])}

    def get_thread_message_id(self, thread_id):
        messages = self.get_thread(thread_id).get('messages', [])
        for message in messages:
            value = self.headers(message).get('message-id')
            if value and 'SENT' in message.get('labelIds', []):
                return value
        raise ValueError('Original sent Message-ID is unavailable; refusing an unthreaded follow-up')

    def format_email_html(self, plain_body):
        """Escape plain text; only recognized signature URL lines become hyperlinks."""
        blocks = []
        for paragraph in plain_body.split('\n\n'):
            if not paragraph.strip():
                continue
            lines = []
            for line in paragraph.splitlines():
                match = re.fullmatch(r'(Resume|GitHub|LinkedIn|WhatsApp|Phone / WhatsApp):\s*(https://[^\s]+)', line)
                if match:
                    lines.append(f'<a href="{html.escape(match[2], quote=True)}">{html.escape(match[1])}</a>')
                else:
                    lines.append(html.escape(line))
            blocks.append('<br>'.join(lines))
        return '<div dir="ltr">' + '<br><br>'.join(blocks) + '</div>'

    def _build_mime_message(self, to_email, subject, body, thread_id=None, message_id=None):
        if not isinstance(to_email, str) or not re.fullmatch(r'[^\s<>@,;\r\n]+@[^\s<>@,;\r\n]+\.[^\s<>@,;\r\n]+', to_email):
            raise ValueError('One valid recipient email is required')
        if not isinstance(subject, str) or not subject.strip() or '\r' in subject or '\n' in subject:
            raise ValueError('A nonempty, single-line subject is required')
        if not isinstance(body, str) or not body.strip():
            raise ValueError('Email body cannot be empty')
        msg = MIMEMultipart('alternative')
        msg['To'], msg['Subject'] = to_email, subject
        if message_id:
            if not re.fullmatch(r'<[^<>\s@]+@[^<>\s@]+>',message_id): raise ValueError('Invalid Message-ID')
            msg['Message-ID'] = message_id
            msg['X-Outreach-ID'] = message_id
        if thread_id:
            original = self.get_thread_message_id(thread_id)
            msg['In-Reply-To'] = original
            msg['References'] = original
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        msg.attach(MIMEText(self.format_email_html(body), 'html', 'utf-8'))
        payload = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')}
        if thread_id: payload['threadId'] = thread_id
        return payload

    def create_draft(self, to_email, subject, body, thread_id=None, message_id=None):
        return self._api_request('drafts', method='POST', payload={'message': self._build_mime_message(to_email, subject, body, thread_id, message_id)})

    def update_draft(self, draft_id, to_email, subject, body, thread_id=None, message_id=None):
        return self._api_request(f'drafts/{draft_id}', method='PUT', payload={'id':draft_id, 'message':self._build_mime_message(to_email, subject, body, thread_id, message_id)})

    def send_draft(self, draft_id):
        return self._api_request('drafts/send', method='POST', payload={'id':draft_id})

    def send_message(self, to_email, subject, body, thread_id=None, message_id=None):
        return self._api_request('messages/send', method='POST', payload=self._build_mime_message(to_email, subject, body, thread_id, message_id))

    def get_draft(self, draft_id):
        try:
            return self._api_request(f'drafts/{urllib.parse.quote(draft_id, safe="")}?format=metadata')
        except urllib.error.HTTPError as exc:
            if exc.code == 404: return None
            raise

    def list_all(self, endpoint, key, query=''):
        items, token = [], None
        while True:
            params = {'maxResults':100}
            if query: params['q'] = query
            if token: params['pageToken'] = token
            page = self._api_request(endpoint + '?' + urllib.parse.urlencode(params))
            items.extend(page.get(key, []))
            token = page.get('nextPageToken')
            if not token: return items

    def find_delivery(self, message_id, created_at=None):
        candidates = self.list_all('messages','messages', f'in:anywhere rfc822msgid:{message_id.strip("<>")}')
        matching = []
        for candidate in candidates:
            message = self._api_request(f'messages/{candidate["id"]}?format=metadata')
            if self.headers(message).get('message-id') == message_id: matching.append(message)
        if not matching and created_at:
            # Gmail can replace RFC Message-ID. Our retained custom header identifies the attempt.
            # ponytail: scan metadata since attempt creation; use Gmail history if mailbox throughput grows.
            since = int(db.parse_time(created_at).timestamp()) - 300
            for candidate in self.list_all('messages','messages',f'in:anywhere after:{since}'):
                message = self._api_request(f'messages/{candidate["id"]}?format=metadata')
                if self.headers(message).get('x-outreach-id') == message_id: matching.append(message)
        sent = [m for m in matching if 'SENT' in m.get('labelIds', [])]
        if len(sent) > 1: raise RuntimeError('Multiple sends found for one campaign attempt; review required')
        if sent: return {'state':'SENT', 'message':sent[0]}
        drafts = [m for m in matching if 'DRAFT' in m.get('labelIds', [])]
        if drafts:
            # ponytail: linear draft lookup; Gmail history/watch can replace this if the mailbox grows large.
            found = [d for d in self.list_all('drafts','drafts') if d['message']['id'] in {m['id'] for m in drafts}]
            if len(found) != 1: raise RuntimeError('Ambiguous campaign draft; review required')
            return {'state':'DRAFTED','draft':found[0]}
        return None

    def find_legacy_sent(self, recipient, subject, created_at):
        """Conservative migration for old manually-sent drafts that lacked a stored RFC ID."""
        since = int(db.parse_time(created_at).timestamp())
        query = f'in:sent to:{recipient} after:{since}'
        found = []
        for candidate in self.list_all('messages','messages',query):
            message = self._api_request(f'messages/{candidate["id"]}?format=metadata')
            headers = self.headers(message)
            recipients = {a.lower() for _,a in getaddresses([headers.get('to','')])}
            if recipient.lower() in recipients and headers.get('subject') == subject and int(message['internalDate']) >= since * 1000:
                found.append(message)
        if len(found) > 1: raise RuntimeError('Multiple matching legacy sends; review required')
        return found[0] if found else None

    def check_recipient_replied(self, recipient_email, thread_id=None, sent_at=None):
        if not thread_id or not sent_at: raise ValueError('Campaign thread and original send time are required')
        since = db.parse_time(sent_at).timestamp() * 1000
        for message in self.get_thread(thread_id).get('messages', []):
            labels = set(message.get('labelIds', []))
            headers = self.headers(message)
            if labels & {'SENT','DRAFT','TRASH','SPAM'} or int(message.get('internalDate',0)) <= since: continue
            if headers.get('auto-submitted','no').lower() != 'no': continue
            if headers.get('precedence','').lower() in ('bulk','junk','list'): continue
            if headers.get('x-autoreply') or headers.get('x-autorespond'): continue
            senders = getaddresses([headers.get('from','')])
            if any(address for _,address in senders): return True
        return False

    def delete_draft(self, draft_id):
        try:
            return self._api_request(f'drafts/{draft_id}', method='DELETE')
        except urllib.error.HTTPError as exc:
            if exc.code != 404: raise

    def list_recent_drafts(self, max_results=25):
        """Lists recent drafts."""
        return self._api_request(f"drafts?maxResults={max_results}")

if __name__ == "__main__":
    client = GmailClient()
    token = client.refresh_access_token()
    print("Gmail Client authenticated successfully.")
