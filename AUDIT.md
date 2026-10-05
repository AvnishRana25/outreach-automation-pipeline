# Outreach project audit

**Remediation update:** Local repairs and validation are documented in [VALIDATION.md](VALIDATION.md). The findings below describe the original baseline; live deployment and delivery acceptance remain pending.

Reviewed 5 October 2026, Asia/Kolkata. Baseline: branch `main`, commit `20686b681669`. Review only; application code, campaign data, Gmail, GitHub configuration, and notification settings were not changed.

The project is a small, understandable outreach prototype with useful Gmail and SQLite building blocks. It is not yet reliable enough for unattended sending. Its largest problems are state durability, manual-send reconciliation, inaccurate operational displays, and misleading success signals. A framework rewrite would not solve these problems; focused repairs in the existing modules will.

## Scope and verification

Read every Python source in full: 17 files, 3,937 lines. Read the workflow, README, ignore files, and Serena configuration. Parsed all JSON and CSV records and all campaign rows in SQLite. Compared stored email copy with its source templates and migrations, and compared every character of generated HTML against the dashboard builder. Generated HTML matches its builder exactly. Inspected local tooling database/file inventory; Git object internals and compiled bytecode were not treated as application source.

Checks performed:

- All 17 Python files parse successfully.
- SQLite `PRAGMA integrity_check` returns `ok`.
- Thirteen isolated Python reproductions confirmed failure cases, using temporary databases, mocked Gmail/notifications, and blocked network access.
- Executed the actual generated dashboard JavaScript with a minimal DOM stub; confirmed search crashes on absent `target_role`.
- Standard-library test discovery reports **zero tests**. The existing “mock” script is a live integration exercise and was not executed.
- SHA-256 checks confirmed the production database, JSON, CSV, and dashboard were unchanged by the reproductions.

This is a local code/data audit, not verification of current Gmail delivery, recipient identity, company funding, remote workflow health, or repository visibility. No credentials outside the project were opened. No obvious Google/GitHub token literals were found by a narrow pattern scan of Python sources; this is not a complete secret-history audit.

## Actual flow

GitHub schedules/manual dispatch → action selection → Python orchestrator → SQLite selection → Gmail draft/send/search → SQLite update → Git commit/push. Mobile notifications run alongside these actions. Research draws from a fixed Python list and writes SQLite. The dashboard and CSV instead draw from curated JSON, which the live lifecycle never updates. That disconnected export path explains the observed stale views.

Audit reproductions are available in `/tmp/outreach-project-audit/checks.py` for this local session. They confirm current defects rather than assert repaired behavior. Run with `python3 -B /tmp/outreach-project-audit/checks.py`; no real email or notification is sent.

## Current state

| Store | Lead count | Recorded status |
| --- | ---: | --- |
| SQLite | 53 | 24 `SENT`, 28 `Drafted in Gmail`, 1 `REPLIED` |
| Curated JSON | 52 | All `Drafted in Gmail` |
| Dashboard embedded data | 52 | Exact copy of curated JSON |
| CSV tracker | 25 | All `Drafted in Gmail`; old copy and dates |

SQLite's extra row is the live test lead. The 24 sent rows all have the same batch timestamp, `2026-10-05T16:29:22.871702+00:00`. These are recorded states, not independently verified Gmail delivery receipts. All 52 production leads retain a Gmail draft ID, including sent rows whose original drafts should have been consumed.

None of the 52 current JSON records contains `target_role`, `batch_or_stage`, or `hook_angle`, although the CLI and dashboard expect these fields. The 27 fixed research prospects are all already present in SQLite. Production JSON/SQLite email copy has no detected GitHub placeholders; the CSV retains placeholders in all 25 breakup emails.

## Findings

P1 means repair before relying on unattended outreach. P2 means a material correctness, reliability, or security issue. P3 means a usability or maintenance issue. Numbering is stable so individual findings can be selected for repair.

### 1. P1 — Concurrent workflow snapshots can send duplicate emails and lose state

Evidence: `.github/workflows/outreach_pipeline.yml:58`, `cloud_orchestrator.py:99`, `cloud_orchestrator.py:129`, `research_and_generate.py:539`.

