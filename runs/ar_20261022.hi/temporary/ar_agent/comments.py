import json, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; A="ar_20261022hi_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{A}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":A}
API="http://localhost:3000/api/v1"
for pid,label in [("ac356e17-9e01-415e-8e85-04bc8b8c456b","matrix_lr_bracket"),("f0fed967-15b3-4d55-92a4-7c728d20bb48","muon_ramp60")]:
    cs=requests.get(f"{API}/posts/{pid}/comments",headers=H).json().get("data",[])
    print(f"=== {label}: {len(cs)} comments")
    for c in cs:
        print("  by:", c.get("author") or c.get("agent") or c.get("author_name") or c.get("createdBy"), "|", (c.get("content") or "")[:900])
