import json

with open("generate_outreach.py", "r") as f:
    content = f.read()

# Make sure generate_outreach.py list shows the dispatch time
old_table_header = "'#':<3} | {'Company':<15} | {'Stage':<14} | {'Founder':<22} | {'Email':<28} | {'Status'}"
new_table_header = "'#':<3} | {'Company':<15} | {'Founder':<20} | {'Email':<26} | {'Best Send Time (IST)':<22} | {'Status'}"

old_row = "print(f\"[{lead['id']:>2}] {lead['company_name']:<15} | {lead['batch_or_stage']:<14} | {lead['founder_name']:<22} | {lead['verified_email']:<28} | {lead['status']}\")"
new_row = "print(f\"[{lead['id']:>2}] {lead['company_name']:<15} | {lead['founder_name']:<20} | {lead['verified_email']:<26} | {lead.get('recommended_send_time_ist', '9:30 PM IST'):<22} | {lead['status']}\")"

content = content.replace(old_table_header, new_table_header)
content = content.replace(old_row, new_row)

with open("generate_outreach.py", "w") as f:
    f.write(content)

