---
name: gq-second-moment-null
description: At the 956-step champion, 5x longer second-moment windows are neutral on AdamW and Muon; price further horizon arms below sigma
type: feedback
---

Measured 2026-10-24 on champion exp_tput_batch_2e17 (val_bpb 1.088286, 956 steps, 2**17 batch):

- ADAM_BETAS (0.8,0.95) -> (0.8,0.99), beta1 pinned: 1.089357, delta +0.001071 (0.37 sigma).
- Muon beta2 0.95 -> 0.99 (train.py:261), momentum untouched: 1.088789, delta -0.000503 (0.18 sigma).

Both null. Together they cover 100% of params (AdamW 60% incl. the 4 value-embedding tables, Muon matrices 40%).
Conclusion: the "second-moment window is only 2.1% of a 956-step run, so it is too short" hypothesis is not
supported on either optimizer. This is a null, not a refutation (single seed each), but the pair removes the
group-idiosyncrasy explanation.

Calibration: the frac-delta -> bpb transfer from the earlier muon-momentum result (0.03 frac -> +0.00018 bpb)
held; a 0.04 frac change stayed inside noise. Price any future horizon-bracket arm at << sigma 0.002865 and
run it only on an idle slot.

Unmeasured degree of freedom left: beta1 (0.7,0.95) or (0.9,0.95).
