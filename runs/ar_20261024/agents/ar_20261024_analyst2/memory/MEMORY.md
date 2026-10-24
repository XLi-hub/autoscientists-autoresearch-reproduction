# Memory Index

- [Step saturation boundary](finding_step_saturation_boundary.md) — per-update return collapses 16x between a 487-step and a 956-step base; proven unconfounded by two pure batch doublings. "Cheaper step" is dead above ~600 steps; capacity-UP arms are now free.
- [Muon ramp anchor](finding_muon_ramp_anchor.md) — reference run is 953 steps/300s; 300-step ramp is ~31% and may not complete on 4080S.
- [Step-coupled constants](finding_step_coupled_constants.md) — 193->433 steps re-scales Adam betas and the Muon ramp; wall-clock schedules unaffected. NOTE: superseded in part by the saturation boundary — at 956 steps the design point is restored and muon_ramp is a null.
- [API notes](feedback_api_notes.md) — analysts can write main knowledge ledger; queue needs If-Match.
- [Cross-team duplicate](feedback_cross_team_duplicate.md) — re-list the feed right before posting a proposal; withdraw rather than double-run.
- [WEIGHT_DECAY channel + capacity re-pricing](finding_weight_decay_channel.md) — the only first-order gq lever and the lr*wd*p de-confounder for MATRIX_LR; capacity numbers rebased to MLP=2
