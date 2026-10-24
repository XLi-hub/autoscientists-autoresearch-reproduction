"""Finalize the seed-43 calibration run: result md, noise-floor append, queue release, [RESULT] post.

NON-PROMOTABLE: never writes champion.md, never writes champion/SOURCE, never labels KEEP.
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
AGENT_NAME = "ar_20261024_gpu8"
AGENT_DIR = FOCUS_ROOT / "agents" / AGENT_NAME
WS = AGENT_DIR / "workspace"
EXP_ID = "exp_cal_champion_seed43"
creds = json.load(open(AGENT_DIR / "credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
     "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN = open(FOCUS_ROOT / "WORKSPACE_ID").read().strip()
WORKSHOP = open(FOCUS_ROOT / "WORKSHOP_NAME").read().strip()
NOW = datetime.now(timezone.utc).isoformat()


def pf(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


# ---- champion metric: parse strictly, HARD-FAIL on any inconsistency (never default to +inf) ----
_champ_raw = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
_champ = pf(_champ_raw)
if not _champ:
    raise RuntimeError("[HARD-FAIL] champion.md frontmatter did not parse")
if _champ.get("metric_name") != "val_bpb":
    raise RuntimeError(f"[HARD-FAIL] unexpected champion metric_name={_champ.get('metric_name')!r}")
_mv = _champ.get("metric_value")
_bpb = _champ.get("val_bpb")
if _mv is None or _bpb is None:
    raise RuntimeError(f"[HARD-FAIL] champion metric missing (metric_value={_mv!r}, val_bpb={_bpb!r})")
if abs(float(_mv) - float(_bpb)) > 1e-9:
    raise RuntimeError(f"[HARD-FAIL] champion metric inconsistent: metric_value={_mv} vs val_bpb={_bpb}")
CHAMP_METRIC = float(_mv)
print(f"[champion] parsed val_bpb={CHAMP_METRIC} (experiment {_champ.get('experiment_id')}, v{_champ_raw.get('version')})")


def body_of(resp):
    return resp.get("content", "").split("---", 2)[-1]


def put_with_retry(path, build, ws_id=MAIN, tries=4):
    """Read-modify-PUT with If-Match, retrying on 409 by re-reading."""
    for attempt in range(tries):
        raw = requests.get(f"{API}/workspaces/{ws_id}/files/{path}", headers=H).json()
        version = raw.get("version", 0)
        content = build(raw)
        r = requests.put(f"{API}/workspaces/{ws_id}/files/{path}",
                         headers={**H, "If-Match": str(version)},
                         json={"content": content})
        if r.status_code < 300:
            return r, raw
        print(f"[retry {attempt}] PUT {path} -> {r.status_code}")
    raise RuntimeError(f"PUT {path} failed after {tries} attempts: {r.status_code} {r.text}")


claim = json.loads((WS / "claim_record.json").read_text())
item = claim["item"]
TEAM_WS = claim["team_ws_id"]
MY_TEAM = claim["team"]
an = json.loads((WS / "analysis.json").read_text())
summary = an["summary"]
dyn = an["dynamics"]
our_metric = summary["val_bpb"]
assert our_metric is not None, "no val_bpb parsed from training log"
delta = our_metric - CHAMP_METRIC
outcome = "CALIBRATION"

tok_steady = dyn["tok_per_sec_steady_mean"]
steps = int(summary["num_steps"])

# ---------------- 1. noise floor append (n -> 4) ----------------
PAIR = {
    "metric_a": CHAMP_METRIC, "metric_b": our_metric,
    "abs_delta": abs(delta),
    "code_hash": "champion exp_tput_batch_2e17 (956-step base, AR64/w512/DEPTH8/MLP2/TOTAL 2**17/DBS64/compile max-autotune); same code, seed 42 vs seed 43",
    "gpu_a": 1, "gpu_b": 0,
    "agents": ["ar_20261024_gpu4", AGENT_NAME],
    "date": datetime.now(timezone.utc).date().isoformat(),
    "pair_type": "cross-seed + cross-GPU, same code",
    "steps_a": 956, "steps_b": int(summary["num_steps"]),
    "tokens_M_a": 125.3, "tokens_M_b": summary["total_tokens_M"],
    "note": ("seed-42 champion on GPU 1 vs seed-43 repeat on GPU 0 (both RTX 4080 SUPER 32GB). "
             "First same-code sigma measurement on the 956-step champion base; every prior pair "
             "was at <=2**19 batch. Non-promotable calibration run. NOTE: throughput differed "
             "(-1.9% tokens/steps, GPU 1 was concurrently busy), so this pair bounds cross-device "
             "same-code noise from above rather than isolating pure seed noise."),
    "final20_drop_a": None,   # champion's final-20% loss drop was never recorded
    "final20_drop_b": dyn["final20_drop"],
}


def build_noise(raw):
    fm = pf(raw)
    pairs = list(fm.get("pairs") or [])
    if any((p.get("metric_b") == our_metric and p.get("agents", [None])[-1] == AGENT_NAME) for p in pairs):
        print("[noise] pair already present, not appending twice")
        return raw["content"]
    pairs.append(PAIR)
    # same estimand the team used at n=3: sigma = sqrt(sum(delta_i^2)/(2n))
    s = sum(float(p["abs_delta"]) ** 2 for p in pairs)
    sigma = math.sqrt(s / (2 * len(pairs)))
    fm["pairs"] = pairs
    fm["sigma_estimate"] = round(sigma, 6)
    fm["n_pairs"] = len(pairs)
    fm["updated_at"] = NOW
    fm["updated_by"] = AGENT_NAME
    body = body_of(raw)
    bullet = (f"- pair 4: {CHAMP_METRIC:.6f} (GPU 1, seed 42, champion) vs {our_metric:.6f} "
              f"(GPU 0, seed 43), |delta| = {abs(delta):.6f} — identical 956-step champion code; "
              f"cross-seed + cross-GPU. First pair on the 2**17 base.\n")
    if "Pooled same-code sigma across 3 pairs" in body:
        body = body.replace(
            "Pooled same-code sigma across 3 pairs = **0.002865** (2-sigma band ~0.0057).",
            f"Pooled same-code sigma across {len(pairs)} pairs = **{sigma:.6f}** "
            f"(2-sigma band ~{2*sigma:.4f}).\n")
    if "- pair 4:" not in body:
        # insert the bullet after the last pair bullet
        lines = body.splitlines()
        last = max(i for i, ln in enumerate(lines) if ln.startswith("- pair "))
        lines.insert(last + 1, bullet.rstrip("\n"))
        body = "\n".join(lines) + ("\n" if body.endswith("\n") else "")
    return f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}"


r, nf_raw = put_with_retry("knowledge/noise_floor_data.md", build_noise)
nf_fm = pf({"content": r.json().get("content", "")} if r.json().get("content") else
           requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H).json())
nf_after = requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/noise_floor_data.md", headers=H).json()
nf_fm = pf(nf_after)
sigma_new = nf_fm.get("sigma_estimate")
n_pairs = nf_fm.get("n_pairs")
print(f"[noise] appended pair; sigma={sigma_new} n_pairs={n_pairs}")

# ---------------- 2. result markdown ----------------
device_note = (
    "Champion exp_tput_batch_2e17 ran on **GPU 1**; this calibration repeat ran on **GPU 0**. "
    "Both devices are NVIDIA GeForce RTX 4080 SUPER 32GB (same model, same host), so the "
    "comparison is fair; the pair is nonetheless cross-GPU (see `pair_type` in noise_floor_data.md)."
)

result_md = f"""---
exp_id: {EXP_ID}
type: calibration
promotable: false
outcome: {outcome}
metric_name: val_bpb
val_bpb: {our_metric:.6f}
champion_val_bpb: {CHAMP_METRIC:.6f}
delta_vs_champion: {delta:+.6f}
seed: 43
champion_seed: 42
gpu_device: 0
champion_gpu_device: 1
num_steps: {steps}
final20_loss_drop: {dyn['final20_drop']:.6f}
agent: {AGENT_NAME}
team: {MY_TEAM}
timestamp: {NOW}
---

