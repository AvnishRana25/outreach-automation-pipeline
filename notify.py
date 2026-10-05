import subprocess
import json

def send_mac_notification(title, subtitle, message):
    script = f'''display notification "{message}" with title "{title}" subtitle "{subtitle}" sound name "Glass"'''
    subprocess.run(["osascript", "-e", script])

with open("curated_leads.json", "r") as f:
    leads = json.load(f)

# Group by timezone
tz_summary = {
    "India (9:30 AM IST)": 0,
    "Middle East (11:00 AM IST)": 0,
    "UK & Europe (1:00 PM IST)": 0,
    "US / Silicon Valley (9:30 PM IST)": 0,
}

for l in leads:
    t = l.get("recommended_send_time_ist", "")
    if "9:30 AM" in t:
        tz_summary["India (9:30 AM IST)"] += 1
    elif "11:00" in t or "11:30" in t:
        tz_summary["Middle East (11:00 AM IST)"] += 1
    elif "1:00" in t or "1:30" in t:
        tz_summary["UK & Europe (1:00 PM IST)"] += 1
    else:
        tz_summary["US / Silicon Valley (9:30 PM IST)"] += 1

msg = f"India: {tz_summary['India (9:30 AM IST)']} | ME: {tz_summary['Middle East (11:00 AM IST)']} | UK/EU: {tz_summary['UK & Europe (1:00 PM IST)']} | US: {tz_summary['US / Silicon Valley (9:30 PM IST)']}"
send_mac_notification("Cold Outreach Engine", "25 New Drafts Saved to Gmail", msg)
print("Notification triggered successfully!")
print(f"Summary: {msg}")
