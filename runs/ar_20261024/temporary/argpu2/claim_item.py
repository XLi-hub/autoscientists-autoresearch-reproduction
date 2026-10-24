import json, sys, requests, yaml
from datetime import datetime, timezone
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"; TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"
target = sys.argv[1]
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
fm = yaml.safe_load(q.get("content","").split("---")[1])
ids = [it.get("id") for it in (fm.get("pending") or [])]
print("queue v", q.get("version"), "pending", ids, "claims", fm.get("claims"))
if target not in ids:
    print("NOT PENDING"); sys.exit(1)
fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": target, "claimed_at": datetime.now(timezone.utc).isoformat()}
body = q.get("content","").split("---",2)[-1]
new = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new.split("---")[1]) == fm
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**H, "If-Match": str(q.get("version",0))}, json={"content": new})
print("PUT", r.status_code, r.text[:200])
