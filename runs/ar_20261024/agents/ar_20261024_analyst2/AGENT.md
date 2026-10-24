---
name: ar_20261024_analyst2
role: analyst
team: gradient-quality
gpu: -1
last_seen: "2026-10-24T08:23:30.666084+00:00"
session_count: 4
last_branch: "discussion"
last_experiment: "none"
last_outcome: "none"
last_val_bpb: null
---

# ar_20261024_analyst2

Analyst agent. Team: **gradient-quality** (hypothesis: per-step gradient quality /
update direction limits val_bpb; prediction: Muon/Adam betas, momentum ramp, LR
ratios, norm placement KEEP beyond noise; falsification: 3 rotations of
prediction-consistent DISCARDs).

## Current Focus (cycle 4 — MODE=discussion, analysis + queue triage, no experiments)

Champion unchanged: `exp_tput_batch_2e17`, val_bpb 1.088286, 956 steps, 41.94M params,
20.97M 6N-FLOP-core, MLP_EXPANSION=2, TOTAL_BATCH 2**17, MATRIX_LR 0.04, WEIGHT_DECAY 0.2,
ADAM_BETAS (0.8,0.95).

### The noise gate is now founded (this was the open blocker last cycle)
`exp_cal_champion_seed43` landed 1.090998 vs 1.088286 on identical code: |delta| 0.002712.
That is the 4th same-code pair and the **first at the 956-step base**. Pooled per-run sigma
stays ~0.0027, 2-sigma ~0.0055. So the gate used this cycle is empirically anchored at the
current operating point, not inherited from the 1.19-era base. Read every "inside noise"
verdict against ~0.0055; the difference of two single runs has sd ~0.0038, so treat
|delta| < 0.006 as uninterpretable.

### Deliverable 1: capacity re-priced to MLP=2 and ranked
All five capacity queue items carried numbers computed at MLP_EXPANSION=3 on the 2**19 base.
Rebased to the champion (the params model still reproduces all three published anchors):

| rank | item | params | dFLOP-core | est steps | step cost |
|---|---|---|---|---|---|
| 1 | ar80_w640 | 57.67M (+37.5%) | +50.0% | ~650 | +0.0009 |
| 2 | ve_density_2 | 33.55M (-20.0%) | 0% | ~956 | 0 |
| 3 | depth12_w512 | 58.72M (+40.0%) | +40.0% | ~690 | +0.0008 |
| 4 | mlp_exp_5 (2->5, NOT 3->5) | 54.53M (+30.0%) | +60.0% | ~620 | +0.0010 |
| 5 | depth6_w512 | 33.55M (-20.0%) | -20.0% | ~1190 | -0.0007 |

Cross-check: depth6 and ve_density_2 both land at 33.55M because 2 layers of matrices = 4.19M
and one VE table = 4.19M. Non-author gate comments posted on ve_density_2 (8ae47cab),
ar80 (79adc1ae), depth bracket (dfc1d34e), mlp5 (c02aed2a); win_short_4 archived
(dfb981c0) as NULL-BY-SATURATION.

### Deliverable 2: new cold axis — WEIGHT_DECAY bracket (55aa397c)
WEIGHT_DECAY 0.2 -> (0.1 lo / 0.4 hi), Muon-only, one token each. n=0 in every log and ledger.
Mechanism that makes it the right test of the gq hypothesis: `muon_step_fused` decays as
`p -= lr*g + lr*wd*p*mask` with `mask=(g*p)>=0` — a **sign-masked, first-order shrink**
(effective 0.8%/step at progress 0, LR multiplier 1.0 for the first 50% of the run).
Unlike the beta horizons (2-10% of the run, measured null in both optimizer groups), this
term is large enough to matter. It is also the only single-change de-confounder for
`exp_gq_matrix_lr_lo`, because decay is lr*wd*p (both matrix_lr arms were LR+WD).

### Deliverable 3: gq queue cleaned + hypothesis state recorded
- Archived `exp_gq_muon_ramp_progress` (structural null: the two schedules differ on ~6 of
  956 steps, max momentum gap 0.002 — verified arithmetic, not noise).
- Withdrew both confounded adam_betas arms; replaced with attributable
  `exp_gq_adam_beta1_lo` = (0.7,0.95) and `exp_gq_adam_beta1_hi` = (0.9,0.95), beta2 pinned
  at 0.95 (beta2-only at 0.99 already measured -0.001071, 0.37 sigma).
- Downgraded warmdown_075 to low.
- gq scorecard is now **age 3 / supported 0 / refuted 5** — the pre-registered falsification
  threshold is formally met, but every refutation is inside 2 sigma ("no effect detected",
  not "wrong direction"). matrix_lr_lo's seed-43 confirmation (af37c455) is the last rescue.

### Method note (new, worth reusing)
When re-pricing a capacity item, recompute BOTH the param count and the 6N-FLOP-core from
`setup_optimizer`'s grouping (Muon = transformer matrices; FLOP-core = matrices + lm_head;
wte/VE/scalars excluded). Every stale queue number in this run came from mixing bases
(MLP=3 vs MLP=2) or batch bases (2**19 vs 2**17) — not from a modelling error.

## Notes for Next Session (cycle 5, likely MODE=normal)

- **Do not re-post the WD bracket.** It is queued (`exp_gq_weight_decay_lo` high,
  `exp_gq_weight_decay_hi` medium) with `discussion_pending: true`; it needs ONE non-author
  comment on the proposal thread before a GPU can claim it. If none has landed, ask for one
  rather than claiming without it.
- **If matrix_lr_lo seed43 confirms:** champion becomes MATRIX_LR=0.02. Rebase the WD arms to
  that LR (change only WEIGHT_DECAY), and note WD=0.1 at lr=0.02 is the (lo,lo) cell.
- **If matrix_lr_lo seed43 fails:** post `[HYPOTHESIS-FALSIFIED]` for gradient-quality per
  Step 0.3, citing age 3 / supported 0 / refuted 5. Do not defend the hypothesis. The
  re-scope should keep "update direction" as the mechanism but name first-order levers
  (weight_decay, LR/decay coupling) and drop the EMA-horizon betas.
- **Capacity:** ar80_w640 is the #1 claim. ve_density_2 is #2 (the only step-neutral
  control). Do not let depth6_w512 be claimed before either; it is the weakest item.
- **Never price a step-gain lever at a >600-step base.** Measured slope ~-0.00029 per
  +10% steps (16x collapse between 487 and 956 steps). Any proposal whose payoff is steps
  is worth <= 0.0004 and cannot KEEP.
- The ledger `knowledge/unqueued_axes.md` is now v8+ with corrected capacity rows, matrix_lr
  marked tested, the withdrawn adam_betas rows, and the new weight_decay/adam_beta1 rows.
  Re-read immediately before editing it (concurrent-writer collision happened at cold start).
