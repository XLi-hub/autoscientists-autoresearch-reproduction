import os, json, requests, yaml, sys
FOCUS_ROOT='/root/autodl-tmp/ar_20261024'
AGENT_NAME='ar_20261024_gpu3'
API=os.environ.get('CLAWINSTITUTE_API','http://localhost:3000/api/v1')
creds=json.load(open(f'{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json'))
HEADERS={'Authorization':f"Bearer {creds['api_key']}",'Content-Type':'application/json','X-Agent-Name':AGENT_NAME}
MAIN_WS_ID=open(f'{FOCUS_ROOT}/WORKSPACE_ID').read().strip()
WORKSHOP=open(f'{FOCUS_ROOT}/WORKSHOP_NAME').read().strip()
TEAM='capacity'
TEAM_WS_ID='d7c6f814-aab0-4029-a887-04345d274f9b'
def pf(resp):
    c=resp.get('content','')
    parts=c.split('---')
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}
def get(ws,path):
    return requests.get(f'{API}/workspaces/{ws}/files/{path}',headers=HEADERS,timeout=30).json()
def ls(ws):
    return requests.get(f'{API}/workspaces/{ws}/files',headers=HEADERS,timeout=30).json().get('files',[])
