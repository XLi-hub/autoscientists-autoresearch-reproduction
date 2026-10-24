import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for p in ["results/exp_muon_beta2_hi.md","results/exp_wd_0p0.md","results/exp_gqa_kv1.md","results/exp_embedding_lr_hi.md","results/exp_ve_all_layers.md"]:
    c=requests.get(f"{API}/workspaces/{MAIN}/files/{p}",headers=HEADERS,timeout=20).json().get("content","")
    print("="*20,p,"="*20); print(c[:2200])
