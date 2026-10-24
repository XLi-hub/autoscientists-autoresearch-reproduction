import json, requests
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
r=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=40",headers=H).json()
data=r.get("data",[])
print("keys:", list(data[0].keys()) if data else "none")
print("total returned:", len(data))
for p in data[:14]:
    print("\n---")
    print(json.dumps({k:v for k,v in p.items() if k not in ("content",)}, indent=1, default=str)[:700])
    print("CONTENT:", str(p.get("content",""))[:400])
