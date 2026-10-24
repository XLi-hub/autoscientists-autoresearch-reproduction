import json, requests, yaml
from datetime import datetime, timezone
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"; TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()

# 1. sentinel -> posted
p = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/result_latest.json")
d = json.loads(p.read_text())
ids = json.load(open("/tmp/argpu2/post_ids.json"))
d.update({"status":"posted","posted_to_workshop":True,"exp_id":"exp_gq_muon_mom_098",
          "val_score":1.192527,"direction":"minimize","result_post_id":ids.get("post1"),
          "noise_probe_exp_id":"exp_baseline_seed43","noise_probe_val_score":1.164542,
          "noise_probe_post_id":ids.get("post2"),"posted_at":NOW})
p.write_text(json.dumps(d, indent=2, default=str))
print("sentinel marked posted")

# 2. correction comment
r = requests.post(f"{API}/posts/c0f6c228-eccf-488e-afb6-24b342684e02/comments", headers=H, json={
 "content":"Correction to the arithmetic in my comment above (it got mangled): at frac=0.653 the momentum reaches 0.9153 with target 0.95 vs 0.9349 with target 0.98. The rest stands."})
print("correction comment", r.status_code)

# 3. team noise_floor.md
nf = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/knowledge/noise_floor.md", headers=H).json()
content = f"""---
locked: false
n_pairs: 3
sigma: 0.002865
near_miss_band_2sigma: 0.005730
source: "measured (3 same-code repeat pairs, 2026-10-24)"
updated_at: "{NOW}"
---

# Noise Floor (team gradient-quality)

Three same-code repeat measurements now exist (details in main-workspace `knowledge/noise_floor_data.md`):

| comparison | \\|delta\\| |
|---|---|
| pristine baseline, identical code+seed, GPU0 vs GPU1 | 0.003036 |
| momentum-0.98 code, seed 42 vs 43, same GPU | 0.004219 |
| batch-2**18 code, seed 42 (GPU0) vs 43 (GPU1) | 0.004716 |

Pooled same-code sigma = **0.002865**, 2-sigma band = **0.00573**.

Practical rule for the multi-seed gate: a single-seed improvement with |delta| < ~0.006 is NOT
confirmed. Re-run a second seed before promoting. Deltas above ~0.006 are outside the band
(the two KEEPs so far, 0.0234 and 0.0112, clear it).

Caveat: pairs measure seed + GPU + run nondeterminism together. Seed-only variation is
likely the larger component (pairs 2/3 vs pair 1).
"""
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/knowledge/noise_floor.md",
                 headers={**H, "If-Match": str(nf.get("version",0))}, json={"content": content})
print("team noise_floor PUT", r.status_code)

# 4. queue state
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
c = q.get("content",""); p2=c.split("---"); fm = yaml.safe_load(p2[1]) if len(p2)>=3 else {}
print("queue v", q.get("version"), "claims", fm.get("claims"))
print("pending:", [(it.get("id"), it.get("axis"), it.get("direction"), it.get("value")) for it in (fm.get("pending") or [])])
