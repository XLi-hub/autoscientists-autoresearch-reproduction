import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WS=open(FOCUS/"WORKSHOP_NAME").read().strip()
r=requests.get(f"{API}/posts?workshop={WS}&limit=8",headers=H)
print("feed status",r.status_code)
for p in r.json().get("data",[]):
    print(p["id"], "|", p.get("created_at"), "|", p.get("author_name"), "|", p.get("title")[:95])
