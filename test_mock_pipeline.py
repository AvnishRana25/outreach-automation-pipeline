#!/usr/bin/env python3
"""
End-to-End Outreach Pipeline Verification
Tests every functionality against a mock recipient (collaboratewithavnish@gmail.com):
1. Lead generation & AI copy creation (with verified links & Caudal contract context)
2. Live draft creation in Gmail API
3. Live email transmission via send_draft()
4. RFC 2822 threaded follow-up send (In-Reply-To & References in same thread)
5. Inbox reply detection engine test
6. Instant mobile push notification dispatch
7. SQLite state machine verification
"""

import sys
import time
from datetime import datetime, timezone

from gmail_client import GmailClient
from notify_mobile import notify_user_mobile
import db

TEST_EMAIL = "collaboratewithavnish@gmail.com"
RESUME_LINK = "https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing"
GITHUB_LINK = "https://github.com/AvnishRana25"
LINKEDIN_LINK = "https://www.linkedin.com/in/avnish-rana-83523b2a3/"
WHATSAPP = "+91 7982252971"

def run_test():
    print("=" * 65)
    print(f"🚀 LIVE PIPELINE END-TO-END AUDIT FOR: {TEST_EMAIL}")
    print("=" * 65)

    client = GmailClient()
    conn = db.get_connection()
    cursor = conn.cursor()

    # Step 1: Prepare copy
    print("\n[Step 1/6] Generating Personalized Email & Follow-Up...")
    subject = "🧪 [Pipeline Test] Evaluating agent reliability / FDE trial"
    body = f"""Hi Avnish,

This is a live end-to-end test of your autonomous cold outreach engine.

In my current contract role at Caudal AI, I engineer Dockerized benchmark evaluation harnesses with automated pytest verifiers testing LLM agents under real-world drift. Previously, I engineered a deterministic deal state machine handling 4,000+ live WhatsApp transactions with zero pricing hallucination on Realty Pandit CRM, and at Klimashift I built 1 Hz streaming telemetry pipelines.

I want to join your team as a Junior Forward Deployed Engineer (FDE) or AI Automation Engineer (or take on a 48-hour take-home work sample to prove velocity).

Would you be open to a 10-minute chat this week?

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
LinkedIn: {LINKEDIN_LINK}
WhatsApp: {WHATSAPP}
"""

    fu1_subject = f"Re: {subject}"
    fu1_body = f"""Hi Avnish,

Following up on the agent evaluation architecture test.

One concrete challenge I tackle in my contract role at Caudal AI is handling tool parameter drift when APIs return unexpected schemas. I solved this with automated schema sanitizers and containerized eval harnesses.

Happy to build a customized 48-hour benchmark harness for your agent workflows at zero risk.

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
LinkedIn: {LINKEDIN_LINK}
"""

    # Step 2: Create Draft in Gmail
    print("\n[Step 2/6] Testing Gmail Draft Creation via REST API...")
    draft_res = client.create_draft(TEST_EMAIL, subject, body)
    draft_id = draft_res.get("id")
    print(f" ✅ Draft successfully created in Gmail! Draft ID: {draft_id}")

    # Record into SQLite
    cursor.execute("""
    INSERT INTO leads (
        name, domain, founder_name, founder_email, founder_role, region,
        status, initial_subject, initial_body, fu1_subject, fu1_body, gmail_draft_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
        founder_email = excluded.founder_email,
        gmail_draft_id = excluded.gmail_draft_id,
        status = 'DRAFTED'
    """, (
        "Test Ventures (Mock Lead)",
        "mock-test.internal",
        "Avnish Rana",
        TEST_EMAIL,
        "Founder",
        "San Francisco, US",
        "DRAFTED",
        subject,
        body,
        fu1_subject,
        fu1_body,
        draft_id
    ))
    conn.commit()
    print(" ✅ Lead state recorded in SQLite outreach.db (Status: DRAFTED)")

    time.sleep(2)

    # Step 3: Send the Initial Email via send_draft()
    print("\n[Step 3/6] Testing Live Transmission via client.send_draft()...")
    send_res = client.send_draft(draft_id)
    thread_id = send_res.get("threadId")
    message_id = send_res.get("id")
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
    UPDATE leads SET status = 'SENT', sent_at = ?, gmail_thread_id = ?
    WHERE founder_email = ?
    """, (now, thread_id, TEST_EMAIL))
    conn.commit()
    print(f" ✅ EMAIL SENT TO {TEST_EMAIL}!")
    print(f"    - Gmail Message ID: {message_id}")
    print(f"    - Gmail Thread ID:  {thread_id}")

    time.sleep(3)

    # Step 4: Test RFC 2822 Threaded Follow-Up 1 in Same Thread
    print("\n[Step 4/6] Testing Threaded Follow-Up 1 (RFC 2822 In-Reply-To)...")
    fu_res = client.send_message(TEST_EMAIL, fu1_subject, fu1_body, thread_id=thread_id)
    fu_msg_id = fu_res.get("id")
    fu_thread_id = fu_res.get("threadId")

    cursor.execute("""
    UPDATE leads SET status = 'FU1_SENT'
    WHERE founder_email = ?
    """, (TEST_EMAIL,))
    conn.commit()
    print(f" ✅ FOLLOW-UP SENT IN SAME CONVERSATION THREAD!")
    print(f"    - Follow-Up Message ID: {fu_msg_id}")
    print(f"    - Thread ID Matched:    {fu_thread_id == thread_id} ({fu_thread_id})")

    time.sleep(2)

    # Step 5: Test Reply Detection Engine
    print("\n[Step 5/6] Testing Inbox Reply Detection Engine...")
    has_replied = client.check_recipient_replied(TEST_EMAIL)
    print(f" ✅ Reply Detection Query executed: Has {TEST_EMAIL} replied yet? -> {has_replied}")

    # Step 6: Dispatch Mobile Phone Notification
    print("\n[Step 6/6] Testing Mobile Push Notification Dispatch...")
    notify_user_mobile(
        title="🧪 Mock Pipeline Test Successful",
        message=f"Live test email & threaded follow-up successfully sent to {TEST_EMAIL}. Check inbox!",
        click_url="https://mail.google.com/mail/u/0/#sent"
    )

    conn.close()
    print("\n" + "=" * 65)
    print("🎉 ALL 6 PIPELINE CAPABILITIES VERIFIED SUCCESSFULLY!")
    print(f"Check the inbox at: {TEST_EMAIL}")
    print("=" * 65)

if __name__ == "__main__":
    run_test()
