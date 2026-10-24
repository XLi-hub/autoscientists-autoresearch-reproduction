import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for q in ["Followup","Follow-up","head_dim","silu","silu(x).square","relu(x)"]:
    try:
        r=requests.get(f"{API}/workspaces/{MAIN}/search?q={q}",headers=HEADERS,timeout=20).json()
        res=r.get("results",[])
        print(f"\nq={q!r} -> {len(res)} hits")
        for h in res[:8]:
            print("   ", h.get("path"), "| matches:", len(h.get("matches",[])))
    except Exception as e:
        print(q, "ERR", e)
