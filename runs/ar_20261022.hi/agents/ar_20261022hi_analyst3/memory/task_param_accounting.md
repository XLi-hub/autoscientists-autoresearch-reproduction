---
name: param-accounting-and-activation-decomposition
description: Champion param/FLOP split with vocab 8192, and the single-property decomposition of ReLU^2
type: finding
---

# Champion accounting (exp_batch_2e17) - load-bearing for every proposal

**vocab_size is 8192, not 32768** (GPTConfig's default is never used; `vocab_size = tokenizer.get_vocab_size()`).
50.3M params split:
- transformer matrices 25.2M (50%)
- value embeddings 16.8M (33%!) - 4 tables of 8192 x 512
- wte 4.19M, lm_head 4.19M
Per-token FLOPs ~239M: MLP ~42%, attention ~26%, embeddings/unembedding the rest (MLP is NOT 2/3 of
per-token FLOPs once embeddings are counted - older notes and review comments overstate MLP's share).
Consequence: MLP expansion 4->6 costs +21% FLOPs/token -> ~594 steps (-22%) -> ~0.022 val_bpb of step
penalty by the fitted slope (0.1159 per ln step below the 719-step knee).

# Single-property decomposition of the MLP activation
Champion is `F.relu(x).square()` (ReLU^2). Swapping the whole expression for `F.silu(x)` changes TWO
properties (rectifier AND squaring) - two reviewers rejected it.
- `relu^2 -> silu^2` = rectifier swap, squaring preserved (queued, post a98037fd).
- `relu^2 -> relu` = squaring off, rectifier preserved (follow-up candidate; cleanest test of the
  squared-ReLU primitive).
Never propose an activation change that alters both at once.
