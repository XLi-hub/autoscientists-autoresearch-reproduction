import json, shutil, requests, yaml
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
MY_TEAM = "gradient-quality"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
ws = AGENT_DIR / "workspace"; rep = ws / "repo"
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
NOW = datetime.now(timezone.utc).isoformat()

our_metric = 1.192708
exp_id = "baseline_shared"
metric_name = "val_bpb"

# stamped copies (isolation)
shutil.copy(rep / "train.py", rep / f"train_{exp_id}.py")

# 1. champion.md
cur = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md", headers=HEADERS).json()
assert "awaiting_baseline" in cur.get("content",""), "champion already established by someone else!"
champion_content = f"""---
metric_name: val_bpb
metric_value: {our_metric}
seed_values: [{our_metric}]
direction: minimize
experiment_id: {exp_id}
agent: {AGENT_NAME}
timestamp: {NOW}
status: baseline_established
hardware_adaptation: DEVICE_BATCH_SIZE 128->64 (TOTAL_BATCH_SIZE 2**19 unchanged, grad_accum 2->4); pristine 128 OOMs on 32GB RTX 4080S
---

# Champion: baseline_shared (pristine upstream, micro-batch adapted to 32GB)

## Experiment Description

Shared baseline: karpathy/autoresearch train.py unchanged except DEVICE_BATCH_SIZE 128 -> 64
to fit 32GB. Effective batch (tokens/optimizer step) is unchanged at 2**19; grad_accum rises
2 -> 4. All model and optimizer hyperparameters are upstream defaults.

## Result

- **Recorded metric (1 seed):** val_bpb = {our_metric}
- **All seed values:** [{our_metric}]
- **Delta from previous:** N/A (first baseline)
- Steps: 196 in 300.8s training time; 102.8M tokens; peak VRAM 22.8GB; MFU 7.83%

## Complete Hyperparameters

```json
{json.dumps({
  "DEPTH": 8, "ASPECT_RATIO": 64, "HEAD_DIM": 128, "WINDOW_PATTERN": "SSSL",
  "n_layer": 8, "n_head": 4, "n_kv_head": 4, "n_embd": 512, "vocab_size": 8192,
  "seq_len": 2048, "params_M": 50.33,
  "TOTAL_BATCH_SIZE": 524288, "DEVICE_BATCH_SIZE": 64, "grad_accum_steps": 4,
  "EMBEDDING_LR": 0.6, "UNEMBEDDING_LR": 0.004, "MATRIX_LR": 0.04, "SCALAR_LR": 0.5,
  "WEIGHT_DECAY": 0.2, "ADAM_BETAS": [0.8, 0.95],
  "WARMUP_RATIO": 0.0, "WARMDOWN_RATIO": 0.5, "FINAL_LR_FRAC": 0.0,
  "muon_momentum": "0.85 -> 0.95 over step/300", "TIME_BUDGET": 300, "seed": 42
}, indent=2)}
```

## Reproduction

1. Copy `{FOCUS_ROOT}/champion/train.py`, set DEVICE_BATCH_SIZE=64 (already the champion value)
2. `CUDA_VISIBLE_DEVICES=1 HF_HOME=/root/autodl-tmp/cache/huggingface python train.py`
3. Expected val_bpb ~ {our_metric}

## Provenance

- Agent: {AGENT_NAME}; GPU 1 (RTX 4080S 32GB)
- Timestamp: {NOW}
"""
r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/champion.md",
                 headers={**HEADERS, "If-Match": str(cur.get("version", 0))},
                 json={"content": champion_content})
print("champion PUT", r.status_code, r.text[:200])

# 2. result file in main workspace
result_md = f"""# baseline_shared — shared baseline

- metric: {metric_name} = {our_metric} (minimize)
- agent: {AGENT_NAME} (GPU 1, RTX 4080S 32GB)
- timestamp: {NOW}
- outcome: BASELINE (seeds champion)
- config: pristine upstream train.py with DEVICE_BATCH_SIZE 128 -> 64 (TOTAL_BATCH_SIZE 2**19 unchanged)
- dynamics: 196 optimizer steps in 300.8s; loss 9.01 -> 3.358; loss@80% = 3.480 (final drop -0.122); still slowly decreasing at end (undertrained signal)
- throughput: ~322K tok/s steady, MFU 7.83%, peak VRAM 22.8GB, total wall 374.7s
- note: pristine DEVICE_BATCH_SIZE=128 OOMs at 32GB (torch.OutOfMemoryError, 31.4GB alloc); analysts had already flagged this in [SUGGESTION]
"""
r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/results/{exp_id}.md",
                 headers=HEADERS, json={"content": result_md})
print("result file PUT", r.status_code)

# 3. workshop [RESULT]
r = requests.post(f"{API}/posts", headers=HEADERS, json={
    "workshop": WORKSHOP,
    "title": f"[RESULT] {exp_id}: val_bpb={our_metric} (BASELINE)",
    "content": (f"## Experiment\nShared baseline: pristine karpathy/autoresearch train.py, with "
                f"DEVICE_BATCH_SIZE 128->64 so it fits 32GB (effective batch 2**19 unchanged; "
                f"grad_accum 2->4). Pristine 128 OOMs (31.4GB).\n\n"
                f"## Result\nval_bpb: {our_metric}\nDelta: N/A (first baseline, seeds champion)\n"
                f"Outcome: BASELINE\nSteps: 196 in 300.8s; 102.8M tokens; peak VRAM 22.8GB; MFU 7.83%\n"
                f"Loss 9.01 -> 3.358; still declining slowly at end.\n\n"
                f"## Team\ngradient-quality\n\n"
                f"champion.md now seeded with metric_value={our_metric} (minimize). All agents can diff against it."),
    "tags": [f"team:{MY_TEAM}", "type:result", "outcome:baseline"],
})
print("RESULT post", r.status_code, r.text[:200])
result_post_id = r.json().get("id") if r.ok else None

# 4. release baseline lock
lock = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md", headers=HEADERS).json()
requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md",
             headers={**HEADERS, "If-Match": str(lock.get("version", 0))},
             json={"content": f"holder: {AGENT_NAME}\nstatus: completed\nval_bpb: {our_metric}\nreleased_at: {NOW}\n"})
print("lock updated")

# 5. sentinel
rl = ws / "result_latest.json"
d = json.loads(rl.read_text())
d.update({"val_score": our_metric, "direction": "minimize", "exp_id": exp_id,
          "train_path": str(rep / f"train_{exp_id}.py"), "status": "posted",
          "posted_to_workshop": True, "result_post_id": result_post_id, "posted_at": NOW})
rl.write_text(json.dumps(d, indent=2, default=str))
print("sentinel posted")
