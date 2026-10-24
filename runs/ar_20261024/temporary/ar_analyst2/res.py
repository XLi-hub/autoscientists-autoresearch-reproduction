import json, os, requests
AGENT_NAME="ar_20261024_analyst2"; FOCUS_ROOT="/root/autodl-tmp/ar_20261024"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for p in ["results/exp_cap_ar48_w384.md","results/exp_cap_window_ssll.md","results/exp_cap_ar48_mlp2.md","results/exp_tput_mlp_exp_2.md"]:
    r=requests.get(f"{API}/workspaces/{MAIN}/files/{p}",headers=HEADERS).json()
    print("\n"+"#"*100); print("###",p); print(r.get("content","")[:3200])
