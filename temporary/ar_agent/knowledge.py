import json, requests, yaml, datetime
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; A="ar_20261022hi_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{A}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":A}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS="032e5282-1362-4eef-9226-3d40299116aa"
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()

def put(wid, path, content):
    cur=requests.get(f"{API}/workspaces/{wid}/files/{path}",headers=H)
    if cur.status_code==200:
        v=cur.json().get("version",0)
        r=requests.put(f"{API}/workspaces/{wid}/files/{path}",headers={**H,"If-Match":str(v)},json={"content":content})
    else:
        r=requests.put(f"{API}/workspaces/{wid}/files/{path}",headers=H,json={"content":content})
    print(f"PUT {path}: {r.status_code}")
    return r.status_code

baseline_cov = """---
version: 1
updated_at: "@NOW@"
author: ar_20261022hi_analyst2
champion_geometry: "DEPTH=8 -> model_dim=512, n_head=4, head_dim=128, vocab=8192, seq=2048, ~50M params"
budget: "TIME_BUDGET=300s, TOTAL_BATCH_SIZE=2**19 tokens/step, DEVICE_BATCH_SIZE=128 -> grad_accum=2"
---

# Baseline Coverage Audit — champion/train.py (pristine seed, cycle 1)

Every named parameter + inline literal that a human could have chosen differently.
`tested?` is NO for all rows because no experiment result exists yet (cycle 1, baseline locked by gpu1).
Queued rows are marked `queued` and reference the cycle-1 proposal.

| parameter | current_value | tested? | result summary |
|---|---|---|---|
| DEPTH | 8 | queued (exp_depth_10, capacity) | no data |
| ASPECT_RATIO | 64 | NO | never varied; model_dim = DEPTH*64 rounded up to HEAD_DIM multiple |
| HEAD_DIM | 128 | NO | never varied; sets n_head (512/128 = 4) |
| WINDOW_PATTERN | "SSSL" | NO | never varied; last layer forced long; S = seq//2 = 1024 |
| TOTAL_BATCH_SIZE | 2**19 | queued (exp_batch_2e18, throughput) | no data |
| DEVICE_BATCH_SIZE | 128 | NO | never varied; grad_accum = TOTAL_BATCH // (128*2048) = 2 |
| EMBEDDING_LR | 0.6 | NO | very high vs nanochat defaults; never swept |
| UNEMBEDDING_LR | 0.004 | NO | never swept |
| MATRIX_LR (Muon) | 0.04 | queued bracket (exp_matrix_lr_lo/hi, this team) | no data; NOT dim-scaled |
| SCALAR_LR | 0.5 | NO | resid group uses scalar_lr*0.01 = 0.005, x0 group uses 0.5 |
| WEIGHT_DECAY | 0.2 | NO | cautious mask; decays as WD*(1-progress) |
| ADAM_BETAS | (0.8, 0.95) | NO | beta1=0.8 is low (fast EMA); beta2=0.95 short memory |
| ADAM eps | 1e-10 | NO | all Adam groups |
| WARMUP_RATIO | 0.0 | queued (exp_warmup_0p1, this team) | no data; time-based, 0.1 = 30 s |
| WARMDOWN_RATIO | 0.5 | NO | half the budget decays LR to FINAL_LR_FRAC |
| FINAL_LR_FRAC | 0.0 | NO | LR -> 0 at end |
| get_muon_momentum divisor | 300 | queued (exp_muon_mom_ramp60, this team) | ramp unreachable in a ~100-step run |
| get_muon_momentum endpoints | 0.85 -> 0.95 | NO | endpoint never reached at ~100 steps |
| Muon group momentum (init) | 0.95 | NO | overwritten each step by schedule |
| Muon ns_steps | 5 | NO | polar-express iterations; more = compute cost |
| Muon beta2 (NorMuon) | 0.95 | NO | variance adaptation of orthogonal step |
| Muon lr shape scale | max(1, shape[-2]/shape[-1])**0.5 | NO | per-shape LR multiplier for 2D params |
| polar norm divisor | 1.02 | NO | X / (norm*1.02 + 1e-6) |
| logit softcap | 15 | NO | tanh softcap on logits |
| RoPE base | 10000 | NO | in _precompute_rotary_embeddings |
| rotary_seq_len multiplier | seq_len * 10 | NO | precompute buffer length |
| short window divisor | long_window // 2 | NO | S-window = 1024 |
| ve_gate_channels | 32 | NO | value-embedding gate input slice |
| has_ve alternation | layer_idx % 2 == (n_layer-1) % 2 | NO | 4 of 8 layers get value embeds |
| MLP expansion | 4 * n_embd | NO | relu().square() activation |
| init std: wte | 1.0 | NO | normal init |
| init std: lm_head | 0.001 | NO | normal init |
| init bound: matrices | 3**0.5 * n_embd**-0.5 | NO | uniform |
| x0_lambdas init | 0.1 | NO | x0 residual mix strength |
| resid_lambdas init | 1.0 | NO | residual stream scale |
| x0 group betas | (0.96, 0.95) | NO | differs from ADAM_BETAS |
| ve_gate init | zeros | NO | gate = 2*sigmoid(0) = 1.0 neutral |
| failure threshold | train_loss > 100 | NO | fast-fail guard |
| timing warmup skip | step > 10 | NO | first 10 steps excluded from time budget |
| gc collect interval | every 5000 steps | NO | likely never triggers in a ~100-step run |
| ema_beta (logging) | 0.9 | NO | log smoothing only, not a hypothesis axis |
| H100_BF16_PEAK_FLOPS | 989.5e12 | BUG (reporting) | device is RTX 4080S (~195 TFLOP/s bf16 dense) -> mfu % understated ~5x |
| vocab_size default in GPTConfig | 32768 | overridden | build_model_config passes tokenizer vocab = 8192 |
| n_layer/n_head/n_embd defaults | 12/6/768 | overridden | build_model_config overrides from DEPTH/ASPECT_RATIO |

## Derived facts
- Adam LRs are dim-scaled by (512/768)^-0.5 = 1.2247; Muon MATRIX_LR is NOT dim-scaled -> untested asymmetry.
- grad_accum_steps = 2**19 / (128*2048) = 2 (1 if TOTAL_BATCH_SIZE -> 2**18).
- Order-of-magnitude step count: ~50M params, ~3.75e8 flops/token, 2**19 tokens/step. At 25-40% MFU on a 4080S that is ~2.5-5 s/step -> roughly 60-120 optimizer steps in 300 s. This makes schedule constants calibrated in *steps* (momentum ramp /300) suspect.

## Untested-and-worth-probing (ranked by expected information per GPU-minute)
1. muon_momentum_ramp (queued) 2. matrix_lr (queued) 3. adam_betas beta2 4. warmdown_ratio 5. embedding_lr 6. ns_steps (compute-cost caution) 7. window_pattern 8. softcap.
""".replace("@NOW@", NOW)

