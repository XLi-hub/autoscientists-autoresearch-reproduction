# Memory Index

- [Champion audit facts](feedback_champion-audit-autoresearch.md) - vocab 8192; param budget at MLP2 (41.94M, AdamW scope 60%); ASPECT_RATIO axis is QUANTIZED by HEAD_DIM rounding; the only 4 step-count-coupled constants; 956-step EMA fractions
- [Rebase discipline](feedback_rebase-discipline.md) - recompute param/FLOP/steps vs the CURRENT champion; VE is FLOP-free; old-base sigma is not authoritative
- [Saturation at 956 steps](findings_saturation-at-956-steps.md) — step/token channel is dead above ~950 steps; only zero-cost structure moved the metric (head_dim, 2.70 sigma)
