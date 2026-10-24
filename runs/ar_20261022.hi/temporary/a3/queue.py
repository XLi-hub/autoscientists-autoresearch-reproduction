import json, requests, yaml
from datetime import datetime, timezone
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"
TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"; NOW=datetime.now(timezone.utc).isoformat()
raw=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
ver=raw.get("version",0); content=raw.get("content","")
parts=content.split("---")
fm=yaml.safe_load(parts[1]) if len(parts)>=3 else {}
body="---".join(parts[3:]) if len(parts)>=4 else "\n# Experiment Queue\n"
pending=fm.get("pending",[]) or []; completed=fm.get("completed",[]) or []
byid={it["id"]:it for it in pending}

new_items=[
 {"id":"exp_activation_silu","description":"MLP activation ReLU^2 -> SiLU. Step-neutral (0 params, <0.1% FLOPs); isolates per-step representational quality under the post-2e16 saturated-step regime.",
  "priority":"high","axis":"activation_fn","direction":"replace","value":"silu","current_value":"relu^2",
  "diff":"In class MLP.forward change `x = F.relu(x).square()` to `x = F.silu(x)`. Unconditional; no EXPERIMENT_ID gating.",
  "proposed_by":"ar_20261022hi_analyst3","proposal_post":"ff2578ae-14b9-44db-848d-24767546d204",
  "proposed_at":NOW,"discussion_pending":True,
  "expected_delta":"-0.006..+0.010","step_estimate":"~719 (unchanged)"},
 {"id":"exp_ve_none","description":"Remove value embeddings entirely (has_ve -> False). -16.8M params (-33%), zero step cost. Far/opposite arm of the 4/8/0 bracket.",
  "priority":"high","axis":"value_embedding_layers","direction":"decrease","value":"0",
  "current_value":"alternating (4 of 8)","bold_bet":True,
  "diff":"Change `def has_ve(layer_idx, n_layer): return layer_idx % 2 == (n_layer - 1) % 2` to `return False`. Safe: GPT.forward passes None when str(i) not in value_embeds, and attention guards `if ve is not None`. Unconditional.",
  "proposed_by":"ar_20261022hi_analyst3","proposal_post":"6c84e454-b57e-49a9-a7c6-24182787f013",
  "proposed_at":NOW,"discussion_pending":True,
  "expected_delta":"-0.010..+0.008","step_estimate":"~719 (unchanged)"},
]
# retire step-gain-premised items
for rid,reason in [
  ("exp_depth_6","SUPERSEDED: premise was +steps. exp_batch_2e16 showed 719->1396 steps is FLAT (+0.0003), so this is now a pure -58%-capacity probe with no compensating step gain. Also confounds depth with width (n_embd 384)."),
  ("exp_mlp_expansion_3","SUPERSEDED: premise was +11% steps. Step lever saturated (exp_batch_2e16 flat), so the -12.5% capacity cost no longer buys anything."),
]:
    if rid in byid:
        it=dict(byid[rid]); it.update({"completed_at":NOW,"completed_by":"ar_20261022hi_analyst3","outcome":"SUPERSEDED","reason":reason})
        completed.append(it); pending.remove(byid[rid])
# deprioritise mlp_6 (scale-up arm; keep only as Step 1e fallback)
if "exp_mlp_expansion_6" in byid:
    it=byid["exp_mlp_expansion_6"]
    it["priority"]="low"
    it["premise_note"]=("Weakened 2026-10-22: steps are saturated (2e16 flat) and this arm costs ~-19% steps, "
                        "which is now below the ~719-step knee; every zero-step-cost scale-up has DISCARDed "
                        "(ve_all -0.0060, depth_10 -0.0215). Retained only as the Step 1e scale-up fallback.")
if "exp_head_dim_64" in byid:
    byid["exp_head_dim_64"]["priority"]="high"
    byid["exp_head_dim_64"]["premise_note"]="Promoted 2026-10-22: zero params, zero FLOPs, zero step change -> the cleanest remaining structural probe."
ids={it["id"] for it in pending}
for it in new_items:
    if it["id"] not in ids: pending.append(it)
fm2={"claims":fm.get("claims",{}) or {},"pending":pending,"completed":completed,
     "revision":3,
     "revision_note":"2026-10-22 analyst3 cycle 3: step-count levers retired after exp_batch_2e16 (1396 steps FLAT, +0.00032). Queue pivoted to step-neutral quality probes: activation_silu, ve_none, head_dim_64. depth_6_w512 withdrawn before queueing (its +28%-steps premise died with 2e16).",
     "updated_at":NOW}
new_content="---\n"+yaml.safe_dump(fm2,sort_keys=False)+"---"+body
r=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",headers={**H,"If-Match":str(ver)},json={"content":new_content})
print("queue PUT:",r.status_code)
print("pending now:",[ (i["id"],i.get("priority")) for i in pending])
print("completed now:",[(i["id"],i.get("outcome")) for i in completed])
