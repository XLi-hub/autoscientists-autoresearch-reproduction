import json, os, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
recent=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=40",headers=HEADERS).json().get("data",[])
print("N posts:",len(recent))
for p in recent:
    print(f"{p.get('createdAt','?')[:19]} | {p['id'][:8]} | {p.get('title','')[:110]} | {(p.get('author') or {}).get('name') if isinstance(p.get('author'),dict) else p.get('author')} | comments={p.get('commentCount', '?')}")
