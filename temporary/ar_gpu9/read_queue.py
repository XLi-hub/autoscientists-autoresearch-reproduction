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
TEAM_WS_ID = "d7c6f814-aab0-4029-a887-04345d274f9b"

q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS, timeout=30).json()
content = q.get("content","")
fm = yaml.safe_load(content.split("---")[1])
print("=== PENDING ITEMS:", len(fm.get("pending",[])), " CLAIMS:", fm.get("claims"))
for it in fm.get("pending",[]):
    print(f"  - {it['id']}  pri={it.get('priority')}  axis={it.get('axis')}/{it.get('direction')}  "
          f"pending_disc={it.get('discussion_pending')}  proposed_by={it.get('proposed_by')}")
    print(f"      diff: {str(it.get('diff'))[:180]}")
print("\n=== COMPLETED (last 15):")
comp = fm.get("completed",[])
for it in comp[-15:]:
    print(f"  - {it['id']}  outcome={it.get('outcome')}  val={it.get('val_score')}  by={it.get('completed_by')}")
print("\n=== FULL BODY (non-frontmatter) ===")
body = content.split("---",2)[-1]
print(body[:3000])
