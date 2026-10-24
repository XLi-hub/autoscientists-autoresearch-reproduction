---
name: rebase-discipline
description: Recompute all proposal numbers against the CURRENT champion every cycle; never quote stale param/FLOP counts
type: feedback
---

# Rebase discipline (evidence: ar_20261024 cycle 2)

The champion moved three times inside one rotation (TOTAL_BATCH 2**18 -> MLP 3x -> compile
max-autotune), from 1.192708 to 1.147892. Every cycle-1 capacity proposal had stale numbers:
depth12 was quoted at 71.30M params (MLP 4x) and is 65.01M at MLP 3x; "MLP 5x = +10.5% FLOPs"
became +23.5%.

Rule: before posting or queueing, recompute from the champion's actual code using
GPT.estimate_flops() semantics:
  params = wte + VE*n_ve + lm_head + depth*(4*n_embd^2 + 2*MLP*n_embd^2 + ve_gate) + 2*depth
  FLOPs  = 6*(params - wte - VE_params - 2*depth) + sum_layers(12*n_head*head_dim*min(window,seq))
  steps_est = champion_steps * champion_FLOPs / arm_FLOPs
VE and wte are EXCLUDED from the 6N term - that is why VE density is a zero-FLOP capacity probe.

Also: noise sigma 0.002865 was measured on the superseded base. Same-code noise is base-dependent
(step time changed 1.55 s -> 0.69 s, autotune changed kernel reduction orders). Do not treat an
old-base sigma as authoritative for the new champion.
