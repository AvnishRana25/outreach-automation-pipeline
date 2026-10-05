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

    def get_thread_message_id(self, thread_id: str) -> str:
        """Fetches the Message-ID header of the first message in a thread for RFC 2822 compliance."""
        try:
            res = self._api_request(f"threads/{thread_id}?format=metadata&metadataHeaders=Message-ID")
            messages = res.get("messages", [])
            if messages:
                for header in messages[0].get("payload", {}).get("headers", []):
                    if header.get("name", "").lower() == "message-id":
                        return header.get("value")
        except Exception as e:
            print(f"[GmailClient] Warning fetching thread Message-ID: {e}", file=sys.stderr)
        return None

    def format_email_html(self, plain_body: str) -> str:
        """Converts plain email body to clean, beautifully formatted modern HTML."""
        paragraphs = [p.strip() for p in plain_body.split('\n\n') if p.strip()]
        html_paragraphs = []
        
        for p in paragraphs:
            # Detect signature block
            if p.startswith('Best,') or p.startswith('Best regards,') or 'Avnish Rana' in p:
                sig_html = """<p style="margin: 18px 0 4px 0; color: #111827; font-size: 14px;">Best,<br><strong>Avnish Rana</strong></p>
<p style="margin: 6px 0 0 0; font-size: 13px; color: #4b5563;">
  <a href="https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing" style="color: #2563eb; text-decoration: underline; font-weight: 500;">Resume</a> &nbsp;•&nbsp; 
  <a href="https://github.com/AvnishRana25" style="color: #2563eb; text-decoration: underline; font-weight: 500;">GitHub</a> &nbsp;•&nbsp; 
  <a href="https://www.linkedin.com/in/avnish-rana-83523b2a3/" style="color: #2563eb; text-decoration: underline; font-weight: 500;">LinkedIn</a> &nbsp;•&nbsp; 
  <a href="https://wa.me/917982252971" style="color: #2563eb; text-decoration: underline; font-weight: 500;">+91 7982252971</a>
</p>"""
                html_paragraphs.append(sig_html)
                break
            else:
                # Remove artificial hard wraps inside sentences so it flows fluidly
                clean_p = ' '.join(p.split())
                html_paragraphs.append(f'<p style="margin: 0 0 14px 0; line-height: 1.55; color: #1f2937; font-size: 14px;">{clean_p}</p>')
                
        content_html = '\n'.join(html_paragraphs)
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.55; color: #1f2937; margin: 0; padding: 0;">
<div style="max-width: 600px;">
{content_html}
</div>
</body>
</html>"""

    def _build_mime_message(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Builds a multipart email with both clean fluid plain text and beautiful rich HTML."""
        msg = MIMEMultipart("alternative")
        msg["to"] = to_email
        msg["subject"] = subject
        
        if thread_id:
            orig_msg_id = self.get_thread_message_id(thread_id)
            if orig_msg_id:
                msg["In-Reply-To"] = orig_msg_id
                msg["References"] = orig_msg_id

        # Clean plain text version (remove artificial line wraps)
        clean_plain_paragraphs = []
        for p in [p.strip() for p in body.split('\n\n') if p.strip()]:
            if p.startswith('Best,') or 'Avnish Rana' in p:
                clean_plain_paragraphs.append(p)
            else:
                clean_plain_paragraphs.append(' '.join(p.split()))
        clean_plain = '\n\n'.join(clean_plain_paragraphs)

        html_content = self.format_email_html(body)

        part_plain = MIMEText(clean_plain, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")

        msg.attach(part_plain)
        msg.attach(part_html)

        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        msg_payload = {"raw": raw_msg}
        if thread_id:
            msg_payload["threadId"] = thread_id

        return msg_payload

    def create_draft(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Creates a draft email in Gmail."""
        msg_payload = self._build_mime_message(to_email, subject, body, thread_id)
        payload = {"message": msg_payload}
        return self._api_request("drafts", method="POST", payload=payload)

    def update_draft(self, draft_id: str, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Updates an existing draft email in Gmail."""
        msg_payload = self._build_mime_message(to_email, subject, body, thread_id)
        payload = {"id": draft_id, "message": msg_payload}
        return self._api_request(f"drafts/{draft_id}", method="PUT", payload=payload)

    def send_draft(self, draft_id: str) -> dict:
        """Sends an existing draft directly, removing it from drafts."""
        payload = {"id": draft_id}
        return self._api_request("drafts/send", method="POST", payload=payload)

    def send_message(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Sends an email directly through Gmail."""
        msg_payload = self._build_mime_message(to_email, subject, body, thread_id)
        return self._api_request("messages/send", method="POST", payload=msg_payload)

    def check_recipient_replied(self, recipient_email: str) -> bool:
        """
        Checks if the recipient has sent an email to us (replied).
        Searches: 'from:<recipient_email>'
        """
        query = urllib.parse.quote(f"from:{recipient_email}")
        res = self._api_request(f"messages?q={query}&maxResults=5")
        messages = res.get("messages", [])
        return len(messages) > 0

    def list_recent_drafts(self, max_results=25):
        """Lists recent drafts."""
        return self._api_request(f"drafts?maxResults={max_results}")

if __name__ == "__main__":
    client = GmailClient()
    token = client.refresh_access_token()
    print(f"Gmail Client authenticated successfully! Token starts with: {token[:12]}...")
