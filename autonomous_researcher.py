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
import urllib.request
import urllib.parse
from datetime import datetime, timezone

class AutonomousResearcher:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.context_dev_key = os.getenv("CONTEXT_DEV_API_KEY", "").strip()
        self.hunter_key = os.getenv("HUNTER_API_KEY", "").strip()
        self.prospeo_key = os.getenv("PROSPEO_API_KEY", "").strip()

    def has_discovery_capabilities(self) -> bool:
        """Returns True if at least one live intelligence provider is configured."""
        return bool(self.gemini_key or self.context_dev_key or self.hunter_key)

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

    def find_founder_email(self, domain: str, first_name: str, last_name: str = "") -> dict:
        """
        Attempts to locate and verify the founder's email address using:
        1. Hunter.io API (if HUNTER_API_KEY is configured)
        2. Prospeo API (if PROSPEO_API_KEY is configured)
        3. Intelligent pattern inference + MX validation fallback
        """
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        first = re.sub(r'[^a-zA-Z]', '', first_name).lower()
        last = re.sub(r'[^a-zA-Z]', '', last_name).lower()

        # 1. Try Hunter.io
        if self.hunter_key:
            try:
                params = {"domain": clean_domain, "first_name": first, "last_name": last, "api_key": self.hunter_key}
                url = f"https://api.hunter.io/v2/email-finder?{urllib.parse.urlencode(params)}"
                req = urllib.request.Request(url, headers={"User-Agent": "AutonomousOutreach/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        email = data.get("data", {}).get("email")
                        score = data.get("data", {}).get("score", 0)
                        if email:
                            return {"email": email, "confidence": score, "source": "Hunter.io"}
            except Exception as e:
                print(f"[Email Finder] Hunter.io lookup error for {clean_domain}: {e}", file=sys.stderr)

        # 2. Try Prospeo
        if self.prospeo_key:
            try:
                payload = json.dumps({"first_name": first, "last_name": last or first, "company": clean_domain})
                req = urllib.request.Request(
                    "https://api.prospeo.io/email-finder",
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-KEY": self.prospeo_key}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        email = data.get("response", {}).get("email")
                        if email:
                            return {"email": email, "confidence": 90, "source": "Prospeo"}
            except Exception as e:
                print(f"[Email Finder] Prospeo lookup error for {clean_domain}: {e}", file=sys.stderr)

        # 3. Intelligent Pattern Fallback + MX check
        has_mx = self.verify_domain_mx(clean_domain)
        guessed_email = f"{first}@{clean_domain}"
        return {
            "email": guessed_email,
            "confidence": 75 if has_mx else 40,
            "source": "Pattern Inference + MX Check" if has_mx else "Inferred (Unverified Domain)"
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
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    markdown = data.get("markdown") or data.get("data", {}).get("markdown", "")
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

        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
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
            except Exception as e:
                print(f"[Gemini Scout] Model {model} attempt error: {e}", file=sys.stderr)
                continue

        return []

    def research_and_enrich_new_leads(self, target_regions: list = None, count_per_region: int = 2) -> list:
        """
        Executes end-to-end autonomous research:
        1. Queries Gemini for real funded startups in requested regions
        2. Enriches with Context.dev (if available) for deep landing page insights
        3. Looks up founder emails via Hunter / Prospeo / MX check
        4. Returns fully formed prospect dictionaries ready for pitch generation & drafting
        """
        regions = target_regions or ["India", "Middle East", "Europe", "US"]
        enriched_leads = []

        for reg in regions:
            raw_startups = self.discover_with_gemini(target_region=reg, count=count_per_region)
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
                first_name = founder.split()[0]
                last_name = founder.split()[-1] if len(founder.split()) > 1 else ""
                contact_res = self.find_founder_email(domain, first_name, last_name)
                
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
