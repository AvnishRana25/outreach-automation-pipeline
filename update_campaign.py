import json

RESUME_LINK = "https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing"
GITHUB_LINK = "https://github.com/AvnishRana25"
LINKEDIN_LINK = "https://www.linkedin.com/in/avnish-rana-83523b2a3/"

SIGNATURE = f"""Best,
Avnish Rana
Resume: {RESUME_LINK}
GitHub: {GITHUB_LINK}
LinkedIn: {LINKEDIN_LINK}
Phone / WhatsApp: +91 7982252971"""

SCHEDULE_MAP = {
    # India (IST) -> 9:30 AM IST
    "Composio": ("9:30 AM IST", "9:30 AM IST (India)"),
    "Dextr AI": ("9:30 AM IST", "9:30 AM IST (India)"),
    "Runable": ("9:30 AM IST", "9:30 AM IST (India)"),
    "Ignosis AI": ("9:30 AM IST", "9:30 AM IST (India)"),
    
    # Middle East -> 10:30 AM - 11:30 AM IST
    "Erad": ("11:00 AM IST", "8:30 AM - 9:00 AM AST (Riyadh)"),
    "Lucidya": ("11:30 AM IST", "9:00 AM AST (Riyadh)"),
    
    # UK / Europe -> 1:00 PM - 2:00 PM IST
    "Atla": ("1:30 PM IST", "9:00 AM BST (London)"),
    "Topo": ("1:00 PM IST", "9:30 AM CEST (Paris)"),
}

DEFAULT_US_TIME = ("9:30 PM IST", "9:00 AM PDT (San Francisco)")

with open("curated_leads.json", "r") as f:
    leads = json.load(f)

for lead in leads:
    cname = lead["company_name"]
    time_ist, local_window = SCHEDULE_MAP.get(cname, DEFAULT_US_TIME)
    lead["recommended_send_time_ist"] = time_ist
    lead["founder_local_window"] = local_window
    lead["resume_link"] = RESUME_LINK
    lead["github_link"] = GITHUB_LINK
    lead["linkedin_link"] = LINKEDIN_LINK

    # Replace placeholder links in initial_body
    body = lead["initial_body"]
    # Remove old signature
    if "Best,\nAvnish Rana" in body:
        body = body.split("Best,\nAvnish Rana")[0].strip()
        body += "\n\n" + SIGNATURE
    lead["initial_body"] = body

    # Update FU1
    fu1 = lead["fu1_body"]
    if "Best,\nAvnish" in fu1:
        fu1 = fu1.split("Best,\nAvnish")[0].strip()
        fu1 += f"\n\nBest,\nAvnish Rana\nResume: {RESUME_LINK} | GitHub: {GITHUB_LINK}"
    lead["fu1_body"] = fu1

    # Update FU2
    fu2 = lead["fu2_body"]
    if "Best,\nAvnish" in fu2:
        fu2 = fu2.split("Best,\nAvnish")[0].strip()
        fu2 += f"\n\nBest,\nAvnish Rana\nResume: {RESUME_LINK}\nGitHub: {GITHUB_LINK}\nLinkedIn: {LINKEDIN_LINK}\nDirect / WhatsApp: +91 7982252971"
    lead["fu2_body"] = fu2

with open("curated_leads.json", "w") as f:
    json.dump(leads, f, indent=2)

print("✅ Updated curated_leads.json with user links & timezone schedules.")