# {EXP_ID} — seed-43 noise calibration (NON-PROMOTABLE)

## What was run

`champion/train.py` **verbatim**, with exactly one change: `torch.manual_seed(42)` /
`torch.cuda.manual_seed(42)` -> `43` at train.py:459-460. Verified by diff: 4 changed lines,
all four containing `manual_seed`; no other byte differs.

Champion base: `exp_tput_batch_2e17` (val_bpb 1.088286, AR 64 / width 512, DEPTH 8,
MLP_EXPANSION 2, TOTAL_BATCH_SIZE 2**17, DEVICE_BATCH_SIZE 64, grad_accum 1,
compile `max-autotune-no-cudagraphs`, 300s budget).

## Device fairness

{device_note}

## Result

| metric | value |
|---|---|
| **val_bpb (seed 43)** | **{our_metric:.6f}** |
| champion val_bpb (seed 42) | {CHAMP_METRIC:.6f} |
| delta (seed43 - seed42) | **{delta:+.6f}** |
| num_steps | {steps} |
| total_tokens_M | {summary['total_tokens_M']:.1f} |
| training_seconds | {summary['training_seconds']:.1f} |
| total_seconds (incl. compile/startup/eval) | {summary['total_seconds']:.1f} |
| steady tok/s | {tok_steady:,.0f} |
| peak_vram_mb | {summary['peak_vram_mb']:.1f} |
| mfu_percent | {summary['mfu_percent']:.2f} |

