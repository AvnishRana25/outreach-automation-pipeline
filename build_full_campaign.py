#!/usr/bin/env python3
"""
Populates all 25 highly personalized cold outreach campaigns + 2-stage follow-up sequences.
"""

import json
import os

LEADS = [
    {
        "id": 1,
        "company_name": "Hamming AI",
        "batch_or_stage": "YC S24",
        "location": "San Francisco, US (Remote)",
        "domain": "hamming.ai",
        "founder_name": "Sumanyu Sharma",
        "founder_role": "Co-founder & CEO",
        "verified_email": "sumanyu@hamming.ai",
        "target_role": "AI Evaluation / QA Engineer Intern (or 1-Mo Trial)",
        "hook_angle": "Adversarial benchmark authoring & pytest verifiers for agent pipelines",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "quick technical question re: Hamming's agent eval verifiers",
        "initial_body": """Hi Sumanyu,

Saw your launch of Hamming for agent QA and prompt optimization — the focus on moving teams away from 'vibe checks' to deterministic regression testing is spot on.

At Caudal AI, I author contamination-resistant benchmark tasks for frontier coding agents in Docker environments. I write adversarial edge cases and pytest verifiers that catch hallucinated fixes and incomplete execution across complex trajectories before they reach benchmark datasets.

Previously, I shipped a production WhatsApp sales agent running 4,000+ live deals where deterministic state machines prevented LLMs from hallucinating pricing or availability.

I’d love to join Hamming as an AI Eval / Solutions Engineer intern (or tackle a 1-month trial contract) to author specialized agent benchmarks, build client evaluation pipelines, or stress-test your voice/chat runners.

Open to a 10-minute chat this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: quick technical question re: Hamming's agent eval verifiers",
        "fu1_body": """Hi Sumanyu,

Thought about Hamming's test runners over the weekend.

When evaluating multi-step agent trajectories at Caudal AI, we noticed models often pass static rubric checks but fail when state persists unexpectedly across tool retries. We handled this by pairing unit-test assertions with dynamic state-machine verifiers to isolate false passes.

If your team is busy onboarding customer pilots, I’d be happy to take on a 2-week trial sprint to author a benchmark suite or test harness for voice/chat edge cases.

Still open to a brief chat this week?

Best,
Avnish""",
        "fu2_subject": "Re: quick technical question re: Hamming's agent eval verifiers",
        "fu2_body": """Hi Sumanyu,

Assuming your plate is completely full scaling Hamming right now, so I'll leave this here.

If you ever need an engineer who specializes in Dockerized agent benchmarks, adversarial pytest verifiers, and deterministic guardrails, feel free to keep my details handy:
- Production WhatsApp Sales Agent (4,000+ deals, zero price improvisation): [GitHub]
- Caudal AI: Frontier agent benchmark verifiers in Docker shell environments
- Direct / WhatsApp: +91 7982252971

Wishing you and the team continued momentum.

Best,
Avnish"""
    },
    {
        "id": 2,
        "company_name": "Composio",
        "batch_or_stage": "Together Fund / Seed",
        "location": "Bengaluru & SF",
        "domain": "composio.dev",
        "founder_name": "Soham Ganatra",
        "founder_role": "Co-founder & CEO",
        "verified_email": "soham@composio.dev",
        "target_role": "Junior Forward Deployed Engineer (FDE) / Integrations",
        "hook_angle": "Tool-use reliability, Docker sandboxes, and production CRM WhatsApp agents",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "composio tool-use reliability + agent eval sandboxes",
        "initial_body": """Hi Soham,

Been following Composio's rapid expansion as the go-to tool execution layer for agent builders — native auth and execution sandboxing are game-changers for reliability.

At Caudal AI, I author Dockerized shell environments and adversarial pytest verifiers that stress-test frontier coding agents on tool inspection, command execution, and runtime debugging. Previously, I built a production multimodal WhatsApp agent running 4,000+ live deals, using strict deterministic trees so the model never improvises deal state or tool arguments.

I also have customer-facing experience (Klimashift, where 2 of my 4 product proposals were adopted into the roadmap and I built ROI models for enterprise pitches).

I would love to help Composio as a Junior FDE intern or contract engineer building bespoke enterprise tool integrations, sandbox verifiers, and customer POCs.

Worth a brief 10-min sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: composio tool-use reliability + agent eval sandboxes",
        "fu1_body": """Hi Soham,

Quick follow-up on Composio's tool execution layer.

A recurring failure mode we saw with agentic tool calls at Caudal AI is schema drift when external APIs return unexpected nulls or wrapped payloads. We solved this with contract verifiers that catch schema mismatches before agents loop uncontrollably.

I'd be glad to prototype custom tool connectors or regression tests for Composio on a 2-week trial sprint.

Do you have 10 minutes Thursday or Friday?

Best,
Avnish""",
        "fu2_subject": "Re: composio tool-use reliability + agent eval sandboxes",
        "fu2_body": """Hi Soham,

Figure you're heads-down driving Composio's growth, so I won't crowd your inbox.

If you ever need an engineer who understands both tool-use execution sandboxes (Caudal AI) and commercial client delivery (Klimashift + Realty Pandit CRM), here is my contact info:
- GitHub: [GitHub Link]
- WhatsApp / Cell: +91 7982252971

Rooting for Composio's continued dominance in agent tooling.

Best,
Avnish"""
    },
    {
        "id": 3,
        "company_name": "Atla",
        "batch_or_stage": "YC S23 / Creandum",
        "location": "London, UK (Remote)",
        "domain": "atla-ai.com",
        "founder_name": "Maurice Burger",
        "founder_role": "Co-founder & CEO",
        "verified_email": "maurice@atla-ai.com",
        "target_role": "AI Evaluation / Agent Benchmarking Intern",
        "hook_angle": "Agent trajectory grading, adversarial test design, and verifier correctness",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "agent trajectory grading & adversarial verifiers for Atla",
        "initial_body": """Hi Maurice,

Saw Atla's work on agent improvement engines and LLM-as-a-judge error pattern detection — the emphasis on automated failure attribution is exactly what agentic systems are missing.

At Caudal AI, I author contamination-resistant tasks for frontier coding agent benchmarks inside Dockerized shell environments. My core focus is writing adversarial edge cases and pytest verifiers that reduce false passes/failures, and grading agent trajectories against strict rubrics to catch subtle logic slips.

I'd love to join Atla for a 3-month remote internship or trial contract to help author adversarial test suites, build ground-truth agent benchmark tasks, or refine error taxonomy grading.

Open to a brief conversation this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: agent trajectory grading & adversarial verifiers for Atla",
        "fu1_body": """Hi Maurice,

Quick thought regarding LLM judges: when evaluating frontier agents, we noticed LLM judges often suffer from length bias and overlook skipped steps in long shell histories. We addressed this by combining rubric-based deterministic verifiers with adversarial edge cases.

I'd love to help Atla benchmark complex agent trajectories or build adversarial test sets on a short trial sprint.

Worth a 10-minute call?

Best,
Avnish""",
        "fu2_subject": "Re: agent trajectory grading & adversarial verifiers for Atla",
        "fu2_body": """Hi Maurice,

Understand you're fully focused on building Atla, so I'll keep this as my last note.

If you ever need an agent benchmark researcher with production trajectory evaluation experience:
- Caudal AI: Frontier coding benchmark tasks & pytest verifiers in Docker
- Live Projects & Code: [GitHub Link]
- Direct: +91 7982252971

All the best with Atla's next milestone!

Best,
Avnish"""
    },
    {
        "id": 4,
        "company_name": "Emergent",
        "batch_or_stage": "YC S24 / Unicorn",
        "location": "San Francisco, US (Remote)",
        "domain": "emergent.sh",
        "founder_name": "Mukund Jha",
        "founder_role": "Co-founder & CEO",
        "verified_email": "mj@emergent.sh",
        "target_role": "AI Coding Agent / Eval & Integration Contractor",
        "hook_angle": "Stress-testing coding agents in Docker and multi-agent contract verification",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "stress-testing Emergent's multi-agent code generation pipelines",
        "initial_body": """Hi Mukund,

Huge congrats on Emergent's trajectory — scaling multi-agent fullstack code generation (FastAPI + React) for non-technical creators is a massive achievement.

At Caudal AI, my day-to-day is authoring contamination-resistant benchmarks for frontier coding agents in Docker shell environments, testing whether agents can inspect systems, run commands, and debug runtime failures end-to-end without hallucinated fixes.

On the product side, I built and shipped Realty Pandit (React/Node.js/PostgreSQL) with deterministic state machines and zero-downtime database migrations.

I’d love to contribute as an AI Engineering / Eval contractor or intern to help stress-test Emergent's code execution sandboxes, build adversarial test suites, or squash deployment edge cases.

Do you have 10 minutes for a quick chat?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: stress-testing Emergent's multi-agent code generation pipelines",
        "fu1_body": """Hi Mukund,

Quick follow-up: in multi-agent code generation, the most frequent failure point is handoff drift between architecture agents and frontend/backend subagents (e.g. mismatched API schemas or unhandled route states).

At Caudal AI, we design adversarial test beds specifically to catch these inter-agent contract violations before execution.

I'd be thrilled to tackle a 2-week scoped project on sandbox validation or benchmark authoring.

Open to a brief call this week?

Best,
Avnish""",
        "fu2_subject": "Re: stress-testing Emergent's multi-agent code generation pipelines",
        "fu2_body": """Hi Mukund,

Assuming you're flat out scaling Emergent's platform right now, so I'll bow out.

If you ever need an engineer skilled in stress-testing coding agents, Docker sandboxes, and fullstack agent pipelines:
- GitHub: [GitHub Link]
- Direct / WhatsApp: +91 7982252971

Wishing Emergent massive continued success!

Best,
Avnish"""
    },
    {
        "id": 5,
        "company_name": "Persana AI",
        "batch_or_stage": "YC W23",
        "location": "San Francisco, US (Remote)",
        "domain": "persana.ai",
        "founder_name": "Sriya Maram",
        "founder_role": "Co-founder & CEO",
        "verified_email": "sriya@persana.ai",
        "target_role": "Forward Deployed Engineer (FDE) / Agent Workflow Contractor",
        "hook_angle": "B2B sales agents, CRM data pipelines, and deterministic conversational guards",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "quick technical note: Persana agent data pipelines & CRM guards",
        "initial_body": """Hi Sriya,

Love what you and the Persana AI team are building to turn outbound into autonomous multi-source intelligence.

I recently built and shipped Realty Pandit CRM — deploying a multimodal WhatsApp sales qualification agent across 4,000+ active deals. To make sure the agent never hallucinated inventory or pricing, I designed deterministic decision trees and a state-machine pipeline alongside a zero-downtime PostgreSQL migration for a 35+ member sales team.

I also have experience authoring adversarial verifiers for agentic benchmarks at Caudal AI.

I would love to help Persana as a Junior FDE or contract engineer building bespoke customer CRM integrations, data normalization adapters, or qualification agents.

Would you be open to a 10-minute chat this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: quick technical note: Persana agent data pipelines & CRM guards",
        "fu1_body": """Hi Sriya,

Following up with a quick thought on sales agent reliability: when ingesting diverse third-party CRM data, unstructured notes often trigger unintended state transitions. We mitigated this by enforcing strict state machines where LLM outputs can only trigger predefined transitions.

I’d love to help Persana build customer CRM connectors or outbound verification workflows on a trial contract.

Still open to a quick 10-min chat?

Best,
Avnish""",
        "fu2_subject": "Re: quick technical note: Persana agent data pipelines & CRM guards",
        "fu2_body": """Hi Sriya,

I know you have a million priorities scaling Persana, so I won't follow up again.

If you ever need an engineer who can build production CRM agent pipelines and deterministic sales workflows:
- Realty Pandit CRM (4,000+ deals on WhatsApp): [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Wishing you and the Persana team all the best!

Best,
Avnish"""
    },
    {
        "id": 6,
        "company_name": "Dextr AI",
        "batch_or_stage": "Seed ($6.7M Elevation / Foundation)",
        "location": "Bengaluru & US",
        "domain": "dextr.ai",
        "founder_name": "Sajid Shariff",
        "founder_role": "Co-founder & CEO",
        "verified_email": "sajid@dextr.ai",
        "target_role": "Junior FDE / Voice & Messaging Agent Integrations",
        "hook_angle": "Production conversational agents, zero hallucination guardrails, and customer ROI",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "dextr AI reservation agents + deterministic guardrails",
        "initial_body": """Hi Sajid,

Congrats on the $6.7M seed round led by Elevation Capital. Replacing legacy reservation contact centers with autonomous hospitality agents is an enormous market.

When deploying conversational agents in high-stakes hospitality/sales, preventing edge-case hallucinations is critical. I built a production WhatsApp sales agent for Realty Pandit handling 4,000+ active customer deals with strict deterministic trees so the LLM never improvises booking availability or rates. At Caudal AI, I author adversarial benchmark verifiers that catch logic failures in autonomous agents.

I'd love to join Dextr as a Junior Solutions Engineer / FDE intern to help build customer reservation connectors, integration test suites, and pilot deployments.

Open to a brief 10-minute call this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: dextr AI reservation agents + deterministic guardrails",
        "fu1_body": """Hi Sajid,

Thought of Dextr when reviewing contact center edge cases: guest date alterations and multi-room bookings often cause LLM state confusion. Implementing transactional rollbacks in the agent's dialog tree eliminated double-booking in our Realty Pandit deployment.

I’d be glad to build out similar hotel reservation connectors or eval test cases for Dextr on a trial sprint.

Worth 10 minutes this week?

Best,
Avnish""",
        "fu2_subject": "Re: dextr AI reservation agents + deterministic guardrails",
        "fu2_body": """Hi Sajid,

Assuming you're flat out deploying seed capital and onboarding hotel properties, so I'll wrap up here.

Feel free to keep my info on file if you need hands-on conversational agent engineering:
- WhatsApp: +91 7982252971
- GitHub: [GitHub Link]

Best of luck scaling Dextr!

Best,
Avnish"""
    },
    {
        "id": 7,
        "company_name": "Gumloop",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "gumloop.com",
        "founder_name": "Max Brodeur-Urbas",
        "founder_role": "Co-founder & CEO",
        "verified_email": "max@gumloop.com",
        "target_role": "Integration Engineer / FDE Intern",
        "hook_angle": "Workflow nodes, API connectors, and execution reliability",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "building bespoke workflow nodes & eval verifiers for Gumloop",
        "initial_body": """Hi Max,

Really impressive seeing Gumloop power automated workflows for teams like Instacart. The modular node approach is by far the cleanest abstraction in the agentic automation space.

I specialize in building reliable agent tooling: at Caudal AI, I write adversarial pytest verifiers and Dockerized benchmarks testing agent execution; previously, I shipped a production WhatsApp sales agent handling 4,000+ deals using deterministic state machines.

I’d love to help Gumloop build new third-party integration nodes, customer-requested workflow templates, or execution error diagnostics on an internship or 1-month trial contract basis.

Worth a brief conversation this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: building bespoke workflow nodes & eval verifiers for Gumloop",
        "fu1_body": """Hi Max,

Quick note on node execution: when users chain multiple web scraping and LLM nodes, silent structural changes on target pages frequently break downstream nodes. We tackled this at Caudal AI by embedding schema self-healing verifiers.

Happy to build custom integration nodes or validation templates for Gumloop on a trial sprint.

Still open to a quick chat?

Best,
Avnish""",
        "fu2_subject": "Re: building bespoke workflow nodes & eval verifiers for Gumloop",
        "fu2_body": """Hi Max,

Figure you're laser-focused on Gumloop's product velocity, so I'll bow out.

If you ever need an engineer for node integrations, customer workflows, or agent verifiers:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Rooting for Gumloop's continued growth!

Best,
Avnish"""
    },
    {
        "id": 8,
        "company_name": "Erad",
        "batch_or_stage": "Series A ($22M MEVP)",
        "location": "Riyadh & Dubai",
        "domain": "erad.co",
        "founder_name": "Salem Abu-Hammour",
        "founder_role": "Co-founder & CEO",
        "verified_email": "salem@erad.co",
        "target_role": "AI / Automation Contractor",
        "hook_angle": "Automated document/telemetry parsing, ROI modeling, and zero-hallucination pipelines",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "automated underwriting data ingestion & financial telemetry",
        "initial_body": """Hi Salem,

Congrats on Erad's $22M Series A round to expand automated financing across the GCC.

At Klimashift, I built fault diagnostics on 1 Hz telemetry and designed commercial ROI models from 350+ customer bills used directly in B2B sales conversations. In parallel, I've built production LLM systems with explainable, deterministic rule engines so models never improvise numerical or financial data.

I’d love to assist Erad as an AI Automation / Integration contractor to build automated financial statement ingestion, underwriting verification pipelines, or partner API connectors.

Would you be open to a 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: automated underwriting data ingestion & financial telemetry",
        "fu1_body": """Hi Salem,

Following up on SME underwriting telemetry: in energy and billing data at Klimashift, we found that combining deterministic rule engines (14-rule explainability) with LLM parsing captured anomalies that standard financial audits missed entirely.

I’d welcome the chance to prototype automated statement parsers or partner connectors for Erad on a trial contract.

Available for a 10-min call Thursday?

Best,
Avnish""",
        "fu2_subject": "Re: automated underwriting data ingestion & financial telemetry",
        "fu2_body": """Hi Salem,

I know you have major regional expansion plans in motion, so I won't follow up again.

If you ever need an engineer who merges financial telemetry parsing with strict, explainable LLM pipelines:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

Wishing Erad tremendous success across the GCC!

Best,
Avnish"""
    },
    {
        "id": 9,
        "company_name": "Archal",
        "batch_or_stage": "YC",
        "location": "San Francisco, US (Remote)",
        "domain": "archal.ai",
        "founder_name": "Aidan Tiruvan",
        "founder_role": "Founder",
        "verified_email": "aidan@archal.ai",
        "target_role": "AI Sandbox & Evaluation Engineer Intern",
        "hook_angle": "API sandboxes for coding agents, state inspection, and Docker environments",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "API sandboxes for coding agents + Dockerized state verifiers",
        "initial_body": """Hi Aidan,

Love what you're building with Archal — providing API sandboxes where coding agents can run integrations and inspect state changes is critical for autonomous software engineering.

At Caudal AI, I author contamination-resistant benchmark tasks for frontier coding agents in Dockerized shell environments where models must inspect systems, run commands, and debug failures end-to-end. I design adversarial pytest verifiers that validate state transitions across every valid solution path.

I'd love to join Archal as an AI Sandbox / Systems intern or trial contractor to build realistic integration mocks, inspect sandbox side-effects, and author agent test suites.

Open to a 10-minute chat this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: API sandboxes for coding agents + Dockerized state verifiers",
        "fu1_body": """Hi Aidan,

Quick follow-up on agent sandboxes: in Docker benchmark environments at Caudal AI, the biggest headache was cleaning state leakages between adversarial agent runs. We built automated ephemeral teardowns and state verifiers to guarantee repeatability.

I'd love to help Archal stress-test sandbox APIs or build integration benchmarks on a 2-week trial sprint.

Free for a quick call?

Best,
Avnish""",
        "fu2_subject": "Re: API sandboxes for coding agents + Dockerized state verifiers",
        "fu2_body": """Hi Aidan,

Assuming you're heads-down shipping Archal sandboxes, so I'll leave this here.

If you ever need an engineer experienced in Dockerized agent execution and sandbox verification:
- Caudal AI Benchmark Work: [GitHub]
- WhatsApp / Phone: +91 7982252971

All the best with Archal's launch!

Best,
Avnish"""
    },
    {
        "id": 10,
        "company_name": "Arga Labs",
        "batch_or_stage": "YC P26",
        "location": "San Francisco, US (Remote)",
        "domain": "argalabs.com",
        "founder_name": "Phillip Li",
        "founder_role": "Co-founder & CEO",
        "verified_email": "phillip@argalabs.com",
        "target_role": "AI Agent Sandbox & Validation Engineer Intern",
        "hook_angle": "Digital-twin staging environments, mock third-party services, and verifier design",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "digital-twin staging sandboxes for agent validation",
        "initial_body": """Hi Phillip,

Saw Arga Labs' work building digital-twin staging environments (mocking Stripe, Slack, Drive) for testing AI agents — creating high-fidelity sandbox state before production is the exact missing link for agent reliability.

At Caudal AI, I author Dockerized shell environments and adversarial pytest verifiers that test whether autonomous coding agents can inspect systems and recover from runtime failures without hallucinated shortcuts.

I’d love to help Arga Labs as an AI Validation / Sandbox Engineer intern or contractor building digital-twin mocks, adversarial test suites, and agent regression harnesses.

Do you have 10 minutes for a brief call this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: digital-twin staging sandboxes for agent validation",
        "fu1_body": """Hi Phillip,

Following up on digital-twin sandboxes: one subtle challenge with mock third-party APIs is simulating asynchronous state changes (e.g. Stripe webhooks or Slack event subscriptions). At Caudal AI, we designed verifiers that handle non-deterministic timing gracefully.

Happy to build out mock service adapters or adversarial tests on a trial sprint.

Worth 10 minutes this week?

Best,
Avnish""",
        "fu2_subject": "Re: digital-twin staging sandboxes for agent validation",
        "fu2_body": """Hi Phillip,

I'll assume you're fully occupied scaling Arga Labs, so I won't follow up again.

Feel free to keep my details handy for agent validation and sandbox testing:
- GitHub: [GitHub Link]
- Direct / WhatsApp: +91 7982252971

Best of luck with Arga Labs!

Best,
Avnish"""
    },
    {
        "id": 11,
        "company_name": "Runable",
        "batch_or_stage": "Series A ($21M Nexus / Together)",
        "location": "Bengaluru & US",
        "domain": "runable.com",
        "founder_name": "Umesh Kumar",
        "founder_role": "Co-founder & CEO",
        "verified_email": "umesh@runable.com",
        "target_role": "Forward Deployed Engineer (FDE) / Enterprise Agent Contractor",
        "hook_angle": "Enterprise agent workflows, state machines, and customer ROI metrics",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "enterprise business agents + zero-downtime state pipelines",
        "initial_body": """Hi Umesh,

Congratulations on Runable's $21M Series A co-led by Nexus and Together Fund. Scaling autonomous business agents across complex enterprise workflows is a tremendous opportunity.

When shipping agents in production, preventing unexpected branching and hallucinated states is crucial. For Realty Pandit CRM, I deployed an agent handling 4,000+ active deals using deterministic state machines and ran a zero-downtime PostgreSQL migration for a 35+ member team. At Klimashift, I modeled customer ROI used in live B2B pitches.

I'd love to help Runable as an FDE intern or contract engineer building enterprise client POCs, custom ERP/CRM connectors, or reliability evals.

Open to a brief 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: enterprise business agents + zero-downtime state pipelines",
        "fu1_body": """Hi Umesh,

Quick note on enterprise agent rollouts: in client deployments, business stakeholders demand strict explainability and rollback capabilities before giving agents operational authority.

At Caudal AI and Realty Pandit, I implemented transactional state guards so models can never execute unapproved business actions.

I’d be glad to handle a customer POC or integration sprint on a trial contract.

Free for a 10-min chat?

Best,
Avnish""",
        "fu2_subject": "Re: enterprise business agents + zero-downtime state pipelines",
        "fu2_body": """Hi Umesh,

Assuming you're completely immersed in scaling Runable post-Series A, so I'll wrap up here.

If you need a Junior FDE who combines hands-on agent engineering with customer-facing ROI sense:
- WhatsApp: +91 7982252971
- GitHub: [GitHub Link]

Wishing Runable massive continued success!

Best,
Avnish"""
    },
    {
        "id": 12,
        "company_name": "Ignosis AI",
        "batch_or_stage": "Peak XV Surge ($4M)",
        "location": "Bengaluru & Mumbai",
        "domain": "ignosis.ai",
        "founder_name": "Nirav Prajapati",
        "founder_role": "Co-founder & CEO",
        "verified_email": "nirav.prajapati@ignosis.ai",
        "target_role": "AI Data & Agent Integration Engineer",
        "hook_angle": "Financial data intelligence, debt-collection agent pipelines, and guardrails",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "debt collection agent pipelines + zero-hallucination financial guards",
        "initial_body": """Hi Nirav,

Congrats on Ignosis securing $4M in pre-Series A funding led by Peak XV's Surge. Deploying AI data intelligence and automated collection agents in BFSI requires strict compliance and zero errors.

I specialize in building deterministic agent workflows: for Realty Pandit CRM, I built an agent managing 4,000+ active deals with deterministic decision trees so the model never improvised numbers or payment commitments. In parallel, I author adversarial verifiers for agentic benchmarks at Caudal AI.

I'd love to join Ignosis as an AI Integration / Solutions Engineer intern to build financial data ingestion pipelines, banking API connectors, or compliance verifiers.

Open to a 10-minute call this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: debt collection agent pipelines + zero-hallucination financial guards",
        "fu1_body": """Hi Nirav,

Following up on financial agent compliance: in collection workflows, auditory and textual hallucinations in settlement terms represent severe regulatory liabilities. We tackled this by wrapping LLM interactions in deterministic rule verifiers that reject unauthorized repayment proposals.

Happy to build proof-of-concept compliance verifiers for Ignosis on a 2-week trial sprint.

Worth a brief conversation?

Best,
Avnish""",
        "fu2_subject": "Re: debt collection agent pipelines + zero-hallucination financial guards",
        "fu2_body": """Hi Nirav,

I know you have major execution priorities scaling Ignosis with Surge, so I won't follow up again.

If you ever need an engineer for compliance-first agent pipelines and financial data intelligence:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

All the best with Ignosis's growth!

Best,
Avnish"""
    },
    {
        "id": 13,
        "company_name": "Armature",
        "batch_or_stage": "YC P26",
        "location": "San Francisco, US (Remote)",
        "domain": "armature.tech",
        "founder_name": "Theodore Otzenberger",
        "founder_role": "Co-founder & CEO",
        "verified_email": "theodore@armature.tech",
        "target_role": "AI Coding Agent Usability & Benchmarking Intern",
        "hook_angle": "Benchmarking coding agents, SDK usability, and Docker test environments",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "evaluating SDK agent-usability + Dockerized coding benchmarks",
        "initial_body": """Hi Theodore,

Love Armature's focus on making products 'agent-usable' by monitoring how coding agents navigate codebases and SDKs — measuring agent friction is a massive blind spot for devtool companies.

At Caudal AI, I author contamination-resistant benchmark tasks for frontier coding agents in Docker shell environments. My role is to grade agent trajectories, write adversarial edge cases, and design pytest verifiers that pinpoint where agents hallucinate fixes or fail to understand library interfaces.

I’d love to help Armature author agentic benchmark tasks, stress-test SDK usability runners, or build developer telemetry analyzers on an internship or trial contract.

Open to a 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: evaluating SDK agent-usability + Dockerized coding benchmarks",
        "fu1_body": """Hi Theodore,

Quick follow-up on agent usability: coding agents consistently get tripped up by implicit dependencies, missing return type annotations, or incomplete CLI error outputs.

At Caudal AI, we designed grading rubrics that evaluate the exact trajectory step where an agent's mental model diverged from the API contract.

Happy to build out benchmark tasks or usability telemetry for Armature on a trial sprint.

Free for a brief chat?

Best,
Avnish""",
        "fu2_subject": "Re: evaluating SDK agent-usability + Dockerized coding benchmarks",
        "fu2_body": """Hi Theodore,

Assuming you're flat out scaling Armature, so I'll step aside.

Feel free to keep my info on hand if you need an engineer for coding agent benchmarks and usability evals:
- Caudal AI Benchmark Work: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Wishing Armature massive success!

Best,
Avnish"""
    },
    {
        "id": 14,
        "company_name": "Boom AI",
        "batch_or_stage": "YC F25",
        "location": "San Francisco, US (Remote)",
        "domain": "useboom.ai",
        "founder_name": "Juan Casian",
        "founder_role": "Co-founder & CEO",
        "verified_email": "juan@useboom.ai",
        "target_role": "Junior FDE / eCommerce Conversational Agent Contractor",
        "hook_angle": "Multimodal sales agents, WhatsApp commerce, and conversion telemetry",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "eCommerce recovery agents + WhatsApp multimodal pipelines",
        "initial_body": """Hi Juan,

Awesome seeing Boom AI tackle eCommerce revenue recovery through instant conversational agents.

I recently shipped a production multimodal WhatsApp sales agent for Realty Pandit CRM qualifying leads across 4,000+ active deals. To maximize speed-to-lead without risking hallucinations, I built deterministic state trees preventing the model from improvising inventory details, backed by an analytics cockpit tracking conversion funnels.

I’d love to join Boom AI as a Junior FDE or contract engineer building Shopify/ERP connectors, recovery dialog trees, or conversion telemetry pipelines.

Would you have 10 minutes for a brief call this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: eCommerce recovery agents + WhatsApp multimodal pipelines",
        "fu1_body": """Hi Juan,

Quick note on cart abandonment conversations: response latency and contextual photo/receipt parsing made the biggest difference in lead reactivation in our WhatsApp deployment.

I also write adversarial verifiers for agentic benchmarks at Caudal AI to ensure agents don't hallucinate coupon codes or prices.

I'd love to prototype an integration adapter or recovery flow for Boom on a trial contract.

Still open to a quick call?

Best,
Avnish""",
        "fu2_subject": "Re: eCommerce recovery agents + WhatsApp multimodal pipelines",
        "fu2_body": """Hi Juan,

I know you have your hands full scaling Boom AI, so I won't follow up further.

If you ever need an engineer who has shipped conversational sales agents at scale:
- WhatsApp: +91 7982252971
- GitHub: [GitHub Link]

Best of luck with Boom AI!

Best,
Avnish"""
    },
    {
        "id": 15,
        "company_name": "Veles",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "getveles.com",
        "founder_name": "Simon Ooley",
        "founder_role": "Co-founder & CEO",
        "verified_email": "simon@getveles.com",
        "target_role": "Forward Deployed Engineer (FDE) / CPQ Automation Contractor",
        "hook_angle": "CPQ automation, deal documentation pipelines, and zero-downtime databases",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "sales CPQ deal pipelines + deterministic document guardrails",
        "initial_body": """Hi Simon,

Really impressed by Veles automating the Configure, Price, Quote (CPQ) process and deal documentation for both human reps and agents — manual quoting is a massive drag on deal velocity.

In my recent project, Realty Pandit CRM, I engineered a state-machine deal pipeline forecasting an INR 130+ Cr pipeline and deployed a sales agent across 4,000+ deals with deterministic rules so pricing was never hallucinated. In parallel, at Caudal AI, I author pytest verifiers for agent benchmarks.

I’d love to join Veles as an FDE intern or contract engineer building CRM quoting connectors, customer ERP adapters, or document verification workflows.

Open to a brief 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: sales CPQ deal pipelines + deterministic document guardrails",
        "fu1_body": """Hi Simon,

Following up on CPQ automation: discount thresholds and multi-tiered billing rules are where LLMs most frequently make arithmetic and policy errors in quote generation. We resolved this by combining deterministic validation layers with LLM draft generators.

I’d be glad to build customer quoting adapters or verification suites on a 2-week trial sprint.

Do you have 10 minutes Thursday?

Best,
Avnish""",
        "fu2_subject": "Re: sales CPQ deal pipelines + deterministic document guardrails",
        "fu2_body": """Hi Simon,

Assuming you're completely absorbed in growing Veles, so I'll wrap up here.

If you ever need an FDE who understands complex deal pipelines and deterministic document guardrails:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

Wishing you and Veles tremendous success!

Best,
Avnish"""
    },
    {
        "id": 16,
        "company_name": "Linzumi",
        "batch_or_stage": "YC",
        "location": "San Francisco, US (Remote)",
        "domain": "linzumi.com",
        "founder_name": "Sean Grove",
        "founder_role": "Co-Founder",
        "verified_email": "sean@linzumi.com",
        "target_role": "AI Coding Agent Orchestration & Testing Engineer",
        "hook_angle": "Managing fleets of coding agents, trajectory verification, and Docker harnesses",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "managing coding agent fleets + trajectory verifiers",
        "initial_body": """Hi Sean,

Exciting to see Linzumi building a team chat command center for managing and verifying fleets of coding agents — managing multi-agent output without review bottlenecks is the next frontier.

At Caudal AI, I author contamination-resistant benchmark tasks for frontier coding agents in Dockerized shell environments. I grade agent execution trajectories against strict rubrics and pytest verifiers, catching logic errors, loop states, and incomplete diffs before code merges.

I’d love to contribute to Linzumi as an AI Systems / Verification intern or trial contractor to help build agent status inspectors, trajectory diff verifiers, or test environments.

Would you be open to a 10-minute chat this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: managing coding agent fleets + trajectory verifiers",
        "fu1_body": """Hi Sean,

Quick follow-up on agent fleet verification: when multiple agents execute concurrently on related code modules, catching race conditions and conflicting file modifications in the chat stream requires real-time AST or diff verifiers.

At Caudal AI, we built adversarial test harnesses specifically for multi-step agent debugging.

Happy to build verification modules or agent runners on a trial sprint.

Worth a brief call?

Best,
Avnish""",
        "fu2_subject": "Re: managing coding agent fleets + trajectory verifiers",
        "fu2_body": """Hi Sean,

Assuming your focus is 100% on Linzumi's product build, so I'll bow out.

If you ever need an engineer who specializes in coding agent trajectory verification and Docker execution:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Best of luck scaling Linzumi!

Best,
Avnish"""
    },
    {
        "id": 17,
        "company_name": "Autosana",
        "batch_or_stage": "YC",
        "location": "San Francisco, US (Remote)",
        "domain": "autosana.ai",
        "founder_name": "Yuvan Sundrani",
        "founder_role": "Co-Founder",
        "verified_email": "yuvan@autosana.ai",
        "target_role": "Autonomous QA & Benchmark Engineer Intern",
        "hook_angle": "E2E testing agents, Docker shell environments, and adversarial test suites",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "autonomous E2E testing agents + adversarial pytest verifiers",
        "initial_body": """Hi Yuvan,

Great mission with Autosana — using AI agents to autonomously generate and run end-to-end tests for mobile and web applications finally solves test maintenance debt.

At Caudal AI, I author contamination-resistant benchmark tasks and adversarial pytest verifiers in Docker shell environments, testing whether autonomous agents can inspect systems, run commands, and debug failures end-to-end. Previously, I worked on mobile engineering at Manacle Tech cutting auth drop-off 25%.

I’d love to join Autosana as an AI QA / Benchmark Engineer intern or trial contractor to author adversarial test suites, build web/mobile crawler harnesses, or refine trajectory grading.

Open to a 10-minute sync this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: autonomous E2E testing agents + adversarial pytest verifiers",
        "fu1_body": """Hi Yuvan,

Following up on E2E testing agents: a persistent bottleneck in agent-driven QA is handling dynamic DOM hydration and transient network flickers without creating flaky tests. We resolved this in our benchmarks by enforcing state assertions rather than timing sleeps.

I'd be glad to build out custom test generators or verifier suites on a trial contract.

Still open to a brief chat?

Best,
Avnish""",
        "fu2_subject": "Re: autonomous E2E testing agents + adversarial pytest verifiers",
        "fu2_body": """Hi Yuvan,

I'll assume you're heads-down driving Autosana's roadmap, so I won't follow up again.

Feel free to keep my details handy for autonomous testing and benchmark engineering:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Wishing Autosana huge success!

Best,
Avnish"""
    },
    {
        "id": 18,
        "company_name": "Midplane",
        "batch_or_stage": "YC",
        "location": "San Francisco, US (Remote)",
        "domain": "midplane.ai",
        "founder_name": "Dustin Lange",
        "founder_role": "Co-founder & CEO",
        "verified_email": "dustin@midplane.ai",
        "target_role": "AI Security & Policy Enforcement Engineer Intern",
        "hook_angle": "Database guardrails for coding agents, SQL AST parsing, and zero-downtime migrations",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "coding agent database security + SQL AST policy enforcement",
        "initial_body": """Hi Dustin,

Midplane's security layer sitting between AI coding agents and databases is brilliant — letting Cursor or Claude touch databases without strict query parsing and audit policies is a disaster waiting to happen.

I have extensive hands-on experience with production databases and agent reliability: I executed a 5-phase zero-downtime PostgreSQL migration for Realty Pandit CRM and author adversarial pytest verifiers for agentic benchmarks at Caudal AI.

I’d love to help Midplane as an AI Infrastructure / Policy intern or trial contractor building SQL AST policy parsers, agent sandbox adapters, or database mock environments.

Do you have 10 minutes for a brief call this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: coding agent database security + SQL AST policy enforcement",
        "fu1_body": """Hi Dustin,

Quick note on agent database interactions: beyond destructive DROP/DELETE calls, agents often execute unindexed table scans or un-paginated queries that lock production tables. Building query cost estimators into the policy proxy provides a vital safeguard.

Happy to build policy rules or benchmark suites for Midplane on a 2-week trial sprint.

Worth 10 minutes?

Best,
Avnish""",
        "fu2_subject": "Re: coding agent database security + SQL AST policy enforcement",
        "fu2_body": """Hi Dustin,

Figure your plate is completely full with Midplane, so I'll leave this here.

If you ever need an engineer who understands database systems, migration safety, and agent verification:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

Rooting for Midplane's growth!

Best,
Avnish"""
    },
    {
        "id": 19,
        "company_name": "Maihem",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "tekton-dynamics.com",
        "founder_name": "Max Ahrens",
        "founder_role": "Co-Founder",
        "verified_email": "max@tekton-dynamics.com",
        "target_role": "AI Agent Simulation & Testing Engineer",
        "hook_angle": "Adversarial simulations, agent trajectory grading, and Docker test beds",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "adversarial agent simulations + Dockerized test harnesses",
        "initial_body": """Hi Max,

Loving Maihem's mission to make AI agents reliable through automated adversarial testing and simulation — simulating edge cases before deployment is essential for production agents.

At Caudal AI, I author contamination-resistant benchmark tasks for frontier coding agents in Dockerized shell environments. My primary focus is designing adversarial edge cases and pytest verifiers that catch hallucinated fixes and logic loops across complex trajectories.

I’d love to join Maihem as an AI Testing / Simulation Engineer intern or contractor to build synthetic user personas, adversarial prompt test beds, or verifier suites.

Open to a 10-minute chat this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: adversarial agent simulations + Dockerized test harnesses",
        "fu1_body": """Hi Max,

Quick follow-up: in agent stress-testing, static jailbreaks are easy to detect, but multi-turn social engineering (e.g. slowly coercing an agent to bypass authorization) requires stateful conversational simulation.

At Caudal AI, we designed adversarial verifiers that monitor trajectory drift across multi-step interactions.

I’d be glad to author custom test scenarios for Maihem on a trial sprint.

Free for a brief chat?

Best,
Avnish""",
        "fu2_subject": "Re: adversarial agent simulations + Dockerized test harnesses",
        "fu2_body": """Hi Max,

I'll assume you're 100% focused on product execution at Maihem, so I won't follow up again.

Keep my details on file if you ever need an engineer who lives and breathes adversarial agent testing:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

All the best with Maihem!

Best,
Avnish"""
    },
    {
        "id": 20,
        "company_name": "Marr Labs",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "marrlabs.com",
        "founder_name": "Dave Grannan",
        "founder_role": "Co-Founder & CEO",
        "verified_email": "dave@marrlabs.com",
        "target_role": "Conversational AI Integration / FDE Intern",
        "hook_angle": "Voice agent workflows, deterministic dialog trees, and telemetry monitoring",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "conversational voice agents + deterministic state guards",
        "initial_body": """Hi Dave,

Exciting to see Marr Labs pushing the frontier of human-like conversational voice agents for enterprise phone operations.

When handling live customer calls, models must navigate interruptions and ambient noise without hallucinating commitments. In my recent project Realty Pandit CRM, I deployed an agent handling 4,000+ customer deals using deterministic state trees so rates and schedules were strictly regulated. At Caudal AI, I author adversarial verifiers for autonomous agents.

I’d love to join Marr Labs as a Junior Solutions Engineer / FDE intern to help build customer telephony connectors, dialog state verifiers, or call telemetry analytics.

Open to a 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: conversational voice agents + deterministic state guards",
        "fu1_body": """Hi Dave,

Following up on voice agent reliability: customer barge-ins and mid-sentence corrections often corrupt context buffers. Implementing transactional rollback nodes in our dialog pipeline helped maintain conversational continuity without dropped variables.

Happy to build customer integration adapters or eval suites on a 2-week trial sprint.

Worth a brief call?

Best,
Avnish""",
        "fu2_subject": "Re: conversational voice agents + deterministic state guards",
        "fu2_body": """Hi Dave,

Figure you have high-priority operational demands scaling Marr Labs, so I'll wrap up here.

If you ever need an engineer for conversational state pipelines and agent integrations:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

Wishing you and Marr Labs tremendous success!

Best,
Avnish"""
    },
    {
        "id": 21,
        "company_name": "Topo",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "topo.io",
        "founder_name": "Dan Elkaïm",
        "founder_role": "Co-founder & CEO",
        "verified_email": "dan@topo.io",
        "target_role": "Forward Deployed Engineer (FDE) / Outbound Agent Integrations",
        "hook_angle": "Outbound sales agents, CRM data pipelines, and conversion analytics",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "outbound sales agents + CRM data state pipelines",
        "initial_body": """Hi Dan,

Love Topo's vision of building AI agents that reproduce top-performing SDR behaviors by grounding in CRM data and call transcripts.

I built and shipped Realty Pandit CRM — deploying an agent managing 4,000+ active deals with deterministic qualification trees, alongside an analytics cockpit tracking conversion funnels and an INR 130+ Cr pipeline forecast. At Caudal AI, I write adversarial pytest verifiers for autonomous agents.

I’d love to join Topo as a Junior FDE or contract engineer building customer CRM integrations, data normalization pipelines, or outbound qualification adapters.

Open to a brief 10-minute chat this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: outbound sales agents + CRM data state pipelines",
        "fu1_body": """Hi Dan,

Quick note on SDR agent grounding: when pulling signals from heterogeneous CRM custom fields, subtle schema discrepancies often derail dynamic message generation. Building pre-flight normalization adapters reduced deal drop-off significantly in our deployment.

I'd be glad to prototype customer CRM connectors or outbound test suites on a trial contract.

Still open to a quick call?

Best,
Avnish""",
        "fu2_subject": "Re: outbound sales agents + CRM data state pipelines",
        "fu2_body": """Hi Dan,

I'll assume you're laser-focused on Topo's expansion, so I won't follow up again.

If you ever need an FDE who has built production sales agents and CRM pipelines:
- WhatsApp: +91 7982252971
- GitHub: [GitHub Link]

Best of luck scaling Topo!

Best,
Avnish"""
    },
    {
        "id": 22,
        "company_name": "Domu Technology",
        "batch_or_stage": "YC S24",
        "location": "San Francisco, US (Remote)",
        "domain": "domu.ai",
        "founder_name": "Nick Diaz",
        "founder_role": "Co-founder & CEO",
        "verified_email": "nick@domu.ai",
        "target_role": "AI Workflow & Compliance Engineer Contractor",
        "hook_angle": "Automated collections workflows, compliance guardrails, and transactional safety",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "collections agent pipelines + transactional compliance guardrails",
        "initial_body": """Hi Nick,

Incredible momentum with Domu automating collections interactions across calls, texts, and emails for major financial institutions.

In high-stakes debt servicing, models cannot deviate from compliance guidelines. For Realty Pandit CRM, I deployed an agent across 4,000+ active deals with deterministic state machines ensuring the model never improvised pricing or terms. At Caudal AI, I author adversarial verifiers testing autonomous agent execution.

I’d love to assist Domu as a Junior FDE or contract engineer building banking CRM connectors, regulatory verification layers, or omnichannel message adapters.

Do you have 10 minutes for a brief chat this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: collections agent pipelines + transactional compliance guardrails",
        "fu1_body": """Hi Nick,

Following up on collections compliance: debtor dispute handling requires immediate branching to human escalation without looping. Enforcing deterministic decision trees allowed our agents to qualify complex customer objections safely.

I'd be thrilled to build integration connectors or compliance test verifiers on a 2-week trial sprint.

Worth 10 minutes?

Best,
Avnish""",
        "fu2_subject": "Re: collections agent pipelines + transactional compliance guardrails",
        "fu2_body": """Hi Nick,

Assuming you're flat out scaling Domu's enterprise pilots, so I'll leave this here.

Feel free to keep my info on file if you need an engineer for compliance-first agent pipelines:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

All the best with Domu!

Best,
Avnish"""
    },
    {
        "id": 23,
        "company_name": "Basepilot",
        "batch_or_stage": "YC W24",
        "location": "San Francisco, US (Remote)",
        "domain": "basepilot.com",
        "founder_name": "Ken Hendricks",
        "founder_role": "Co-Founder",
        "verified_email": "ken@basepilot.com",
        "target_role": "AI Browser Automation & Integration Contractor",
        "hook_angle": "Browser-based automation, claims processing workflows, and DOM state verification",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "browser-based back-office agents + DOM state verifiers",
        "initial_body": """Hi Ken,

Loving Basepilot's approach to browser-based AI coworkers for insurance and back-office operations — automating legacy web portals without APIs is where the highest operational ROI lies.

At Caudal AI, I author Dockerized shell environments and adversarial pytest verifiers for autonomous agents where models must inspect interfaces, run commands, and debug runtime failures. At Klimashift, I automated operations dashboards and analyzed 1 Hz telemetry.

I’d love to join Basepilot as an Automation / Integration contractor building portal crawlers, claims processing workflows, or execution verification checks.

Open to a brief 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: browser-based back-office agents + DOM state verifiers",
        "fu1_body": """Hi Ken,

Quick thought on browser automation: legacy insurance portals frequently present dynamic iframes and modal popups that derail autonomous agents. In our benchmark tasks, we built state verifiers that inspect DOM mutations to confirm successful payload submission.

Happy to build custom portal connectors or verification checks on a trial sprint.

Free for a quick chat?

Best,
Avnish""",
        "fu2_subject": "Re: browser-based back-office agents + DOM state verifiers",
        "fu2_body": """Hi Ken,

Figure you're fully occupied expanding Basepilot's customer deployments, so I'll bow out.

If you ever need an engineer for browser automation, agent verifiers, and portal integrations:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

Rooting for Basepilot's success!

Best,
Avnish"""
    },
    {
        "id": 24,
        "company_name": "Bluejay",
        "batch_or_stage": "YC S25",
        "location": "San Francisco, US (Remote)",
        "domain": "getbluejay.ai",
        "founder_name": "Rohan Vasishth",
        "founder_role": "Co-founder & CEO",
        "verified_email": "rohan@getbluejay.ai",
        "target_role": "AI Voice/Text Agent QA & Benchmark Engineer Intern",
        "hook_angle": "Synthetic customer stress-testing, diverse accents/noise, and verifier design",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "stress-testing voice agents with synthetic personas + pytest verifiers",
        "initial_body": """Hi Rohan,

Saw Bluejay's launch to engineer trust into AI interactions by stress-testing voice and text agents with synthetic customers across diverse accents, emotional tones, and noise conditions — this is the exact testing layer agent deployments need.

At Caudal AI, I author contamination-resistant benchmark tasks and adversarial pytest verifiers for frontier agents in Docker environments. I focus on reducing false passes/failures and grading trajectories against strict rubrics. Previously, I shipped a production WhatsApp sales agent running 4,000+ live deals.

I’d love to join Bluejay as an AI QA / Benchmark Engineer intern or trial contractor building synthetic customer generators, audio edge-case benchmarks, or regression harnesses.

Do you have 10 minutes for a brief call this Thursday?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: stress-testing voice agents with synthetic personas + pytest verifiers",
        "fu1_body": """Hi Rohan,

Following up on synthetic customer stress-testing: audio latency and rapid topic-switching are where voice agents experience the highest failure rate. In our benchmark design, adversarial interruption tests revealed critical logic leaks that static transcript evals missed.

I'd be glad to build synthetic test suites or benchmark runners on a 2-week trial sprint.

Worth 10 minutes this week?

Best,
Avnish""",
        "fu2_subject": "Re: stress-testing voice agents with synthetic personas + pytest verifiers",
        "fu2_body": """Hi Rohan,

I'll assume you're completely absorbed in building Bluejay, so I won't follow up again.

Feel free to keep my details handy for agent testing and benchmark engineering:
- GitHub: [GitHub Link]
- WhatsApp / Phone: +91 7982252971

All the best with Bluejay!

Best,
Avnish"""
    },
    {
        "id": 25,
        "company_name": "Lucidya",
        "batch_or_stage": "Growth / Funded",
        "location": "Riyadh, Saudi Arabia",
        "domain": "lucidya.com",
        "founder_name": "Abdullah Asiri",
        "founder_role": "Co-founder & CEO",
        "verified_email": "asiri@lucidya.com",
        "target_role": "AI Solutions / Customer Experience Agent Contractor",
        "hook_angle": "Enterprise CX agents, Arabic NLP, customer telemetry, and explainable rule engines",
        "status": "Ready to Send",
        "scheduled_initial": "2026-10-06",
        "scheduled_fu1": "2026-10-09",
        "scheduled_fu2": "2026-10-14",
        "initial_subject": "enterprise CX agents + explainable telemetry rule engines",
        "initial_body": """Hi Abdullah,

Impressive seeing Lucidya lead the charge in Arabic-first autonomous customer experience agents across the Middle East.

I build production-grade conversational and telemetry systems: for Realty Pandit CRM, I deployed an agent handling 4,000+ live customer deals using deterministic state trees so the model never improvised availability or pricing. At Klimashift, I developed fault diagnostics on 1 Hz telemetry and built ROI models for enterprise pitches.

I’d love to assist Lucidya as an AI Solutions Engineer / Integration contractor building enterprise CX connectors, customer feedback parsers, or reliability verifiers.

Would you be open to a 10-minute sync this week?

Best,
Avnish Rana
GitHub: https://github.com/ | LinkedIn: https://linkedin.com/in/ | +91 7982252971""",
        "fu1_subject": "Re: enterprise CX agents + explainable telemetry rule engines",
        "fu1_body": """Hi Abdullah,

Quick note on enterprise CX agents: managing customer sentiment shifts across multilingual interactions requires coupling LLM dialog with deterministic business rules (like our 14-rule explainability engine) to prevent erratic escalation.

I’d welcome the chance to prototype customer integration connectors or evaluation test beds on a trial sprint.

Do you have 10 minutes Thursday?

Best,
Avnish""",
        "fu2_subject": "Re: enterprise CX agents + explainable telemetry rule engines",
        "fu2_body": """Hi Abdullah,

Assuming you're fully occupied with Lucidya's regional expansion, so I'll wrap up here.

If you ever need an engineer who merges conversational agent pipelines with strict, explainable rule engines:
- WhatsApp / Phone: +91 7982252971
- GitHub: [GitHub Link]

Wishing Lucidya tremendous continued growth across the Kingdom and GCC!

Best,
Avnish"""
    }
]

def main():
    target_json = os.path.join(os.path.dirname(__file__), "curated_leads.json")
    with open(target_json, "w", encoding="utf-8") as f:
        json.dump(LEADS, f, indent=2)
    print(f"✅ Successfully wrote {len(LEADS)} comprehensive campaigns to {target_json}")

if __name__ == "__main__":
    main()
