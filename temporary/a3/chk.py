import json, requests, yaml
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; WS=open(f"{FR}/WORKSHOP_NAME").read().strip()
posts=requests.get(f"{API}/posts?workshop={WS}&limit=60",headers=H).json().get("data",[])
print("n posts",len(posts))
for p in posts:
    t=p.get("title","")
    if any(k in t.lower() for k in ["gqa","activation","silu","gelu","window","kv"]): print("TITLE HIT:",t)
# search bodies for gqa/silu
for p in posts[:20]:
    d=requests.get(f"{API}/posts/{p['id']}",headers=H).json().get("content","") or ""
    for k in ["gqa","silu","gelu"]:
        if k in d.lower():
            print(f"BODY {k} in: {p.get('title','')[:80]}")
            break
print("\n--- other team queues now ---")
for name,ws in {"throughput":"54202fe1-b766-43f1-b374-9e4ed188c153","gradient-quality":"032e5282-1362-4eef-9226-3d40299116aa"}.items():
    c=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=H).json().get("content","")
    p2=c.split("---")
    fm=yaml.safe_load(p2[1]) if len(p2)>=3 else {}
    print(name,"claims:",list((fm.get("claims") or {}).keys()))
    for it in fm.get("pending",[]) or []: print("   ",it.get("id"),it.get("priority"),it.get("axis"))
