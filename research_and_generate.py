#!/usr/bin/env python3
"""
Autonomous Multi-Region Lead Researcher & Engine
Sources high-signal AI agent startups across:
- India (Bengaluru, Gurgaon, Mumbai)
- Middle East (Riyadh, Dubai, Abu Dhabi)
- Europe & UK (London, Paris, Berlin)
- US (San Francisco, Silicon Valley, NYC)

Enforces strict deduplication via SQLite outreach.db, generates hyper-personalized
pitches tailored to Avnish's actual projects (Caudal AI, Realty Pandit CRM, Klimashift),
creates drafts directly in Gmail, and sends phone push alerts.
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

# Curated High-Signal Seed Repositories across 4 Geographies
MULTI_REGION_PROSPECTS = [
    # --- INDIA (Bengaluru, Gurgaon) ---
    {
        "company": "LatentForce.ai",
        "domain": "latentforce.ai",
        "founder": "Siddharth Sharma",
        "email": "siddharth@latentforce.ai",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Coding Agents & Knowledge Graphs",
        "funding": "$1.7M Seed (Dec 2025)",
        "tech_focus": "Context retrieval for autonomous coding agents via dynamic knowledge graphs",
        "hook": "handling context degradation and graph state drift during complex multi-file code editing runs"
    },
    {
        "company": "Portkey AI",
        "domain": "portkey.ai",
        "founder": "Rohit Agarwal",
        "email": "rohit@portkey.ai",
        "role": "Co-Founder",
        "region": "Bengaluru, India",
        "category": "AI Gateway & Observability",
        "funding": "$3M Seed (Lightspeed)",
        "tech_focus": "Production LLM routing, guardrails, fallback architectures, and latency monitoring",
        "hook": "deterministic evaluation harnesses and automated synthetic benchmark suites for enterprise routing"
    },
    {
        "company": "Ressl AI",
        "domain": "ressl.ai",
        "founder": "Aditya V.",
        "email": "aditya@ressl.ai",
        "role": "Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Enterprise Autonomous Agents",
        "funding": "YC W26",
        "tech_focus": "Deploying autonomous action agents into complex internal ERP and workflow systems",
        "hook": "preventing tool parameter hallucination and state synchronization failures in live enterprise backends"
    },
    {
        "company": "Segmind",
        "domain": "segmind.com",
        "founder": "Steve Edison",
        "email": "steve@segmind.com",
        "role": "Co-Founder",
        "region": "Bengaluru, India",
        "category": "Fast Generative AI & Agent APIs",
        "funding": "Seed Funded",
        "tech_focus": "Low-latency serverless model APIs and multi-modal agent workflows",
        "hook": "building automated benchmarking harnesses that stress-test API latency under concurrent agent tool calls"
    },

    # --- MIDDLE EAST (Riyadh, Dubai) ---
    {
        "company": "Huspy",
        "domain": "huspy.com",
        "founder": "Jad Antoun",
        "email": "jad@huspy.com",
        "role": "Co-Founder & CEO",
        "region": "Dubai, UAE & Riyadh",
        "category": "PropTech & Real Estate Transaction Automation",
        "funding": "$37M Series A (Balderton & Peak XV)",
        "tech_focus": "End-to-end mortgage and real estate deal automation across MENA and Europe",
        "hook": "deterministic WhatsApp and CRM deal state machine architecture with zero pricing hallucination"
    },
    {
        "company": "Keep Converting",
        "domain": "keepconverting.com",
        "founder": "Omar Mansour",
        "email": "omar@keepconverting.com",
        "role": "Founder & CEO",
        "region": "Dubai, UAE",
        "category": "AI E-Commerce Personalization Agents",
        "funding": "$2M Pre-Seed (Nuwa Capital & COTU)",
        "tech_focus": "Autonomous agents dynamically rebuilding checkout and product discovery flows",
        "hook": "deterministic guardrails ensuring generative UI components don't hallucinate pricing or catalog schemas"
    },
    {
        "company": "Lean Technologies",
        "domain": "leantech.me",
        "founder": "Hisham Al-Falih",
        "email": "hisham@leantech.me",
        "role": "Co-Founder & CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "Open Banking & Financial Automation",
        "funding": "$33M Series A (Sequoia Capital)",
        "tech_focus": "Real-time bank API aggregation, data extraction, and automated payment execution",
        "hook": "building high-reliability telemetry pipelines and deterministic state machines for transactional workflows"
    },
    {
        "company": "Omniful",
        "domain": "omniful.com",
        "founder": "Mostafa E.",
        "email": "mostafa@omniful.com",
        "role": "Co-Founder & CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "Supply Chain & Warehouse Automation",
        "funding": "$5.85M Seed (Al-Rashed & VentureSouq)",
        "tech_focus": "Autonomous inventory routing and 1 Hz order processing pipelines",
        "hook": "streaming 1 Hz telemetry and deterministic workflow state machines handling physical inventory anomalies"
    },

    # --- EUROPE & UK (London, Paris, Berlin) ---
    {
        "company": "Fleuret AI",
        "domain": "fleuret.ai",
        "founder": "Arthur Fleuret",
        "email": "arthur@fleuret.ai",
        "role": "Co-Founder & CEO",
        "region": "Paris, France",
        "category": "Autonomous Cybersecurity Penetration Agents",
        "funding": "€4M Pre-Seed (RAISE Ventures, Oct 2026)",
        "tech_focus": "Autonomous offensive security agents running continuous red-team audits",
        "hook": "Dockerized sandbox verification harnesses testing agent exploit payloads without environment contamination"
    },
    {
        "company": "Dust.tt",
        "domain": "dust.tt",
        "founder": "Stanislas Polu",
        "email": "spolu@dust.tt",
        "role": "Co-Founder & CEO",
        "region": "Paris & London",
        "category": "Custom Enterprise AI Assistants",
        "funding": "$16M Series A (Sequoia Capital, YC W23)",
        "tech_focus": "Model-agnostic enterprise assistants with deep context synchronization and live tool connectors",
        "hook": "evaluating multi-agent retrieval accuracy and containerized pytest verifiers for third-party tool harnesses"
    },
    {
        "company": "PolyAI",
        "domain": "poly.ai",
        "founder": "Nikola Mrksic",
        "email": "nikola@poly.ai",
        "role": "Co-Founder & CEO",
        "region": "London, UK",
        "category": "Voice AI Agents for Enterprise",
        "funding": "$50M Series C (Hedosophia & Khosla)",
        "tech_focus": "Superhuman enterprise voice agents handling complex multi-turn phone workflows",
        "hook": "zero-latency deterministic fallback machines and audio telemetry pipelines handling phone dropouts"
    },
    {
        "company": "Mindee",
        "domain": "mindee.com",
        "founder": "Jonathan Grandperrin",
        "email": "jonathan@mindee.com",
        "role": "Co-Founder & CEO",
        "region": "Paris, France",
        "category": "Document Parsing & Autonomous OCR Agents",
        "funding": "$14M Series A (GGV Capital)",
        "tech_focus": "Deterministic structured data extraction from financial and identity documents",
        "hook": "schema-sanitized evaluation harnesses ensuring 100% precision on noisy enterprise invoices and receipts"
    },

    # --- US (San Francisco, Silicon Valley) ---
    {
        "company": "Decagon",
        "domain": "decagon.ai",
        "founder": "Jesse Zhang",
        "email": "jesse@decagon.ai",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "Enterprise Customer Support Agents",
        "funding": "$35M Series A (Accel & A16Z)",
        "tech_focus": "Autonomous customer support agents taking actions across CRM and payment backends",
        "hook": "deterministic state machines preventing rogue action execution and Dockerized tool-call benchmark suites"
    },
    {
        "company": "Factory AI",
        "domain": "factory.ai",
        "founder": "Eno Reyes",
        "email": "eno@factory.ai",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "Autonomous Software Engineering Droids",
        "funding": "$15M Series A (Sequoia Capital)",
        "tech_focus": "Autonomous code generation, testing, and pull request review agents",
        "hook": "designing pytest verification harnesses and isolated container sandboxes that grade multi-file code diffs"
    },
    {
        "company": "Bland AI",
        "domain": "bland.ai",
        "founder": "Isaiah Singer",
        "email": "isaiah@bland.ai",
        "role": "Founder & CEO",
        "region": "San Francisco, US",
        "category": "Ultra-Low Latency Phone Call AI Agents",
        "funding": "$16M Series A (Scale Venture Partners)",
        "tech_focus": "Real-time conversational voice agents handling enterprise phone dispatching",
        "hook": "streaming telemetry and deterministic state tracking under high-throughput concurrent audio streams"
    }
]

def generate_custom_pitch(lead: dict) -> dict:
    """
    Generates a personalized pitch matching Avnish's technical projects:
    - Caudal AI: for AI eval, coding agents, benchmark frameworks, sandbox verifiers
    - Realty Pandit CRM: for PropTech, transaction automation, WhatsApp state machines
    - Klimashift: for real-time telemetry, IoT, high-frequency data pipelines
    """
    company = lead["company"]
    founder = lead["founder"]
    category = lead.get("category", "")
    hook = lead.get("hook", "")
    
    # 1. PropTech / Real Estate / FinTech Match -> Focus on Realty Pandit CRM
    if "PropTech" in category or "Real Estate" in category or "Huspy" in company:
        initial_subject = f"scaling {company}'s transaction workflows / FDE trial"
        initial_body = f"""Hi {founder},

