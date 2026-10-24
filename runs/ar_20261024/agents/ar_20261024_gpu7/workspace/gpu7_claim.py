import json, sys
from datetime import datetime, timezone
import requests, yaml

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu7"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
     "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()


def pf(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


def body_of(resp):
    return resp.get("content", "").split("---", 2)[-1]


# ---- 1. join gradient-quality ----
rr = requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md", headers=H).json()
fm = pf(rr)
gq = fm["teams"]["gradient-quality"]
if AGENT_NAME not in gq["members"]:
    gq["members"].append(AGENT_NAME)
    new = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body_of(rr)}"
    assert yaml.safe_load(new.split("---")[1]) == fm
    r = requests.put(f"{API}/workspaces/{MAIN}/files/teams/roster.md",
                     headers={**H, "If-Match": str(rr.get("version", 0))},
                     json={"content": new})
    print("roster join:", r.status_code)
    if r.status_code >= 300:
        print(r.text); sys.exit(1)
else:
    print("already in roster")
TEAM_WS = gq["workspace_id"]
print("TEAM_WS", TEAM_WS)

# ---- 2. claim exp_gq_matrix_lr_hi ----
EXP_ID = "exp_gq_matrix_lr_hi"
qr = requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md", headers=H).json()
qfm = pf(qr)
qfm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP_ID, "claimed_at": NOW}
new = f"---\n{yaml.safe_dump(qfm, sort_keys=False)}---{body_of(qr)}"
assert yaml.safe_load(new.split("---")[1]) == qfm
r = requests.put(f"{API}/workspaces/{TEAM_WS}/files/queue.md",
                 headers={**H, "If-Match": str(qr.get("version", 0))},
                 json={"content": new})
print("claim:", r.status_code)
if r.status_code >= 300:
    print(r.text); sys.exit(1)

# ---- 3. print the item ----
for it in qfm.get("pending", []):
    if it.get("id") == EXP_ID:
        print(json.dumps(it, indent=2, default=str))
