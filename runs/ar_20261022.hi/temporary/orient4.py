import json, os, requests, yaml, re
from pathlib import Path
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
creds = json.load(open(Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")/"credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
st = json.load(open("/tmp/part0_state.json")); TEAM_WS_ID = st["TEAM_WS_ID"]
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
c = q.get("content","")
parts = c.split("---")
fm = yaml.safe_load(parts[1])
print("PENDING:")
for it in fm.get("pending",[]) or []:
    print(" -", it.get("id"), "| pri", it.get("priority"), "| axis", it.get("axis"), it.get("direction"), it.get("value"), "| disc_pending", it.get("discussion_pending"), "| proposed_at", it.get("proposed_at"))
print("COMPLETED:")
for it in fm.get("completed",[]) or []:
    print(" -", it.get("id"), "|", it.get("outcome"), "| val", it.get("val_score"))
print("CLAIMS:", fm.get("claims"))
print("\nREVISION:", fm.get("revision"), fm.get("revision_note"))