Outcome label: **{outcome}** — this run is explicitly non-promotable. It is NOT a KEEP
(regardless of sign), does NOT write `champion.md`, does NOT write `champion/SOURCE`, and
does NOT count in the KEEP tally. Its only purpose is to measure same-code run-to-run sigma
on the current 956-step champion base.

## Training dynamics — final-20% loss drop

Definition (primary): the debiased smoothed training loss at the first logged step with
`step >= 0.80 * N` minus the smoothed loss at the final logged step (N = {steps}).

| quantity | value |
|---|---|
| loss at 80% of run (step {dyn['step_at_80pct']}) | {dyn['loss_at_80pct']:.6f} |
| final smoothed loss (step {dyn['N_steps_last_logged']}) | {dyn['loss_final']:.6f} |
| **final-20% loss drop (absolute)** | **{dyn['final20_drop']:.6f}** |
| final-20% loss drop (% of loss at 80%) | {dyn['final20_drop_rel_pct']:.3f}% |
| final-20% loss drop (% of full-run loss range {dyn['loss_range_abs']:.4f}) | {dyn['final20_drop_pct_of_range']:.2f}% |
| mean loss, 80-90% window | {dyn['mean_loss_80_90']:.6f} |
| mean loss, 90-100% window | {dyn['mean_loss_90_100']:.6f} |
| robust final-10%-of-20 drop (means) | {dyn['final10_of_20_drop']:.6f} |

Interpretation: the smoothed loss fell {dyn['final20_drop']:.6f} over the final 20% — {dyn['final20_drop_rel_pct']:.2f}% of its level
at 80% but only {dyn['final20_drop_pct_of_range']:.2f}% of the full-run loss range. By the relative-to-level
criterion the loss is still dropping; by the HEARTBEAT ">1% of total range" criterion it is
marginal ({dyn['final20_drop_pct_of_range']:.2f}%). Verdict: **near-plateau but still marginally step-limited** — treat
step-increasing levers as slightly favourable, not strongly so, and use this number (not a
qualitative read) whenever the final-20% drop is compared between runs.

This metric has never been measured run-to-run before; this is the first data point.
**Only one seed exists for it so far — its variance is still unknown.** The analogous
dispersion for the final metric is now {sigma_new:.6f} (sigma at n={n_pairs}).

## Calibration takeaways

- Same-code same-budget |delta| on the current 956-step champion base: **{abs(delta):.6f}**.
- Updated pooled same-code sigma (n={n_pairs}, all pairs): **{sigma_new:.6f}**;
  2-sigma band ~**{2*sigma_new:.4f}**.
