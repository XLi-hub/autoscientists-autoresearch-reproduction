import json, os, re, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME="ar_20261022hi_analyst3"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
def parse_frontmatter(resp):
    content=resp.get("content","")
    parts=content.split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}
r=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=30",headers=HEADERS)
print("posts status",r.status_code)
data=r.json().get("data",[])
print("n posts",len(data))
for p in data[:30]:
    print(p.get("id"), p.get("createdAt") or p.get("created_at"), "|", p.get("title"))
# triggers
trigs=[p for p in data if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("\nTRIGGERS:",len(trigs))
for t in trigs:
    c=requests.get(f"{API}/posts/{t['id']}/comments",headers=HEADERS).json().get("data",[])
    done=[x for x in c if "[DISCUSS-DONE]" in (x.get("content") or "")]
    more=[x for x in c if "[DISCUSS-MORE]" in (x.get("content") or "")]
    print(t["id"],t["title"],"| comments",len(c),"DONE",len(done),"MORE",len(more))
roster_raw=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md",headers=HEADERS).json()
print("\nroster status keys",list(roster_raw.keys()))
print("roster content preview:", str(roster_raw.get("content"))[:800])
