import json, requests, yaml, datetime
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; A="ar_20261022hi_analyst2"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{A}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":A}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
SHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()

# 1. Notification check
n=requests.get(f"{API}/notifications?limit=10",headers=H).json().get("data",[])
print("NOTIFICATIONS:", len(n))
for x in n[:10]: print("  ", (x.get("title") or x.get("type") or "")[:100], "post:", x.get("post_id"))

# 2. Verify feed contains both proposals + comments count
posts=requests.get(f"{API}/posts?workshop={SHOP}&limit=50",headers=H).json().get("data",[])
mine=[p for p in posts if A in (p.get("title","")+str(p.get("author"))) or "exp_muon_mom_ramp60" in p["title"] or "exp_matrix_lr_bracket" in p["title"]]
print("\nFEED POSTS:", len(posts))
for p in posts:
    cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=H).json().get("data",[])
    print(f"  {p['title'][:85]:87s} comments={len(cs)}")
print("BOTH PROPOSALS IN FEED:", all(any(k in p["title"] for p in posts) for k in ["exp_muon_mom_ramp60","exp_matrix_lr_bracket"]))

# 3. AGENT.md + memory + mirror
sc_path=AGENT_DIR/"memory"/".session_count"
sc=int(sc_path.read_text().strip()) if sc_path.exists() else 0
content=f"""---
name: {A}
role: analyst
team: gradient-quality
gpu: -1
server: server2
last_seen: "{NOW}"
status: idle
session_count: {sc+1}
last_branch: "normal"
last_experiment: none
last_outcome: none
last_val_bpb: null
---

# {A}

Analyst. Team: gradient-quality. Team workspace 032e5282-1362-4eef-9226-3d40299116aa.

## Current Focus
H-gradient-quality: the fixed 300 s budget yields only O(100) optimizer steps, but several schedule constants were calibrated for much longer runs. The Muon momentum ramp `min(step/300, 1)` therefore never reaches its designed 0.95 endpoint (effective momentum ~0.88). Probes:
- exp_muon_mom_ramp60 (queued, post f0fed967): ramp divisor 300 -> 60.
- exp_matrix_lr_bracket (queued, post ac356e17): MATRIX_LR 0.02 / 0.08 around 0.04; Muon LR is the only LR not dim-scaled, and was never validated at dim=512.

## Notes for Next Session
1. First action next cycle: read the baseline run's `num_steps`, `tok/sec`, `peak_vram_mb` from its result to replace the ~60-120 step estimate with a measured number. If steps are far from that range, re-derive the momentum-ramp rationale.
2. Read results for exp_warmup_0p1, exp_muon_mom_ramp60, exp_matrix_lr_lo/hi and update strategy.md supported_keeps / refuted_discards (age_rotations stayed 0 this cycle because no result-bearing rotation had completed).
3. Queue items were added with `discussion_pending: true`; a non-author comment is still needed before GPU agents may claim them.
4. Reporting bug found (not a scored axis): `H100_BF16_PEAK_FLOPS = 989.5e12` is hardcoded while the hardware is 2x RTX 4080S (~195 TFLOP/s bf16 dense), so printed mfu_percent is ~5x understated. Do not use mfu to judge experiments.
5. Ledger `knowledge/unqueued_axes.md` (main ws) now has ~20 unqueued rows; next cycle must walk it and queue/skip each with a written reason.
"""
(AGENT_DIR/"AGENT.md").write_text(content)
sc_path.write_text(str(sc+1))

mem=AGENT_DIR/"memory"/"finding_step_budget_calibration.md"
mem.write_text(f"""---
name: step-budget-calibration
description: Why schedule constants calibrated in optimizer steps are suspect in the 300s autoresearch budget
type: finding
---

# Step-budget calibration finding (cycle 1, {NOW[:10]})

Champion geometry: DEPTH=8 -> model_dim=512, 4 heads x 128, ~50M params, seq 2048, TOTAL_BATCH_SIZE=2**19 tokens/step, TIME_BUDGET=300 s.

Derived: ~3.75e8 flops/token; at 25-40% MFU on an RTX 4080S (~195 TFLOP/s bf16 dense) this is ~2.5-5 s/step, i.e. roughly **60-120 optimizer steps per run**.

Consequences (all testable, zero compute cost):
- `get_muon_momentum`: `frac = min(step/300, 1)` => momentum ends at 0.85 + 0.1*(steps/300) ~ 0.87-0.89; the designed 0.95 is never reached. Ramp is calibrated for runs of thousands of steps.
- `WARMDOWN_RATIO = 0.5` therefore decays the LR over the last ~30-60 steps, i.e. it is a large fraction of total parameter movement, unlike in a long run.
- `gc` every 5000 steps never triggers.

Reporting bug: `H100_BF16_PEAK_FLOPS = 989.5e12` is hardcoded; on 4080S the printed mfu is ~5x understated (reporting only, not val_bpb).

Verification path: count `num_steps:` in the first baseline result file. If steps >> 300, discard this finding.
""")
idx=AGENT_DIR/"memory"/"MEMORY.md"
idx.write_text("# Memory Index\n\n- [Step-budget calibration](finding_step_budget_calibration.md) — schedule constants calibrated in steps are suspect at ~100 steps/run\n")

r=requests.put(f"{API}/workspaces/{MAIN}/files/agents/{A}.md",headers=H,json={"content":content})
print("AGENT.md mirror:", r.status_code)
print("<promise>"+A+" cycle complete (branch=normal)</promise>")
