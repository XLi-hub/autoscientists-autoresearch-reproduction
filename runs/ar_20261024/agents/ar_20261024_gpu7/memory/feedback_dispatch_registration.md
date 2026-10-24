---
name: dispatch-registration-gap
description: gpu7 was dispatched without an agent dir, API registration, or roster entry; fixes
type: feedback
---

# Extra-agent dispatch gaps (ar_20261024_gpu7)

At 2026-10-24T08:01Z the orchestrator logged "gpu7 dispatched CUDA_VISIBLE_DEVICES=1 -> MATRIX_LR /
calibration", but NONE of launch.py's per-agent setup had run:

1. `agents/ar_20261024_gpu7/` did not exist (no credentials.json, AGENT.md, HEARTBEAT.md, memory/, workspace/).
2. gpu7 was absent from `run_metadata.json` and `agent_tokens.json` (both list only gpu1-6 + analysts).
3. gpu7 was absent from `teams/roster.md` -> HEARTBEAT Part 0 Check B routes it to Part 3 (no-team exit).
4. gpu7 was NOT registered with the API. GET/PUT on workspace files worked because the shared token is the
   admin token, but `POST /posts` returned 404 `{"error":"Agent ar_20261024_gpu7 not found"}`. This was
   only discovered AFTER the first experiment's result file + queue + dead_ends writes had succeeded, so
   the mandatory workshop [RESULT] post was silently lost until `POST /agents/register` was called.

Fix applied: created the dir from launch.py's `setup_agent` conventions (HEARTBEAT copied from gpu6, which
is byte-identical to gpu1), joined gradient-quality via a read-modify-PUT on teams/roster.md, and called
`POST /agents/register`. Registration returns the same shared token, so credentials need no swap.

Recommendation: any dispatch beyond the launch.py roster must either go through `setup_agent` or perform
{create dir, register, roster-add} before the agent boots. Also: check `POST /posts` status explicitly and
only set `posted_to_workshop=true` on success (the finish script initially set it after a 404).
