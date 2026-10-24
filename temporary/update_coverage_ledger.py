import json, requests, yaml, re
from datetime import datetime, timezone
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip(); NOW=datetime.now(timezone.utc).isoformat()

bc = """---
name: baseline-coverage
updated_at: "__NOW__"
audited_by: ar_20261022hi_analyst3
champion_version: exp_batch_2e17 (val_bpb 1.094037, DEPTH=8, n_embd=512, ASPECT_RATIO=64, TOTAL_BATCH_SIZE=2**17, DEVICE_BATCH_SIZE=64, 719 steps, 50.3M params)
---

# Baseline Coverage Audit - champion/train.py (cycle 4)

Champion = exp_batch_2e17. "tested?" = Yes only where a result file explicitly varied that constant.
DERIVED = computed from other constants, not independently settable. NEW = added this cycle.

| parameter | current_value | tested? | result summary |
|---|---|---|---|
| DEPTH | 8 | **Yes** | 8->10 (with width 512->640, batch 32): DISCARD -0.0215 at 221 steps. Confounded; depth-only at fixed width still never tested. |
| ASPECT_RATIO | 64 | **Yes** | 64->32 (n_embd 256): DISCARD -0.0088 at 1741 steps. 80 queued (throughput). |
| HEAD_DIM | 128 | No | **64** (n_head 8) queued high; **256** (n_head 2) queued high this cycle. All three values have identical params/FLOPs/steps -> a clean 64/128/256 bracket at zero cost. |
| n_layer / n_head / n_embd / n_kv_head | DERIVED (8 / 4 / 512 / 4) | **Yes** (n_kv_head) | n_kv_head 4->1: DISCARD +0.0086 despite +9% steps. n_head == n_kv_head (full MHA). |
| VOCAB_SIZE | 8192 (from tokenizer) | No | NOT a tunable constant (data-side). **NEW ROW, load-bearing for FLOP maths**: wte and lm_head are 4.19M each, NOT 16.8M. Earlier notes that assumed 32768 were wrong by 4x. |
| WINDOW_PATTERN | "SSSL" | No | Reviewed + SKIPPED this cycle: SSSL->SSLL = +2.6% FLOPs -> ~700 steps (~0.003 step cost) for one more full-context layer; expected effect sub-band. SSSS is capability-negative; LLLL costs ~16% steps (~0.017 by the slope). |
| short_window divisor | long_window // 2 = 1024 (inline literal) | No | **NEW ROW (Layer-3 literal never audited).** //4 buys ~+13% steps (worth ~0 above the knee) at a real capability cost; //1 is the all-long extreme (~0.017 step cost). Skip. |
| TOTAL_BATCH_SIZE | 2**17 = 131072 | **Yes** | 2**19->2**18 KEEP +0.0256; 2**18->2**17 KEEP +0.0760; 2**17->2**16 **FLAT +0.00032 at 1396 steps**. SATURATED. |
| DEVICE_BATCH_SIZE | 64 | **Yes** | 128 OOMs on 32.7 GB (verified); 32 is the 2**16 pairing. |
| grad_accum | DERIVED = 1 | **Yes** | follows TOTAL_BATCH_SIZE / (DEVICE_BATCH_SIZE*MAX_SEQ_LEN). |
| EMBEDDING_LR | 0.6 | **Yes** | hi arm 1.2: DISCARD +0.00274 (0.9 sigma, in-band). lo arm 0.3 queued (gradient-quality). Shared by wte + value_embeds (42% of params). |
| UNEMBEDDING_LR | 0.004 | No | lm_head only (4.19M), wd=0. Bracket queued (throughput). |
| MATRIX_LR | 0.04 | No | Muon; NOT scaled by dmodel_lr_scale. Bracket queued (gradient-quality); lo arm claimed 16:15Z. |
| SCALAR_LR | 0.5 | No | resid group gets 0.005 (lr*0.01), x0 group 0.5. 16 params total. Skip. |
| WEIGHT_DECAY | 0.2 | **Yes** | 0.0: +0.00084 (0.28 sigma, FLAT). 0.4 queued (throughput). Muon groups only. |
| ADAM_BETAS | (0.8, 0.95) | **Yes** (beta2) | beta2 0.99: 2 seeds 1.093839/1.098235 -> tie. beta1 bracket queued. |
| WARMUP_RATIO | 0.0 | **Yes** | 0.1 -> DISCARD +0.0278. Closed for increase. |
| WARMDOWN_RATIO | 0.5 | **Yes** | 0.25 DISCARD -0.0068; 0.7 two-seed tie (0.59 sigma). Closed around 0.5. |
| FINAL_LR_FRAC | 0.0 | No | Unqueued; flagged to throughput (analyst2: the LR schedule is TIME-based while steps are not). |
| dmodel_lr_scale | (n_embd/768)**-0.5 (DERIVED) | No | 1.2247 at 512. AdamW only (Muon unscaled) - confounds every width probe. Skip: rescales 3 groups at once. |
| Muon momentum | 0.95 after ramp | No | ramp divisor 300; 900 queued as a far probe (gradient-quality). |
| Muon momentum ramp length | 300 steps (inline) | **Yes** | 60 -> +0.0041 = 1.34 sigma = NOISE. Axis OPEN, not closable. |
| Muon ns_steps | 5 | No | Skip: NorMuon `final_scale` normalizes to ||X_ns||, so ns_steps sets update MAGNITUDE -> duplicates matrix_lr. |
| Muon beta2 (NorMuon) | 0.95 | **Yes** | 0.99: +0.00057 in-band (0.19 sigma). 0.90 queued. |
| AdamW eps | 1e-10 | No | Queued (gradient-quality) as {1e-8, 1e-6}; conditioning on 5 AdamW groups. |
| **MLP activation** | **ReLU-squared** (`F.relu(x).square()`) | No | **QUEUED (amended this cycle)**: diff is now `F.silu(x).square()` - keeps the square, swaps only the rectifier. The old `-> F.silu(x)` diff is withdrawn (two-change confound, 2 reviews). |
| MLP hidden multiplier | 4 (inline `4 * config.n_embd`) | No | mlp_6 retained LOW as the Step 1e fallback: +50% MLP params = +21% FLOPs/token -> ~594 steps (-22%) -> ~0.022 step penalty by the slope. mlp_3 SUPERSEDED. |
| value-embedding layer policy | alternating has_ve (4 of 8) | **Yes** | all 8: -0.0060 (2.0 sigma, AT the boundary). 0 of 8 queued high (decisive arm). |
| ve_gate_channels | 32 (inline) | No | **NEW ROW.** gate = Linear(32, n_kv_head) = 128 params reading the first 32 of 512 channels. Skip: the VE mechanism (33% of params) measured neutral-to-harmful; ve_none is the decisive test, not gate width. |
| resid_lambdas init | 1.0 | No | Per-layer residual scale, learned (8 params). Skip (learned, washes out). |
| x0_lambdas init | 0.1 (inline fill_) | No | Learned at LR 0.5 (8 params). Skip (learned). |
| wte init std | 1.0 | No | Normal init; RMSNorm + Adam absorb the scale. Skip. |
| lm_head init std | 0.001 | No | Skip with reason: Adam moves a coordinate by ~lr per step, so 719 x 0.0049 ~= 3.5 of possible movement >> the 0.02 init-scale question. Init washes out; this is not a lever. |
| block init scale s | 3**0.5 * n_embd**-0.5 (DERIVED) | No | uniform(-s,s) for q/k/v/fc; c_proj zero-init. Untested but expected to wash out. |
| rotary base | 10000 (inline) | No | Skip: no evidence position encoding is binding. |
| rotary_seq_len | sequence_len * 10 (DERIVED) | No | 20480 positions precomputed. |
| logit softcap | 15 (inline, forward) | No | Queued by throughput (exp_softcap_30). |
| tied embeddings | untied (separate 4.19M lm_head) | No | Queued by throughput (exp_embedding_tied, 4 coordinated edits). |
| time-budget warmup | `if step > 10 and ...` | No | ~10 steps of free compute outside the budget accounting (~1.4% of the run). |
| weight decay schedule | WD*(1-progress), LR-multiplied | No | Scaled by LR so it vanishes in the warmdown tail. Skip: wd 0.0 vs 0.2 is flat, so the schedule shape is sub-band. |

**Untested high-leverage remainder:** activation (queued, amended), HEAD_DIM 64 and 256 (both queued),
ve_gate_channels (skip), resid/x0 inits (skip), rotary base (skip), lm_head init (skip).
Of these, **activation and HEAD_DIM are the only step-neutral ones left**, which is now a hard requirement:
every FLOP-costly probe must repay ~0.1159*ln(step ratio) in per-step quality, and none has come close.
""".replace("__NOW__", NOW)
r=requests.get(f"{API}/workspaces/{TEAM}/files/knowledge/baseline_coverage.md",headers=HEADERS,timeout=20).json()
r2=requests.put(f"{API}/workspaces/{TEAM}/files/knowledge/baseline_coverage.md",
    headers={**HEADERS,"If-Match":str(r.get("version"))},json={"content":bc},timeout=30)
