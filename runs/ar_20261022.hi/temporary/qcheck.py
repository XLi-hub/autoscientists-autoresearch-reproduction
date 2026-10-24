import json, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
r=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=HEADERS,timeout=20).json()
fm=yaml.safe_load(r["content"].split("---")[1])
print("v",r["version"],"rev",fm.get("revision"),"claims",fm.get("claims"))
for it in fm["pending"]:
    print(f"  {it['id']:24s} pri={it.get('priority'):6s} pending={it.get('discussion_pending')} post={it.get('proposal_post','')[:8]}")
a=[i for i in fm["pending"] if i["id"]=="exp_activation_silu"][0]
print("\nactivation diff ->", a["diff"][:180])
print("activation value ->", a["value"], "| review_basis:", a.get("review_basis","")[:90])
