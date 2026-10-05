#!/usr/bin/env python3
"""Build an accessible, self-contained campaign snapshot from SQLite."""
import html
import json
import db

OUTPUT_HTML = str(db.ROOT / 'index.html')


def build_dashboard(output=OUTPUT_HTML, leads=None):
    leads = db.campaign_leads() if leads is None else leads
    # Escape script terminators even though values are rendered with textContent below.
    data = json.dumps(leads,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outreach campaign</title>
<style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,sans-serif;background:#0a101b;color:#e2e8f0}*{box-sizing:border-box}body{margin:0}main{max-width:1200px;margin:auto;padding:32px 20px}h1{margin:0 0 8px;font-size:30px}h2{font-size:19px}p{line-height:1.5}.muted,small{color:#a8b5c9}header,.toolbar,.actions,.tabs{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}header{margin-bottom:26px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}.card{background:#121d2e;border:1px solid #28374d;border-radius:15px;padding:20px}.metric{font-size:30px;font-weight:750;margin-top:12px}button,input,select{font:inherit;color:inherit;border:1px solid #40506a;background:#16243a;border-radius:8px;padding:9px 13px}button{cursor:pointer}button:hover{background:#223957}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid #5eead4;outline-offset:3px}a{color:#5eead4}.primary{background:#075e57}label{display:flex;gap:8px;align-items:center}input{min-width:200px}.table-wrap{margin:18px 0;overflow:auto;border:1px solid #28374d;border-radius:12px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:16px;border-bottom:1px solid #28374d}th{background:#132238;color:#a8b5c9}td small{display:block;margin-top:6px}tbody tr:last-child td{border-bottom:0}.error{color:#fda4af;font-size:12px;max-width:280px}dialog{background:#111e30;color:#e2e8f0;border:1px solid #40506a;border-radius:15px;width:min(780px,95vw);max-height:90vh;padding:24px}dialog::backdrop{background:#000b}.tabs{justify-content:flex-start;margin:22px 0}button[aria-selected=true]{background:#075e57;border-color:#5eead4}pre{font:14px/1.7 system-ui,sans-serif;white-space:pre-wrap;overflow-wrap:anywhere;background:#091422;border-radius:10px;padding:20px;margin:14px 0}#toast{position:fixed;bottom:20px;right:20px;background:#17483f;border-radius:10px;padding:14px;max-width:90vw}#toast:empty{display:none}@media(max-width:650px){.cards{grid-template-columns:repeat(2,1fr)}.toolbar{align-items:stretch}label{flex-wrap:wrap}h1{font-size:25px}main{padding:24px 12px}th,td{padding:12px}}
</style></head><body><main>
<header><div><h1>Outreach campaign</h1><p class="muted">Avnish Rana · AI agents, evaluation & business automation</p></div><a href="https://mail.google.com/mail/u/0/#drafts" target="_blank" rel="noopener noreferrer">Open Gmail</a></header>
<p class="muted">Snapshot generated <time id="exportTime">__TIME__</time>. Regenerate to see newer campaign changes.</p>
<div class="cards"><section class="card"><small>Campaign leads</small><div class="metric" id="total">0</div></section><section class="card"><small>Pending initial outreach</small><div class="metric" id="pending">0</div></section><section class="card"><small>Contacted</small><div class="metric" id="sent">0</div></section><section class="card"><small>Replies recorded</small><div class="metric" id="replies">0</div></section></div>
<p>Automatic dispatch uses each recorded timezone, weekdays 09:00–11:00. Recipient timezones inferred from company location should be reviewed for hybrid teams. Address verification is recorded only when a verified import supplies its date and source.</p>
<div class="toolbar"><h2>Campaign directory <small id="resultsCount"></small></h2><div class="actions"><label for="searchInput">Search <input id="searchInput" type="search" placeholder="Company, founder, email or role"></label><label for="regionFilter">Region <select id="regionFilter"><option value="All">All regions</option><option value="US">US</option><option value="India">India</option><option value="ME">Middle East</option><option value="EU">Europe / UK</option></select></label></div></div>
<div class="table-wrap"><table><thead><tr><th scope="col">Company</th><th scope="col">Recipient</th><th scope="col">Status</th><th scope="col">Local window</th><th scope="col">Actions</th></tr></thead><tbody id="leadsTableBody"></tbody></table></div>
</main>
<dialog id="emailModal" aria-labelledby="modalTitle"><header><div><h2 id="modalTitle"></h2><p class="muted" id="modalSubtitle"></p></div><button id="closeModal" aria-label="Close email sequence" autofocus>Close</button></header>
<div class="tabs" role="tablist" aria-label="Email sequence"><button id="tabStep1" role="tab" aria-controls="emailPanel" aria-selected="true">Initial · Day 0</button><button id="tabStep2" role="tab" aria-controls="emailPanel" aria-selected="false" tabindex="-1">Follow-up 1 · Day 3</button><button id="tabStep3" role="tab" aria-controls="emailPanel" aria-selected="false" tabindex="-1">Follow-up 2 · Day 7+</button></div>
<section id="emailPanel" role="tabpanel" aria-labelledby="tabStep1"><div class="actions"><strong id="modalSubject"></strong><button id="copySubject">Copy subject</button></div><pre id="modalBodyText"></pre><button id="copyBody">Copy body</button></section><p class="muted" id="modalSendTime"></p>
<div id="toast" role="status" aria-live="polite"></div></dialog>
<script>
const leadsData = __DATA__;
let currentSelectedLead = null;
let lastOpener = null;
let toastTimer;
const byId = id => document.getElementById(id);
const tabs = ['tabStep1','tabStep2','tabStep3'];
function showToast(text){clearTimeout(toastTimer);byId('toast').textContent=text;toastTimer=setTimeout(()=>byId('toast').textContent='',4000);}
async function copyText(text,label){try{if(!navigator.clipboard)throw new Error('Clipboard unavailable');await navigator.clipboard.writeText(text);showToast(label);}catch(error){showToast('Could not copy. Select the text and copy it manually.');}}
function cell(row,text,detail){const td=document.createElement('td');td.textContent=text || 'Not recorded';if(detail){const sub=document.createElement('small');sub.textContent=detail;td.appendChild(sub);}row.appendChild(td);return td;}
function renderTable(data){const body=byId('leadsTableBody');body.replaceChildren();byId('resultsCount').textContent=`${data.length} shown`;
if(!data.length){const row=document.createElement('tr');const td=cell(row,'No matching campaigns.');td.colSpan=5;body.appendChild(row);return;}
for(const lead of data){const tr=document.createElement('tr');cell(tr,lead.company_name,`${lead.batch_or_stage || 'Stage not recorded'} · ${lead.target_role || 'AI / Automation Engineer'}`);cell(tr,lead.founder_name,lead.verified_email);const status=cell(tr,lead.status,lead.email_verified_at ? `Verification recorded ${lead.email_verified_at}` : 'Email verification not recorded');if(lead.last_error){const error=document.createElement('p');error.className='error';error.textContent=lead.last_error;status.appendChild(error);}cell(tr,lead.recipient_timezone,'Weekdays 09:00–11:00');const td=document.createElement('td');const view=document.createElement('button');view.textContent='View sequence';view.setAttribute('aria-label',`View sequence for ${lead.company_name}`);view.addEventListener('click',()=>openModal(lead.id,view));td.appendChild(view);tr.appendChild(td);body.appendChild(tr);}}
function filterLeads(){const query=byId('searchInput').value.toLowerCase();const region=byId('regionFilter').value;renderTable(leadsData.filter(lead=>[lead.company_name,lead.founder_name,lead.target_role,lead.verified_email].some(value=>String(value || '').toLowerCase().includes(query)) && (region==='All' || lead.region_code===region)));}
function openModal(id,opener){const lead=leadsData.find(lead=>lead.id===id);if(!lead)return;currentSelectedLead=lead;lastOpener=opener;byId('modalTitle').textContent=lead.company_name;byId('modalSubtitle').textContent=`${lead.founder_name || ''} · ${lead.verified_email}`;byId('modalSendTime').textContent=`${lead.recipient_timezone}: weekdays 09:00–11:00. FU2 is at least 24 hours after FU1.`;switchTab(0);byId('emailModal').showModal();}
function switchTab(index){if(!currentSelectedLead)return;tabs.forEach((id,i)=>{byId(id).setAttribute('aria-selected',String(i===index));byId(id).tabIndex=i===index?0:-1;});byId('emailPanel').setAttribute('aria-labelledby',tabs[index]);const prefix=['initial','fu1','fu2'][index];byId('modalSubject').textContent=currentSelectedLead[prefix+'_subject'] || currentSelectedLead.initial_subject || '';byId('modalBodyText').textContent=currentSelectedLead[prefix+'_body'] || 'Email copy has not been recorded.';}
tabs.forEach((id,index)=>{byId(id).addEventListener('click',()=>switchTab(index));byId(id).addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?2:(index+(event.key==='ArrowRight'?1:2))%3;switchTab(next);byId(tabs[next]).focus();}});});
byId('closeModal').addEventListener('click',()=>byId('emailModal').close());byId('emailModal').addEventListener('close',()=>{if(lastOpener)lastOpener.focus();});
byId('copySubject').addEventListener('click',()=>copyText(byId('modalSubject').textContent,'Subject copied.'));byId('copyBody').addEventListener('click',()=>copyText(byId('modalBodyText').textContent,'Body copied.'));byId('searchInput').addEventListener('input',filterLeads);byId('regionFilter').addEventListener('change',filterLeads);
byId('total').textContent=leadsData.length;byId('pending').textContent=leadsData.filter(lead=>['DRAFTED','Drafted in Gmail','Ready to Send','INITIAL_QUEUED','INITIAL_UNCERTAIN'].includes(lead.status)).length;byId('sent').textContent=leadsData.filter(lead=>lead.sent_at).length;byId('replies').textContent=leadsData.filter(lead=>lead.status==='REPLIED').length;renderTable(leadsData);
</script></body></html>'''
    page = page.replace('__DATA__',data).replace('__TIME__',html.escape(db.utcnow()))
    db.atomic_write(output,lambda handle:handle.write(page))
    print(f'Dashboard snapshot saved: {output}')
    return page


if __name__ == '__main__':
    build_dashboard()