There is no workflow concurrency group. Each runner reads its own checked-out SQLite snapshot, selects pending leads, and performs Gmail writes before persisting its state to Git. Separate snapshots can therefore send the same direct message or follow-up. Research can create duplicate drafts before one insert wins its uniqueness race. A local reproduction sent the same undrafted lead twice from two database snapshots. A consumed Gmail draft may prevent a second initial draft send; it does not protect direct sends or follow-ups.

Repair: serialize cloud runs using one concurrency group with cancellation of active sending runs disabled; refresh the checked-out state after acquiring that slot. Prevent overlapping local senders too. GitHub's native concurrency feature is sufficient for the cloud serialization part. [GitHub concurrency documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

### 2. P1 — A successful send can outlive its campaign record

Evidence: `.github/workflows/outreach_pipeline.yml:148`, `.github/workflows/outreach_pipeline.yml:153`, `cloud_orchestrator.py:131`, `cloud_orchestrator.py:139`, `cloud_orchestrator.py:213`.

Gmail sends and SQLite commits are separate operations. A crash between them leaves the message sent but the lead pending. Even successfully committed local changes are lost from the next runner if the workflow fails before the final Git push. The persistence step normally skips after an earlier step fails. It also tries `git pull --rebase` while the database is dirty, suppresses pull failures, then pushes without recovery. A concurrent commit can reject that push after email has already gone out. Binary SQLite files cannot be safely merged like source text.

Repair: give sends durable intent/message identifiers and an explicit uncertain-outcome state; reconcile with Gmail before retrying. Preserve state on failure and surface persistence failures. Serializing runs reduces races but does not make Gmail and SQLite atomic. Do not blindly retry an ambiguous send or resolve a database conflict by overwriting either side.

### 3. P1 — Reviewing and manually sending drafts breaks campaign progression

Evidence: `cloud_orchestrator.py:25`, `cloud_orchestrator.py:131`, `cloud_orchestrator.py:182`, `cloud_orchestrator.py:216`, `cloud_orchestrator.py:238`.

When a user sends an initial draft in Gmail, nothing moves its SQLite row to `SENT` or records its send time. A future batch tries the consumed draft ID and fails; reply checks and follow-ups exclude that pending row. Follow-up draft creation discards the returned draft ID and changes status to `FU1_QUEUED` or `FU2_QUEUED`. Neither state is handled by the send engine or reply checker. A reproduction confirmed that FU1 became unreachable and stopped being checked for replies.

Repair: record each follow-up draft ID and reconcile sent drafts/messages before selecting the next action. Include queued leads in reply cancellation. Define one explicit transition path for both automatic and manual sending.

### 4. P1 — `--dry-run` does not reliably prevent side effects

Evidence: `cloud_orchestrator.py:278`, `cloud_orchestrator.py:290`, `cloud_orchestrator.py:299`, `cloud_orchestrator.py:163`, `research_and_generate.py:595`.

The research CLI accepts `--dry-run` but calls its worker with `dry_run=False, create_drafts=True`. Follow-ups ignore the flag too, so `--action followups --auto-send --dry-run` can send actual email. Batch dry-run avoids Gmail writes but still dispatches a real phone alert claiming the batch is ready/sent. Calling the research worker with its own dry-run option still notifies if prospects qualify. Research CLI behavior and batch notification behavior were reproduced with mocks.

Repair: propagate dry-run to every mutating action and suppress database writes, Gmail writes, and notifications consistently. Report proposed actions separately from completed actions.

### 5. P1 — The local preview server exposes the whole repository to the network

Evidence: `serve_dashboard.py:12`, `serve_dashboard.py:16`, `serve_dashboard.py:22`.

The server binds to all interfaces and serves the repository root using `SimpleHTTPRequestHandler`. When running, reachable peers can request the campaign database, contact lists, source files, and Git metadata. This is broader than a local dashboard preview. Exposure depends on network/firewall reachability; the audit did not start this server.

Repair: bind to `127.0.0.1` and serve only the dashboard/static assets, or open the self-contained HTML directly. Restricting the bind address alone still leaves repository files accessible to local clients.

### 6. P1 — CSV export fails after truncating the existing tracker

Evidence: `generate_outreach.py:49`, `generate_outreach.py:53`, `generate_outreach.py:114`.

Current JSON records include `gmail_draft_id`, which is absent from `DictWriter.fieldnames`. `writer.writerow()` raises `ValueError` on the first lead, after opening the destination with `w` and writing its header. This affects `sync` and the no-argument CLI path. A temporary-file reproduction confirmed a header-only output.

