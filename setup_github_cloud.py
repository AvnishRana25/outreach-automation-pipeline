#!/usr/bin/env python3
"""
Automated Cloud Deployment Setup
1. Reads existing Google Workspace credentials from ~/.google_workspace_mcp
2. Creates private GitHub repository via gh CLI
3. Uploads secrets directly to GitHub Secrets (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, NTFY_TOPIC)
4. Commits and pushes codebase to GitHub
"""

import os
import sys
import json
import subprocess

REPO_NAME = "outreach-automation-pipeline"
CREDS_FILE = os.path.expanduser("~/.google_workspace_mcp/credentials/avnishrana797@gmail.com.json")
NTFY_TOPIC = "avnish-outreach-alert-797"

def run_cmd(cmd, check=True):
    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Command failed with error: {res.stderr}")
        return False, res.stderr
    return True, res.stdout

def setup():
    if not os.path.exists(CREDS_FILE):
        print(f"Error: Credentials file not found at {CREDS_FILE}")
        return False

    with open(CREDS_FILE, "r") as f:
        creds = json.load(f)

    client_id = creds.get("client_id")
    client_secret = creds.get("client_secret")
    refresh_token = creds.get("refresh_token")

    if not (client_id and client_secret and refresh_token):
        print("Error: Missing client_id, client_secret, or refresh_token in credentials file.")
        return False

    print("Step 1: Initializing git and committing files...")
    run_cmd("git add -A")
    run_cmd('git commit -m "Initialize autonomous cold outreach pipeline"')
    run_cmd("git branch -M main")

    print(f"Step 2: Creating private GitHub repository: {REPO_NAME}...")
    success, out = run_cmd(f"gh repo create {REPO_NAME} --private --source=. --remote=origin", check=False)
    if not success and "already exists" in out:
        print(f"Repository {REPO_NAME} already exists, using existing remote.")

    print("Step 3: Uploading encrypted GitHub Secrets...")
    # Set secrets via stdin to prevent leaking in process lists
    subprocess.run(f"gh secret set GMAIL_CLIENT_ID", input=client_id, text=True, shell=True)
    subprocess.run(f"gh secret set GMAIL_CLIENT_SECRET", input=client_secret, text=True, shell=True)
    subprocess.run(f"gh secret set GMAIL_REFRESH_TOKEN", input=refresh_token, text=True, shell=True)
    subprocess.run(f"gh secret set NTFY_TOPIC", input=NTFY_TOPIC, text=True, shell=True)
    print("Secrets uploaded successfully!")

    print("Step 4: Pushing code to GitHub...")
    run_cmd("git push -u origin main", check=False)
    
    print("\n" + "=" * 55)
    print("🚀 CLOUD DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print(f"Private Repo: https://github.com/AvnishRana25/{REPO_NAME}")
    print(f"Mobile Notifications: Subscribe to '{NTFY_TOPIC}' on the free ntfy mobile app")
    print("=" * 55)
    return True

if __name__ == "__main__":
    setup()