noise_floor = f"""---
updated_at: "{NOW}"
author: {A}
sigma: null
conservative_delta_band: 0.003
n_pairs: 0
locked: false
---

# Noise Floor — team gradient-quality

No same-code seed pairs exist yet (`knowledge/noise_floor_data.md` absent; no experiments run).

Per HEARTBEAT Step 0.5: **conservative band |delta| < 0.003** is the near-miss band until n >= 3 empirical pairs.
Do NOT close any axis on a single sample inside this band. Once n >= 5 pairs exist, set `locked: true` and record sigma at lock time; later pairs only update the running estimate.

Data source: the GPU multi-seed gate appends (code_hash, metric_a, metric_b) triples to `knowledge/noise_floor_data.md` whenever a borderline KEEP triggers a second-seed re-run.
"""

axis_priors = f"""---
updated_at: "{NOW}"
author: {A}
n_results: 0
---

# Empirical Axis Priors (cycle 1)

No experiment results exist yet, so every axis is COLD (n < 3) and gets the exploration bonus.

| axis | direction | n | mean_abs_delta | status |
|---|---|---|---|---|
| muon_momentum_ramp | decrease | 0 | - | COLD (queued) |
| matrix_lr | decrease | 0 | - | COLD (queued) |
| matrix_lr | increase | 0 | - | COLD (queued) |
| warmup_ratio | increase | 0 | - | COLD (queued, gpu4) |
| total_batch_size | decrease | 0 | - | COLD (queued) |
| depth | increase | 0 | - | COLD (queued) |
| adam_betas | any | 0 | - | COLD |
| warmdown_ratio | increase | 0 | - | COLD |
| embedding_lr | decrease | 0 | - | COLD |
| window_pattern | replace | 0 | - | COLD |
| softcap | any | 0 | - | COLD |

Ranking rule until data exists: prefer 1) proposals that test the team hypothesis with a mechanism-level prediction, 2) cold numeric axes with a bracketed probe, 3) anything that changes the optimizer step count or step size.
"""

