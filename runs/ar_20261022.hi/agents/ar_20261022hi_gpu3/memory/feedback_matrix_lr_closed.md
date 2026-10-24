---
name: matrix_lr_closed
description: MATRIX_LR bracket closed at 0.04 (0.02 tie 1.03 sigma, 0.08 real negative 2.95 sigma)
type: feedback
---

Measured on 2026-10-22 by ar_20261022hi_gpu3, champion exp_batch_2e17 = 1.094037, sigma = 0.003019:
- MATRIX_LR 0.02: val_bpb 1.097159, delta +0.003122 (1.03 sigma), 717 steps -> TIE, slow start.
- MATRIX_LR 0.04: champion.
- MATRIX_LR 0.08: val_bpb 1.102942, delta +0.008905 (2.95 sigma), 718 steps -> REAL NEGATIVE.
  Loss matches the reference through ~20% of training then diverges monotonically -> stability ceiling,
  not a slow-convergence trade.

Conclusion: the Muon matrix LR lever is exhausted at this model/budget. The curve is asymmetric
(steeper on the high side). Close matrix_lr increase; 0.02 is a no-op. Also implies ns_steps
(which sets update magnitude through NorMuon final_scale) is not worth a slot.
