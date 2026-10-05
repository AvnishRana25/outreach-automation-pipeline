# Repair and validation checklist

Validated locally on 5 October 2026. The original audit is preserved in AUDIT.md; its findings describe the pre-repair baseline. The repository has been made private with user approval. The repairs are deployed and the cloud status acceptance run passed; see the update below.

## Automated checks

`python3 -B -m unittest discover -v` passes **47 tests**. The suite blocks external networking, uses temporary databases and fake Gmail, and exercises a real temporary local Git remote for checkpoint persistence. It never sends mail or mobile notifications. All Python sources parse; `git diff --check` passes.

| Functionality | Result and evidence |
| --- | --- |
| Database bootstrap and repeated schema migration | Passed integrity and idempotency checks |
| Input validation | Passed invalid recipient, header injection, missing copy, unsupported region/timezone and verification checks |
| Verified JSON lead imports | Passed region selection, validation before writes, evidence updates and missing-file refusal; no fallback to seed addresses |
| Company/domain deduplication | Passed preservation of recipient, copy and sending history on repeated import |
| Dry runs | Passed every CLI action and positional calls; no campaign DB changes, Gmail calls or notifications |
| Initial drafting and automatic sending | Passed create/queue/send progression and send-once checks with fake Gmail |
| Verification and exclusive sender guards | Passed refusal of unverified initial auto-send and unconfigured local auto-send |
| Manual initial sends | Passed tracked and legacy draft reconciliation without resending |
| Unknown send outcomes | Passed accepted-send timeout, delayed Gmail search, missing legacy draft and draft-creation failure; held without blind retry |
| Durable checkpoints | Passed failure before Gmail writes, real local Git push, failure after successful send and crash between attempt/lead updates |
| Follow-up progression | Passed queued FU1, manual FU1 reconciliation, delayed FU2, no repeat send and preservation of initial timestamp |
| Reply detection | Passed thread/time boundaries, own message exclusion, automated reply exclusion and colleague reply recognition |
| Reply cancellation and alerts | Passed queued draft cancellation, retry after cancellation failure, one-time success alerts and retry after failed alert |
| Failure reporting | Passed per-lead continuation, aggregate failure and independent tick action progression |
| Timezone scheduling | Passed summer/winter local morning windows and weekend exclusion |
| Gmail transport | Passed pagination, token refresh, MIME tracking headers, thread requirement and HTML content preservation |
| JSON/CSV/dashboard exports | Passed reading current database state, extra-field handling, atomic replacement and preservation on export failure |
| Dashboard injection protection | Passed script-terminator escaping and text-only rendering; no external CDN dependencies |
| Local preview privacy | Passed dashboard access and rejection of database/source/directory paths |
| Mobile privacy and errors | Passed no default channel, disclosed-topic rejection, authenticated ntfy request, Telegram result validation and token redaction |
| Cloud setup | Passed command failure reporting, rejection of public repositories and rejection of mismatched origin URLs before credential upload/push |
| Concurrency and workflow | Passed competing local process lock; workflow structure checks serialization, default status, checkpoints and recovery artifact |
| Historical migrations | Passed harmless retired entry points with no database/Gmail mutations |

## Browser and live read-only checks

- [x] Actual dashboard opened in the local browser, displaying 52 real leads: 28 drafted, 24 sent and zero recorded real replies.
- [x] Empty search shows a zero-result message; company search finds Hamming AI without a missing-field crash.
- [x] All region filters match SQLite: US 24, India 11, Europe/UK 8, Middle East 9. Mercor is excluded from Middle East.
- [x] Initial, FU1 and FU2 previews display the recorded copy.
- [x] Subject and body copying match the selected text; success feedback is accessible inside the dialog.
- [x] Keyboard arrow navigation switches tabs; Escape closes the dialog and restores focus to its opener.
- [x] Browser error/warning log was empty after the interaction checks. At the existing 551-pixel viewport, the page has no document-wide horizontal overflow; the campaign table scrolls horizontally.
- [x] Live Gmail profile authentication succeeded through the existing credentials. No live campaign writes were performed.

Screenshot evidence is saved locally in `backups/dashboard-verified.jpg`.

## Campaign preservation

The pre-repair database is preserved in `backups/outreach-before-repairs.db` (ignored by Git). All 53 original row IDs, recipients, email bodies/subjects, creation dates, initial send dates and reply dates remain unchanged. Status labels were normalized and consumed initial draft IDs cleared; regions/timezones and missing editorial metadata were restored. SQLite integrity is `ok`.

All three snapshots contain the same 52 real leads and status counts. The old mock-test row remains in SQLite for preservation and is excluded from exports. No verification date/source was invented. The 52 current real contacts have no recorded verification evidence, and the 28 unsent initial campaigns are held from automatic sending until verified imports provide it. Inferred recipient timezones need human review where company location is ambiguous.

## Live acceptance still pending

- [x] Deployed to the private campaign repository. Cloud status run 37355917369 passed 47 regressions, the action, checkpoint/push and exports. Future scheduled delivery timing remains dependent on GitHub scheduling.
- [ ] Supply verified lead evidence and confirm recipient timezones before enabling new initial automatic sends.
- [x] Controlled live draft/send/thread/reply cycle passed using the authorized inbox; queued follow-up cancellation and actual Gmail draft removal were verified.
- [ ] Verify mobile delivery using a configured private ntfy topic or Telegram destination.

Fake transport checks establish local behavior; they do not establish real Gmail delivery, inbox placement, recipient identity, or live mobile/workflow health. Unknown outcomes intentionally stop sending until delivery is positively reconciled. The one-authoritative-sender restriction and remote push availability remain operating requirements. No flawless production guarantee is implied.

## Audit finding coverage

Findings 1–4: serialized runner, durable attempt/checkpoint recovery, manual draft progression and complete dry-run handling. Findings 5–9: restricted localhost preview, atomic CSV exports, thread-aware replies and authoritative accessible dashboard/CLI snapshots. Findings 10–14: local-time tick scheduling, canonical region routing, visible failures, separate follow-up timestamps and verified JSON import source. Findings 15–18: escaped email/dashboard content, private notification configuration, offline regression assertions and retired unsafe migrations/accessibility repairs.

## Live acceptance update

The user authorized deployment to a private repository and a controlled message to `collaboratewithavnish@gmail.com`. The repository visibility is confirmed private. The live sent message and follow-up draft share a Gmail thread. The test exposed Gmail replacing the supplied RFC Message-ID; recovery now uses a retained X-Outreach-ID header as well. The retained header and draft lookup were verified against Gmail, and a regression covers rewritten IDs for sent/draft recovery. The original test's sent Message-ID was reconciled from its actual Gmail message. No campaign recipient was contacted.

The incoming reply from the controlled recipient was detected and the queued follow-up draft was cancelled and removed from Gmail. The private [cloud run](https://github.com/AvnishRana25/outreach-automation-pipeline/actions/runs/37355917369) completed successfully, including 47 tests and checkpoint/export pushes. Existing phone alerts were reported by the user to work under the old setup; a protected topic/token is still needed to validate the repaired mobile configuration. NTFY_TOKEN is currently absent from repository secrets, so the repaired pipeline will not send alerts through that old setup. Use the deployed notify-test action after configuring the private channel.