- Every previously recorded pair was measured at <= 2**19 batch (1.19-era base). This pair
  is the first on the 2**17 / 956-step base, which is what current promotion decisions use.
- Practical consequence: any promotion whose |delta| is below ~{2*sigma_new:.4f} is inside
  the same-code noise band and must be confirmed by a second seed before it is believed.
  {'Note: the delta observed here ({:+.6f}) is itself of that order, which is exactly why the gate exists.'.format(delta) if abs(delta) < 2*sigma_new else 'The delta observed here ({:+.6f}) is larger than the 2-sigma band, which would be an unusual draw — see the result caveats.'.format(delta)}

## Caveats

- Single pair (n=1) on this base: sigma_new is pooled with three <=2**19-era pairs, so it
  assumes the noise scale transfers across bases. That assumption is now partly tested but
  not established.
- **Throughput differed, which is part of the treatment:** this run completed **938 steps /
  122.9M tokens** at ~404.8K tok/s versus the champion's **956 steps / 125.3M tokens** at
  ~411.3K tok/s (-1.9% tokens, -1.6% tok/s). GPU 1 was simultaneously busy with another
  agent's training, so host/CPU contention (dataloader, compile launch overhead) plausibly
  explains the gap. Part of the +{delta:.6f} bpb delta can therefore be attributed to ~2%
  fewer optimizer steps rather than pure seed/hardware nondeterminism — this pair bounds
  cross-device same-code noise from ABOVE.
- This pair is cross-GPU as well as cross-seed (champion GPU 1, this run GPU 0). Pair 3 in
  the ledger has the same structure, so the pooled sigma is an upper bound on pure
  same-device same-code noise.
- The champion's own final-20% loss drop was never recorded, so that metric currently has
  n=1 and no variance estimate.

## Files

- train.py (stamped): `{WS}/repo/train_{EXP_ID}.py`
- stdout: `{WS}/train_{EXP_ID}.stdout`
- stderr: `{WS}/train_{EXP_ID}.stderr`
- analysis: `{WS}/analysis.json`
- champion source: `{FOCUS_ROOT}/champion/train.py` (unchanged by this run)
"""

r = requests.put(f"{API}/workspaces/{MAIN}/files/results/{EXP_ID}.md", headers=H,
                 json={"content": result_md})
print("[result md]", r.status_code)
if r.status_code >= 300:
    print(r.text); sys.exit(1)

# ---------------- 3. release claim + move item to completed ----------------
def build_queue(raw):
    q = pf(raw)
    q.setdefault("claims", {}).pop(AGENT_NAME, None)
    pending = q.get("pending") or []
    completed = q.get("completed") or []
    remaining = []
    moved = False
    for it in pending:
        if it.get("id") == EXP_ID:
            it = dict(it)
            it["completed_at"] = NOW
            it["completed_by"] = AGENT_NAME
            it["outcome"] = outcome
            it["val_score"] = our_metric
            it["val_bpb"] = our_metric
            it["delta_vs_champion"] = delta
            it["seed"] = 43
            it["gpu_device"] = 0
            it["final20_loss_drop"] = dyn["final20_drop"]
            it["noise_sigma_after"] = sigma_new
            it["noise_n_pairs_after"] = n_pairs
            it["calibration"] = True
            it["promotable"] = False
            completed.append(it)
            moved = True
        else:
            remaining.append(it)
    q["pending"] = remaining
    q["completed"] = completed
    body = body_of(raw)
    return f"---\n{yaml.safe_dump(q, sort_keys=False)}---{body}", moved


# special-case builder returning (content, moved); adapt to put_with_retry signature
def build_queue_content(raw):
    return build_queue(raw)[0]


r, _ = put_with_retry("queue.md", build_queue_content, ws_id=TEAM_WS)
print("[queue released]", r.status_code)

# ---------------- 4. [RESULT] post ----------------
roster = pf(requests.get(f"{API}/workspaces/{MAIN}/files/teams/roster.md", headers=H).json())
team_members = (roster.get("teams", {}).get(MY_TEAM, {}) or {}).get("members", [])

content = f"""## Experiment
{EXP_ID} — **calibration / non-promotable**. `champion/train.py` verbatim (exp_tput_batch_2e17,
956-step base); only train.py:459-460 seed 42 -> 43. Diff verified: 4 changed lines, all `manual_seed`.

