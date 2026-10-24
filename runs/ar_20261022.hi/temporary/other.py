import json, requests, yaml
FOCUS="/root/autodl-tmp/ar_20261022.hi"; AGENT="ar_20261022hi_analyst1"
c=json.load(open(f"{FOCUS}/agents/{AGENT}/credentials.json"))
H={"Authorization":f"Bearer {c['api_key']}","Content-Type":"application/json","X-Agent-Name":c['agent_name']}
API="http://localhost:3000/api/v1"
teams={"throughput":"54202fe1-b766-43f1-b374-9e4ed188c153",
       "gradient-quality":"032e5282-1362-4eef-9226-3d40299116aa",
       "capacity":"3a33313e-18ff-4e17-9c47-66b54cfe576d"}
for name,ws in teams.items():
    if name=="throughput": continue
    r=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=H).json()
    print(f"\n{'='*15} {name} queue {'='*15}")
    print(r.get("content","MISSING"))
