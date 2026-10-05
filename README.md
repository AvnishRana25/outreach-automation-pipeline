# Autonomous Cold Outreach Engine 🚀

An autonomous, 24/7 cold email outreach & follow-up agent running on GitHub Actions. Positions **Avnish Rana** for Junior Forward Deployed Engineer (FDE), AI Benchmark/Eval Engineer, and AI Automation contracts.

---

## ⚡ How It Works (Laptop Can Be Turned Off)

1. **Target Timezone Dispatches**:
   - **India**: `04:00 UTC` (9:30 AM IST)
   - **Europe / UK**: `07:30 UTC` (1:00 PM IST)
   - **US West Coast (SF/Bay Area)**: `16:00 UTC` (9:30 PM IST)
2. **Deterministic Deduplication**:
   - Backed by SQLite `outreach.db`. Never contacts the same startup or domain twice.
3. **Smart Follow-Up Engine**:
   - Day +3: Checks Gmail inbox to see if the founder replied. If not, auto-drafts/sends **Follow-Up 1** (Technical edge-case code teardown).
   - Day +7: Auto-drafts/sends **Follow-Up 2** (Low-pressure breakup email).
   - If the founder replies at any time: Cancels all follow-ups and triggers a high-priority phone alert!
4. **Phone Notifications (No Mac Screen Popups)**:
   - Dispatches instant mobile push notifications directly to iOS / Android via `ntfy` or Telegram Bot.

---

## 📱 Getting Push Notifications on Your Phone

### Option A: ntfy App (Recommended — 30 Seconds, No Sign-up)
1. Install **ntfy** from the iOS App Store or Android Play Store.
2. Open the app, tap `+` (Subscribe to topic).
3. Type: `avnish-outreach-alert-797`.
4. Done! You will now receive instant push banners on your lock screen with direct links to your Gmail drafts and high-priority reply alerts.

### Option B: Telegram Bot
Set the repository secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to receive updates directly in Telegram.

---

## 🔐 GitHub Secrets Configuration

| Secret | Description |
| :--- | :--- |
| `GMAIL_CLIENT_ID` | Google OAuth Client ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth Client Secret |
| `GMAIL_REFRESH_TOKEN` | Google Workspace OAuth Refresh Token |
| `NTFY_TOPIC` | Mobile notification topic (default: `avnish-outreach-alert-797`) |
| `TELEGRAM_BOT_TOKEN` | Optional Telegram bot token |
| `TELEGRAM_CHAT_ID` | Optional Telegram user ID |
| `GEMINI_API_KEY` | Optional Gemini API key for on-the-fly startup research & drafting |

---

## 🛠 Local CLI Commands

```bash
# Check status of campaign
python3 cloud_orchestrator.py --action status

# Check if any founders have replied
python3 cloud_orchestrator.py --action check-replies

# Process a specific regional batch
python3 cloud_orchestrator.py --action send-batch --region US

# Trigger follow-ups for unreplied prospects
python3 cloud_orchestrator.py --action followups

# Send test notification to your phone
python3 notify_mobile.py "Phone Test" "Your outreach agent is live!"
```