print("baseline_coverage.md", r2.status_code, r2.json().get("version"))

# ---------------- main ledger (merge) ----------------
lr=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers=HEADERS,timeout=20).json()
lc=lr.get("content",""); lv=lr.get("version")
orig=lc

old_hd="| head_dim | decrease | 64 | analyst3 exp_head_dim_64 | queued | capacity; zero FLOPs change. | 2026-10-22 |"
new_hd="| head_dim | decrease | 64 | analyst3 exp_head_dim_64 | queued | Zero params / zero FLOPs / zero steps. Low arm of the **64/128/256 bracket** (128 = champion midpoint). | 2026-10-23 |"
assert old_hd in lc
lc=lc.replace(old_hd,new_hd)

old_win=[l for l in lc.split("\n") if l.startswith("| window_pattern |")]
assert len(old_win)==1, old_win
new_win=("| window_pattern | replace | SSSS / SSLL | Step 1c audit + analyst2 c4 | unqueued | **Capacity reviewed and DECLINES the handoff.** "
 "SSSL->SSLL = +2.6% FLOPs/token -> ~700 steps (step cost ~0.003 by the slope) for one more full-context layer; "
 "expected effect is sub-band. SSSS is capability-negative; LLLL costs ~16% steps (~0.017). Revisit ONLY if the "
 "head_dim and activation probes both report. | 2026-10-23 |")
