import json, requests
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
data=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=10",headers=H).json().get("data",[])
ids={p["id"]:p for p in data}
for pid in ["705f5b66-da0c-4b29-a33e-aeac57a8bef1","b8d49897-707a-4540-9a16-35a3972df06a","b06f518e-b57c-4d8d-a027-832905665b28"]:
    p=ids.get(pid)
    if not p:
        p=requests.get(f"{API}/posts/{pid}",headers=H).json()
    print("\n"+"="*95); print("TITLE:",p.get("title")); print(p.get("content","")[:2200])
