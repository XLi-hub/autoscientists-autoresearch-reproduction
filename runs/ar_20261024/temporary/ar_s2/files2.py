import json, os, requests, yaml, time
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
def put(path, content):
    for attempt in range(2):
        r=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/{path}",headers=HEADERS).json()
        v=r.get("version",0)
        resp=requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/{path}",
            headers={**HEADERS,"If-Match":str(v)},json={"content":content})
        if resp.status_code==200:
            print("PUT",path,"ok v",resp.json().get("version")); return True
        print("PUT",path,"fail",resp.status_code,resp.text[:200]); time.sleep(1)
    return False

priors = """---
updated_at: "2026-10-24T07:24:00Z"
updated_by: ar_20261024_analyst2
n_experiments: 7
sigma: 0.002865
band_2sigma: 0.00573
source: "experiments.jsonl + results/ as of 2026-10-24T07:18Z; champion val_bpb 1.147892"
note: "Step 3g rule: every (axis,direction) with n<3 is COLD and earns the exploration bonus.
  Observed |delta| is shown as a SECONDARY sort because it is the only empirical signal we have.
  All gq deltas are measured against the CONTEMPORANEOUS base, not the current champion, and all
  gq bases had a different step count than today's champion (433 steps) — none transfer directly."
---

# Empirical Axis Priors

| axis | direction | n | mean_|delta| | vs 2-sigma (0.00573) | status |
|---|---|---|---|---|---|
| total_batch_size | decrease | 1 | 0.023450 | 4.1x ABOVE | COLD (n<3); strongest measured gradient; far probe 2**17 now due |
| mlp_expansion | decrease | 1 | 0.011151 | 1.9x ABOVE | COLD (n<3); positive slope; 2x arm filed, 5x arm queued |
| compile_mode | replace | 1 | 0.010215 | 1.8x ABOVE | COLD (n<3); KEEP |
| warmdown_ratio | decrease | 1 | 0.004863 | BELOW | COLD; flat in this neighborhood, axis open (noise) |
| muon_momentum | increase | 1 | 0.000181 | 32x BELOW | COLD; flat, and stale base (196 steps) — deprioritized |
| warmdown_ratio | increase | 0 | - | - | COLD (exploration bonus); queued as bracket high arm |
| muon_momentum_ramp | replace | 0 | - | - | COLD; queued, now higher relevance at 433 steps |
| adam_betas | increase | 0 | - | - | COLD; queued (0.9, 0.99) high arm |
| adam_betas | decrease | 0 | - | - | COLD; queued (0.7, 0.90) low arm |
| matrix_lr | increase | 0 | - | - | COLD; unledgered until today; next gq candidate after betas |
| matrix_lr | decrease | 0 | - | - | COLD; bracket counterpart |
| embedding_lr | decrease | 0 | - | - | COLD; ~45% of weights (wte + value_embeds) |
| unembedding_lr | increase | 0 | - | - | COLD; lm_head only (~9% of weights) |
| weight_decay | decrease | 0 | - | - | COLD; not separately ledgered yet |
| final_lr_frac | increase | 0 | - | - | COLD; not separately ledgered yet |
| warmup_ratio | increase | 0 | - | - | COLD; anti-throughput, low priority |
| muon_beta2 | increase | 0 | - | - | COLD; NorMuon memory-length axis |
| ns_steps | decrease | 0 | - | - | COLD; <0.1% FLOPs, update-geometry probe |
| window_pattern | replace | 0 | - | - | COLD; capacity SSLL queued; SSSS is the 0-param throughput control |
| depth | increase | 0 | - | - | COLD; capacity bracket queued (12 / 6) |
| head_dim | decrease | 0 | - | - | COLD; capacity probe queued (64) |
| device_batch_size | decrease | 0 | - | - | COLD; memory-fit control, not a step-count knob |
| dataloader_prefetch | replace | 0 | - | - | COLD; step time 0.69 s now crosses the ledger's <1 s revisit threshold |

## Reading

1. The only gradients that clear the noise band are throughput gradients (step count). Every gq
   measurement so far is inside the band. That is the central fact of this rotation.
2. Consequently the gq lane should spend its next slots on the few gq constants whose tuned value
   is defined in optimizer STEPS (Adam betas, Muon momentum ramp), because those are the constants
   the throughput KEEPs directly invalidated. Proposals filed this cycle follow exactly that.
3. Do not fine-bracket the muon_momentum target or warmdown until a step-count-coupled retest
   exists on the current 433-step champion.
"""

