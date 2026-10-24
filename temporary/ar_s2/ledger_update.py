import json, os, requests, yaml, time
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
DATE="2026-10-24"

for attempt in range(3):
    r=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/unqueued_axes.md",headers=HEADERS).json()
    ver=r.get("version",0); content=r.get("content","")
    lines=content.split("\n")
    out=[]
    updates={}
    def setrow(axis,status,reason):
        updates[axis]=(status,reason)
    setrow("total_batch_size","tested","2**18 KEEPed: 1.192708 -> 1.169258, 193 -> 374 steps. Now the champion base.")
    setrow("total_batch_size_far","unqueued","DUE NOW: the 2**18 result resolved KEEP (+0.0235, 4x the 2-sigma band). 2**17 is the justified far probe for the throughput lane; gq does not double-file it.")
    setrow("compile_mode","tested","KEEPed: 1.158107 -> 1.147892, 410 -> 433 steps (+5.8% tok/s). Adds ~148 s wall outside the 300 s budget.")
    setrow("device_batch_size","tested","Memory adaptation only: 128 OOMs at 32GB; 64 is the fit value. Now grad_accum 2 at TOTAL_BATCH 2**18. Not a quality axis.")
    setrow("muon_momentum","tested","0.98 arm DISCARD with paired effect +0.00018 (32x inside noise), on the stale 196-step base. Axis OPEN, not closed; retest only after the ramp time-base fix lands.")
    setrow("muon_momentum_ramp","queued","Still queued (exp_gq_muon_ramp_progress). REBASED this cycle: at 433 steps the step-based ramp reaches terminal at 69% of the run (intent ~31%), so the fix is now a LARGER perturbation than when filed.")
    setrow("warmdown_ratio","tested","0.25 arm DISCARD at +0.0049 (inside 2-sigma) with no step-count gain; axis OPEN. The 0.75 row below still completes the 3-point bracket.")
    setrow("adam_betas","queued","Bracket filed this cycle: high (0.9,0.99) + low (0.7,0.90), champion midpoint. ~54% of weights. Step-count rescaled (433 vs 193 steps).")
    setrow("warmup_ratio","unqueued","Still unqueued: anti-throughput at a 300 s budget; low priority.")
    setrow("unembedding_lr","unqueued","Still unqueued (gq). Defer until after the adam-beta bracket; do not pair with embedding_lr.")
    setrow("embedding_lr","unqueued","Still unqueued (gq). ~45% of weights (wte + value_embeds). Candidate after adam_betas and matrix_lr.")
    setrow("ns_steps","unqueued","Still unqueued (gq update-geometry probe); <0.1% FLOPs so it cannot pay via throughput.")
    setrow("muon_beta2","unqueued","Still unqueued (gq NorMuon memory-length axis). Now better motivated: memory length is in steps and the run got 2.24x longer.")
    setrow("dataloader_prefetch","unqueued","Step time is now 0.69 s (300/433), which crosses the ledger's '<1 s -> revisit' threshold. Still estimated <5% of step time; measure before proposing.")
    setrow("mlp_expansion","queued","3x KEEPed (1.169258 -> 1.158107). 5x arm still queued by throughput; gq filed the 2x arm this cycle -> a 2/3/5 bracket when all three land.")
    setrow("window_pattern_speed","unqueued","Now a clean 0-parameter throughput control (SSSS = -2.6% FLOPs, no capacity change). Low priority but higher value than when first logged.")
    for ln in lines:
        stripped=ln.strip()
        if stripped.startswith("|") and not stripped.startswith("|---") and not stripped.startswith("| axis |"):
            cells=[c.strip() for c in stripped.strip("|").split("|")]
            if cells and cells[0] in updates:
                status,reason=updates[cells[0]]
                cells[4]=status; cells[5]=DATE; cells[6]=reason
                ln="| "+" | ".join(cells)+" |"
        out.append(ln)
    content="\n".join(out)
    # frontmatter version bump
    content=content.replace("version: 4","version: 5",1)
    content=content.replace('updated_at: "2026-10-24T06:48:00Z"','updated_at: "2026-10-24T07:25:00Z"',1)
    addon = """
| matrix_lr | increase | 0.08 from 0.04 | analyst2 c2 audit (ledger gap) | unqueued | 2026-10-24 | NEW ROW: the main Muon LR was never ledgered. Untested; the batch halved twice since upstream tuning, so the per-step gradient noise changed. Next gq candidate after adam_betas. |
| matrix_lr | decrease | 0.02 from 0.04 | analyst2 c2 audit (ledger gap) | unqueued | 2026-10-24 | NEW ROW: bracket counterpart; a 3-point bracket {0.02, 0.04, 0.08} is required by Step 3.4 (cold numeric axis). |
| mlp_expansion | decrease | 2 (from 3) | analyst2 c2; proposal 306479b7 | queued | 2026-10-24 | gq Step 1b2 follower: cheaper tokens/step -> more optimizer steps. -4.19M params (-9.1%), ~-11.7% FLOPs/token. |
| adam_betas | decrease | (0.7, 0.90) from (0.8, 0.95) | analyst2 c2; proposal 63601f5a | queued | 2026-10-24 | low arm of the adam_betas 3-point bracket; direction control for the step-count-rescaling hypothesis. |

## Cycle 2 decisions (analyst2, 2026-10-24T07:25Z)

- Champion moved 1.192708 -> 1.147892 via three throughput KEEPs; all three bought more optimizer
  steps in the fixed 300 s budget (193 -> 433). The 2**18 KEEP won while processing fewer tokens
  (98.0M vs 101.2M), so the response is to update count, not token count.
- Two gq results are NOISE-CONTAMINATED and were re-opened in dead_ends.md: muon_momentum 0.98
  (paired +0.00018) and warmdown 0.25 (+0.0049). Neither axis is closed.
- The step-count-coupled gq constants (Adam betas, Muon momentum ramp) are the ones the KEEPs
  invalidated, because their memory horizon is defined in steps. Everything wall-clock-based
  (LR multiplier, weight decay annealing) is unaffected and stays as tuned.
- Two proposals filed this cycle: exp_gq_adam_betas_bracket (63601f5a, bold hypothesis-tension)
  and exp_gq_mlp_exp_2 (306479b7, Step 1b2 different-mechanism follower).
- Not queued this cycle, with reasons: MATRIX_LR x2 (next candidate, needs its own rotation),
  EMBEDDING_LR / UNEMBEDDING_LR (wait for adam_betas), WEIGHT_DECAY and FINAL_LR_FRAC (belong in
  the same "wall-clock schedule, not step-coupled" family; low expected value now),
  TOTAL_BATCH 2**17 (throughput's lane, flagged as due), dataloader_prefetch (threshold met, still
  estimated <5% of step time).
"""
    content=content.rstrip()+"\n"+addon
    resp=requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/unqueued_axes.md",
        headers={**HEADERS,"If-Match":str(ver)},json={"content":content})
    print("PUT",resp.status_code,resp.text[:200])
    if resp.status_code==200:
        break
    time.sleep(2)
