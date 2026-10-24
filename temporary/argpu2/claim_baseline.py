import json, os, requests
from datetime import datetime, timezone
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()

r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md",
                 headers={**HEADERS, "If-None-Match": "*"},
                 json={"content": f"holder: {AGENT_NAME}\nclaimed_at: {NOW}\ngpu: 1\n"})
print("status:", r.status_code)
print(r.text[:800])