coverage = """---
audited_by: ar_20261024_analyst2
updated_at: "2026-10-24T07:24:00Z"
champion: exp_tput_compile_autotune (val_bpb 1.147892)
source: "champion/train.py @ 46,144,000-ish params (MLP_EXPANSION=3), DEPTH=8, n_embd=512, 433 steps/300s"
notes: "'tested?' = explicit variation of THIS constant with a result file. Sweep of 3+ values in both
  directions or a re-confirmation after an architecture change counts as tested; a mention does not.
  Three throughput constants are now tested by KEEPs; every gq constant remains untested."
---

# Baseline Coverage Audit — champion/train.py (cycle 2)

Config: DEPTH=8, ASPECT_RATIO=64 -> n_embd=512, n_head=4, head_dim=128, seq_len=2048, vocab=8192,
MLP_EXPANSION=3, params 46.14M. TOTAL_BATCH_SIZE=2**18, DEVICE_BATCH_SIZE=64 (grad_accum 2),
compile max-autotune-no-cudagraphs, 433 optimizer steps / 300 s.

| parameter | current_value | tested? | result summary |
|---|---|---|---|
| ASPECT_RATIO | 64 | NO | cold; sets n_embd = depth*64 (512 at depth 8) |
| HEAD_DIM | 128 | NO (queued) | capacity proposal exp_cap_head_dim_64 targets 64 |
| WINDOW_PATTERN | "SSSL" | NO (queued) | capacity proposal targets SSLL; 0-param throughput mirror SSSS unqueued |
| DEPTH | 8 | NO (queued) | capacity bracket 12 / 6 queued |
| MLP_EXPANSION | 3 | YES | 4->3 KEEP: 1.169258 -> 1.158107, 374 -> 410 steps, -10.5% FLOPs. 2x filed by gq; 5x queued |
| TOTAL_BATCH_SIZE | 2**18 | YES | 2**19->2**18 KEEP: 1.192708 -> 1.169258, 193 -> 374 steps. Far probe 2**17 now due |
| DEVICE_BATCH_SIZE | 64 | MEMORY-ONLY | 128 OOMs at 32GB; 64 is a fit adaptation, never a quality sweep |
| compile_mode | max-autotune-no-cudagraphs | YES | KEEP: 1.158107 -> 1.147892, 410 -> 433 steps, +5.8% tok/s, +148 s wall outside budget |
| EMBEDDING_LR | 0.6 (effective 0.735 after dmodel scale) | NO | cold; wte + value_embeds ~45% of weights |
| UNEMBEDDING_LR | 0.004 (effective 0.0049) | NO | cold; lm_head only |
| MATRIX_LR | 0.04 (Muon) | NO | cold; NEVER appeared in the ledger until this cycle — added as next gq candidate |
| SCALAR_LR | 0.5 | NO | cold; resid_lambdas get scalar_lr*0.01 = 0.005 |
| WEIGHT_DECAY | 0.2, annealed by progress | NO | cold |
| ADAM_BETAS | (0.8, 0.95) | NO (queued) | gq bracket {(0.7,0.90),(0.9,0.99)} filed this cycle; ~54% of weights |
| WARMUP_RATIO | 0.0 | NO | cold; anti-throughput, low priority |
| WARMDOWN_RATIO | 0.5 | NO | 0.25 arm DISCARD inside noise (+0.0049); axis open; 0.75 arm queued |
| FINAL_LR_FRAC | 0.0 | NO | cold |
| get_muon_momentum terminal target | 0.95 | NO | 0.98 arm DISCARD, inside noise, stale base; retest only after the ramp time-base fix |
| get_muon_momentum ramp base | 0.85 | NO | cold |
| get_muon_momentum ramp horizon | step/300 | NO (queued) | CALIBRATION: 433-step run reaches terminal at step 300 = 69% of run; intent ~31%; exp_gq_muon_ramp_progress |
| Muon momentum (constant in setup_optimizer) | 0.95 | NO | overwritten every step by the ramp |
| Muon ns_steps | 5 | NO | cold; polar-express iteration count, <0.1% FLOPs |
| Muon beta2 (NorMuon) | 0.95 | NO | cold; second-moment memory-length axis |
| Muon LR shape factor | max(1, rows/cols)**0.5 | NO | inline in _step_muon; standard Muon scaling |
| polar_express_coeffs | 5 triples | NO | fixed constants from the polar-express paper; not proposed |
| X pre-norm rescale | 1.02 (plus 1e-6) | NO | inline stabilizer in muon_step_fused |
| softcap | 15 (inline in GPT.forward) | NO | inline magic number; logits = 15*tanh(logits/15) |
| rotary base | 10000 | NO | inline default arg in _precompute_rotary_embeddings |
| rotary_seq_len | sequence_len*10 = 20480 | NO | inline in GPT.__init__ |
| wte init std | 1.0 | NO | inline in init_weights |
| lm_head init std | 0.001 | NO | inline in init_weights |
| init bound s | sqrt(3)*n_embd**-0.5 | NO | inline in init_weights |
| x0_lambdas init | 0.1 | NO | inline in init_weights; residual_init_x0 axis |
| resid_lambdas init | 1.0 | NO | inline in init_weights |
| ve_gate_channels | 32 | NO | inline class attr; value-embedding gate input width |
| x0 betas | (0.96, 0.95) | NO | inline in setup_optimizer; NOT governed by ADAM_BETAS |
| dmodel_lr_scale | (n_embd/768)**-0.5 = 1.2247 | NO | LR scale tuned at width 768, reused at 512 |
| loss fast-fail | loss > 100 | N/A | loop guard, not a metric knob |
| EMA beta (logging) | 0.9 | N/A | logging only; does not affect training |
| gc cadence | every 5000 steps | N/A | loop overhead |
| warmup exemption | step <= 10 excluded from budget | N/A | loop bookkeeping |
| H100_BF16_PEAK_FLOPS | 989.5e12 | N/A | reporting only; mislabeled for 4080S, does not affect training |
| prepare.MAX_SEQ_LEN | 2048 | N/A | read-only (prepare.py) |
| prepare.TIME_BUDGET | 300 | N/A | fixed protocol |
| prepare.EVAL_TOKENS | 40*524288 | N/A | read-only; eval cost, not the trained metric |

## Untested-parameter triage (cycle 2)

- Queued: ADAM_BETAS bracket (0.7,0.90)/(0.9,0.99) [this cycle], MLP 3->2 [this cycle],
  muon ramp time base [rebased], warmdown 0.75 [bracket completion].
- Newly ledgered / next gq candidates: MATRIX_LR bracket (0.02 / 0.08), EMBEDDING_LR 0.6->0.3,
  UNEMBEDDING_LR 0.004->0.008, WEIGHT_DECAY, FINAL_LR_FRAC.
- Deferred by other teams with reasons: see knowledge/unqueued_axes.md.
"""

print(put("knowledge/axis_priors.md", priors))
print(put("knowledge/baseline_coverage.md", coverage))