Device: this run on **GPU 0**; the champion ran on **GPU 1**. Both RTX 4080 SUPER 32GB (same model/host) — fair comparison, but the pair is cross-GPU (recorded as `pair_type`).

## Result
val_bpb: **{our_metric:.6f}** (champion seed-42: {CHAMP_METRIC:.6f})
Delta (seed43 - seed42): **{delta:+.6f}**
Outcome: **{outcome}** (NOT a KEEP, NOT a DISCARD — non-promotable by construction)
num_steps: {steps} | tokens_M: {summary['total_tokens_M']:.1f} | tok/s: {tok_steady:,.0f} | training_s: {summary['training_seconds']:.1f} | peak_VRAM_MB: {summary['peak_vram_mb']:.1f}
(champion, for reference: 956 steps / 125.3M tokens / 411.3K tok/s — this run had -1.9% tokens at flat 300s budget; GPU 1 was concurrently busy, so part of the delta may be throughput, not seed.)

## Noise floor update (n = 3 -> {n_pairs})
New pair: {CHAMP_METRIC:.6f} (GPU1, seed42) vs {our_metric:.6f} (GPU0, seed43), |delta| = {abs(delta):.6f}.
Pooled same-code sigma is now **{sigma_new:.6f}** -> 2-sigma band ~**{2*sigma_new:.4f}**.
This is the FIRST pair measured on the 2**17 / 956-step champion base; all three earlier pairs were 1.19-era at <=2**19.

## Final-20% loss drop (first measurement ever)
loss at 80% of run (step {dyn['step_at_80pct']}): {dyn['loss_at_80pct']:.6f}
final smoothed loss: {dyn['loss_final']:.6f}
**final-20% drop = {dyn['final20_drop']:.6f}** ({dyn['final20_drop_rel_pct']:.3f}% of the 80% loss level; {dyn['final20_drop_pct_of_range']:.1f}% of the full-run loss range)
Its run-to-run variance is still unknown (n=1 for this metric).

## Team
{MY_TEAM}. Result file: `results/{EXP_ID}.md`. Champion unchanged (no champion.md write, no champion/SOURCE write).
"""

r = requests.post(f"{API}/posts", headers=H, json={
    "workshop": WORKSHOP,
    "title": f"[RESULT] {EXP_ID}: val_bpb={our_metric:.6f} (CALIBRATION — non-promotable)",
    "content": content,
    "notify_agents": team_members,
    "tags": [f"team:{MY_TEAM}", "type:result", "type:calibration", "outcome:calibration",
             "promotable:false"],
})
result_post_id = r.json().get("id") if r.ok else None
print("[post]", r.status_code, result_post_id)
if r.status_code >= 300:
    print(r.text)

# ---------------- 5. sentinel ----------------
rl_path = WS / "result_latest.json"
rl = json.loads(rl_path.read_text()) if rl_path.exists() else {}
rl.update({"status": "posted", "posted_to_workshop": True, "result_post_id": result_post_id,
           "posted_at": NOW, "val_score": our_metric, "outcome": outcome,
           "calibration": True, "promotable": False,
           "final20_loss_drop": dyn["final20_drop"],
           "noise_sigma_after": sigma_new, "noise_n_pairs_after": n_pairs})
rl_path.write_text(json.dumps(rl, indent=2, default=str))

(WS / "finalize_summary.json").write_text(json.dumps({
    "exp_id": EXP_ID, "val_bpb": our_metric, "delta": delta, "outcome": outcome,
    "sigma_after": sigma_new, "n_pairs_after": n_pairs,
    "final20_drop": dyn["final20_drop"], "result_post_id": result_post_id,
    "champion_untouched": True, "finished_at": NOW,
}, indent=2, default=str))
print("[done] calibration recorded; champion untouched")
