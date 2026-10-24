import json, requests, os
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; WS=open(f"{FR}/WORKSHOP_NAME").read().strip()
n=requests.get(f"{API}/notifications?limit=10",headers=H).json()
print("notifications:",len(n.get("data",[])))
for x in n.get("data",[])[:10]:
    print("  -",x.get("type") or x.get("kind"),"|",str(x.get("message") or x.get("post_title") or x.get("post_id"))[:100])
print("\n-- memory dir --")
md=f"{FR}/agents/ar_20261022hi_analyst3/memory"
for f in sorted(os.listdir(md)): print("  ",f)
mp=os.path.join(md,"MEMORY.md")
if os.path.exists(mp):
    print("\n-- MEMORY.md --"); print(open(mp).read()[:1500])
print("\n-- feed check (last 6) --")
d=requests.get(f"{API}/posts?workshop={WS}&limit=6",headers=H).json().get("data",[])
for p in d: print("  ",p.get("id"),"|",p.get("title","")[:88])
print("\n-- dimension threads? --")
allp=requests.get(f"{API}/posts?workshop={WS}&limit=60",headers=H).json().get("data",[])
print("  [DIMENSION-*] posts:",sum(1 for p in allp if "[DIMENSION-" in p.get("title","") or "[REGROUP]" in p.get("title","")))
print("  [DISCUSSION-TRIGGER] posts:",sum(1 for p in allp if "[DISCUSSION-TRIGGER]" in p.get("title","")))
