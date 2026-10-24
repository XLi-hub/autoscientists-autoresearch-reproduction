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

def pf(resp):
    parts = resp.get("content","").split("---")
    return yaml.safe_load(parts[1]) if len(parts)>=3 else {}

# ---------- dead_ends ----------
de = requests.get(f"{API}/workspaces/{GQ}/files/dead_ends.md", headers=HEADERS, timeout=30).json()
de_fm = pf(de)
entry = f"""

## CLOSED AT 2x SCALE (FLAT) — bracket exhausts the axis at this spacing

- exp_id: exp_gq_matrix_lr_lo + exp_gq_matrix_lr_lo_seed43  (2-seed mean of the lo arm)
  axis: matrix_lr
  direction: decrease
  value: 0.02  (seed 42 = 1.086983, seed 43 = 1.089445)
  current_value: 0.04  (champion 1.088286)
  delta: {((1.086983+1.089445)/2 - 1.088286):+.6f}  (2-seed mean vs champion)
  hi_arm: exp_gq_matrix_lr_hi (0.08) = +0.003688
  family: exp_gq_matrix_lr
  date: 2026-10-24
  status: AXIS FLAT AT 2x SPACING — do NOT spend a third slot (pre-registered rule, proposal 552e2db3)
  reason: |
    2x bracket {0.02, 0.04, 0.08} measured with n=3 runs. hi = +0.003688, lo (2-seed mean) = -0.000072;
    both inside the 2-sigma band, opposite signs -> the pre-registered "both arms inside +/-0.0057"
    rule fires: close matrix_lr at 2x scale as FLAT.
    Decisive detail: the lo arm's two seeds differ by 0.002462 on identical code and identical GPU —
    seed-only noise is ~1.9x LARGER than the arm's apparent -0.0013 gain. The seed-42 result was a
    lucky draw, NOT a mechanism.
    POWER CAVEAT: this bracket could only detect >0.006. FLAT != "0.04 is optimal". The log-midpoint
    0.028 is unmeasured; re-open only with a predicted effect >0.006.
"""
de_body = de.get("content","").split("---",2)[-1].rstrip()
de_fm["updated_at"] = NOW; de_fm["updated_by"] = AGENT_NAME
de_fm["noise_floor_sigma"] = 0.002503; de_fm["noise_band_2sigma"] = 0.005007
new_de = f"---\n{yaml.safe_dump(de_fm, sort_keys=False)}---{de_body}{entry}"
r = requests.put(f"{API}/workspaces/{GQ}/files/dead_ends.md",
                 headers={**HEADERS, "If-Match": str(de.get("version",0))}, json={"content": new_de})
print("dead_ends PUT:", r.status_code)

# ---------- queue: release claim + move pending -> completed ----------
outcome, our = "DISCARD", 1.089445
for attempt in range(4):
    q = requests.get(f"{API}/workspaces/{GQ}/files/queue.md", headers=HEADERS, timeout=30).json()
    q_fm = pf(q)
    claim_removed = q_fm.get("claims", {}).pop(AGENT_NAME, None) is not None
    pending = q_fm.get("pending", []) or []
    completed = q_fm.get("completed", []) or []
    remaining = []
    for it in pending:
        if it.get("id") == EXP:
            it = dict(it); it["completed_at"] = NOW; it["completed_by"] = AGENT_NAME
            it["outcome"] = outcome; it["val_score"] = our; it["second_seed_of"] = "exp_gq_matrix_lr_lo"
            completed.append(it)
        else:
            remaining.append(it)
    q_fm["pending"] = remaining; q_fm["completed"] = completed
    body = q.get("content","").split("---",2)[-1]
    r = requests.put(f"{API}/workspaces/{GQ}/files/queue.md",
                     headers={**HEADERS, "If-Match": str(q.get("version",0))},
                     json={"content": f"---\n{yaml.safe_dump(q_fm, sort_keys=False)}---{body}"})
    print(f"queue PUT attempt {attempt}: {r.status_code}")
    if r.status_code in (200,201): break

q2 = requests.get(f"{API}/workspaces/{GQ}/files/queue.md", headers=HEADERS, timeout=30).json()
f2 = pf(q2)
print("claims after:", f2.get("claims"))
print("pending after:", [i.get("id") for i in f2.get("pending",[])])
print("last completed:", [(i.get("id"), i.get("outcome")) for i in f2.get("completed",[])[-2:]])
