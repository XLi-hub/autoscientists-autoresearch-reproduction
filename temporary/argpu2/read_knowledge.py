import json, requests
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/ar_20261024_gpu2/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": "ar_20261024_gpu2"}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for ws,path in ((MAIN,"knowledge/noise_floor_data.md"),(MAIN,"results/baseline_shared_hw.md"),(MAIN,"results/exp_tput_batch_2e18.md"),("005cb9ec-6fce-4bba-9340-21c08ab914c5","knowledge/noise_floor.md")):
    r = requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=H).json()
    print(f"\n===== {path} (v{r.get('version')}) =====")
    print(r.get("content","")[:2500])
