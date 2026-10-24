import json, os, yaml, requests
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "032e5282-1362-4eef-9226-3d40299116aa"
def getfile(ws, path):
    r = requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS, timeout=30)
    return r.json().get("content","") if r.ok else f"<<404>>"

for p in ["results/exp_batch_2e17.md","results/exp_aspect_ratio_32.md","results/exp_depth_10.md","results/exp_ve_all_layers.md"]:
    print(f"\n########## {p} ##########")
    print(getfile(MAIN_WS_ID,p)[:4500])

print("\n########## MAIN knowledge/unqueued_axes.md ##########")
print(getfile(MAIN_WS_ID,"knowledge/unqueued_axes.md")[:5000])
for p in ["knowledge/axis_priors.md","knowledge/baseline_coverage.md","knowledge/noise_floor.md"]:
    print(f"\n########## TEAM {p} ##########")
    print(getfile(TEAM_WS_ID,p)[:3000])
print("\n########## logs ##########")
import subprocess
print(subprocess.run(["bash","-lc","ls -la /root/autodl-tmp/ar_20261022.hi/logs/ && wc -l /root/autodl-tmp/ar_20261022.hi/logs/experiments.jsonl 2>/dev/null; tail -c 3000 /root/autodl-tmp/ar_20261022.hi/logs/experiments.jsonl 2>/dev/null"],capture_output=True,text=True).stdout)
