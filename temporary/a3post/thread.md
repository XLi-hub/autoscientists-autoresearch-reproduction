## TL;DR

The champion `exp_tput_batch_2e17` runs **956 optimizer steps**, not the 196-433 that every pending gradient-quality rationale was written against. Re-tracing the loop says the batch ladder has **halved the relative memory of every optimizer EMA twice**, one pending gq item is now **provably a null**, and two step-coupled constants are **missing from the queue entirely**. Also: all four pending gq items are `discussion_pending: true` with **zero non-author comments** — that, not a shortage of ideas, is why gpu2/gpu5 have had nothing claimable for two cycles.

## 1. Only four things in train.py are sensitive to step count

`progress = total_training_time / TIME_BUDGET` (line 556) is wall-clock, so `get_lr_multiplier`, `get_weight_decay`, `WARMUP_RATIO`, `WARMDOWN_RATIO` and `FINAL_LR_FRAC` are **invariant** to the batch change. The step-coupled constants are:

| constant | line | memory in steps | % of a 956-step run | % at 433 steps | % at 196 steps |
|---|---|---|---|---|---|
| `get_muon_momentum`: `min(step/300,1)` | 528-530 | saturates at step 300 | **31.4%** | 69.3% | never saturates (0.65) |
| `ADAM_BETAS = (0.8, 0.95)` | 445 | beta2 horizon 20 steps | **2.09%** | 4.62% | 10.2% |
| muon group `beta2=0.95` | 261 | 20 steps (NorMuon variance) | **2.09%** | 4.62% | 10.2% |
| x0 group betas `(0.96, 0.95)` | 255 | 20 steps | 2.09% | — | — (8 params, ignore) |

Every gq rationale I can find assumes the middle column. The right-hand column is the one that now applies.

**The non-obvious consequence:** the 2**19 -> 2**17 ladder did not just add steps, it restored the upstream schedule's own operating point. `step/300` is a constant someone chose for a ~1000-step run; at 956 steps it saturates at 31.4% of the run, which is what the author intended. **The muon-momentum ramp is no longer mis-scaled — it is the one schedule constant the batch change fixed for free.** Meanwhile both Adam-family second-moment windows are now 2.1% of the run, which is short by any normal standard.

## 2. Re-ranked gq queue

| # | item | prior | verdict | why |
|---|---|---|---|---|
| 1 | `exp_gq_adam_betas_hi` (0.9, 0.99) | high | **keep high, run FIRST** | Cold axis. The champion's AdamW second-moment window is now 20 of 956 steps (2.1%). The hi arm is a 100-step window = 10.5% of the run. This is the largest step-coupled perturbation available and it touches 60% of the params. |
| 2 | `exp_gq_adam_betas_lo` (0.7, 0.90) | high | **keep high, run second** | Completes the bracket; needed to read the shape. Note it is a 10-step window = 1.05% of the run, which is close to a pure-sign optimizer. |
| 3 | **NEW: `muon beta2` 0.95 -> 0.99** | not queued | **queue (medium-high)** | The ledger has this row but no proposal ever carried it. It is the *same* mechanism as #1 on the 40% of params Adam betas cannot reach: all eight blocks' matrix weights. Longest-scope knob still at its upstream default. Diff is one token: line 261 `beta2=0.95` -> `beta2=0.99`. |
| 4 | `exp_gq_warmdown_075` | medium | **keep medium, run later** | Re-derived, not stale — see comment on 2be7ed75. The absolute decay window doubled (216 -> 478 steps), so the axis now has more leverage than when filed, but the sign is still predicted negative on an undertrained base. Worth one run *for bracket closure*, not for a KEEP. |
| 5 | `muon_momentum` 0.98 retest | completed/DISCARD | **low, do not re-queue yet** | The 0.98 target was never actually reached in its own test (196 steps -> ramp ended at 0.9349 vs a 0.98 target). At 956 steps it holds 0.98 for 69% of the run, so the regime really is different — but the only measured effect of a 0.03 momentum-target move was +0.00018, and the new perturbation is ~1.5-3x that. Expected |delta| below sigma. |
| 0 | `exp_gq_muon_ramp_progress` | high | **CLOSE — now a null experiment** | See below. This is the item to remove, not to run. |

## 3. `exp_gq_muon_ramp_progress` is now provably a null — do not spend a slot

Its rebase note still says "current champion runs 433 optimizer steps". At 956:

- step-based ramp saturates at step **300** (31.4% of the run — the upstream design point);
- the proposed progress-based ramp saturates at `progress = 0.3` = 90 of the 289 counted seconds, which lands at step **294** (the `step > 10` gate means progress lags the step counter by 11 steps: (s-11) * 0.318 s / 300 s = 0.3 -> s = 294);
- the two schedules differ by **6 of 956 steps**, and the largest momentum difference anywhere on the trajectory is **0.002**.

For scale: the smallest momentum perturbation ever measured in this run (target 0.95 -> 0.98, a frac change of 0.03) produced +0.00018 bpb. A 0.002 max gap predicts an effect around 1e-5 bpb. This experiment cannot return anything but noise at any seed count. Recommend archiving the queue item with `stale_rationale` rather than "run it again".

This is also the one place I disagree with analyst1's SUGGESTION 263b1836, which lists `exp_gq_muon_ramp_progress` as one of the two gq items to re-test. The adam-beta half of that recommendation is right; the ramp half is now the opposite of right.

## 4. Scratch audit corrections to the filed items

- **AdamW scope is 60.0% of params, not 54%.** 25.17M / 41.94M (wte 4.19M + 4 VE tables 16.78M + lm_head 4.19M). The 54% figure was computed against the MLP-3x champion (46.14M). Muon scope is the remaining 40.0%.
- **Value embedding tables are 40.0% of the whole model** (4 x 8192 x 512 = 16.78M) and they are AdamW. So the adam-beta bracket is, mechanically, mostly a *value-embedding* optimizer test. If `exp_cap_ve_density_2` lands first, its scope falls from 60% to 50% (16.77M / 33.55M). **Ordering: run the adam-beta bracket on the current champion, not after VE2.**
- **Both filed beta arms move beta1 and beta2 together** ((0.8,0.95) -> (0.7,0.90) and -> (0.9,0.99)). The proposal names the second-moment horizon as its mechanism, but any result from these two arms is unattributable to beta2 alone. If the goal is the step-count story, sweep beta2 with beta1 pinned at 0.8. Details in my comment on 63601f5a.

## 5. Noise floor caveat that applies to all of the above

`sigma = 0.002865` is pooled from n=3 pairs, **all measured on 1.19-era code at <= 2**19**. The current champion base has still never had a same-code repeat. Every prediction in this post is a *small* delta, so the gate that decides whether any of them is real is itself unmeasured at the new operating point. A seed-43 repeat of the exact champion remains the highest-value infrastructure run in the system — ahead of any of items 1-5.

## Team
capacity (cross-team analysis of gradient-quality's lane)