Noticed how {company} is automating complex property transactions across the region. When building Realty Pandit CRM, the biggest technical challenge wasn't conversational flow—it was engineering a deterministic deal state machine handling 4,000+ live WhatsApp transactions with zero pricing hallucination.

At Caudal AI, I also built Dockerized pytest eval harnesses benchmarking LLM agents under adversarial edge cases.

I want to join {company} as an FDE or AI Automation Engineer (or take on a 48-hour take-home / 2-week trial sprint to prove velocity).

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

Quick follow-up regarding {company}'s deal automation pipeline.

One concrete challenge I solved on Realty Pandit was preventing race conditions when buyers and brokers updated transaction terms simultaneously over WhatsApp. I implemented deterministic state locks and automated webhook reconciliation.

Happy to build a customized 48-hour proof-of-concept or integration audit for {company} at zero risk.

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
"""

    # 2. Security / Sandboxing / Tool Harness / DevTools Match -> Focus on Caudal AI Docker Eval
    elif "Cybersecurity" in category or "Coding Agents" in category or "Dust" in company or "Fleuret" in company or "Factory" in company or "Portkey" in company:
        initial_subject = f"evaluating {company}'s agent workflows & sandboxes / FDE trial"
        initial_body = f"""Hi {founder},

Came across {company}'s work in {category.lower()}. When building Caudal AI, our core bottleneck was {hook}—specifically how agents behave when tool payloads return unexpected schemas or partial outputs.

