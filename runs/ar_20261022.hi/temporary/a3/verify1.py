import json, requests
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; WS=open(f"{FR}/WORKSHOP_NAME").read().strip()
d=requests.get(f"{API}/posts?workshop={WS}&limit=8",headers=H).json().get("data",[])
for p in d: print(p.get("id"),"|",p.get("createdAt"),"|",p.get("title")[:95])
