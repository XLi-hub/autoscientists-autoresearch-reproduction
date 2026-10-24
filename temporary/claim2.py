import json, os, requests, yaml
from pathlib import Path
from datetime import datetime, timezone
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID = st["TEAM_WS_ID"]
NOW = datetime.now(timezone.utc).isoformat()
def pf(resp):
    c = resp.get("content",""); p = c.split("---")
    return yaml.safe_load(p[1]) if len(p)>=3 else {}
q_raw = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
fm = pf(q_raw); pending = fm.get("pending") or []
EXP_ID = "exp_activation_silu"
item = next((it for it in pending if it.get("id")==EXP_ID), None)
assert item is not None
assert not item.get("discussion_pending"), "gate not cleared"
fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP_ID, "claimed_at": NOW}
body = q_raw.get("content","").split("---", 2)[-1]
new = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new.split("---")[1]) == fm
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(q_raw.get("version",0))}, json={"content": new})
print("[CLAIM2]", r.status_code, EXP_ID)
json.dump({"exp_id": EXP_ID, "item": item}, open("/tmp/claim_state.json","w"), indent=2)
# refresh champion copy from canonical source
import shutil
for f in ("train.py","prepare.py","pyproject.toml","uv.lock"):
    shutil.copy(f"{FOCUS_ROOT}/champion/{f}", f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/repo/{f}")
print("[COPY] refreshed from champion")
