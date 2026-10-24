---
name: seed-noise-sigma
description: Measured per-seed sigma is 0.00302, twice the protocol default; 2-sigma = 0.00604
type: finding
---

Two independent same-code seed pairs (warmdown_070 code 1.093748/1.097886; adam_beta2_hi code
1.093839/1.098235) give |delta| 0.004138 and 0.004396. Pooled per-seed sigma = 0.00302, 2-sigma =
0.00604, 3-sigma = 0.00906. The "conservative 0.003 band" is 1-sigma, not 2-sigma.

Consequences that must survive across sessions:
- Any 1-seed |delta| < 0.006 is a TIE. Never KEEP on it, never close an axis on it.
- exp_muon_mom_ramp60 (+0.004053 = 1.34 sigma) is noise, not a near-miss; the ramp axis is open.
- exp_ve_all_layers (-0.006029) is exactly 2.00 sigma - boundary, not a result.
- exp_adam_beta2_hi seed-42 beat the champion by 0.000198 (0.07 sigma); only the 2-seed gate stopped
  a false KEEP on the champion.
- Fixed-seed reproducibility is ~2e-4; seed choice dominates run-to-run variance.
- Not locked (n=2 < 5). Record every future pair in main knowledge/noise_floor_data.md.
