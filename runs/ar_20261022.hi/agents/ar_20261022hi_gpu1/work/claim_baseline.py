import json, os, requests
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME = "ar_20261022hi_gpu1"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": AGENT_NAME}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
NOW = datetime.now(timezone.utc).isoformat()

r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/baseline_lock.md",
                 headers={**HEADERS, "If-None-Match": "*"},
                 json={"content": f"holder: {AGENT_NAME}\nclaimed_at: {NOW}\n"})
print("PUT baseline_lock:", r.status_code, r.text[:300])
