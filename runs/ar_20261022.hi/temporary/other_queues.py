import json, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
TEAMS={"throughput":"54202fe1-b766-43f1-b374-9e4ed188c153","gradient-quality":"032e5282-1362-4eef-9226-3d40299116aa"}
def pf(c):
    p=c.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
for name,ws in TEAMS.items():
    r=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=HEADERS,timeout=20).json()
    fm=pf(r.get("content",""))
    print(f"\n##### {name} queue v{r.get('version')} #####")
    print("claims:", fm.get("claims"))
    for it in (fm.get("pending") or []):
        print(f"  - {it.get('id')} | {it.get('priority')} | axis={it.get('axis')} dir={it.get('direction')} val={it.get('value')} | pending={it.get('discussion_pending')} | post={it.get('proposal_post')}")
        print(f"      diff: {str(it.get('diff'))[:160]}")
    comp = fm.get("completed") or []
    print("  completed:", [(c.get('id'),c.get('outcome')) for c in comp])
