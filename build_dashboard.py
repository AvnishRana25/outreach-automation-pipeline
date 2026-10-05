#!/usr/bin/env python3
"""
Builds an ultra-modern, aesthetic dashboard for Avnish's Outreach Engine.
Self-contained single-page application with Tailwind CSS and Lucide icons.
"""

import json
import os

LEADS_FILE = os.path.join(os.path.dirname(__file__), "curated_leads.json")
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "index.html")

with open(LEADS_FILE, "r", encoding="utf-8") as f:
    leads = json.load(f)

leads_json_str = json.dumps(leads)

html_template = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Avnish Rana | AI Outreach Command Center</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#f0fdf4',
              500: '#10b981',
              600: '#059669',
              900: '#064e3b',
            }},
            darkBg: '#090d16',
            cardBg: '#111827',
            cardBorder: '#1f2937',
            accentViolet: '#8b5cf6',
            accentCyan: '#06b6d4',
          }},
          fontFamily: {{
            sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
          }}
        }}
      }}
    }}
  </script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #090d16;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #374151;
      border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: #4b5563;
    }}
    .glass-card {{
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .glow-effect {{
      box-shadow: 0 0 25px -5px rgba(16, 185, 129, 0.15);
    }}
  </style>
</head>
<body class="bg-darkBg text-slate-100 min-h-screen font-sans antialiased selection:bg-brand-500 selection:text-white">

  <!-- Top Navigation Bar -->
  <nav class="sticky top-0 z-40 border-b border-gray-800 bg-[#090d16]/80 backdrop-blur-md px-6 py-4">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-500 to-accentViolet flex items-center justify-center shadow-lg shadow-brand-500/20">
          <i data-lucide="send" class="w-5 h-5 text-white"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-lg font-bold tracking-tight text-white">Avnish Rana</h1>
            <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-brand-500/10 text-brand-500 border border-brand-500/20 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse"></span> 25 Drafts Live
            </span>
          </div>
          <p class="text-xs text-gray-400">Autonomous Cold Outreach & Junior FDE / AI Evals Pipeline</p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <a href="https://drive.google.com/file/d/1ekE5qIvlxSTAbdRzmktkMarLCAUYklWW/view?usp=sharing" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800/80 hover:bg-gray-700 text-gray-200 border border-gray-700 flex items-center gap-1.5 transition">
          <i data-lucide="file-text" class="w-3.5 h-3.5 text-brand-500"></i> Resume
        </a>
        <a href="https://github.com/AvnishRana25" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800/80 hover:bg-gray-700 text-gray-200 border border-gray-700 flex items-center gap-1.5 transition">
          <i data-lucide="github" class="w-3.5 h-3.5 text-accentViolet"></i> GitHub
        </a>
        <a href="https://www.linkedin.com/in/avnish-rana-83523b2a3/" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-800/80 hover:bg-gray-700 text-gray-200 border border-gray-700 flex items-center gap-1.5 transition">
          <i data-lucide="linkedin" class="w-3.5 h-3.5 text-accentCyan"></i> LinkedIn
        </a>
        <a href="https://mail.google.com/mail/u/0/#drafts" target="_blank" class="px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white shadow-md shadow-brand-500/20 flex items-center gap-1.5 transition ml-2">
          <i data-lucide="external-link" class="w-3.5 h-3.5"></i> Open Gmail Drafts
        </a>
      </div>
    </div>
  </nav>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">

    <!-- KPI Metric Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="glass-card p-5 rounded-2xl glow-effect">
        <div class="flex items-center justify-between text-gray-400 mb-2">
          <span class="text-xs font-medium uppercase tracking-wider">Active Gmail Drafts</span>
          <div class="p-2 rounded-lg bg-brand-500/10 text-brand-500">
            <i data-lucide="mail-check" class="w-4 h-4"></i>
          </div>
        </div>
        <div class="text-3xl font-extrabold text-white">25</div>
        <p class="text-xs text-brand-400 mt-1 flex items-center gap-1">
          <i data-lucide="check" class="w-3 h-3"></i> Formatted & Ready to Send
        </p>
      </div>

      <div class="glass-card p-5 rounded-2xl">
        <div class="flex items-center justify-between text-gray-400 mb-2">
          <span class="text-xs font-medium uppercase tracking-wider">Geographic Hubs</span>
          <div class="p-2 rounded-lg bg-accentCyan/10 text-accentCyan">
            <i data-lucide="globe" class="w-4 h-4"></i>
          </div>
        </div>
        <div class="text-3xl font-extrabold text-white">4 Regions</div>
        <p class="text-xs text-gray-400 mt-1">US (SF), UK (London), Gulf, India</p>
      </div>

      <div class="glass-card p-5 rounded-2xl">
        <div class="flex items-center justify-between text-gray-400 mb-2">
          <span class="text-xs font-medium uppercase tracking-wider">Deliverability Score</span>
          <div class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <i data-lucide="shield-check" class="w-4 h-4"></i>
          </div>
        </div>
        <div class="text-3xl font-extrabold text-white">100%</div>
        <p class="text-xs text-emerald-400 mt-1 flex items-center gap-1">
          <i data-lucide="check-circle" class="w-3 h-3"></i> MX & SMTP Verified
        </p>
      </div>

      <div class="glass-card p-5 rounded-2xl">
        <div class="flex items-center justify-between text-gray-400 mb-2">
          <span class="text-xs font-medium uppercase tracking-wider">Target Role Focus</span>
          <div class="p-2 rounded-lg bg-accentViolet/10 text-accentViolet">
            <i data-lucide="cpu" class="w-4 h-4"></i>
          </div>
        </div>
        <div class="text-3xl font-extrabold text-white">Jr. FDE & Evals</div>
        <p class="text-xs text-accentViolet mt-1">High conversion vs generic SDE</p>
      </div>
    </div>

    <!-- Timezone Schedule Banner -->
    <div class="glass-card p-6 rounded-2xl border-l-4 border-l-brand-500">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <i data-lucide="clock" class="w-5 h-5 text-brand-500"></i>
            <h2 class="text-base font-bold text-white">Timezone Dispatch Windows (Tuesday, Oct 6)</h2>
          </div>
          <p class="text-xs text-gray-400 mt-1">Emails are timed to hit founders' inboxes during their local morning window (9:00 AM – 10:00 AM).</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="px-3 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 border border-gray-700">
            🇮🇳 <strong>India (4)</strong>: 9:30 AM IST
          </span>
          <span class="px-3 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 border border-gray-700">
            🇸🇦 <strong>Gulf (2)</strong>: 11:00 AM IST
          </span>
          <span class="px-3 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 border border-gray-700">
            🇬🇧 <strong>UK/EU (2)</strong>: 1:00 PM IST
          </span>
          <span class="px-3 py-1.5 rounded-lg bg-gray-800 text-xs text-gray-300 border border-gray-700">
            🇺🇸 <strong>US West (17)</strong>: 9:30 PM IST
          </span>
        </div>
      </div>
    </div>

    <!-- Strategy Accordion -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="glass-card p-5 rounded-xl border border-gray-800">
        <div class="flex items-center gap-2 text-brand-400 font-semibold text-sm mb-2">
          <i data-lucide="shield" class="w-4 h-4"></i> Superpower 1: AI Evals
        </div>
        <p class="text-xs text-gray-300 leading-relaxed">
          <strong>Caudal AI</strong>: Authoring Dockerized benchmarks for frontier coding agents, adversarial pytest verifiers, and rubric-based trajectory grading.
        </p>
      </div>

      <div class="glass-card p-5 rounded-xl border border-gray-800">
        <div class="flex items-center gap-2 text-accentViolet font-semibold text-sm mb-2">
          <i data-lucide="message-square" class="w-4 h-4"></i> Superpower 2: Agent Systems
        </div>
        <p class="text-xs text-gray-300 leading-relaxed">
          <strong>Realty Pandit CRM</strong>: Shipped WhatsApp agent managing 4,000+ live deals using deterministic trees so the LLM never improvises deal pricing.
        </p>
      </div>

      <div class="glass-card p-5 rounded-xl border border-gray-800">
        <div class="flex items-center gap-2 text-accentCyan font-semibold text-sm mb-2">
          <i data-lucide="line-chart" class="w-4 h-4"></i> Superpower 3: Commercial ROI
        </div>
        <p class="text-xs text-gray-300 leading-relaxed">
          <strong>Klimashift</strong>: 1 Hz telemetry diagnostics, physics simulators, and commercial ROI models used directly in live B2B client pitches.
        </p>
      </div>
    </div>

    <!-- Leads Directory Section -->
    <div class="space-y-4">
      <!-- Search & Filters -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-bold text-white flex items-center gap-2">
            <span>The 25 Curated Outreach Campaigns</span>
            <span class="text-xs font-medium text-gray-400 px-2 py-0.5 rounded-full bg-gray-800" id="resultsCount">25 Startups</span>
          </h2>
          <p class="text-xs text-gray-400">Click any row to preview full initial email, follow-up 1, and follow-up 2.</p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Search Input -->
          <div class="relative">
            <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-3 top-2.5"></i>
            <input type="text" id="searchInput" placeholder="Search startup, founder, role..." class="bg-gray-900 border border-gray-700 text-xs rounded-xl pl-9 pr-4 py-2 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-500 w-64 transition">
          </div>

          <!-- Region Filter -->
          <select id="regionFilter" class="bg-gray-900 border border-gray-700 text-xs rounded-xl px-3 py-2 text-gray-200 focus:outline-none focus:border-brand-500 transition">
            <option value="ALL">All Geographies</option>
            <option value="US">🇺🇸 US (Silicon Valley)</option>
            <option value="India">🇮🇳 India</option>
            <option value="Gulf">🇸🇦 Middle East</option>
            <option value="Europe">🇬🇧/🇪🇺 UK & Europe</option>
          </select>
        </div>
      </div>

      <!-- Leads Grid / Table -->
      <div class="glass-card rounded-2xl overflow-hidden border border-gray-800">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-gray-300">
            <thead class="bg-gray-900/90 text-gray-400 uppercase tracking-wider text-[11px] border-b border-gray-800">
              <tr>
                <th class="py-3.5 px-4 font-semibold">#</th>
                <th class="py-3.5 px-4 font-semibold">Company & Stage</th>
                <th class="py-3.5 px-4 font-semibold">Founder & Email</th>
                <th class="py-3.5 px-4 font-semibold">Target Role</th>
                <th class="py-3.5 px-4 font-semibold">Best Send Time (IST)</th>
                <th class="py-3.5 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody id="leadsTableBody" class="divide-y divide-gray-800/60">
              <!-- Rendered via JS -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </main>

  <!-- Modal / Drawer for Viewing Email Sequence -->
  <div id="emailModal" class="fixed inset-0 z-50 hidden bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-[#111827] border border-gray-700 w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
      
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/60">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 rounded-lg bg-brand-500/10 text-brand-500 flex items-center justify-center font-bold text-sm" id="modalCompanyInitial">
            H
          </div>
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2" id="modalTitle">
              Company Name
            </h3>
            <p class="text-xs text-gray-400" id="modalSubtitle">Founder Name &bull; Email</p>
          </div>
        </div>
        <button onclick="closeModal()" class="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-800 transition">
          <i data-lucide="x" class="w-5 h-5"></i>
        </button>
      </div>

      <!-- Sequence Steps Tab Navigation -->
      <div class="px-6 pt-3 border-b border-gray-800 flex space-x-4 text-xs font-medium bg-gray-900/30">
        <button onclick="switchTab('step1')" id="tabStep1" class="pb-3 border-b-2 border-brand-500 text-brand-400 font-semibold flex items-center gap-1.5">
          <i data-lucide="send" class="w-3.5 h-3.5"></i> Initial Email (Day 0)
        </button>
        <button onclick="switchTab('step2')" id="tabStep2" class="pb-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
          <i data-lucide="rotate-cw" class="w-3.5 h-3.5"></i> Follow-Up 1 (+3 Days)
        </button>
        <button onclick="switchTab('step3')" id="tabStep3" class="pb-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
          <i data-lucide="door-open" class="w-3.5 h-3.5"></i> Follow-Up 2 (+7 Days Breakup)
        </button>
      </div>

      <!-- Modal Body (Email Draft Copy) -->
      <div class="p-6 overflow-y-auto space-y-4 text-xs text-gray-200 leading-relaxed font-mono bg-[#0b0f19]">
        <div class="p-3 bg-gray-900/90 rounded-xl border border-gray-800 flex items-center justify-between">
          <div class="space-y-1">
            <div class="text-gray-400 text-[11px]">SUBJECT:</div>
            <div class="font-bold text-white text-xs font-sans" id="modalSubject">Subject line here</div>
          </div>
          <button onclick="copySubject()" class="px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-sans flex items-center gap-1 transition">
            <i data-lucide="copy" class="w-3 h-3"></i> Copy
          </button>
        </div>

        <div class="p-4 bg-gray-900/40 rounded-xl border border-gray-800/80 relative">
          <button onclick="copyBody()" class="absolute right-3 top-3 px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-sans flex items-center gap-1 transition">
            <i data-lucide="copy" class="w-3 h-3"></i> Copy Body
          </button>
          <pre class="whitespace-pre-wrap font-sans text-xs text-gray-200 leading-relaxed" id="modalBodyText">Email body here...</pre>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="px-6 py-3 border-t border-gray-800 bg-gray-900/60 flex items-center justify-between text-xs">
        <span class="text-gray-400 flex items-center gap-1.5">
          <i data-lucide="clock" class="w-3.5 h-3.5 text-brand-500"></i> Best send window: <strong class="text-gray-200" id="modalSendTime">9:30 PM IST</strong>
        </span>
        <div class="flex items-center gap-2">
          <button onclick="closeModal()" class="px-4 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition">Close</button>
          <a href="https://mail.google.com/mail/u/0/#drafts" target="_blank" class="px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium flex items-center gap-1.5 transition">
            <i data-lucide="external-link" class="w-3.5 h-3.5"></i> Open in Gmail
          </a>
        </div>
      </div>

    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 hidden bg-brand-600 text-white px-4 py-2.5 rounded-xl shadow-lg shadow-brand-500/20 text-xs font-medium flex items-center gap-2 transition transform translate-y-2">
    <i data-lucide="check-circle-2" class="w-4 h-4"></i>
    <span id="toastMsg">Copied to clipboard!</span>
  </div>

  <!-- Embedded Dataset -->
  <script>
    const leadsData = {leads_json_str};
    let currentSelectedLead = null;
    let currentStep = 'step1';

    function renderTable(data) {{
      const tbody = document.getElementById('leadsTableBody');
      tbody.innerHTML = '';

      if (data.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-gray-500">No matching outreach campaigns found.</td></tr>`;
        document.getElementById('resultsCount').innerText = '0 Startups';
        return;
      }}

      document.getElementById('resultsCount').innerText = `${{data.length}} Startups`;

      data.forEach((lead) => {{
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40 transition cursor-pointer group';
        tr.onclick = (e) => {{
          if (!e.target.closest('button') && !e.target.closest('a')) {{
            openModal(lead.id);
          }}
        }};

        tr.innerHTML = `
          <td class="py-3 px-4 text-gray-500 font-mono text-[11px]">${{lead.id}}</td>
          <td class="py-3 px-4">
            <div class="font-bold text-white group-hover:text-brand-400 transition flex items-center gap-1.5">
              ${{lead.company_name}}
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-normal border border-gray-700">${{lead.batch_or_stage}}</span>
            </div>
            <div class="text-[11px] text-gray-400">${{lead.location}}</div>
          </td>
          <td class="py-3 px-4">
            <div class="text-gray-200 font-medium">${{lead.founder_name}}</div>
            <div class="text-gray-400 font-mono text-[11px] flex items-center gap-1">
              ${{lead.verified_email}}
              <button onclick="copyText('${{lead.verified_email}}', 'Email address copied!')" class="text-gray-500 hover:text-white p-0.5 transition" title="Copy email">
                <i data-lucide="copy" class="w-3 h-3"></i>
              </button>
            </div>
          </td>
          <td class="py-3 px-4">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-accentViolet/10 text-accentViolet border border-accentViolet/20">
              ${{lead.target_role}}
            </span>
          </td>
          <td class="py-3 px-4">
            <div class="text-gray-200 font-medium">${{lead.recommended_send_time_ist}}</div>
            <div class="text-[10px] text-gray-500">${{lead.founder_local_window}}</div>
          </td>
          <td class="py-3 px-4 text-right">
            <div class="flex items-center justify-end space-x-1.5">
              <button onclick="openModal(${{lead.id}})" class="px-2.5 py-1 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white text-[11px] font-medium transition">
                View Sequence
              </button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      }});

      lucide.createIcons();
    }}

    function filterLeads() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      const region = document.getElementById('regionFilter').value;

      const filtered = leadsData.filter(l => {{
        const matchesQuery = l.company_name.toLowerCase().includes(query) ||
                             l.founder_name.toLowerCase().includes(query) ||
                             l.target_role.toLowerCase().includes(query) ||
                             l.verified_email.toLowerCase().includes(query);

        let matchesRegion = true;
        if (region === 'US') matchesRegion = l.location.includes('US') || l.location.includes('San Francisco');
        else if (region === 'India') matchesRegion = l.location.includes('Bengaluru') || l.location.includes('Mumbai');
        else if (region === 'Gulf') matchesRegion = l.location.includes('Riyadh') || l.location.includes('Dubai');
        else if (region === 'Europe') matchesRegion = l.location.includes('London') || l.location.includes('Paris') || l.location.includes('UK');

        return matchesQuery && matchesRegion;
      }});

      renderTable(filtered);
    }}

    document.getElementById('searchInput').addEventListener('input', filterLeads);
    document.getElementById('regionFilter').addEventListener('change', filterLeads);

    function openModal(leadId) {{
      const lead = leadsData.find(l => l.id === leadId);
      if (!lead) return;
      currentSelectedLead = lead;

      document.getElementById('modalTitle').innerHTML = `${{lead.company_name}} <span class="text-xs font-normal text-gray-400 px-2 py-0.5 rounded bg-gray-800">${{lead.batch_or_stage}}</span>`;
      document.getElementById('modalSubtitle').innerText = `${{lead.founder_name}} (${{lead.founder_role}}) • ${{lead.verified_email}}`;
      document.getElementById('modalCompanyInitial').innerText = lead.company_name[0];
      document.getElementById('modalSendTime').innerText = `${{lead.recommended_send_time_ist}} (${{lead.founder_local_window}})`;

      switchTab('step1');
      document.getElementById('emailModal').classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeModal() {{
      document.getElementById('emailModal').classList.add('hidden');
    }}

    function switchTab(step) {{
      currentStep = step;
      const tab1 = document.getElementById('tabStep1');
      const tab2 = document.getElementById('tabStep2');
      const tab3 = document.getElementById('tabStep3');

      [tab1, tab2, tab3].forEach(t => {{
        t.className = 'pb-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5';
      }});

      if (step === 'step1') {{
        tab1.className = 'pb-3 border-b-2 border-brand-500 text-brand-400 font-semibold flex items-center gap-1.5';
        document.getElementById('modalSubject').innerText = currentSelectedLead.initial_subject;
        document.getElementById('modalBodyText').innerText = currentSelectedLead.initial_body;
      }} else if (step === 'step2') {{
        tab2.className = 'pb-3 border-b-2 border-brand-500 text-brand-400 font-semibold flex items-center gap-1.5';
        document.getElementById('modalSubject').innerText = currentSelectedLead.fu1_subject;
        document.getElementById('modalBodyText').innerText = currentSelectedLead.fu1_body;
      }} else if (step === 'step3') {{
        tab3.className = 'pb-3 border-b-2 border-brand-500 text-brand-400 font-semibold flex items-center gap-1.5';
        document.getElementById('modalSubject').innerText = currentSelectedLead.fu2_subject;
        document.getElementById('modalBodyText').innerText = currentSelectedLead.fu2_body;
      }}
    }}

    function copySubject() {{
      const sub = document.getElementById('modalSubject').innerText;
      copyText(sub, 'Subject line copied!');
    }}

    function copyBody() {{
      const body = document.getElementById('modalBodyText').innerText;
      copyText(body, 'Email body copied!');
    }}

    function copyText(text, msg) {{
      navigator.clipboard.writeText(text).then(() => {{
        showToast(msg);
      }});
    }}

    function showToast(msg) {{
      const toast = document.getElementById('toast');
      document.getElementById('toastMsg').innerText = msg;
      toast.classList.remove('hidden');
      setTimeout(() => {{
        toast.classList.add('hidden');
      }}, 2500);
    }}

    // Close modal on Escape
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeModal();
    }});

    // Initial Render
    renderTable(leadsData);
  </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ Aesthetic dashboard generated successfully at: {OUTPUT_HTML}")
