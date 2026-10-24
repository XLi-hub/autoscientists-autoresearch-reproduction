---
name: autoresearch-run-env-facts
description: "Operational fixes needed to run task-autoresearch on this 2x RTX 4080S host (launch.py gaps, uv hang, flash-attn cache)"
metadata:
  node_type: memory
  type: project
  originSessionId: 82136335-4b1d-419b-ac36-d8c4dbd9b0be
  modified: 2026-10-24T08:01:18.269Z
---

For AutoScientists `task-autoresearch` runs on this host (2x RTX 4080S 32GB, conda env `/root/autodl-tmp/envs/ar`):

- `launch.py <run> --task task-autoresearch` takes the "task-bundled repo" branch, which leaves `champion/` EMPTY and does not copy `repo/` into GPU agent workspaces. Seed `champion/{train.py,prepare.py,pyproject.toml,uv.lock}` from `repo/` and copy `repo/` into each `agents/*_gpuN/workspace/repo/` before dispatching.
- The workspace `champion.md` written by launch.py uses `metric: null`, but `ROLE-GPU`/`HEARTBEAT` read `metric_name` and compare against `champ.get(metric_name, inf)`. Rewrite it with `metric_name: val_bpb`, `direction: minimize`, `status: awaiting_baseline`, and NO `metric_value` key (a present-but-null key makes comparisons raise).
- Once GPU agents start writing `champion.md` themselves, they store the metric as `metric_value:`, which the `champ.get(metric_name, inf)` recipe reads as `inf` — every run then looks like a KEEP, and one agent actually false-promoted a DISCARD because of it. Keep BOTH keys in the frontmatter (`metric_value:` and a duplicated top-level `val_bpb:`) so either reader works.
- A training run is ~484s wall (300s budget + ~164s compile/startup/eval), longer with a max-autotune recompile. Run it as a background process with a blocking wait; the 600s foreground Bash limit is too tight.
- `launch.py` does not copy `scripts/` into the run dir; the profile's cycle-3 `meta_improve` hook imports `<run>/scripts/meta_diagnostics.py`. Install it (copy from a prior run) or meta-improvement crashes.
- `uv run python train.py` HANGS here (empty uv cache / no network). Use the active conda env directly: `python train.py`.
- flash-attn3 kernel loads only with `HF_HOME=/root/autodl-tmp/cache/huggingface` and `HF_HUB_OFFLINE=1` (the run-local `.cache/huggingface` is empty).
- Pristine `DEVICE_BATCH_SIZE=128` OOMs on 32GB; use 64. Training data + tokenizer are cached at `~/.cache/autoresearch`.
- `prepare.py` in `task-autoresearch/repo` is locally patched to `hf-mirror.com`; keep that patch.
- The ClawInstitute server must be started per session: `source env.sh && clawinstitute start` (log to `/root/autodl-tmp/logs/`). Token: `~/.clawinstitute/token`.

**Why:** These were all discovered by burning a cold-start cycle on failures that are cheap to avoid.
**How to apply:** Run the checklist above between `launch.py` and the first agent dispatch of any new `task-autoresearch` run.
