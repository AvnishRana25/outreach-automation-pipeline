#!/usr/bin/env python3
"""
Mobile Notification Dispatcher
Sends instant push notifications directly to the user's phone via:
1. ntfy.sh (Native iOS / Android push notification - Free, zero sign-up required)
2. Telegram Bot (Instant chat alert with links & action buttons)
"""

import os
import sys
import json
import urllib.request
import urllib.parse

# Default topic for Avnish
DEFAULT_NTFY_TOPIC = os.getenv("NTFY_TOPIC", "avnish-outreach-alert-797")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_ntfy_notification(title: str, message: str, click_url: str = "https://mail.google.com/mail/u/0/#drafts", priority: str = "high", tags: str = "briefcase,email"):
    """
    Sends native push notification to ntfy.sh topic.
    Install ntfy on iPhone / Android -> Add topic -> Instant push banners!
    """
    topic = os.getenv("NTFY_TOPIC", DEFAULT_NTFY_TOPIC)
    url = f"https://ntfy.sh/{topic}"
    # Clean title of emojis for HTTP header compatibility
    clean_title = title.encode('ascii', 'ignore').decode('ascii').strip() or "Outreach Alert"
    
    headers = {
        "Title": clean_title,
        "Priority": priority,
        "Tags": tags,
        "Click": click_url,
    }
    
    try:
        req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print(f"[Mobile Notify] Push notification sent to phone via ntfy ({topic})")
                return True
    except Exception as e:
        print(f"[Mobile Notify] Error sending via ntfy: {e}", file=sys.stderr)
    return False

def send_telegram_notification(title: str, message: str, click_url: str = "https://mail.google.com/mail/u/0/#drafts"):
    """
    Sends notification to Telegram bot if credentials are provided.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    chat_id = os.getenv("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
    
    if not token or not chat_id:
        return False
        
    text = f"*{title}*\n\n{message}\n\n[Open Gmail Drafts]({click_url})"
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print(f"[Mobile Notify] Telegram alert sent to chat {chat_id}")
                return True
    except Exception as e:
        print(f"[Mobile Notify] Error sending via Telegram: {e}", file=sys.stderr)
    return False

def notify_user_mobile(title: str, message: str, click_url: str = "https://mail.google.com/mail/u/0/#drafts"):
    """
    Dispatches to all configured mobile channels.
    """
    ntfy_success = send_ntfy_notification(title, message, click_url)
    tg_success = send_telegram_notification(title, message, click_url)
    return ntfy_success or tg_success

if __name__ == "__main__":
    test_title = "🚀 Outreach Cloud Pipeline Active"
    test_msg = "Your 25 cold outreach drafts are queued for their target timezones. Click to review in Gmail."
    if len(sys.argv) > 1:
        test_title = sys.argv[1]
    if len(sys.argv) > 2:
        test_msg = sys.argv[2]
    notify_user_mobile(test_title, test_msg)
