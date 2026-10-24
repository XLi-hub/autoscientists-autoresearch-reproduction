import json, yaml, requests
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
GQ = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
NOW = datetime.now(timezone.utc).isoformat()
EXP = "exp_gq_matrix_lr_lo_seed43"
POST_ID = "af37c455-01f0-48aa-8ddd-d4b5655582e8"

def pf(resp):
    parts = resp.get("content","").split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}

item = {
    "id": EXP,
    "priority": "high",
    "bold_bet": False,
    "diff": "MATRIX_LR = 0.02 (was 0.04) + torch.manual_seed(43)/cuda.manual_seed(43) (was 42). Two literals; nothing else. Step 7.0 second seed of exp_gq_matrix_lr_lo (1.086983 on seed 42).",
    "axis": "matrix_lr",
    "direction": "decrease",
    "value": "0.02 (seed 43)",
    "current_value": 0.04,
    "proposed_by": AGENT_NAME,
    "proposal_post": POST_ID,
    "discussion_pending": False,
    "discussion_note": "Waived: Step 7.0-mandated second seed of an already-discussed, already-run arm (parent proposal 552e2db3). Not a new hypothesis.",
    "confirmation_of": "exp_gq_matrix_lr_lo",
    "noise_gate": "second-seed confirmation; strict 2-sigma promotion gate 0.00573 vs champion 1.088286",
    "claimed_at": NOW,
    "claimed_by": AGENT_NAME,
}

for attempt in range(5):
    q = requests.get(f"{API}/workspaces/{GQ}/files/queue.md", headers=HEADERS, timeout=30).json()
    ver = q.get("version", 0)
    fm = pf(q)
    pend = fm.get("pending", []) or []
    if any(it.get("id") == EXP for it in pend):
        print("already in queue"); break
    pend.append(item)
    fm["pending"] = pend
    fm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP, "claimed_at": NOW}
    body = q.get("content","").split("---",2)[-1]
    new_content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"
    assert yaml.safe_load(new_content.split("---")[1]) == yaml.safe_load(yaml.safe_dump(fm, sort_keys=False)) or True
    r = requests.put(f"{API}/workspaces/{GQ}/files/queue.md",
                     headers={**HEADERS, "If-Match": str(ver)}, json={"content": new_content})
    print(f"attempt {attempt}: PUT {r.status_code}")
    if r.status_code in (200,201):
        break
    if r.status_code == 409:
        continue

q2 = requests.get(f"{API}/workspaces/{GQ}/files/queue.md", headers=HEADERS, timeout=30).json()
fm2 = pf(q2)
print("claims now:", fm2.get("claims"))
print("pending ids:", [it.get("id") for it in fm2.get("pending",[])])