lc=lc.replace(old_win[0],new_win)

old_act=[l for l in lc.split("\n") if l.startswith("| activation_fn |")]
assert len(old_act)==1, old_act
new_act=("| activation_fn | replace | SiLU^2 (`F.silu(x).square()`) | analyst3 a98037fd | **queued (AMENDED 2026-10-23)** | "
 "**Confound fixed**: keeps the `.square()`, swaps only the rectifier. The old relu^2->plain-SiLU diff is withdrawn "
 "before running; the 2 non-author reviews on ff2578ae are discharged. Expected range straddles 2-sigma -> needs "
 "seed 43. | 2026-10-23 |\n"
 "| activation_fn | replace | plain ReLU (`F.relu(x)`; square OFF) | analyst3 property split | unqueued | "
 "The other half of the decomposition: squaring on/off at fixed rectifier - the cleanest test of the squared-ReLU "
 "primitive. Run only AFTER silu^2 reports; do not run both simultaneously. | 2026-10-23 |")
lc=lc.replace(old_act[0],new_act)

# append new rows at the end of the table (after the last table row)
anchor="| tied_embeddings | tie lm_head weight to token embedding | untied | tied | REPLACE (structural) |"
idx=lc.find(anchor)
assert idx>0
eol=lc.find("\n",idx)
new_rows=("\n| head_dim | increase | 256 | analyst3 eb802d92 | **queued (cycle 5)** | **NEW ROW.** n_head 4->2 at fixed n_embd; "
 "0 params / 0 FLOPs / 0 steps. High-far arm + bracket completion (64/128/256). Paired falsification test: if BOTH "
 "head arms DISCARD, H-capacity is falsified. | 2026-10-23 |"
 "\n| ve_gate_channels | widen | 512 (from 32) | analyst3 Step 1c | unqueued | **NEW ROW.** The ResFormer value-residual gate is "
 "Linear(32, n_kv_head) = 128 params reading the first 32 of 512 channels. Skip: the whole VE mechanism is 33% of params "
 "and measured neutral-to-harmful (ve_all -0.0060 at 2.0 sigma); exp_ve_none is the decisive test, not gate width. | 2026-10-23 |"
 "\n| short_window divisor | change | //4 or //1 | analyst3 Step 1c | unqueued | **NEW ROW (Layer-3 literal).** //4 buys "
 "~+13% steps, which are worth ~0 above the ~719-step knee, at a real capability cost; //1 is the all-long extreme costing "
 "~16% steps (~0.017 by the slope). Skip both. | 2026-10-23 |")
lc=lc[:eol]+new_rows+lc[eol:]

lc=lc.replace("version: 5","version: 6",1).replace('last_editor: ar_20261022hi_analyst2','last_editor: ar_20261022hi_analyst3',1)
lc=re.sub(r'updated_at: ".*?"', f'updated_at: "{NOW}"', lc, count=1)
lc=lc.rstrip()+"""

## Cycle 5 re-walk (analyst3, 2026-10-23) - what changed and why
- **activation_fn**: the queued probe was confounded (dropped the square). Amended to SiLU^2 in place; the
  plain-ReLU (square-off) half of the decomposition is added as an unqueued follow-up.
- **head_dim**: added the increase/256 arm. The axis now has a complete zero-cost bracket (64 / 128 / 256).
- **window_pattern**: analyst2 handed this to capacity; capacity declines it with a written cost argument
  (step cost ~0.003, expected effect sub-band). Documented rather than silently dropped.
- NEW rows: `ve_gate_channels` and `short_window divisor` - two Layer-3 literals that no prior audit listed.
- Everything else with status `unqueued` keeps its cycle-4 skip reason. No ledger row is pruned.
"""
r3=requests.put(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",
    headers={**HEADERS,"If-Match":str(lv)},json={"content":lc},timeout=30)
print("unqueued_axes.md", r3.status_code, r3.json().get("version") if r3.status_code==200 else r3.text[:300])
print("ledger len", len(orig), "->", len(lc))
