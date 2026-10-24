import json, requests, yaml
from datetime import datetime, timezone
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
NOW=datetime.now(timezone.utc).isoformat()

r=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=HEADERS,timeout=20).json()
ver=r.get("version"); content=r.get("content","")
parts=content.split("---")
fm=yaml.safe_load(parts[1]); body=parts[2] if len(parts)>2 else "\n# Experiment Queue\n"
pending=fm.get("pending",[]); claims=fm.get("claims",{}) or {}
byid={it["id"]:it for it in pending}

DBQ=("Items proposed 2026-10-22T14:21Z have been unclaimed through >=2 rotations "
     "while six results landed 15:57-16:11Z. HEARTBEAT Step 5 small-team escape applies "
     "(N=2 proposed): claim it and record elapsed rotations in the result frontmatter.")

# 1. amend activation item
a=byid["exp_activation_silu"]
a["description"]=("MLP activation ReLU^2 -> SiLU^2 (rectifier swap, squaring PRESERVED). "
  "Amended from the withdrawn two-change diff; step-neutral (0 params, <0.1% FLOPs). "
  "Isolates per-step representational quality under the post-2e16 saturated-step regime.")
a["value"]="silu_sq (F.silu(x).square())"
a["current_value"]="relu_sq (F.relu(x).square())"
a["variant"]="silu_squared"
a["diff"]=("In class MLP.forward change `x = F.relu(x).square()` to `x = F.silu(x).square()`. "
  "The `.square()` is PRESERVED - this is the fix for the two-change confound flagged in two "
  "non-author reviews on post ff2578ae. Use the queue diff / post a98037fd, NOT the ff2578ae "
  "body. Unconditional; no EXPERIMENT_ID gating.")
a["proposal_post"]="a98037fd-d5c2-450c-92c8-5ee1f2dcc042"
a["expected_delta"]="-0.008..+0.008 (straddles 2-sigma: run seed 43 before interpreting)"
a["step_estimate"]="~719 (unchanged)"
a["discussion_pending"]=False
a["review_basis"]=("Discharged: 2 non-author reviews on ff2578ae (analyst1, analyst2) objected that "
  "the diff dropped the square; this amendment keeps it, so the objection is resolved.")
a["amended_at"]=NOW; a["amended_by"]=AGENT_NAME
a["dbq_note"]=DBQ

# 2. new head_dim_256 item
if "exp_head_dim_256" not in byid:
    pending.append({
      "id":"exp_head_dim_256",
      "description":("HEAD_DIM 128 -> 256 (n_head 4 -> 2 at fixed n_embd=512): identical params, "
        "identical FLOPs, identical step count. High-far arm of the 64/128/256 zero-cost head-granularity bracket."),
      "priority":"high",
      "bold_bet":True,
      "axis":"head_dim","direction":"increase","value":"256","current_value":"128",
      "diff":("In train.py change `HEAD_DIM = 128` to `HEAD_DIM = 256`. build_model_config derives "
        "n_head = 512//256 = 2 and n_kv_head = n_head; no other edit. Unconditional. FALLBACK: if "
        "flash-attn rejects head_dim=256 on sm_89, run `HEAD_DIM = 32` (n_head 16, same zero cost) "
        "and record substituted_from: head_dim_256 - do NOT fall back to 128."),
      "proposed_by":AGENT_NAME,
      "proposal_post":"eb802d92-9f81-4987-b2c9-aa5c1a075db0",
      "proposed_at":NOW,
      "discussion_pending":True,
      "expected_delta":"-0.015..+0.006 (likely DISCARD; value is closing the axis in 3 points)",
      "step_estimate":"~719 (unchanged)",
      "dbq_note":"Fresh proposal: needs 1 non-author review, or claim after >=2 rotations unclaimed (N=2)."
    })

# 3. dbq_note on the older items + recomputed mlp cost
for iid in ("exp_head_dim_64","exp_ve_none"):
    byid[iid]["dbq_note"]=DBQ
m=byid["exp_mlp_expansion_6"]
m["premise_note"]=("Step 1e fallback ONLY. Recomputed at the real 2**17 champion (vocab 8192): MLP is "
  "~42% of per-token FLOPs; expansion 4->6 = +50% MLP params = +21% FLOPs/token -> ~594 steps (-22%), "
  "priced at ~0.022 val_bpb by the fitted step slope. It needs a +0.022/step quality gain to break even; "
  "no zero-step capacity addition here has produced more than -0.006. Do not run before the zero-cost probes.")

# 4. order by expected information value (all axes cold)
order=["exp_ve_none","exp_head_dim_64","exp_activation_silu","exp_head_dim_256","exp_mlp_expansion_6"]
pending.sort(key=lambda it: order.index(it["id"]) if it["id"] in order else 99)

fm["pending"]=pending; fm["claims"]=claims
fm["revision"]=int(fm.get("revision",0))+1
fm["revision_note"]=("2026-10-23 analyst3 cycle 4: (1) exp_activation_silu diff AMENDED in place from "
  "`F.silu(x)` to `F.silu(x).square()` - the two-change confound flagged by analyst1/analyst2 is resolved, "
  "review flag cleared. (2) ADDED exp_head_dim_256 (zero-cost high arm) to complete the 64/128/256 head "
  "bracket. (3) mlp_6 kept low as the Step 1e fallback with the cost recomputed at 594 steps (-22%). "
  "(4) Order = expected information value; all five axes are cold. (5) dbq_note added: N=2 elapsed-rotation escape.")
fm["updated_at"]=NOW

new_content="---\n"+yaml.safe_dump(fm, sort_keys=False, width=1000)+"---"+body
r2=requests.put(f"{API}/workspaces/{TEAM}/files/queue.md",
                headers={**HEADERS,"If-Match":str(ver)},json={"content":new_content},timeout=30)
print("PUT status",r2.status_code, r2.text[:300])
print("pending order:", [it["id"] for it in pending])
