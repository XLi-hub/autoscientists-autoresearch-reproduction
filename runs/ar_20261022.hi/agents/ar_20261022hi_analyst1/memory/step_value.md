---
name: step_value
description: RETRACTED step exchange rate; what replaced it (critical-batch crossing). Read before quoting any "-0.00027 per step" number.
type: feedback
---

# RETRACTED (cycle 4). Do not cite the old exchange rate.

## What was claimed and why it is wrong
Cycle 2 claimed ~-0.00027 val_bpb per +1% optimizer steps, from the single 2**18 -> 2**17 pair.
Cycle 4 got the third and fourth rungs of the same ladder and the claim does not survive:

| run | tokens/update | steps | val_bpb | delta |
|---|---|---|---|---|
| baseline | 2**19 | 193 | 1.195701 | - |
| exp_batch_2e18 | 2**18 | 373 | 1.170054 | -0.025647 |
| exp_batch_2e17 | 2**17 | 719 | 1.094037 | -0.076017 |
| exp_batch_2e16 | 2**16 | 1,396 | 1.094356 | +0.000319 |

Step count rises monotonically (193/373/719/1396); loss does not (down/down-down/flat). A law that
predicted -0.076 from 373->719 must predict at least that again from 719->1396; it predicted 0.0003.

## What replaced it (the working model)
The variable is **tokens per optimizer update relative to the critical batch size**, not step count.
262k tokens/update > critical (redundant gradient) -> halving recovered -0.076. 131k/update is at or
below the knee -> halving again bought nothing. The champion sits on the knee. Tokens seen were held
~constant across all four runs (91.5-97.8M), so this ladder cannot measure a tokens->loss rate at all.

## Rules that follow
1. Never justify a slot by "+N% steps". Justify by (a) quality-per-token (LR, decay, readout,
   capacity with a real memory for the token budget), or (b) raw tokens/s.
2. Decision band is the measured 2-sigma = **0.00604** (sigma 0.003019, two independent same-code
   pairs). Anything with expected |delta| under that is a coin flip.
3. "+X% steps at constant tokens" is only a mechanism if it crosses the critical batch; past the
   knee it is worth ~0. GQA (-7.9% FLOPs => +8.6% tokens) is worth ~0.005 by the external scaling
   rate - below the band.
4. Compounds, unlike steps: tokens/s raises the ceiling of every later run.

Old consequence (b) still holds for a different reason: a 5-6% FLOP trim is under the band.
