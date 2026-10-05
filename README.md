# Outreach campaign

Python 3.11+, SQLite and the Gmail REST API. No third-party Python packages are required. SQLite is the campaign record; JSON, CSV and HTML are generated snapshots. See [VALIDATION.md](VALIDATION.md) for the tested behavior and deployment limits.

## Daily use

```sh
python3 -B -m unittest discover -v
python3 -B cloud_orchestrator.py --action status
python3 -B cloud_orchestrator.py --action send-batch --region US --dry-run
python3 -B cloud_orchestrator.py --action research-and-draft --leads-file verified_leads.json --dry-run
python3 -B cloud_orchestrator.py --action research-and-draft --leads-file verified_leads.json
python3 -B cloud_orchestrator.py --action reconcile
python3 -B cloud_orchestrator.py --action followups
python3 -B update_campaign.py
python3 -B serve_dashboard.py
```

Send-batch and followups create drafts unless `--auto-send` is explicitly supplied. Draft/import/reconcile actions contact Gmail; status and dry runs do not. The dashboard is a snapshot with search, region filters and all three email previews. Its preview serves only that HTML on localhost. Regenerate it after campaign changes.

## Verified JSON imports

Ongoing leads come from a user-supplied verified JSON list, or an object containing `leads`. The default file is `verified_leads.json`; `--leads-file` selects another file locally. Missing import files never fall back to the old seed list. The historical seeds remain reference material, with no new identity or address verification claim.

Each record needs a company, domain, founder, email, location, `email_verified_at` and `email_verification_source`. Supply an explicit region and IANA timezone when the company location does not describe the recipient. Review email copy and business claims before drafting. Verification metadata records your evidence; this tool does not independently prove email ownership or deliverability.

```json
{
  "leads": [{
    "company_name": "Example company",
    "domain": "example.invalid",
    "founder_name": "Example founder",
    "verified_email": "founder@example.invalid",
    "location": "London, UK",
    "region_code": "EU",
    "recipient_timezone": "Europe/London",
    "email_verified_at": "2026-10-01T12:00:00+00:00",
    "email_verification_source": "Replace with the actual evidence/source",
    "category": "AI tooling",
    "hook": "Replace with a reviewed company-specific observation",
    "initial_subject": "Reviewed subject",
    "initial_body": "Reviewed initial message",
    "fu1_subject": "Re: Reviewed subject",
    "fu1_body": "Reviewed first follow-up",
    "fu2_subject": "Re: Reviewed subject",
    "fu2_body": "Reviewed final follow-up"
  }]
}
```

This example is a placeholder, not a verified recipient. If copy is omitted, the existing templates generate it. The whole file is validated before insertion. Reimporting a company/domain updates evidence and editorial metadata while preserving its recipient, copy and sending history. A changed recipient requires explicit campaign review. All existing 52 real leads currently lack verification evidence: automatic initial sending is held until a verified import supplies it.

## Sending, replies and recovery

`tick` checks replies and sends eligible initial messages/follow-ups only on weekdays from 09:00 up to 11:00 in each recorded recipient timezone, including daylight-saving changes. The workflow wakes hourly; GitHub can delay scheduled runs, so delivery time is not guaranteed. FU1 is due at least three days after the initial send. FU2 is due at least seven days after the initial send and at least 24 hours after FU1. Direct send-batch/followups commands bypass morning windows unless called by tick.

A durable attempt with a stable X-Outreach-ID tracking header and an RFC Message-ID is saved before creating or sending its Gmail draft. Cloud writes checkpoint state to Git before Gmail changes. Manually sent drafts are reconciled; consumed initial draft IDs are cleared. Follow-ups retain the original Gmail thread and subject. Incoming thread replies after the initial send stop subsequent follow-ups, cancel queued drafts and trigger a configured mobile alert. Automatic/bulk responses are excluded.

Timeouts and unknown outcomes are held for reconciliation, with no blind resend or replacement draft. Missing legacy drafts require a unique matching sent message. Inspect Gmail and the recorded attempt before any manual state correction; absence from Gmail search is not proof that a send failed. Local and GitHub concurrency guards serialize runs. This design requires one authoritative sender across machines; it is not a distributed lock.

Local automatic sending is disabled by default. For an exclusive local run, first disable the cloud workflow, obtain its latest state, and explicitly set `OUTREACH_ALLOW_LOCAL_SEND=1`. A stale local database must never send alongside the cloud database. Keep backups separate from tracked campaign state.

## Cloud and credentials

The workflow in `.github/workflows/outreach_pipeline.yml` uses `main`, serializes campaign actions, refreshes state before execution, runs offline tests, checkpoints each transition and preserves recovery artifacts on failure. Scheduled ticks send automatically once verified leads are eligible. Manual workflow dispatch defaults to status and drafting. Commit `verified_leads.json` to the private campaign repository when using its import action. The repaired workflow is deployed to the private repository; its live status acceptance run passed. Local edits alone do not change the remote workflow.

Required secrets: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, with existing Gmail scopes covering metadata/search, drafts, sending and deletion of queued drafts. Local Gmail can use the existing Workspace credential file; do not place credentials in this repository. Cloud checkpoints need permission to push `main`; branch protection or push failure stops further Gmail writes.

For ntfy, configure a **reserved topic with access restricted to your account**, `NTFY_TOPIC` and `NTFY_TOKEN`. A bearer token authenticates publishing; topic access restrictions provide privacy. The previously disclosed public topic is rejected. Alternatively configure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. No channel is enabled by default. Failed reply alerts are retried on later checks. The workflow action `notify-test` sends one configured private test alert; confirm its arrival on the phone separately. Live mobile delivery has not been verified.

`setup_github_cloud.py` is an explicit deployment tool: it checks command results, requires a private repository and matching origin, uploads credentials via standard input and pushes reviewed project files. Review the diff first. It was not executed during the repair. Campaign snapshots contain recipients and message copy, so keep the repository and recovery artifacts private.

## Maintenance

`build_full_campaign.py`, `generate_outreach.py sync`, `build_dashboard.py` and `update_campaign.py` export current SQLite state atomically. `refresh_all_drafts_html.py --dry-run` previews formatting refreshes; the real action preserves tracking headers and threads. The old copy-migration and CLI-rewrite scripts are harmless retired entry points. The offline test suite uses temporary databases, fake Gmail and blocked external network; it never sends campaign mail.
