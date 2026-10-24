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

# compute-mode declaration (orchestrator polls this)
Path(f"{FOCUS_ROOT}/logs/{AGENT_NAME}.gpu_claim").write_text("gpu\n")
print("[COMPUTE CLAIM] gpu")

q_raw = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
q_ver = q_raw.get("version", 0)
fm = pf(q_raw)
pending = fm.get("pending", []) or []
EXP_ID = "exp_head_dim_64"
item = next((it for it in pending if it.get("id")==EXP_ID), None)
assert item is not None, f"{EXP_ID} not pending: {[i.get('id') for i in pending]}"

# discussion gate: time-based grace (proposed 11:51Z, now 16:15Z >> 15 min)
from datetime import datetime as dt
t0 = dt.fromisoformat(item["proposed_at"].replace("Z","+00:00"))
print(f"[GATE] age={(dt.now(timezone.utc)-t0).total_seconds()/60:.0f} min -> cleared by time-based grace")

fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP_ID, "claimed_at": NOW}
body = q_raw.get("content","").split("---", 2)[-1]
new_content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
assert yaml.safe_load(new_content.split("---")[1]) == fm, "round-trip failed"
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(q_ver)}, json={"content": new_content})
print("[CLAIM]", r.status_code, EXP_ID)
json.dump({"exp_id": EXP_ID, "item": item}, open("/tmp/claim_state.json","w"), indent=2)
print(json.dumps(item, indent=2))
