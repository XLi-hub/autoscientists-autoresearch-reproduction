import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
r=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",headers=HEADERS).json()
ver=r.get("version"); content=r.get("content","")
body=content.split("---",2)[-1]
fm=yaml.safe_load(content.split("---")[1])
pending=fm.get("pending",[]) or []
print("prev pending:",[p["id"] for p in pending])

# rebase notes on existing items
for it in pending:
    if it["id"]=="exp_gq_muon_ramp_progress":
        it["priority"]="high"
        it["rebase_note"]=("Current champion runs 433 optimizer steps/300s, so the step-based ramp "
            "min(step/300,1) reaches terminal momentum at 69% of the run (upstream intent: ~31%). "
            "This fix is now a LARGER perturbation than when filed: it reaches 0.95 at progress=0.3 "
            "(step ~130) instead of step 300. Diff unchanged and still applies to champion line 528-530/558.")
    if it["id"]=="exp_gq_warmdown_075":
        it["priority"]="medium"
        it["rebase_note"]=("Opposite arm of the 0.25/0.75 bracket. The 0.25 arm landed +0.0049 (inside 2-sigma) "
            "on the pre-compile base; this arm completes the 3-point bracket but is lower expected value on an "
            "undertrained base. Run after the adam-beta bracket and MLP-2x.")

new_items=[
 {"id":"exp_gq_adam_betas_lo","priority":"high","bold_bet":True,
  "diff":"ADAM_BETAS = (0.7, 0.90)   # was (0.8, 0.95); bracket low arm, affects ~54% of weights",
  "proposed_by":AGENT_NAME,"proposal_post":"63601f5a-5a16-4362-be7e-f6a0a6a1039d",
  "axis":"adam_betas","direction":"decrease","value":"(0.7, 0.90)","current_value":"(0.8, 0.95)",
  "bracket":"adam_betas_3pt_low","discussion_pending":True,"paper":None},
 {"id":"exp_gq_adam_betas_hi","priority":"high","bold_bet":True,
  "diff":"ADAM_BETAS = (0.9, 0.99)   # was (0.8, 0.95); bracket high arm, restores step-count-scaled EMA horizon",
  "proposed_by":AGENT_NAME,"proposal_post":"63601f5a-5a16-4362-be7e-f6a0a6a1039d",
  "axis":"adam_betas","direction":"increase","value":"(0.9, 0.99)","current_value":"(0.8, 0.95)",
  "bracket":"adam_betas_3pt_high","discussion_pending":True,"paper":None},
 {"id":"exp_gq_mlp_exp_2","priority":"high","bold_bet":False,
  "diff":"MLP_EXPANSION = 2   # was 3; -4.19M params (-9.1%), ~-11.7% FLOPs/token -> more optimizer steps",
  "proposed_by":AGENT_NAME,"proposal_post":"306479b7-c286-4e16-b198-71cf3a3f720e",
  "axis":"mlp_expansion","direction":"decrease","value":"2","current_value":"3",
  "rebase_note":"Step 1b2 different-mechanism follower (cheaper tokens/step, not fewer tokens/step).",
  "discussion_pending":True,"paper":None},
]
ids={it["id"] for it in pending}
for n in new_items:
    if n["id"] not in ids: pending.append(n)

# rank: minority-direction first, cold axes bonus, then by priority tier stated by proposer
# Simple deterministic ordering requested this cycle: high tier first (adam bracket, mlp2, ramp), then medium.
order={"high":0,"medium":1,"low":2}
pending.sort(key=lambda it: order.get(it.get("priority"),3))
fm["pending"]=pending
fm.setdefault("claims",{})
out="---\n"+yaml.safe_dump(fm,sort_keys=False)+"---\n"+body
resp=requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                  headers={**HEADERS,"If-Match":str(ver)},json={"content":out})
print("PUT",resp.status_code,resp.text[:300])
if resp.status_code!=200:
    rr=requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",headers=HEADERS).json()
    print("reread version",rr.get("version"))
