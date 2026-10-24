import json, os, requests, yaml
from pathlib import Path
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "032e5282-1362-4eef-9226-3d40299116aa"
def get(w,p):
    return requests.get(f"{API}/workspaces/{w}/files/{p}", headers=HEADERS).json().get("content","")
print("=== TASK.MD (main ws) ==="); print(get(MAIN_WS_ID,"task.md")[:6000])
print("=== TEAM strategy.md ==="); print(get(TEAM_WS_ID,"strategy.md")[:4000])
print("=== TEAM hypotheses.md ==="); print(get(TEAM_WS_ID,"hypotheses.md")[:4000])
print("=== TEAM dead_ends.md ==="); print(get(TEAM_WS_ID,"dead_ends.md")[:2000])
print("=== MAIN knowledge/exhausted.md ==="); print(get(MAIN_WS_ID,"knowledge/exhausted.md")[:2000])
print("=== MAIN knowledge/patterns.md ==="); print(get(MAIN_WS_ID,"knowledge/patterns.md")[:3000])
