#!/usr/bin/env python3
"""
Autonomous Lead Researcher & AI Personalization Engine
Discovers new funded AI startups, enforces deduplication against outreach.db,
generates hyper-personalized pitches using Gemini API, and saves drafts into Gmail.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import db
from gmail_client import GmailClient
from notify_mobile import notify_user_mobile

RESUME_LINK = "https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing"
GITHUB_LINK = "https://github.com/AvnishRana25"
LINKEDIN_LINK = "https://www.linkedin.com/in/avnish-rana-83523b2a3/"
WHATSAPP = "+91 7982252971"

AVNISH_BIO = """
Avnish Rana - Full-stack AI / FDE Engineer
Core projects:
1. Caudal AI: Automated benchmark framework testing LLM agents against dynamic Dockerized environments, pytest verifiers, tool harnesses, and grading.
2. Realty Pandit CRM: Production multi-tenant WhatsApp deal tracker (4,000+ real estate transactions). Zero price hallucination via deterministic deal state machine.
3. Klimashift: High-frequency 1 Hz IoT telemetry streaming, physics simulations, commercial ROI modeling.
Links to always include:
- Resume: https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing
- GitHub: https://github.com/AvnishRana25
- LinkedIn: https://www.linkedin.com/in/avnish-rana-83523b2a3/
- WhatsApp: +91 7982252971
"""

def generate_pitch_with_gemini(company: str, domain: str, founder: str, description: str, api_key: str = None) -> dict:
    """
    Uses Gemini API to generate hyper-personalized initial email + FU1 + FU2.
    Falls back to high-converting deterministic template if no API key is set.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    
    if api_key:
        prompt = f"""
        You are an expert tech recruiter and cold outreach copywriter. Write a 3-part cold email sequence for Avnish Rana reaching out to {founder}, founder of {company} ({domain}).
        Company description: {description}
        
        Candidate details:
        {AVNISH_BIO}
        
        Goal: Secure an interview for Junior Forward Deployed Engineer (FDE), AI Benchmark/Eval Engineer, or a 2-4 week unpaid trial contract.
        
        Requirements:
        1. Brutally specific to {company}'s actual product, failure modes, or agent architecture.
        2. No generic buzzwords ("I love your vision"). Open directly with a technical observation or question.
        3. Include Avnish's links naturally:
           Resume: {RESUME_LINK}
           GitHub: {GITHUB_LINK}
           LinkedIn: {LINKEDIN_LINK}
        4. Tone: High agency, humble, eager to prove skill via a 48h work sample or PR.
        
        Return STRICT JSON format with keys:
        - "initial_subject": string
        - "initial_body": string
        - "fu1_subject": string
        - "fu1_body": string (Day +3 technical edge-case code teardown)
        - "fu2_subject": string
        - "fu2_body": string (Day +7 polite low-pressure breakup)
        """
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"[Gemini Pitch Engine] Fallback triggered due to: {e}", file=sys.stderr)
            
    # Deterministic fallback template
    initial_subject = f"evaluating {company}'s agent workflows / FDE trial"
    initial_body = f"""Hi {founder},

Noticed how {company} is tackling agentic reliability. When building Caudal AI, the biggest hurdle wasn't prompt tuning—it was deterministic tool verification and environment state drift under complex multi-step trajectories.

At Realty Pandit, I built a deterministic state machine managing 4,000+ live WhatsApp transactions without hallucination, and at Caudal AI I designed Dockerized pytest harnesses benchmarking agents under real failure modes.

I want to join {company} as an FDE or AI Evaluation Engineer (or tackle a 2-week trial sprint / 48-hour take-home task to prove velocity).

Would you be open to a 10-minute chat this week?

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
LinkedIn: {LINKEDIN_LINK}
WhatsApp: {WHATSAPP}
"""

    fu1_subject = f"Re: {initial_subject}"
    fu1_body = f"""Hi {founder},

Quick follow-up on {company}'s agent evaluation architecture. 

One concrete challenge I found while building Caudal AI was handling tool call parameter drift when APIs return unexpected payload schemas. I solved this with automated schema sanitizers and containerized eval harnesses.

Happy to build a customized 48-hour evaluation pipeline for {company} at zero risk before you decide on anything.

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
"""

    fu2_subject = f"Re: {initial_subject}"
    fu2_body = f"""Hi {founder},

I know you're laser-focused on scaling {company}, so I won't crowd your inbox further.

If you ever need an engineer who can ship agent evaluations, build deterministic workflow guardrails, and build fast, I'd love to connect down the road.

Wishing you and the {company} team all the best!

Avnish Rana
LinkedIn: {LINKEDIN_LINK}
GitHub: {GITHUB_LINK}
"""

    return {
        "initial_subject": initial_subject,
        "initial_body": initial_body,
        "fu1_subject": fu1_subject,
        "fu1_body": fu1_body,
        "fu2_subject": fu2_subject,
        "fu2_body": fu2_body
    }

def add_lead_to_pipeline(company: str, domain: str, founder: str, email: str, role: str, region: str, description: str = ""):
    """Checks deduplication, generates pitch, saves to DB and Gmail drafts."""
    if db.is_company_contacted(domain, company):
        print(f"[Deduplication] Skipping {company} ({domain}) - already in outreach history.")
        return False

    print(f"[Lead Engine] Generating personalized outreach for {company} ({founder})...")
    pitch = generate_pitch_with_gemini(company, domain, founder, description)
    
    # Save draft into Gmail
    client = GmailClient()
    draft_id = None
    try:
        draft_res = client.create_draft(email, pitch["initial_subject"], pitch["initial_body"])
        draft_id = draft_res.get("id")
        print(f"[Gmail Draft] Created draft {draft_id} for {email}")
    except Exception as e:
        print(f"[Gmail Draft] Warning: Could not create draft: {e}", file=sys.stderr)
        
    lead_dict = {
        "company_name": company,
        "domain": domain,
        "founder_name": founder,
        "verified_email": email,
        "founder_role": role,
        "location": region,
        "status": "Drafted in Gmail" if draft_id else "DRAFTED",
        "initial_subject": pitch["initial_subject"],
        "initial_body": pitch["initial_body"],
        "fu1_subject": pitch["fu1_subject"],
        "fu1_body": pitch["fu1_body"],
        "fu2_subject": pitch["fu2_subject"],
        "fu2_body": pitch["fu2_body"],
        "gmail_draft_id": draft_id
    }
    
    db.insert_or_update_lead(lead_dict)
    
    # Send mobile notification
    notify_user_mobile(
        title=f"New Lead Queued: {company}",
        message=f"Drafted email for {founder} ({email}) saved to Gmail Drafts.",
        click_url="https://mail.google.com/mail/u/0/#drafts"
    )
    return True

if __name__ == "__main__":
    print("Testing Lead Engine Deduplication & Pitch Generation...")
    # Test deduplication check against Hamming AI
    is_dup = db.is_company_contacted("hamming.ai", "Hamming AI")
    print(f"Is Hamming AI duplicate? {is_dup} (Expected: True)")
    
    pitch = generate_pitch_with_gemini("Test AI", "testai.com", "Alex", "Agent testing platform")
    print(f"Generated Pitch Subject: {pitch['initial_subject']}")
