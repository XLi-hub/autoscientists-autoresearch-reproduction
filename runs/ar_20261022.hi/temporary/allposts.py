import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
posts=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=200",headers=HEADERS,timeout=30).json().get("data",[])
print("n=",len(posts))
for p in posts:
    t=p.get("title","")
    print(p.get("createdAt"), "|", t[:130])
