import json, requests
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_analyst3"
creds=json.load(open(Path(FOCUS_ROOT)/"agents"/AGENT_NAME/"credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"
for pid,label in [("ff2578ae-14b9-44db-848d-24767546d204","activation_silu"),
                  ("6c84e454-b57e-49a9-a7c6-24182787f013","ve_none"),
                  ("f82bbb14-7582-4237-8cb2-9036757640d7","head_dim_64"),
                  ("3f67134f-1ead-4723-92e0-320f81514fbf","mlp_expansion")]:
    r=requests.get(f"{API}/posts/{pid}/comments",headers=HEADERS,timeout=20).json()
    cs=r.get("data",r if isinstance(r,list) else [])
    print(f"\n=== {label} {pid} comments={len(cs) if hasattr(cs,'__len__') else '?'}")
    if isinstance(cs,list):
        for c in cs:
            print("  -", c.get("author") or c.get("agent") or c.get("agent_name"), ":", (c.get("content") or "")[:400].replace("\n"," "))
