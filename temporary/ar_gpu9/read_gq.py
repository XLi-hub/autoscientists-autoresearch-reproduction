import json, yaml, requests
from pathlib import Path
AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()

roster_raw = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS, timeout=30).json()
roster = yaml.safe_load(roster_raw["content"].split("---")[1]).get("teams", {})
print("=== ROSTER ===")
for n,t in roster.items():
    print(f"{n}: ws={t['workspace_id']} members={t.get('members')} hypothesis={str(t.get('hypothesis'))[:150]}")

GQ = roster["gradient-quality"]["workspace_id"]
print(f"\n=== GQ QUEUE ({GQ}) ===")
q = requests.get(f"{API}/workspaces/{GQ}/files/queue.md", headers=HEADERS, timeout=30).json()
print("version:", q.get("version"))
content = q.get("content","")
fm = yaml.safe_load(content.split("---")[1]) if content.count("---")>=2 else {}
print("claims:", fm.get("claims"))
print("pending items:", len(fm.get("pending",[])))
for it in fm.get("pending",[]):
    print(f"  - {it['id']} pri={it.get('priority')} axis={it.get('axis')}/{it.get('direction')} val={it.get('value')} disc_pending={it.get('discussion_pending')} by={it.get('proposed_by')}")
    print(f"      {str(it.get('diff'))[:160]}")
print("\ncompleted:", len(fm.get('completed',[])))
for it in fm.get('completed',[])[-10:]:
    print(f"  - {it['id']} {it.get('outcome')} {it.get('val_score')} by {it.get('completed_by')}")
print("\n=== GQ FILES ===")
for f in requests.get(f"{API}/workspaces/{GQ}/files", headers=HEADERS, timeout=30).json().get("files",[]):
    print(" ", f.get("path"), "v", f.get("version"))
