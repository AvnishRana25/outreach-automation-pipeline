#!/usr/bin/env python3
"""
Outreach Database Manager (SQLite)
Guarantees deduplication, state tracking across follow-ups, and thread history.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "outreach.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        domain TEXT UNIQUE,
        founder_name TEXT,
        founder_email TEXT,
        founder_role TEXT,
        region TEXT,
        status TEXT DEFAULT 'DRAFTED',
        initial_subject TEXT,
        initial_body TEXT,
        fu1_subject TEXT,
        fu1_body TEXT,
        fu2_subject TEXT,
        fu2_body TEXT,
        gmail_draft_id TEXT,
        gmail_thread_id TEXT,
        created_at TEXT,
        sent_at TEXT,
        last_checked_reply_at TEXT,
        replied_at TEXT
    );

    CREATE TABLE IF NOT EXISTS candidate_pool (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        domain TEXT UNIQUE,
        founder_name TEXT,
        founder_email TEXT,
        founder_role TEXT,
        region TEXT,
        category TEXT,
        funding TEXT,
        tech_focus TEXT,
        hook TEXT,
        status TEXT DEFAULT 'STAGED',
        added_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def is_company_contacted(domain: str, name: str = None) -> bool:
    """Checks if company has ever been queued or contacted."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM leads WHERE domain = ? OR name = ?", (domain.lower(), name))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def insert_or_update_lead(lead_dict: dict):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO leads (
        name, domain, founder_name, founder_email, founder_role, region,
        status, initial_subject, initial_body, fu1_subject, fu1_body,
        fu2_subject, fu2_body, gmail_draft_id, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
        founder_email = excluded.founder_email,
        initial_subject = excluded.initial_subject,
        initial_body = excluded.initial_body,
        fu1_subject = excluded.fu1_subject,
        fu1_body = excluded.fu1_body,
        fu2_subject = excluded.fu2_subject,
        fu2_body = excluded.fu2_body,
        gmail_draft_id = COALESCE(excluded.gmail_draft_id, leads.gmail_draft_id)
    """, (
        lead_dict.get("company_name") or lead_dict.get("company"),
        (lead_dict.get("domain") or "").lower(),
        lead_dict.get("founder_name") or lead_dict.get("founder"),
        lead_dict.get("verified_email") or lead_dict.get("email"),
        lead_dict.get("founder_role") or lead_dict.get("role", "Founder"),
        lead_dict.get("location") or lead_dict.get("region"),
        lead_dict.get("status", "DRAFTED"),
        lead_dict.get("initial_subject"),
        lead_dict.get("initial_body"),
        lead_dict.get("fu1_subject"),
        lead_dict.get("fu1_body"),
        lead_dict.get("fu2_subject"),
        lead_dict.get("fu2_body"),
        lead_dict.get("gmail_draft_id"),
        now
    ))
    conn.commit()
    conn.close()

def add_candidate_lead(cand_dict: dict) -> bool:
    """Inserts a startup into candidate_pool if not already present or contacted."""
    domain = (cand_dict.get("domain") or "").lower().strip()
    name = (cand_dict.get("company") or cand_dict.get("name") or "").strip()
    if not domain or not name:
        return False
    if is_company_contacted(domain, name):
        return False
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    try:
        cursor.execute("""
        INSERT INTO candidate_pool (
            name, domain, founder_name, founder_email, founder_role, region,
            category, funding, tech_focus, hook, status, added_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'STAGED', ?)
        ON CONFLICT(domain) DO UPDATE SET
            founder_email = COALESCE(excluded.founder_email, candidate_pool.founder_email),
            hook = COALESCE(excluded.hook, candidate_pool.hook)
        """, (
            name,
            domain,
            cand_dict.get("founder") or cand_dict.get("founder_name"),
            cand_dict.get("email") or cand_dict.get("founder_email"),
            cand_dict.get("role") or cand_dict.get("founder_role", "Co-Founder & CEO"),
            cand_dict.get("region") or cand_dict.get("location"),
            cand_dict.get("category", "AI Agents"),
            cand_dict.get("funding", "Funded"),
            cand_dict.get("tech_focus", "Autonomous AI"),
            cand_dict.get("hook", "Deterministic agent evaluation"),
            now
        ))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_region_sql_filter(region: str = None, table_alias: str = "") -> str:
    """Returns a SQL WHERE snippet matching target region with robust geographic disambiguation."""
    prefix = f"{table_alias}." if table_alias else ""
    if not region or region.upper() == "ALL":
        return "1=1"
    r_upper = region.upper()
    if "INDIA" in r_upper or "IN" in r_upper:
        return f"({prefix}region LIKE '%Bengaluru%' OR {prefix}region LIKE '%Mumbai%' OR {prefix}region LIKE '%India%' OR {prefix}region LIKE '%Delhi%' OR {prefix}region LIKE '%Gurugram%')"
    elif "ME" in r_upper or "MIDDLE" in r_upper or "DUBAI" in r_upper or "RIYADH" in r_upper:
        return f"({prefix}region LIKE '%Riyadh%' OR {prefix}region LIKE '%Dubai%' OR {prefix}region LIKE '%Saudi%' OR {prefix}region LIKE '%Middle East%' OR {prefix}region LIKE '%UAE%')"
    elif "EU" in r_upper or "UK" in r_upper or "EUROPE" in r_upper or "LONDON" in r_upper:
        return f"({prefix}region LIKE '%London%' OR {prefix}region LIKE '%UK%' OR {prefix}region LIKE '%Europe%' OR {prefix}region LIKE '%Paris%' OR {prefix}region LIKE '%Berlin%' OR {prefix}region LIKE '%Germany%' OR {prefix}region LIKE '%Sweden%')"
    elif "US" in r_upper or "AMERICA" in r_upper:
        return f"(({prefix}region LIKE '%US%' OR {prefix}region LIKE '%SF%' OR {prefix}region LIKE '%San Francisco%' OR {prefix}region LIKE '%California%' OR {prefix}region LIKE '%Palo Alto%' OR {prefix}region LIKE '%Mountain View%') AND {prefix}region NOT LIKE '%Bengaluru%' AND {prefix}region NOT LIKE '%India%' AND {prefix}region NOT LIKE '%Riyadh%' AND {prefix}region NOT LIKE '%Dubai%')"
    return f"{prefix}region LIKE '%{region}%'"

def get_uncontacted_candidates(region: str = None, limit: int = 10) -> list:
    """Retrieves staged candidate leads for a target region not yet in leads table."""
    conn = get_connection()
    cursor = conn.cursor()
    filter_expr = get_region_sql_filter(region, table_alias="c")
    sql = f"""
    SELECT c.name as company, c.domain, c.founder_name as founder, c.founder_email as email,
           c.founder_role as role, c.region, c.category, c.funding, c.tech_focus, c.hook
    FROM candidate_pool c
    WHERE c.domain NOT IN (SELECT domain FROM leads WHERE domain IS NOT NULL)
      AND c.status = 'STAGED'
      AND {filter_expr}
    ORDER BY c.id ASC
    LIMIT ?
    """
    cursor.execute(sql, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_candidate_drafted(domain: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE candidate_pool SET status = 'DRAFTED' WHERE domain = ?", (domain.lower(),))
    conn.commit()
    conn.close()

def get_today_sent_count(region: str = None) -> int:
    """Returns number of emails sent today (UTC date)."""
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    filter_expr = get_region_sql_filter(region)
    sql = f"""
    SELECT COUNT(*) FROM leads
    WHERE status IN ('SENT', 'FU1_SENT', 'FU2_SENT')
      AND sent_at LIKE ?
      AND {filter_expr}
    """
    cursor.execute(sql, (f"{today_str}%",))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_pending_draft_count(region: str = None) -> int:
    """Returns number of leads in drafted status for a region."""
    conn = get_connection()
    cursor = conn.cursor()
    filter_expr = get_region_sql_filter(region)
    sql = f"""
    SELECT COUNT(*) FROM leads
    WHERE LOWER(status) LIKE '%draft%'
      AND {filter_expr}
    """
    cursor.execute(sql)
    count = cursor.fetchone()[0]
    conn.close()
    return count

CANDIDATE_POOL_SEEDS = [
    # INDIA (Bengaluru, Delhi-NCR, Gurugram)
    {
        "company": "Krutrim",
        "domain": "krutrim.com",
        "founder": "Bhavish Aggarwal",
        "email": "bhavish@krutrim.com",
        "role": "Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Sovereign Indic LLMs & AI Cloud",
        "funding": "$50M Series A (Matrix Partners)",
        "tech_focus": "Sovereign AI infrastructure, Indic foundation models, and regional AI cloud APIs",
        "hook": "building deterministic eval harnesses and preventing drift across Indic dialect benchmarks"
    },
    {
        "company": "Wysa",
        "domain": "wysa.com",
        "founder": "Jo Aggarwal",
        "email": "jo@wysa.com",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Conversational Mental Health AI",
        "funding": "$30M Series B (HealthQuad, British Patient Capital)",
        "tech_focus": "Emotionally intelligent conversational agents and clinical safety guardrails",
        "hook": "clinical evaluation benchmarks and preventing conversational hallucination in regulated health workflows"
    },
    {
        "company": "Yellow.ai",
        "domain": "yellow.ai",
        "founder": "Raghu Ravinutala",
        "email": "raghu@yellow.ai",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Enterprise Customer Service Autonomous Agents",
        "funding": "$100M+ Series C (Lightspeed, WestBridge)",
        "tech_focus": "Multi-channel dynamic agent orchestrators across voice and text",
        "hook": "deterministic state tracking and tool execution verification under heavy enterprise volume"
    },
    {
        "company": "CoRover.ai",
        "domain": "corover.ai",
        "founder": "Ankush Sabharwal",
        "email": "ankush@corover.ai",
        "role": "Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Sovereign Conversational AI & BharatGPT",
        "funding": "Funded",
        "tech_focus": "Multilingual conversational agent platforms powering Indian railways and banking",
        "hook": "sub-300ms latency pipelines and edge inference benchmark verification"
    },
    {
        "company": "Rezo.ai",
        "domain": "rezo.ai",
        "founder": "Manish Gupta",
        "email": "manish@rezo.ai",
        "role": "Co-Founder & CEO",
        "region": "Delhi-NCR, India",
        "category": "Autonomous Contact Center AI",
        "funding": "Seed Funded",
        "tech_focus": "Real-time voice and chat bot automation for enterprise call centers",
        "hook": "streaming telephony eval harnesses and automated speech-to-text drift detection"
    },
    {
        "company": "Infilect",
        "domain": "infilect.com",
        "founder": "Anand Narayanan",
        "email": "anand@infilect.com",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Retail Visual Intelligence & Shelf AI Agents",
        "funding": "$3M Series A",
        "tech_focus": "Edge computer vision and image intelligence agents for retail merchandising",
        "hook": "automated containerized test suites verifying visual telemetry and defect tracking"
    },
    {
        "company": "Dubverse.ai",
        "domain": "dubverse.ai",
        "founder": "Varshul Goyal",
        "email": "varshul@dubverse.ai",
        "role": "Co-Founder & CEO",
        "region": "Gurugram, India",
        "category": "Generative AI Video Dubbing & Speech Agents",
        "funding": "Seed Funded",
        "tech_focus": "Real-time video voice cloning and multi-lingual dubbing pipelines",
        "hook": "evaluating audio-video synchronization and streaming speech latency benchmarks"
    },
    {
        "company": "Murf.ai",
        "domain": "murf.ai",
        "founder": "Sneha Roy",
        "email": "sneha@murf.ai",
        "role": "Co-Founder",
        "region": "Bengaluru, India",
        "category": "Synthetic Speech & Voice AI Workflows",
        "funding": "$10M Series A (Matrix Partners)",
        "tech_focus": "Studio-quality synthetic voice generation and enterprise voiceover automation",
        "hook": "low-latency audio synthesis and edge TTS benchmark suites"
    },
    {
        "company": "Lightbeam.ai",
        "domain": "lightbeam.ai",
        "founder": "Himanshu Shukla",
        "email": "himanshu@lightbeam.ai",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "Zero-Trust Data Privacy & AI Governance",
        "funding": "$17M Series A (Vertex Ventures)",
        "tech_focus": "Agentic data discovery, classification, and privacy compliance automation",
        "hook": "deterministic boundary evaluation for automated PII masking across enterprise databases"
    },
    {
        "company": "DevZero",
        "domain": "devzero.io",
        "founder": "Debo Ray",
        "email": "debo@devzero.io",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru & Seattle, India",
        "category": "Cloud Development Environments & Developer Infrastructure",
        "funding": "$26M Series A (Anthos Capital)",
        "tech_focus": "Developer environment orchestration and agentic dev tooling",
        "hook": "containerized sandbox evaluation and automated developer workflow verification"
    },
    {
        "company": "InFeedo",
        "domain": "infeedo.com",
        "founder": "Tanmaya Jain",
        "email": "tanmaya@infeedo.com",
        "role": "Founder & CEO",
        "region": "Gurugram, India",
        "category": "Employee Experience AI & Predictive People Analytics",
        "funding": "$12M Series A",
        "tech_focus": "Conversational workplace bot Amber predicting burnout and attrition",
        "hook": "deterministic sentiment evaluation harnesses and preventing conversational drift"
    },
    {
        "company": "Beatoven.ai",
        "domain": "beatoven.ai",
        "founder": "Mansoor Rahimat Khan",
        "email": "mansoor@beatoven.ai",
        "role": "Co-Founder & CEO",
        "region": "Bengaluru, India",
        "category": "AI Music Generation & Sound Workflows",
        "funding": "$1.3M Seed",
        "tech_focus": "Audio generation agents creating royalty-free adaptive background music",
        "hook": "audio token evaluation and streaming playback performance harnesses"
    },

    # MIDDLE EAST (Riyadh, Dubai)
    {
        "company": "Tonomus",
        "domain": "tonomus.neom.com",
        "founder": "Joseph Bradley",
        "email": "joseph.bradley@tonomus.neom.com",
        "role": "CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "Cognitive City AI Infrastructure & Autonomous Services",
        "funding": "Multi-Billion Backed (NEOM)",
        "tech_focus": "Sovereign AI foundation models and smart cognitive operating systems",
        "hook": "stress-testing high-throughput autonomous agents across municipal digital twin APIs"
    },
    {
        "company": "Squadio",
        "domain": "squadio.com",
        "founder": "Faisal Al-Saif",
        "email": "faisal@squadio.com",
        "role": "Founder & CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "AI Talent Orchestration & Automated Engineering Teams",
        "funding": "Series A Funded",
        "tech_focus": "AI-augmented engineering team matching and productivity analytics",
        "hook": "building automated code review harnesses and deterministic skill grading test suites"
    },
    {
        "company": "Tamara",
        "domain": "tamara.co",
        "founder": "Abdulmajeed Alsukhan",
        "email": "abdulmajeed@tamara.co",
        "role": "Co-Founder & CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "Fintech & Autonomous Credit Risk Engines",
        "funding": "Series C Unicorn ($340M+)",
        "tech_focus": "Real-time credit risk assessment and merchant checkout automation",
        "hook": "deterministic financial state machines and automated transaction fraud verification"
    },
    {
        "company": "Zywa",
        "domain": "zywa.co",
        "founder": "Alok Patil",
        "email": "alok@zywa.co",
        "role": "Co-Founder & CEO",
        "region": "Dubai, UAE",
        "category": "Youth Banking & Gen-Z AI Financial Assistants",
        "funding": "$3M Seed (Y Combinator)",
        "tech_focus": "Gamified banking workflows and conversational financial advisors for youth",
        "hook": "deterministic state machines ensuring zero pricing hallucination across card transactions"
    },
    {
        "company": "AdFalcon",
        "domain": "adfalcon.com",
        "founder": "Mahmoud Arraj",
        "email": "mahmoud@adfalcon.com",
        "role": "Co-Founder",
        "region": "Dubai, UAE",
        "category": "Programmatic Ad AI & Real-time Bidding Agents",
        "funding": "Funded",
        "tech_focus": "Programmatic advertising auctions and algorithmic ad targeting",
        "hook": "microsecond auction latency benchmarks and high-throughput streaming state machines"
    },
    {
        "company": "Cartlow",
        "domain": "cartlow.com",
        "founder": "Mohammad Sleiman",
        "email": "mohammad@cartlow.com",
        "role": "Founder & CEO",
        "region": "Dubai, UAE",
        "category": "Recommerce AI & Reverse Logistics Automation",
        "funding": "$18M Series A",
        "tech_focus": "Automated grading, pricing, and return disposition algorithms",
        "hook": "real-time computer vision grading benchmarks and automated warehouse state machines"
    },
    {
        "company": "Intelmatix",
        "domain": "intelmatix.com",
        "founder": "Anas Alfaris",
        "email": "anas@intelmatix.com",
        "role": "Co-Founder & CEO",
        "region": "Riyadh, Saudi Arabia",
        "category": "Enterprise Decision AI & Cognitive Intelligence",
        "funding": "Series A Funded",
        "tech_focus": "Enterprise predictive intelligence and autonomous supply chain dispatching",
        "hook": "Dockerized eval suites and automated edge decision verification"
    },

    # EUROPE & UK (London, Berlin, Paris, Stockholm)
    {
        "company": "Lovable",
        "domain": "lovable.dev",
        "founder": "Anton Osika",
        "email": "anton@lovable.dev",
        "role": "Co-Founder & CEO",
        "region": "Stockholm, Sweden",
        "category": "Autonomous Full-Stack App Generation",
        "funding": "$7.5M Seed",
        "tech_focus": "Autonomous coding agents generating full-stack production software from natural language",
        "hook": "multi-file code diff evaluation harnesses and sandboxed Docker container verifiers"
    },
    {
        "company": "DeepL",
        "domain": "deepl.com",
        "founder": "Jaroslaw Kutylowski",
        "email": "jaroslaw@deepl.com",
        "role": "Founder & CEO",
        "region": "Cologne, Germany",
        "category": "Neural Machine Translation & Enterprise Language AI",
        "funding": "$300M+ Series C Unicorn",
        "tech_focus": "High-precision neural translation and contextual enterprise document writing agents",
        "hook": "sub-50ms latency translation benchmarks and deterministic terminology consistency verifiers"
    },
    {
        "company": "ElevenLabs",
        "domain": "elevenlabs.io",
        "founder": "Mati Staniszewski",
        "email": "mati@elevenlabs.io",
        "role": "Co-Founder & CEO",
        "region": "London, UK",
        "category": "Generative Voice AI & Speech Foundation Models",
        "funding": "$80M Series B Unicorn",
        "tech_focus": "Real-time multilingual voice synthesis and conversational voice agent APIs",
        "hook": "streaming audio interruption latency benchmarks and automated speech eval harnesses"
    },
    {
        "company": "Wayve",
        "domain": "wayve.ai",
        "founder": "Alex Kendall",
        "email": "alex@wayve.ai",
        "role": "Co-Founder & CEO",
        "region": "London, UK",
        "category": "Embodied AI & End-to-End Autonomous Driving",
        "funding": "$1.05B Series C (SoftBank, NVIDIA)",
        "tech_focus": "World models and end-to-end embodied AI agents for autonomous mobility",
        "hook": "continuous simulation evaluation harnesses and deterministic closed-loop safety verifiers"
    },
    {
        "company": "Encord",
        "domain": "encord.com",
        "founder": "Eric Landau",
        "email": "eric@encord.com",
        "role": "Co-Founder & CEO",
        "region": "London, UK",
        "category": "Multimodal AI Data Engine & Active Learning",
        "funding": "$30M Series B",
        "tech_focus": "Automated data curation and model evaluation for multimodal vision systems",
        "hook": "containerized eval benchmarks stress-testing dataset quality and label drift"
    },
    {
        "company": "Deepset",
        "domain": "deepset.ai",
        "founder": "Milos Rusic",
        "email": "milos@deepset.ai",
        "role": "Co-Founder & CEO",
        "region": "Berlin, Germany",
        "category": "LLM Orchestration & Haystack Framework",
        "funding": "$30M Series B",
        "tech_focus": "Open-source LLM pipelines and enterprise agent orchestration",
        "hook": "deterministic tool call evaluation harnesses and schema drift testing"
    },
    {
        "company": "Black Forest Labs",
        "domain": "blackforestlabs.ai",
        "founder": "Robin Rombach",
        "email": "robin@blackforestlabs.ai",
        "role": "Co-Founder & CEO",
        "region": "Freiburg, Germany",
        "category": "FLUX Foundation Models & Visual AI",
        "funding": "$31M Seed (A16Z)",
        "tech_focus": "State-of-the-art open diffusion and visual generation architectures",
        "hook": "GPU inference throughput benchmarking and automated image quality eval pipelines"
    },

    # US (San Francisco, Mountain View, Palo Alto)
    {
        "company": "Augment Code",
        "domain": "augmentcode.com",
        "founder": "Scott Dietzen",
        "email": "scott@augmentcode.com",
        "role": "CEO",
        "region": "Mountain View, US",
        "category": "Enterprise AI Coding Platform",
        "funding": "$227M Series B (Index, Sutter Hill)",
        "tech_focus": "Deep repository context indexing and collaborative AI coding agents",
        "hook": "benchmarking multi-million line codebase indexing latency and precision"
    },
    {
        "company": "Magic AI",
        "domain": "magic.dev",
        "founder": "Eric Steinberger",
        "email": "eric@magic.dev",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "Ultra-Long Context Frontier AI & Automated Software Engineering",
        "funding": "$465M Series C",
        "tech_focus": "Ultra-long 100M-token context models built specifically for software engineering",
        "hook": "synthetic code benchmark harnesses evaluating cross-file architectural refactoring"
    },
    {
        "company": "Together AI",
        "domain": "together.ai",
        "founder": "Vipul Ved Prakash",
        "email": "vipul@together.ai",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "Cloud AI Acceleration & Open Source Inference",
        "funding": "$106M Series A (Salesforce, Kleiner Perkins)",
        "tech_focus": "Distributed model training and low-latency open-source model inference endpoints",
        "hook": "automated latency and throughput evaluation harnesses under massive burst traffic"
    },
    {
        "company": "Pika",
        "domain": "pika.art",
        "founder": "Demi Guo",
        "email": "demi@pika.art",
        "role": "Co-Founder & CEO",
        "region": "Palo Alto, US",
        "category": "Generative Video Foundation Models",
        "funding": "$80M Series B (Lightspeed)",
        "tech_focus": "Video generation engines and generative camera controls",
        "hook": "video rendering frame-rate benchmarking and automated visual artifact verifiers"
    },
    {
        "company": "Cartesia",
        "domain": "cartesia.ai",
        "founder": "Karan Goel",
        "email": "karan@cartesia.ai",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "State Space Voice Models & Ultra-Fast Audio AI",
        "funding": "Seed Funded",
        "tech_focus": "Ultra-fast streaming audio models powered by state-space architectures (Mamba)",
        "hook": "benchmarking sub-100ms time-to-first-audio latency and real-time streaming test suites"
    },
    {
        "company": "CrewAI",
        "domain": "crewai.com",
        "founder": "Joao Moura",
        "email": "joao@crewai.com",
        "role": "Founder & CEO",
        "region": "San Francisco, US",
        "category": "Multi-Agent Collaboration Framework",
        "funding": "$18M Series A",
        "tech_focus": "Orchestrating autonomous role-playing agents collaborating on enterprise tasks",
        "hook": "deterministic multi-agent state machines and preventing circular agent delegation loops"
    },
    {
        "company": "LlamaIndex",
        "domain": "llamaindex.ai",
        "founder": "Jerry Liu",
        "email": "jerry@llamaindex.ai",
        "role": "Co-Founder & CEO",
        "region": "San Francisco, US",
        "category": "Data Framework for LLMs & Agentic RAG",
        "funding": "$8.5M Seed",
        "tech_focus": "Advanced retrieval-augmented generation and structured document agents",
        "hook": "automated retrieval eval harnesses verifying context precision and recall"
    }
]

def seed_candidate_pool():
    """Populates candidate_pool table with verified uncontacted AI startups."""
    init_db()
    inserted = 0
    for cand in CANDIDATE_POOL_SEEDS:
        if add_candidate_lead(cand):
            inserted += 1
    print(f"Seeded {inserted} startups into candidate_pool buffer in SQLite ({DB_PATH}).")

def seed_from_curated_leads():
    curated_path = os.path.join(os.path.dirname(__file__), "curated_leads.json")
    if not os.path.exists(curated_path):
        return
    with open(curated_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    leads = data if isinstance(data, list) else data.get("leads", [])
    for lead in leads:
        insert_or_update_lead(lead)
    print(f"Seeded {len(leads)} leads into SQLite database ({DB_PATH})")

if __name__ == "__main__":
    init_db()
    seed_from_curated_leads()
    seed_candidate_pool()

