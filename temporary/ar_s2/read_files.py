import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
AGENT_DIR=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds=json.load(open(AGENT_DIR/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
def get(ws,path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=HEADERS).json()
paths_main=["results/exp_gq_warmdown_025.md","results/exp_gq_muon_mom_098.md","results/exp_tput_compile_autotune.md",
 "results/exp_tput_mlp_exp_3.md","results/exp_tput_batch_2e18.md","results/baseline_shared.md","results/baseline_shared_hw.md",
 "knowledge/noise_floor_data.md","baseline_lock.md","knowledge/unqueued_axes.md"]
for p in paths_main:
    r=get(MAIN_WS_ID,p)
    print("\n"+"="*25,p,"v",r.get("version"),"="*25)
    print(r.get("content","")[:6000])
paths_team=["queue.md","dead_ends.md","strategy.md","knowledge/noise_floor.md","knowledge/axis_priors.md","knowledge/baseline_coverage.md","hypotheses.md"]
for p in paths_team:
    r=get(TEAM_WS_ID,p)
    print("\n"+"="*25,"TEAM/"+p,"v",r.get("version"),"="*25)
    print(r.get("content","")[:8000])
