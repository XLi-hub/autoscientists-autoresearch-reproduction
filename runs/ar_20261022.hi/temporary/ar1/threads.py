import json, os, requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WS=open(FOCUS/"WORKSHOP_NAME").read().strip()
posts=requests.get(f"{API}/posts?workshop={WS}&limit=60",headers=H).json().get("data",[])
want=["exp_batch_2e17","Discussion-Before-Queuing","saturated at 2**17"]
for p in posts:
    if any(w in p.get("title","") for w in want):
        print("POST", p["id"], "|", p.get("title"))
        print("  keys:", sorted(p.keys()))
        cm=requests.get(f"{API}/posts/{p['id']}/comments",headers=H).json().get("data",[])
        print("  comments:",len(cm))
        for c in cm:
            print("   -", (c.get("agent_name") or c.get("author") or "?"), ":", (c.get("content") or "")[:400].replace("\n"," "))
        print()
print("=== NOTIFICATIONS ===")
n=requests.get(f"{API}/notifications?limit=10",headers=H).json()
for x in n.get("data",[]):
    print(" -", x.get("title") or x.get("post_title") or x, )
