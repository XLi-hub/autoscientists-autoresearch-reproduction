import json, requests, yaml
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
r=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=HEADERS,timeout=20).json()
c=r.get("content","")
print("VERSION", r.get("version"), "len", len(c))
parts=c.split("---")
print("n parts", len(parts))
fm=yaml.safe_load(parts[1])
print("keys", list(fm.keys()))
print("pending ids:", [i.get("id") for i in fm.get("pending",[])])
print("completed n:", len(fm.get("completed",[])))
print("completed ids:", [i.get("id") for i in fm.get("completed",[])])
print("BODY repr:", repr(parts[2][:500]) if len(parts)>2 else "NONE")
open("/tmp/queue_raw.yaml","w").write(c)