unqueued = f"""---
version: 1
updated_at: "{NOW}"
updated_by: {A}
note: "Cycle-1 initialization. No [DISCUSSION]/[GAPS]/[CONSTANTS]/[RANKED]/[DYNAMICS] posts existed at init time, so rows were seeded from the baseline-coverage audit of champion/train.py per HEARTBEAT Step 0.7."
---

# Unqueued Axes Ledger (canonical backlog, all teams)

| axis | direction | suggested_value | mentioning_posts | status | last_touched |
|---|---|---|---|---|---|
| muon_momentum_ramp | decrease | 60 (divisor, was 300) | post:f0fed967 | queued | 2026-10-22 |
| matrix_lr | bracket | 0.02 / 0.08 (champ 0.04) | post:ac356e17 | queued | 2026-10-22 |
| warmup_ratio | increase | 0.1 | post:69c9209c | queued | 2026-10-22 |
| total_batch_size | decrease | 2**18 | post:98707205 | queued | 2026-10-22 |
| depth | increase | 10 | post:5e4f85d5 | queued | 2026-10-22 |
| adam_betas (beta2) | increase | (0.8, 0.99) | analyst2 baseline audit | unqueued | 2026-10-22 |
| adam_betas (beta1) | increase | (0.9, 0.95) | analyst2 baseline audit | unqueued | 2026-10-22 |
| muon_beta2 (NorMuon) | increase | 0.99 | analyst2 baseline audit | unqueued | 2026-10-22 |
| muon_momentum_max | increase | 0.98 (endpoint) | analyst2 baseline audit | unqueued | 2026-10-22 |
| ns_steps | increase | 7 (compute cost — deprioritize) | analyst2 baseline audit | unqueued | 2026-10-22 |
| embedding_lr | decrease | 0.3 | analyst2 baseline audit | unqueued | 2026-10-22 |
| unembedding_lr | increase | 0.01 | analyst2 baseline audit | unqueued | 2026-10-22 |
| scalar_lr | any | 0.25 | analyst2 baseline audit | unqueued | 2026-10-22 |
| warmdown_ratio | increase | 0.7 | analyst2 baseline audit | unqueued | 2026-10-22 |
| final_lr_frac | increase | 0.05 | analyst2 baseline audit | unqueued | 2026-10-22 |
| weight_decay | decrease | 0.1 | analyst2 baseline audit | unqueued | 2026-10-22 |
| window_pattern | replace | SSLL / SLSL | analyst2 baseline audit | unqueued | 2026-10-22 |
| aspect_ratio | increase | 80 (capacity at ~constant step cost) | analyst2 comment on depth_10 | unqueued | 2026-10-22 |
| head_dim | decrease | 64 | analyst2 baseline audit | unqueued | 2026-10-22 |
| n_kv_head (GQA) | decrease | 2 (from 4 = full MHA) | analyst2 baseline audit | unqueued | 2026-10-22 |
| softcap | increase | 20 | analyst2 baseline audit | unqueued | 2026-10-22 |
| ve_gate_channels | increase | 64 | analyst2 baseline audit | unqueued | 2026-10-22 |
| x0_lambdas init | decrease | 0.05 | analyst2 baseline audit | unqueued | 2026-10-22 |
| rope_base | increase | 20000 | analyst2 baseline audit | unqueued | 2026-10-22 |
| device_batch_size | increase | 256 (grad_accum -> 1) | analyst2 baseline audit | unqueued | 2026-10-22 |

Status legend: unqueued | queued | tested.
"""
put(TEAM_WS,"knowledge/baseline_coverage.md",baseline_cov)
put(TEAM_WS,"knowledge/noise_floor.md",noise_floor)
put(TEAM_WS,"knowledge/axis_priors.md",axis_priors)
put(MAIN,"knowledge/unqueued_axes.md",unqueued)

strategy = """---
hypothesis: H-gradient-quality
prediction: "Changes that reduce gradient noise or improve update direction will KEEP"
falsification: "3 rotations of prediction-consistent experiments all DISCARD"
age_rotations: 0
supported_keeps: 0
refuted_discards: 0
---

# Team gradient-quality

**Hypothesis (H-gradient-quality):** Gradient signal per step is suboptimal.

**Prediction:** Changes that reduce gradient noise or improve update direction will KEEP.

**Falsification:** 3 rotations of prediction-consistent experiments all DISCARD.

Proposals this team queues must be evaluable against the prediction. Any axis is in-scope as long as the change is one the hypothesis predicts will KEEP.

## Cycle-1 state (analyst2)
- `age_rotations` stays 0: no result-bearing rotation has completed yet (baseline still locked by gpu1 at 10:50).
- Queue: exp_warmup_0p1 (claimed by gpu4) + exp_muon_mom_ramp60, exp_matrix_lr_lo, exp_matrix_lr_hi (analyst2, discussion_pending).
- Mechanism note that anchors this team's next probes: with TIME_BUDGET=300s at ~50M params the run has only O(100) optimizer steps, yet several schedule constants (Muon momentum ramp /300, WARMDOWN=0.5, WARMUP=0.0) were calibrated for much longer runs. Step-count calibration is the team's most concrete sub-hypothesis.
- Noise floor: no empirical pairs yet; conservative |delta| < 0.003 band governs near-miss decisions.
"""

def put2(wid,path,content):
    cur=requests.get(f"{API}/workspaces/{wid}/files/{path}",headers=H)
    v=cur.json().get("version",0) if cur.status_code==200 else None
    hd=H if v is None else {**H,"If-Match":str(v)}
    r=requests.put(f"{API}/workspaces/{wid}/files/{path}",headers=hd,json={"content":content})
    print(f"PUT {path}: {r.status_code}")
put2(TEAM_WS,"strategy.md",strategy)
