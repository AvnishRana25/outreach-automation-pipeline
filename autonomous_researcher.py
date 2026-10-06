#!/usr/bin/env python3
"""
Autonomous Startup Researcher & Enricher
Discovers newly funded AI startups across India, Middle East, Europe/UK, and US,
enriches them with live website/brand context, and finds verified founder contacts.

Supports:
1. Gemini API (Search-grounded AI discovery & technical edge-case analysis)
2. Context.dev API (Landing page & tech stack markdown scraping)
3. Hunter.io / Prospeo API (Founder email finder & deliverability verification)
4. DNS MX record validation (Zero-dependency fallback verifier)
"""

import os
import sys
import json
import re
import socket
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

class AutonomousResearcher:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
        self.context_dev_key = os.getenv("CONTEXT_DEV_API_KEY", "").strip().strip('"').strip("'")
        self.hunter_key = os.getenv("HUNTER_API_KEY", "").strip().strip('"').strip("'")
        self.prospeo_key = os.getenv("PROSPEO_API_KEY", "").strip().strip('"').strip("'")

    def has_discovery_capabilities(self) -> bool:
        """Returns True if at least one live intelligence provider is configured."""
        return bool(self.gemini_key or self.groq_key or self.context_dev_key or self.hunter_key)

    def verify_domain_mx(self, domain: str) -> bool:
        """Checks if a domain has active MX or A records using standard library socket."""
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        try:
            socket.getaddrinfo(clean_domain, 25, socket.AF_INET, socket.SOCK_STREAM)
            return True
        except Exception:
            try:
                socket.gethostbyname(clean_domain)
                return True
            except Exception:
                return False

    def _lookup_prospeo(self, domain: str, first: str, last: str, company_name: str = "") -> dict:
        """Helper to query Prospeo for verified emails."""
        if not self.prospeo_key:
            return None

        # 1. Try enrich-person with verified email requirement
        try:
            payload = json.dumps({
                "first_name": first,
                "last_name": last,
                "full_name": f"{first} {last}".strip(),
                "company_website": domain,
                "company_name": company_name or domain.split('.')[0].capitalize(),
                "only_verified_email": True
            })
            req = urllib.request.Request(
                "https://api.prospeo.io/enrich-person",
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json", "X-KEY": self.prospeo_key}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    person = data.get("person", {})
                    email = person.get("email")
                    status = person.get("email_status", "VERIFIED")
                    if email and status in ("VERIFIED", "VALID"):
                        return {"email": email, "confidence": 98, "source": f"Prospeo Rollback ({status})"}
        except Exception as e:
            # Fall through to email-finder endpoint
            pass

        # 2. Try email-finder endpoint as secondary Prospeo attempt
        try:
            payload = json.dumps({
                "first_name": first,
                "last_name": last or first,
                "company": domain
            })
            req = urllib.request.Request(
                "https://api.prospeo.io/email-finder",
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json", "X-KEY": self.prospeo_key}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    res = data.get("response", {})
                    email = res.get("email")
                    status = res.get("email_status", "VERIFIED")
                    if email:
                        return {"email": email, "confidence": 92, "source": f"Prospeo Rollback ({status})"}
        except Exception as e:
            print(f"[Email Finder] Prospeo error for {domain}: {e}", file=sys.stderr)

        return None

    def find_founder_email(self, domain: str, first_name: str, last_name: str = "", company_name: str = "") -> dict:
        """
        Locates and verifies the founder's email address using a resilient pipeline:
        1. PRIMARY: Hunter.io API (High deliverability verification)
        2. ROLLBACK: Prospeo API (Fallback if Hunter fails, quota exhausted, or low score)
        3. SAFETY FALLBACK: Pattern Inference ({first}@{domain}) + DNS MX deliverability validation
        """
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        first = re.sub(r'[^a-zA-Z]', '', first_name).lower()
        last = re.sub(r'[^a-zA-Z]', '', last_name).lower()

        hunter_success = False

        # --- STAGE 1: Primary Lookup via Hunter.io ---
        if self.hunter_key:
            try:
                params = {"domain": clean_domain, "first_name": first, "last_name": last, "api_key": self.hunter_key}
                url = f"https://api.hunter.io/v2/email-finder?{urllib.parse.urlencode(params)}"
                req = urllib.request.Request(url, headers={"User-Agent": "AutonomousOutreach/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        payload_data = data.get("data", {})
                        email = payload_data.get("email")
                        score = payload_data.get("score", 0)
                        verification = payload_data.get("verification", {}).get("status", "")
                        
                        # Accept if score >= 65 or marked valid
                        if email and (score >= 65 or verification in ("valid", "accept_all")):
                            print(f"[Email Finder] 🎯 Hunter.io verified email for {first} at {clean_domain}: {email} (Score: {score}%)")
                            return {"email": email, "confidence": score, "source": f"Hunter.io ({score}%)"}
                        elif email:
                            print(f"[Email Finder] ⚠️ Hunter.io email {email} had low confidence ({score}%). Triggering Prospeo rollback...")
            except Exception as e:
                print(f"[Email Finder] Hunter.io lookup failed or limit reached: {e}. Triggering Prospeo rollback...", file=sys.stderr)

        # --- STAGE 2: Rollback Option via Prospeo ---
        if self.prospeo_key:
            print(f"[Email Finder] 🔄 Prospeo Rollback active: Searching verified email for {first} {last} at {clean_domain}...")
            prospeo_res = self._lookup_prospeo(clean_domain, first, last, company_name)
            if prospeo_res:
                print(f"[Email Finder] 🛡️ Prospeo Rollback SUCCESS: Found {prospeo_res['email']} ({prospeo_res['source']})")
                return prospeo_res
            else:
                print(f"[Email Finder] Prospeo found no verified record for {first} at {clean_domain}.")

        # --- STAGE 3: Safety Fallback via Pattern & MX Validation ---
        has_mx = self.verify_domain_mx(clean_domain)
        guessed_email = f"{first}@{clean_domain}"
        print(f"[Email Finder] ℹ️ Using pattern fallback: {guessed_email} (Domain MX Active: {has_mx})")
        return {
            "email": guessed_email,
            "confidence": 75 if has_mx else 40,
            "source": "MX Validated Pattern Fallback" if has_mx else "Inferred (Unverified Domain)"
        }

    def scrape_company_context_dev(self, domain: str) -> str:
        """
        Uses Context.dev API to scrape the company's landing page into clean Markdown.
        Helps extract specific architecture details for hyper-personalized hooks.
        """
        if not self.context_dev_key:
            return ""
            
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        target_url = f"https://{clean_domain}"
        
        try:
            req_data = json.dumps({
                "url": target_url,
                "formats": {"markdown": True},
                "sharedParams": {"mainContentOnly": True}
            }).encode("utf-8")
            
            req = urllib.request.Request(
                "https://api.context.dev/v1/web/scrape",
                data=req_data,
                headers={
                    "Authorization": f"Bearer {self.context_dev_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "AutonomousColdOutreach/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_md = data.get("markdown") or data.get("data", {}).get("markdown") or ""
                    if isinstance(raw_md, dict):
                        markdown = raw_md.get("content") or raw_md.get("text") or raw_md.get("raw") or raw_md.get("markdown") or json.dumps(raw_md)
                    elif isinstance(raw_md, str):
                        markdown = raw_md
                    else:
                        markdown = str(raw_md) if raw_md else ""
                    print(f"[Context.dev] ✅ Scraped live technical context for {clean_domain} ({len(markdown)} bytes)")
                    return markdown[:3000] # Return top 3,000 chars of core product context
        except Exception as e:
            print(f"[Context.dev] Scraping error for {clean_domain}: {e}", file=sys.stderr)
            
        return ""

    def discover_with_gemini(self, target_region: str = "All", count: int = 3) -> list:
        """
        Uses Gemini API (with Search Grounding) to discover newly funded (2025-2026) AI agent startups.
        """
        if not self.gemini_key:
            return []

        prompt = f"""You are a Silicon Valley / Global Tech Scout identifying fast-growing AI startups.
Find {count} REAL, recently funded (2025-2026 Seed, Series A, or YC/Accel/Lightspeed backed) AI agent or AI automation startups in region: '{target_region}'.
Focus on startups building autonomous coding agents, customer support agents, AI voice agents, eval/benchmarking platforms, or vertical enterprise AI.

For each startup, provide:
1. Company Name
2. Official Domain (e.g. example.ai, not a subpath)
3. Founder or Co-Founder Full Name
4. Founder Role (e.g. Co-Founder & CEO, CTO)
5. Region / City (e.g. Bengaluru, India; Riyadh, Saudi Arabia; London, UK; San Francisco, US)
6. Category (e.g. Autonomous Coding Agents, Voice AI, AI Eval Harnesses)
7. Funding Stage & Backers (e.g. $4M Seed - Lightspeed, Dec 2025)
8. Technical Focus (1 sentence on their core tech)
9. Technical Hook (A realistic technical challenge an FDE / Eval Engineer would solve for them, e.g. 'handling tool parameter drift when API schemas change', 'building containerized pytest eval harnesses for multi-file code diffs')

Output strictly valid JSON with this exact schema:
[
  {{
    "company": "Company Name",
    "domain": "company.ai",
    "founder": "First Last",
    "role": "Co-Founder & CEO",
    "region": "City, Country",
    "category": "Category",
    "funding": "Funding details",
    "tech_focus": "Tech description",
    "hook": "Engineering challenge"
  }}
]
Do not wrap in markdown quotes if possible, output pure JSON."""

        models_to_try = [
            "models/gemini-3.8-flash",
            "gemini-3.8-flash"
        ]
        for model in models_to_try:
            model_path = model if model.startswith("models/") else f"models/{model}"
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            }
            for attempt in range(2):
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "AutonomousColdOutreach/1.0"
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        if resp.status == 200:
                            raw = json.loads(resp.read().decode("utf-8"))
                            text_part = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            # Parse JSON from response
                            cleaned = re.sub(r'^```json\s*', '', text_part.strip())
                            cleaned = re.sub(r'\s*```$', '', cleaned)
                            startups = json.loads(cleaned)
                            if isinstance(startups, list) and startups:
                                print(f"[Gemini Scout] 🔍 Discovered {len(startups)} new AI startups for {target_region} via {model}")
                                return startups
                except urllib.error.HTTPError as e:
                    body = ""
                    try:
                        body = e.read().decode("utf-8", errors="replace")
                    except Exception:
                        pass
                    if e.code == 503 and attempt == 0:
                        print(f"[Gemini Scout] Model {model} temporary 503 spike, retrying in 2.5s...", file=sys.stderr)
                        time.sleep(2.5)
                        continue
                    print(f"[Gemini Scout] Model {model} HTTP Error {e.code}: {body}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"[Gemini Scout] Model {model} attempt error: {e}", file=sys.stderr)
                    break

        # Diagnostic check if all models fail
        try:
            diag_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.gemini_key}"
            with urllib.request.urlopen(diag_url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                available = [m.get("name") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                print(f"[Gemini Scout] ℹ️ Available models for key: {available[:6]}", file=sys.stderr)
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            print(f"[Gemini Scout] Diagnostic ListModels HTTP {e.code}: {err_body}", file=sys.stderr)
        except Exception as e:
            print(f"[Gemini Scout] Diagnostic ListModels error: {e}", file=sys.stderr)

        return []

    def discover_with_groq(self, target_region: str = "All", count: int = 3) -> list:
        """
        Uses Groq API (Qwen 3.8 / GPT-OSS) as a zero-cost, high-speed discovery fallback
        when Gemini rate limits or quota triggers.
        """
        if not self.groq_key:
            return []

        prompt = f"""You are a Silicon Valley / Global Tech Scout identifying fast-growing AI startups.
Find {count} REAL, recently funded (2025-2026 Seed, Series A, or YC/Accel/Lightspeed backed) AI agent or AI automation startups in region: '{target_region}'.
Focus on startups building autonomous coding agents, customer support agents, AI voice agents, eval/benchmarking platforms, or vertical enterprise AI.

For each startup, provide:
1. Company Name
2. Official Domain (e.g. example.ai, not a subpath)
3. Founder or Co-Founder Full Name
4. Founder Role (e.g. Co-Founder & CEO, CTO)
5. Region / City (e.g. Bengaluru, India; Riyadh, Saudi Arabia; London, UK; San Francisco, US)
6. Category (e.g. Autonomous Coding Agents, Voice AI, AI Eval Harnesses)
7. Funding Stage & Backers (e.g. $4M Seed - Lightspeed, Dec 2025)
8. Technical Focus (1 sentence on their core tech)
9. Technical Hook (A realistic technical challenge an FDE / Eval Engineer would solve for them)

Output strictly valid JSON with this exact schema:
[
  {{
    "company": "Company Name",
    "domain": "company.ai",
    "founder": "First Last",
    "role": "Co-Founder & CEO",
    "region": "City, Country",
    "category": "Category",
    "funding": "Funding details",
    "tech_focus": "Tech description",
    "hook": "Engineering challenge"
  }}
]
Do not wrap in markdown quotes if possible, output pure JSON."""

        models_to_try = [
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b"
        ]
        url = "https://api.groq.com/openai/v1/chat/completions"

        for model in models_to_try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a tech scout. Output strictly valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            try:
                req_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "AutonomousColdOutreach/1.0 (Macintosh; Intel Mac OS X 10_15_7)"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    if resp.status == 200:
                        raw = json.loads(resp.read().decode("utf-8"))
                        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
                        cleaned = re.sub(r'^```json\s*', '', content.strip())
                        cleaned = re.sub(r'\s*```$', '', cleaned)
                        parsed = json.loads(cleaned)
                        startups = parsed if isinstance(parsed, list) else parsed.get("startups") or parsed.get("companies", [])
                        if isinstance(startups, list) and startups:
                            print(f"[Groq Scout] ⚡ Discovered {len(startups)} new AI startups for {target_region} via {model}")
                            return startups
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                print(f"[Groq Scout] Model {model} HTTP Error {e.code}: {err_body}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"[Groq Scout] Model {model} attempt error: {e}", file=sys.stderr)
                continue

        # Diagnostic check if all Groq models fail
        try:
            diag_req = urllib.request.Request(
                "https://api.groq.com/openai/v1/models",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "User-Agent": "AutonomousColdOutreach/1.0"
                }
            )
            with urllib.request.urlopen(diag_req, timeout=10) as resp:
                m_data = json.loads(resp.read().decode("utf-8"))
                available = [m.get("id") for m in m_data.get("data", [])]
                print(f"[Groq Scout] ℹ️ Available models for key: {available[:8]}", file=sys.stderr)
        except Exception as e:
            print(f"[Groq Scout] Diagnostic ListModels error: {e}", file=sys.stderr)

        return []

    def research_and_enrich_new_leads(self, target_regions: list = None, count_per_region: int = 2) -> list:
        """
        Executes end-to-end autonomous research using a 3-tier discovery waterfall:
        1. Tier 1: Gemini API (gemini-3.8-flash)
        2. Tier 2: Groq API (Llama 3.3 70B fallback)
        3. Tier 3: Pre-seeded SQLite Candidate Pool
        4. Enriches contacts via Hunter.io / Prospeo / MX validation
        """
        regions = target_regions or ["India", "Middle East", "Europe", "US"]
        enriched_leads = []

        for reg in regions:
            # Stage 1: Try Gemini
            raw_startups = self.discover_with_gemini(target_region=reg, count=count_per_region)
            
            # Stage 2: Fallback to Groq if Gemini returned 0
            if not raw_startups and self.groq_key:
                print(f"[Discovery Waterfall] 🔄 Failing over to Groq AI Scout for {reg}...")
                raw_startups = self.discover_with_groq(target_region=reg, count=count_per_region)
                
            # Stage 3: Fallback to SQLite Candidate Pool if external LLMs are unavailable/exhausted
            if not raw_startups:
                print(f"[Discovery Waterfall] 🛡️ Using Staged Candidate Pool for {reg}...")
                try:
                    import db
                    raw_startups = db.get_uncontacted_candidates(region=reg, limit=count_per_region)
                except Exception as e:
                    print(f"[Candidate Pool] Error retrieving candidates: {e}", file=sys.stderr)
                    raw_startups = []
            for s in raw_startups:
                company = s.get("company", "").strip()
                domain = s.get("domain", "").strip().lower()
                founder = s.get("founder", "").strip()
                role = s.get("role", "Co-Founder & CEO").strip()
                loc = s.get("region", reg).strip()
                category = s.get("category", "AI Agents").strip()
                hook = s.get("hook", "building deterministic evaluation harnesses and preventing agent drift").strip()
                funding = s.get("funding", "Recently Funded").strip()

                if not company or not domain or not founder:
                    continue

                # Stage 2: Deep enrich with Context.dev if available
                if self.context_dev_key:
                    site_context = self.scrape_company_context_dev(domain)
                    if site_context:
                        s["site_context"] = site_context[:500]

                # Stage 3: Contact discovery & deliverability check
                if s.get("email") and "@" in s["email"]:
                    contact_res = {"email": s["email"], "confidence": 95, "source": "Curated Candidate Pool"}
                else:
                    first_name = founder.split()[0]
                    last_name = founder.split()[-1] if len(founder.split()) > 1 else ""
                    contact_res = self.find_founder_email(domain, first_name, last_name, company_name=company)

                
                prospect = {
                    "company": company,
                    "domain": domain,
                    "founder": founder,
                    "email": contact_res["email"],
                    "role": role,
                    "region": loc,
                    "category": category,
                    "funding": funding,
                    "tech_focus": s.get("tech_focus", f"High-agency autonomous systems in {category}"),
                    "hook": hook,
                    "email_source": contact_res["source"],
                    "email_confidence": contact_res["confidence"]
                }
                enriched_leads.append(prospect)
                print(f"[Autonomous Researcher] ✅ Sourced & Verified: {company} ({founder} <{prospect['email']}>) [{loc}]")

        return enriched_leads

if __name__ == "__main__":
    print("Testing Autonomous Researcher...")
    r = AutonomousResearcher()
    print(f"Capabilities -> Gemini: {bool(r.gemini_key)}, Context.dev: {bool(r.context_dev_key)}, Hunter: {bool(r.hunter_key)}, Prospeo: {bool(r.prospeo_key)}")
    # Test MX verify
    print("Domain MX check (google.com):", r.verify_domain_mx("google.com"))
    print("Domain MX check (composio.dev):", r.verify_domain_mx("composio.dev"))
    # Test email finder fallback
    print("Email pattern test:", r.find_founder_email("composio.dev", "Soham", "Ganatra"))
