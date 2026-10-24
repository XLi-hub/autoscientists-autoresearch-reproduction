import json, os, requests, yaml, re
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(FOCUS/"WORKSPACE_ID").read().strip()
WS=open(FOCUS/"WORKSHOP_NAME").read().strip()
TEAMS={"gradient-quality":"032e5282-1362-4eef-9226-3d40299116aa","capacity":"3a33313e-18ff-4e17-9c47-66b54cfe576d","throughput":"54202fe1-b766-43f1-b374-9e4ed188c153"}
def pf(r):
    c=r.get("content",""); p=c.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
for name,ws in TEAMS.items():
    r=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=H)
    fm=pf(r.json()) if r.status_code==200 else {}
    print(f"\n===== {name} queue v{r.json().get('version')} =====")
    print("claims:", fm.get("claims"))
    for it in fm.get("pending",[]) or []:
        print(f"  - {it.get('id'):<28} pri={it.get('priority'):<7} axis={it.get('axis')} dir={it.get('direction')} dp={it.get('discussion_pending')} by={it.get('proposed_by')}")
    print("  completed:", [c.get('id') for c in (fm.get('completed') or [])])
# posts: look for triggers/stuck/falsified across 100
r=requests.get(f"{API}/posts?workshop={WS}&limit=100",headers=H).json()
posts=r.get("data",[])
print("\n=== POSTS with structure/trigger tags ===")
for p in posts:
    t=p.get("title","")
    if any(k in t for k in ["DISCUSSION-TRIGGER","STUCK","HYPOTHESIS-FALSIFIED","DIMENSION","REGROUP","TEAM-REFORMED","SYSTEM-EXHAUSTED"]):
        print(" ", p.get("id","")[:8], t[:110], p.get("createdAt","")[:19])
print("\ntotal posts fetched:",len(posts))
print("newest post createdAt:", posts[0].get("createdAt") if posts else None, "| oldest:", posts[-1].get("createdAt") if posts else None)
