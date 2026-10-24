---
name: noise_floor_and_inert_axes
description: Measured seed sigma 0.00302 -> 0.006 keep-bar; EMA-horizon axes are inert at 719 steps
type: feedback
---

# Noise floor and inert axes (2026-10-22, cycle 4)

- **Measured per-seed sigma = 0.00302** from two same-code seed pairs
  (exp_warmdown_070: 1.093748/1.097886; exp_adam_beta2_hi: 1.093839/1.098235).
  The old hardcoded 0.003 "conservative band" was therefore 1 sigma, not 2.
  Practical keep-bar: **|delta| > 0.006**.
- **EMA-horizon knobs are inert on both optimizers at 719 steps:**
  AdamW beta2 0.95->0.99 = +0.0002 (0.07 sigma); NorMuon beta2 0.95->0.99 = +0.0006 (0.19 sigma).
  Do not spend slots on finer beta2 brackets.
- **EMBEDDING_LR 0.6->1.2** (effective 0.735->1.47 on 42% of params) = +0.0027 (0.91 sigma),
  and behind champion train loss at every checkpoint (+0.032 @20% narrowing to +0.010 @99%).
  The fast AdamW group is not LR-starved; it is at/past its optimum.
- Only large lever observed in this run remains the batch/step change (2**18->2**17, -0.076).
