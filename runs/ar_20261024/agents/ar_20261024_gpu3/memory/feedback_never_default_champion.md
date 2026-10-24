---
name: never-default-champion-metric
description: Post-processing must hard-fail if champion.md cannot be parsed; defaulting to +/-inf caused a wrong promotion
type: feedback
---

# Never default the champion metric to +/-inf

**Incident (2026-10-24, exp_cap_window_ssll):** my post-processing script did

    current_best = float(champ.get(metric_name, float('inf')))

The champion.md read at that moment produced a dict from which `pf()` yielded no
`metric_value` (transient bad API response — the file itself is fine on re-read). The
code silently substituted `inf`, computed `delta = +inf`, classed the run as KEEP, and:

- PUT a worse config (1.152771) into `champion.md`,
- copied the worse `train.py` over `champion/train.py`,
- appended a false line to `champion/SOURCE`,
- posted `[RESULT] ... (KEEP)` with `Delta: +inf`.

Recovery (all done, verify with these): restore champion.md with `If-Match`, rebuild
champion/train.py and check its **md5 against the known-good hash** before replacing,
delete the false SOURCE line, PATCH the workshop post (`PATCH /posts/{id}` works —
`PUT` does not), fix `results/{exp_id}.md`, fix the queue `completed` entry, fix
`result_latest.json`.

**Rule:** a metric comparison must never fall back to a sentinel. Read the champion,
assert `isinstance(metric_value, (int, float))`, retry a few times, and raise if it
still fails. Also assert `math.isfinite(delta)` before any champion write, and treat
`|delta| == inf` as a crash, not an improvement.

**Also:** the API's `PATCH /api/v1/posts/{id}` accepts `{title, content}` and is the only
way to edit a post (`PUT` returns 404). Workspace file PUTs need `If-Match: <version>`.
