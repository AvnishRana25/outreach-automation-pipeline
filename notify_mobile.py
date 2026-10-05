#!/usr/bin/env python3
"""Optional private mobile alerts. No public topic or credential-bearing error logs."""
import json
import os
import re
import sys
import urllib.request
import urllib.parse


def send_ntfy_notification(title,message,click_url='https://mail.google.com/mail/u/0/#drafts',priority='high',tags='briefcase,email'):
    topic=os.getenv('NTFY_TOPIC','')
    token=os.getenv('NTFY_TOKEN','')
    if not topic and not token: return False
    if not topic or not token or topic=='avnish-outreach-alert-797' or not re.fullmatch(r'[A-Za-z0-9_-]+',topic):
        print('ntfy needs a new protected topic and NTFY_TOKEN.',file=sys.stderr)
        return False
    headers={'Authorization':f'Bearer {token}','Title':re.sub(r'[\r\n]',' ',title).encode('ascii','ignore').decode().strip() or 'Outreach alert','Priority':priority,'Tags':tags,'Click':click_url}
    try:
        request=urllib.request.Request(f'https://ntfy.sh/{topic}',data=message.encode(),headers=headers,method='POST')
        with urllib.request.urlopen(request,timeout=10) as response:
            return response.status==200
    except Exception as exc:
        print(f'ntfy delivery failed: {type(exc).__name__}',file=sys.stderr)
        return False


def send_telegram_notification(title,message,click_url='https://mail.google.com/mail/u/0/#drafts'):
    token=os.getenv('TELEGRAM_BOT_TOKEN','')
    chat=os.getenv('TELEGRAM_CHAT_ID','')
    if not token or not chat: return False
    payload={'chat_id':chat,'text':f'{title}\n\n{message}\n\nOpen Gmail: {click_url}','disable_web_page_preview':True}
    try:
        request=urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request,timeout=10) as response:
            return response.status==200 and json.loads(response.read()).get('ok') is True
    except Exception as exc:
        print(f'Telegram delivery failed: {type(exc).__name__}',file=sys.stderr)
        return False


def notify_user_mobile(title,message,click_url='https://mail.google.com/mail/u/0/#drafts'):
    results=[]
    if os.getenv('NTFY_TOPIC') or os.getenv('NTFY_TOKEN'): results.append(send_ntfy_notification(title,message,click_url))
    if os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_CHAT_ID'): results.append(send_telegram_notification(title,message,click_url))
    if not results:
        print('Mobile alerts are not configured.',file=sys.stderr)
        return False
    return any(results)


if __name__=='__main__':
    success=notify_user_mobile(sys.argv[1] if len(sys.argv)>1 else 'Outreach test',sys.argv[2] if len(sys.argv)>2 else 'Private notification delivery test.')
    sys.exit(0 if success else 1)
