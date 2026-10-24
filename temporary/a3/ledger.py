import json, requests
from datetime import datetime, timezone
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FR}/WORKSPACE_ID").read().strip()
NOW=datetime.now(timezone.utc).isoformat()
raw=requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers=H).json()
ver=raw.get("version",0); c=raw.get("content","")
reps=[
("| total_batch_size | decrease | 2**16 | this cycle | unqueued | requires DEVICE_BATCH_SIZE 32; queue ONLY if 2**17 KEEPs | 2026-10-22 |",
 "| total_batch_size | decrease | 2**16 | this cycle | tested | **FLAT +0.00032 at 1396 steps** (exp_batch_2e16). Step lever saturates at ~719; do NOT halve again. | 2026-10-22 |"),
("| aspect_ratio | decrease | 32 | my exp_aspect_ratio_bracket | queued | **queued this cycle** - far low probe, 0.34x FLOPs => ~2.9x steps | 2026-10-22 |",
 "| aspect_ratio | decrease | 32 | my exp_aspect_ratio_bracket | tested | DISCARD -0.0088 at 1741 steps / 228M tokens: width 256 is capacity-limited; steps cannot buy back width. | 2026-10-22 |"),
("| value_embeddings | increase | all layers | analyst3 exp_ve_all_layers | queued | capacity | 2026-10-22 |",
 "| value_embeddings | increase | all layers | analyst3 exp_ve_all_layers | tested | DISCARD -0.0060 at 0 step cost (+33% params); extra embedding capacity is flat-to-harmful. | 2026-10-22 |"),
("| depth | increase | 10 | seed exp_depth_10 | queued | capacity; paired with DEVICE_BATCH_SIZE 32 | 2026-10-22 |",
 "| depth | increase | 10 | seed exp_depth_10 | tested | DISCARD -0.0215 at 221 steps (-41% steps); confounded with width 640. | 2026-10-22 |"),
("| mlp_expansion | increase | 6 | analyst3 exp_mlp_expansion | queued | capacity; serves as its Step 1e arm | 2026-10-22 |",
 "| mlp_expansion | increase | 6 | analyst3 exp_mlp_expansion | queued | Low priority. Premise weakened: costs ~19% steps, now below the ~719 knee; kept only as the Step 1e scale-up fallback. | 2026-10-22 |"),
("| mlp_expansion | decrease | 3 | analyst3 exp_mlp_expansion | queued | capacity; ~+11% steps | 2026-10-22 |",
 "| mlp_expansion | decrease | 3 | analyst3 exp_mlp_expansion | superseded | Superseded 2026-10-22: its only rationale was +11% steps, worthless after the step lever saturated. | 2026-10-22 |"),
]
for a,b in reps:
    if a in c: c=c.replace(a,b); print("OK  ",a[:52])
    else: print("MISS",a[:52])
# depth decrease row (fixed width) + new rows appended to table
c=c.replace("| depth | decrease | 6 | analyst3 exp_depth_6 | queued | capacity; do not re-propose | 2026-10-22 |",
            "| depth | decrease | 6 | analyst3 exp_depth_6 | superseded | Superseded: confounds depth with width (n_embd 384) and its +steps premise died with exp_batch_2e16. | 2026-10-22 |")
anchor="| x0_lambdas / resid_lambdas init | any | ? | Step 1c audit | unqueued | skip: 16 params total; revisit only if the capacity bracket lands | 2026-10-22 |"
new_rows = anchor + "\n" + "\n".join([
"| depth_at_fixed_width | decrease | 6 @ ASPECT_RATIO 85 | analyst3 exp_depth_6_w512 | withdrawn | Withdrawn by author 2026-10-22 before queueing: exp_batch_2e16 killed its +28%-steps premise; residual prediction -0.010..-0.026 = predictable DISCARD. | 2026-10-22 |",
"| value_embedding_layers | decrease | 0 of 8 | analyst3 exp_ve_none | queued | Step-1a far/opposite probe after the -0.0060 near-miss; zero step cost; completes the 0/4/8 bracket. | 2026-10-22 |",
"| activation_fn | replace | SiLU | analyst3 exp_activation_silu | queued | Step 1c blind spot (symbolic literal, not numeric): never varied. Zero params, <0.1% FLOPs => pure per-step-quality probe. | 2026-10-22 |",
])
if anchor in c:
    c=c.replace(anchor,new_rows); print("OK   appended 3 rows")
else: print("MISS anchor")
c=c.replace("version: 3","version: 4").replace("updated_at: \"2026-10-22T11:57:10.492081+00:00\"",f'updated_at: "{NOW}"\nlast_editor: ar_20261022hi_analyst3')
r=requests.put(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers={**H,"If-Match":str(ver)},json={"content":c})
print("ledger PUT:",r.status_code, "new version:", r.json().get("version"))
