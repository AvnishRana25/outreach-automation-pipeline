#!/usr/bin/env python3
"""Explicit cloud setup; every command is checked and credentials use stdin."""
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
import db

REPO_NAME='AvnishRana25/outreach-automation-pipeline'
CREDS_FILE=Path.home()/'.google_workspace_mcp/credentials/avnishrana797@gmail.com.json'


def run_cmd(cmd,check=True,input=None):
    args=shlex.split(cmd) if isinstance(cmd,str) else cmd
    result=subprocess.run(args,cwd=db.ROOT,input=input,capture_output=True,text=True,timeout=120)
    success=result.returncode==0
    if check and not success:
        raise RuntimeError(f'{args[0]} command failed (exit {result.returncode}); setup stopped')
    return success,result.stdout if success else result.stderr


def setup():
    credentials=json.loads(CREDS_FILE.read_text())
    names={'GMAIL_CLIENT_ID':'client_id','GMAIL_CLIENT_SECRET':'client_secret','GMAIL_REFRESH_TOKEN':'refresh_token'}
    if not all(credentials.get(key) for key in names.values()): raise ValueError('Missing Gmail credential fields')
    _,root=run_cmd(['git','rev-parse','--show-toplevel'])
    if Path(root.strip()).resolve()!=db.ROOT: raise ValueError('Setup must run in the outreach repository')
    _,branch=run_cmd(['git','branch','--show-current'])
    if branch.strip()!='main': raise ValueError('Switch to main before cloud setup')
    run_cmd(['gh','api','user'])
    exists,_=run_cmd(['gh','repo','view',REPO_NAME],check=False)
    if not exists: run_cmd(['gh','repo','create',REPO_NAME,'--private'])
    _,visibility=run_cmd(['gh','repo','view',REPO_NAME,'--json','visibility'])
    if json.loads(visibility).get('visibility')!='PRIVATE':
        raise ValueError('Campaign data requires a private repository')
    has_remote,remote=run_cmd(['git','remote','get-url','origin'],check=False)
    if has_remote:
        allowed={f'https://github.com/{REPO_NAME}',f'https://github.com/{REPO_NAME}.git',f'git@github.com:{REPO_NAME}.git',f'ssh://git@github.com/{REPO_NAME}.git'}
        if remote.strip().lower() not in {url.lower() for url in allowed}: raise ValueError('Existing origin points to a different repository')
    else: run_cmd(['git','remote','add','origin',f'https://github.com/{REPO_NAME}.git'])
    files=[p.name for p in db.ROOT.glob('*.py')]+['.github/workflows/outreach_pipeline.yml','.gitignore','README.md','outreach.db','curated_leads.json','leads_tracker.csv','index.html']
    run_cmd(['git','add','--',*files])
    clean,_=run_cmd(['git','diff','--cached','--quiet'],check=False)
    if not clean: run_cmd(['git','commit','-m','Repair outreach campaign reliability'])
    for name,key in names.items(): run_cmd(['gh','secret','set',name,'--repo',REPO_NAME],input=credentials[key])
    for name in ('NTFY_TOPIC','NTFY_TOKEN','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID'):
        if os.getenv(name): run_cmd(['gh','secret','set',name,'--repo',REPO_NAME],input=os.environ[name])
    run_cmd(['git','push','-u','origin','main'])
    print(f'Cloud setup completed: https://github.com/{REPO_NAME}')
    return True


if __name__=='__main__':
    try: setup()
    except Exception as exc:
        print(f'Setup failed: {type(exc).__name__}',file=sys.stderr)
        sys.exit(1)
