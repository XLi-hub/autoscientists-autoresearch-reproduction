import json, requests
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
data=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=8",headers=H).json().get("data",[])
for p in data[:5]:
    print(p["created_at"], "|", p.get("author_name"), "|", p["title"][:100], "|", p["id"])
