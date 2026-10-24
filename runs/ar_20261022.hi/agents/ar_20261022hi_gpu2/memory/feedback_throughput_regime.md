---
name: throughput_regime
description: Step-count lever works only at fixed width; width cuts do not pay on this 300s/4080S budget
type: feedback
---

MEASURED (cycle 2, GPU1, seed 42, 300 s budget, RTX 4080S 32GB):

| config | steps | tokens | params | val_bpb |
|---|---|---|---|---|
| batch 2**18 (champion v4) | 373 | 97.8M | 50.3M | 1.170054 |
| batch 2**17 (champion v5) | 719 | 94.2M | 50.3M | **1.094037** |
| batch 2**17 + ASPECT_RATIO 32 | 1741 | 228.2M | 18.9M | 1.102844 |

Findings:
- Halving the batch at fixed width is a large KEEP (+0.076). Step time 830 -> 425 ms.
- Cutting width 512 -> 256 buys 2.4x tokens and 2.4x steps but LOSES 0.0088 bpb. The run is
  capacity-limited at 256 width; steps and capacity are not interchangeable.
- Loss was still falling at the end of both runs (no plateau) — both configs are mildly
  undertrained, but the 512-wide model converts extra steps into quality far better.
- Peak VRAM: 22.7 GB at width 512 / batch 64; 12.3 GB at width 256.
- Throughput: ~310k tok/s (width 512), ~758k tok/s (width 256).