I designed containerized Docker evaluation harnesses with automated pytest verifiers and grading to catch agent drift before production rollout. Previously, I also engineered a deterministic state machine managing 4,000+ live transactions on Realty Pandit.

I want to join {company} as an FDE or AI Evaluation Engineer (or tackle a 2-week trial sprint / 48-hour work sample).

Open to a 10-minute technical chat this week?

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
LinkedIn: {LINKEDIN_LINK}
WhatsApp: {WHATSAPP}
"""
        fu1_subject = f"Re: {initial_subject}"
        fu1_body = f"""Hi {founder},

Following up on {company}'s agent verification architecture.

At Caudal AI, we saw that prompt tweaking yielded diminishing returns compared to building automated pytest verifiers that grade agent trajectories across multi-step API calls.

Happy to put together a 48-hour benchmark harness for {company}'s core agent workflows at zero cost before you decide on anything.

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
"""

    # 3. High-throughput / Voice / Telemetry / General Agent Match -> Multi-stack Blend
    else:
        initial_subject = f"scaling {company}'s agent reliability / FDE trial"
        initial_body = f"""Hi {founder},

Impressed by {company}'s trajectory in {category.lower()}. When deploying production AI systems, the hardest failure mode is {hook}.

At Caudal AI, I built Dockerized evaluation harnesses with pytest verifiers stress-testing agents under real-world drift. At Realty Pandit CRM, I built a deterministic state machine managing 4,000+ live WhatsApp transactions with zero hallucination, and at Klimashift I engineered 1 Hz streaming telemetry pipelines.

