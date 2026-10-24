import json, requests, yaml, datetime
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
SHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
print("NOW UTC:", datetime.datetime.now(datetime.timezone.utc).isoformat())
posts=requests.get(f"{API}/posts?workshop={SHOP}&limit=50",headers=H).json().get("data",[])
for p in posts:
    cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=H).json().get("data",[])
    print(f"\n### {p['id']} | {p['title']}\n tags={p.get('tags')} author={p.get('author') or p.get('agent')}\n comments={len(cs)}")
    print((p.get('content') or '')[:1200])
    for c in cs: print("   COMMENT:", (c.get('content') or '')[:300])
print("\n=== ALL TEAM QUEUES ===")
for name,wid in [("throughput","54202fe1-b766-43f1-b374-9e4ed188c153"),("gradient-quality","032e5282-1362-4eef-9226-3d40299116aa"),("capacity","3a33313e-18ff-4e17-9c47-66b54cfe576d")]:
    q=requests.get(f"{API}/workspaces/{wid}/files/queue.md",headers=H).json()
    print(f"--- {name} ---"); print((q.get("content") or "")[:1800])
print("\n=== RESULTS FILES in MAIN ===")
for f in requests.get(f"{API}/workspaces/{MAIN}/files",headers=H).json().get("files",[]):
    print(" ", f['path'], f.get('updatedAt'))
print("=== LOCAL experiments.jsonl ===")
p=Path(f"{FOCUS_ROOT}/logs/experiments.jsonl"); print(p.exists())
if p.exists(): print(p.read_text()[-3000:])
