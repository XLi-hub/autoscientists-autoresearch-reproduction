---
name: seed_noise
description: Empirical same-code seed spread is 0.004138 val_bpb, larger than the assumed 0.003 band
type: feedback
---

MEASURED 2026-10-22 (exp_warmdown_070, GPU1, RTX 4080S, 300 s budget):

| seed | val_bpb | steps | tokens |
|---|---|---|---|
| 42 | 1.093748 | 719 | 94.2M |
| 43 | 1.097886 | 718 | 94.1M |

Same code (WARMDOWN_RATIO=0.7), same env, only `torch.manual_seed` differs.
**Same-code seed spread = 0.004138 val_bpb.** That is larger than the team's assumed
0.003 conservative 2-sigma band, i.e. the true sigma is >= ~0.002 (likely more with n>1).

Consequences:
- Any single-seed delta below ~0.004 on this task cannot be distinguished from seed noise.
- exp_batch_2e16 (+0.000319) and exp_muon_mom_ramp60 (+0.004053) are flat, not weak signals.
- KEEP deltas this run (exp_batch_2e17, +0.076) are safely outside.
- When a proposal's predicted effect is <0.01, budget a second seed BEFORE claiming; otherwise
  the gate will fire and the slot buys only a noise measurement.

Recorded in main `knowledge/noise_floor_data.md` (n=1) and team `knowledge/noise_floor.md`.
