import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
AGENT_NAME="ar_20261024_analyst2"
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
print("API",API,"WS",MAIN_WS_ID,"WORKSHOP",WORKSHOP)
# --- A2 trigger scan
recent=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=40",headers=HEADERS).json().get("data",[])
print("N posts", len(recent))
trigger=[p for p in recent if "[DISCUSSION-TRIGGER]" in p.get("title","")]
print("triggers:", [(p.get("id"),p.get("title"),p.get("createdAt")) for p in trigger])
for p in trigger[:3]:
    cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[])
    done=[c for c in cs if "[DISCUSS-DONE]" in (c.get("content") or "")]
    print(" trigger",p["id"],"comments",len(cs),"DONE",len(done))
# --- B roster
roster_raw=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md",headers=HEADERS).json()
rf=parse_frontmatter(roster_raw)
print("ROSTER:")
print(yaml.safe_dump(rf, allow_unicode=True)[:3000])
MY_TEAM=None;TEAM_WS_ID=None;ALL={}
for name,t in (rf.get("teams") or {}).items():
    ALL[name]=t["workspace_id"]
    if AGENT_NAME in t.get("members",[]):
        MY_TEAM=name;TEAM_WS_ID=t["workspace_id"]
print("MY_TEAM",MY_TEAM,"TEAM_WS_ID",TEAM_WS_ID)
# --- C: analyst => skip
_active = False
if trigger:
    _tid = trigger[0]["id"]
    _cs = requests.get(f"{API}/posts/{_tid}/comments", headers=HEADERS).json().get("data", [])
    _done = [c for c in _cs if "[DISCUSS-DONE]" in (c.get("content") or "")]
    _active = len(_done) < 5
print("Role analyst -> Check C skipped; branch =", "Part2" if _active else ("no-team" if MY_TEAM is None else "normal"))