Repair: explicitly project records onto the export schema, write to a temporary file, and atomically replace the tracker only after a successful export. Preserve the previous file on any failure.

### 7. P1 — Reply detection does not identify replies to this campaign

Evidence: `gmail_client.py:181`, `cloud_orchestrator.py:42`, `cloud_orchestrator.py:204`, `cloud_orchestrator.py:225`.

The query is only `from:<recipient>`, with no campaign thread or send-time restriction. Any older or unrelated email from that address counts as a reply and cancels outreach. Automatic responses may also count. Replies from a colleague or another address can be missed. A mocked old unrelated message was treated as a current reply. When follow-up processing finds a reply, it marks it before the subsequent reply checker runs, so the promised high-priority reply alert is skipped on that path.

Repair: inspect messages in the stored campaign thread and their sender/time, distinguish automatic responses where appropriate, and use one shared reply-recording function that also triggers the alert.

### 8. P2 — Dashboard search and CLI draft viewing are broken by schema drift

Evidence: `build_dashboard.py:389`, `build_dashboard.py:433`, `build_dashboard.py:456`, `generate_outreach.py:81`.

Every current JSON record lacks fields consumed by these views. Rows display `undefined` for stage/role. Search calls `l.target_role.toLowerCase()` and crashes as soon as company/founder matching does not short-circuit it. Executing the actual generated script reproduced `Cannot read properties of undefined (reading 'toLowerCase')`. `show_draft()` indexes `batch_or_stage`, `target_role`, and `hook_angle`, raising `KeyError` on the first lead.

Repair: restore required metadata from the original campaigns where available and make genuinely optional display fields safe. Validate the data contract at load/export boundaries.

### 9. P2 — The dashboard and tracker report stale, unsupported operational claims

Evidence: `build_dashboard.py:13`, `build_dashboard.py:91`, `build_dashboard.py:135`, `build_dashboard.py:168`, `curated_leads.json`, `leads_tracker.csv`.

The dashboard reads JSON rather than SQLite, so it labels all 52 leads as drafted while SQLite records 24 sent. Its badges/KPIs still say 25 drafts and show hard-coded geographic counts, a fixed date, and “100% / MX & SMTP Verified.” No email-verification implementation or stored verification evidence exists in this project. Cloud research writes only SQLite; committing JSON does not update it. The CSV contains just the first 25 leads and stale placeholders. This can prompt repeated work or incorrect send decisions.

Repair: generate dashboard and CSV from the authoritative campaign state, calculate counts, show the export timestamp, and remove verification/performance claims without evidence. Preserve optional editorial metadata separately from lifecycle status.

### 10. P2 — Scheduled actions change when a runner starts late

Evidence: `.github/workflows/outreach_pipeline.yml:79`, `.github/workflows/outreach_pipeline.yml:89`.

The action is selected from execution wall-clock time rather than the triggering cron expression. Research triggered at 03:15 but starting after 03:45 becomes an India send. A periodic reply check can become another region's dispatch if delayed into its window. This is inconsistent with the “Queue-Jitter Immune” label. The cron configuration also has no weekend reply checks despite README's “24/7” claim, and fixed UTC dispatches do not adjust for destination daylight-saving changes.