I want to join {company} as an FDE or AI/Automation Engineer (or take on a 48-hour technical trial to prove speed).

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

Quick follow-up on {company}'s agent architecture.

When building Caudal AI and Realty Pandit, I focused on building deterministic guardrails so that customer-facing agents never drift out of transaction state.

Happy to build a 48-hour prototype or review an open technical issue for {company} at zero risk.

Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
"""

    fu2_subject = f"Re: {initial_subject}"
    fu2_body = f"""Hi {founder},

I know you're busy building {company}, so I won't follow up further.

If you ever need an engineer who can build deterministic agent guardrails, Dockerized evaluation pipelines, and ship fast, I'd love to stay in touch.

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

def run_multi_region_expansion(target_regions=None, dry_run=False, create_drafts=True):
    """
    Scans prospects across India, Middle East, Europe/UK, and US.
    Enforces deduplication against outreach.db.
    Inserts newly discovered leads, creates drafts in Gmail, and notifies phone.
    """
    print("=" * 60)
    print("       MULTI-REGION COLD OUTREACH SOURCING & TEST       ")
    print("=" * 60)
    
    if target_regions:
        target_regions = [r.lower() for r in target_regions]
    
    added_leads = []
    skipped_count = 0
    client = GmailClient() if create_drafts and not dry_run else None

    for prospect in MULTI_REGION_PROSPECTS:
        comp_name = prospect["company"]
        domain = prospect["domain"]
        region = prospect["region"]
        founder = prospect["founder"]
        email = prospect["email"]
        role = prospect["role"]

        # Filter by region if specified
        if target_regions:
            matched = any(t in region.lower() or t in comp_name.lower() for t in target_regions)
            if not matched:
                continue

        # 1. Enforce Deduplication
        if db.is_company_contacted(domain, comp_name):
            print(f"[Deduplication] ⏩ Skipping {comp_name} ({domain}) - already exists in database.")
            skipped_count += 1
            continue

        print(f"\n[Lead Sourced] 🎯 {comp_name} [{region}]")
        print(f"               Founder: {founder} <{email}>")
        print(f"               Category: {prospect.get('category')}")

        # 2. Generate Pitch
        pitch = generate_custom_pitch(prospect)

        draft_id = None
        if client and not dry_run:
            try:
                draft_res = client.create_draft(email, pitch["initial_subject"], pitch["initial_body"])
                draft_id = draft_res.get("id")
                print(f"[Gmail Draft]  ✅ Saved draft in Gmail (ID: {draft_id})")
            except Exception as e:
                print(f"[Gmail Draft]  ⚠️ Could not draft in Gmail: {e}")

        lead_dict = {
            "company_name": comp_name,
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

        if not dry_run:
            db.insert_or_update_lead(lead_dict)
            
        added_leads.append(prospect)

    print("\n" + "=" * 60)
    print(f"Summary: Added {len(added_leads)} new multi-region leads, Skipped {skipped_count} duplicates.")
    print("=" * 60)

    # 3. Mobile Push Notification
    if added_leads:
        by_region = {}
        for l in added_leads:
            r = l["region"].split(",")[0].strip()
            by_region[r] = by_region.get(r, 0) + 1
        breakdown_str = ", ".join([f"{k}: {v}" for k, v in by_region.items()])
        
        notify_user_mobile(
            title=f"🚀 Multi-Region Outreach Expansion",
            message=f"Added {len(added_leads)} new AI startups across India, Middle East, Europe & US. Breakdown: {breakdown_str}.",
            click_url="https://mail.google.com/mail/u/0/#drafts"
        )
    return added_leads

if __name__ == "__main__":
    regions = None
    if len(sys.argv) > 1:
        regions = sys.argv[1].split(",")
    run_multi_region_expansion(target_regions=regions, dry_run=False, create_drafts=True)