Repair: map `github.event.schedule` explicitly to the intended action; use current time only to decide whether that action is still appropriate to execute. GitHub documents the triggering schedule value and potential scheduling delays. [Scheduled workflow documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

### 11. P2 — Region routing is inconsistent and can target the wrong country

Evidence: `research_and_generate.py:535`, `cloud_orchestrator.py:85`, `cloud_orchestrator.py:88`, `update_campaign.py:35`.

Research checks substrings of both company name and location. On a fresh database, `EU` selects only **Fleuret AI** by its name, missing most European prospects; `ME` selects **Mercor in San Francisco**, not Middle East prospects. Both cases were reproduced. Sending uses different substring rules; full-word/custom inputs such as Australia contain `US`, and Berlin contains `IN`, causing incorrect classifications. Hybrid India/US profiles are assigned by location text without storing the recipient's actual timezone. Topo's migration recommends a Paris slot while its stored location routes it to US.

Repair: normalize exact supported aliases into a canonical region field, share that mapping across research/sending/dashboard, and record recipient timezone when timing actually matters. Remove company-name matching from geographic filters.

### 12. P2 — Failures either look successful or abort unrelated leads

Evidence: `cloud_orchestrator.py:64`, `cloud_orchestrator.py:156`, `cloud_orchestrator.py:198`, `research_and_generate.py:558`, `setup_github_cloud.py:19`.

Initial send/reply exceptions are printed and swallowed. A batch in which every Gmail send fails returns normally, so the workflow can appear successful. Research counts leads as “drafted in Gmail” even if Gmail draft creation failed. Follow-ups have the opposite problem: an API error, missing body, or one timezone-naive/malformed timestamp stops the entire loop. A naive timestamp and all-send-failure behavior were reproduced. The deployment helper returns success for any failed command when `check=False`; secret upload return codes are ignored, and setup announces completion regardless of push success.

Repair: process leads independently, retain failure details, report attempted/succeeded/failed counts, and exit nonzero for operational failure after saving successful progress. Preserve an uncertain-send state instead of retrying automatically. Check every deployment command's actual result.

### 13. P2 — Follow-up timing overwrites the initial send timestamp

Evidence: `cloud_orchestrator.py:214`, `cloud_orchestrator.py:224`, `cloud_orchestrator.py:235`.

FU1 replaces `sent_at`, then FU2 waits four days from that replacement. Day +7 is achieved only if FU1 ran exactly on day +3. A reproduced lead first processed on day +10 received FU1 and became ineligible for FU2 until approximately day +14. The original send time is lost. Batch send timestamps are also captured once before all sends rather than at each success.

Repair: keep immutable initial send time and separate follow-up send times. Explicitly choose whether FU2 is due seven days after the initial send or four days after FU1; implement and document that policy. Use aware UTC timestamps consistently.

### 14. P2 — “Autonomous research” is a finite seed import, and verification is absent

Evidence: `research_and_generate.py:32`, `research_and_generate.py:525`, `README.md:47`, `.github/workflows/outreach_pipeline.yml:140`.

The worker iterates 27 hard-coded prospects and uses three template branches. There is no source discovery, Gemini request, email verification, or evidence/freshness record. `GEMINI_API_KEY` is configured but never read by Python. All 27 prospects already exist in the production database, so the daily research job currently adds zero leads. The name `verified_email` is not evidence that addresses were verified. Company/founder/funding assertions in templates were not independently checked in this audit.

Repair: label the existing action as importing seed leads. If ongoing discovery is required, add one concrete source and retain source URLs/check dates before automatically sending. A speculative multi-provider research framework is unnecessary.

### 15. P2 — HTML handling can alter email content and execute imported dashboard markup

Evidence: `gmail_client.py:104`, `gmail_client.py:118`, `build_dashboard.py:360`, `build_dashboard.py:386`, `build_dashboard.py:456`.

Email paragraphs are inserted as raw HTML rather than escaped text. Any paragraph containing the sender's full name is interpreted as the signature and stops rendering subsequent content. Both behaviors were reproduced. Dashboard data is interpolated into `innerHTML`, inline event attributes, and a script literal without escaping `</script>`. Imported markup can therefore execute in the dashboard if future data sources are untrusted. No malicious payload was found in current data; Gmail's own sanitization was not tested, so arbitrary script execution in received Gmail is not claimed.

Repair: escape plain email content using `html.escape`, delimit signatures explicitly, use `textContent`/event listeners for dynamic dashboard values, and escape script-terminating characters when embedding JSON.

### 16. P2 — Reply alerts use a disclosed, unauthenticated notification topic

Evidence: `notify_mobile.py:17`, `notify_mobile.py:32`, `README.md:29`, `.github/workflows/outreach_pipeline.yml:137`.

The default topic is written into code and the README. Publishing uses no authorization. Reply alerts contain company/founder details. If that default topic has not been protected separately, anyone who learns it can subscribe or publish misleading alerts. Configuring Telegram does not disable ntfy; both are attempted. Current server-side topic protection was not inspected. ntfy documents topic names as the access secret for unauthenticated use. [ntfy publishing documentation](https://docs.ntfy.sh/publish/).

Repair: require an explicitly configured private notification destination; remove the disclosed fallback. Use authentication/access controls or the configured Telegram channel. Do not print Telegram request errors containing a token-bearing URL without redaction.

### 17. P2 — Existing verification is a live exercise with no failing assertions

Evidence: `test_mock_pipeline.py:49`, `test_mock_pipeline.py:81`, `test_mock_pipeline.py:140`, `test_mock_pipeline.py:159`.

Despite its filename, the script sends a real initial email and follow-up, updates the production database, and sends notifications. It prints whether thread IDs match but does not assert that they match. Reply detection may return false and notification delivery may fail while the script still announces complete verification. It is not discoverable as a unittest suite. It also marks FU1 sent without updating its timestamp as the production function does, so it exercises a different state transition.

Repair: keep an explicitly named live smoke-test command with isolated state and explicit opt-in. Add a small offline regression check for lifecycle transitions, retry uncertainty, dry-run, CSV preservation, and dashboard schema. No new testing framework is needed.

### 18. P3 — Migration scripts and preview UI need small maintenance repairs

Evidence: `build_full_campaign.py:1388`, `update_cli.py:3`, `update_campaign.py:49`, `db.py:68`, `build_dashboard.py:285`, `build_dashboard.py:304`.

Re-running the old campaign builder overwrites the 52-record JSON with 25 old campaigns and placeholders. Several scripts edit data or source at import time using paths relative to the process directory. The database upsert updates email/copy but not domain, location, or founder metadata, and can replace scheduled copy after sending. Schema initialization is available only through `db.py`; the orchestrator cannot bootstrap an absent database. Missing domains become the same unique empty string. These are limitations on fresh setup and future imports, although the current database is healthy.

The modal lacks dialog semantics, focus placement/trapping, and focus restoration. Search/select fields and the icon-only close button lack explicit accessible labels. Clickable rows do not provide a keyboard equivalent for opening the sequence. Clipboard failures have no feedback. Frontend assets depend on external CDNs, including unpinned `lucide@latest`; the “self-contained” dashboard still requires those resources for its intended presentation.

Repair: archive completed migration scripts, guard executable entry points, validate required lead fields, initialize schema at application startup, and define which fields may change after a send. Add native accessibility attributes/focus management and clipboard error feedback; pin the small frontend assets if reproducible display is required.

## Simplification audit

Ranked by likely line reduction; these are proposals, not applied deletions. Repository-wide reference checks found no runtime callers for the standalone historical patch scripts.

1. `shrink:` Move the old 25-record campaign literal into the authoritative store after recovering its missing role/stage metadata, then retire its overwrite-only generator. Replacement: one maintained dataset. `build_full_campaign.py` — up to 1,395 lines.
2. `delete:` Archive the completed signature/timezone migration after preserving any needed transformation history. Replacement: nothing in the runtime path. `update_campaign.py` — 69 lines.
3. `delete:` Archive the legacy macOS notification script; the active pipeline already uses mobile notifications. Replacement: `notify_mobile.py`. `notify.py` — 33 lines.
4. `delete:` Archive the source-text CLI patch script; the patched formatting is already in the maintained CLI. Replacement: normal source edits. `update_cli.py` — 18 lines.
5. `reuse:` Use one canonical region mapping and lifecycle/export projection instead of three incompatible copies. Replacement: small shared helpers in existing modules. `cloud_orchestrator.py`, `research_and_generate.py`, `build_dashboard.py` — line reduction not estimated.

net: up to -1,515 lines, -0 Python dependencies possible. Additional completed cleanup scripts may be archived after the campaign has one authoritative source; their useful draft-update operations should remain available only if still needed.

The use of `sqlite3`, `urllib`, `email`, `csv`, and `argparse` is appropriate. Keep those building blocks. There is no justification here for an ORM, job-queue framework, provider abstraction, or frontend framework.

## Repair order

1. Make preview access local and restricted; make dry-run side-effect free; preserve CSV on errors.
2. Serialize cloud runs, refresh state within the serialized run, preserve state on failure, and reconcile uncertain Gmail sends before retrying.
3. Repair manual draft/queued follow-up transitions and campaign-specific reply detection, including alerts.
4. Restore missing metadata; export dashboard/CSV from authoritative state with calculated counts and timestamps.
5. Replace clock-window action selection and region substring routing with explicit mappings; define follow-up timing.
6. Make failures observable and add small offline regression checks. Separate live verification from routine tests.
7. Correct research/verification claims, require private notification configuration, and archive historical scripts.

Recommend repairing findings 1–7 before continuing unattended sends. No sending schedules were disabled as part of this audit.
