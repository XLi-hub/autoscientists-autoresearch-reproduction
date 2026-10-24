import json, requests
FR="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FR}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"
for label,pid in [("mlp_expansion","3f67134f-1ead-4723-92e0-320f81514fbf"),
                  ("head_dim_64","f82bbb14-7582-4237-8cb2-9036757640d7"),
                  ("activation_silu","ff2578ae-14b9-44db-848d-24767546d204"),
                  ("ve_none","6c84e454-b57e-49a9-a7c6-24182787f013")]:
    c=requests.get(f"{API}/posts/{pid}/comments",headers=H).json().get("data",[])
    print(f"\n=== {label}: {len(c)} comments")
    for x in c:
        print("  author_id",x.get("author_id"),"|",(x.get("content") or "")[:700].replace("\n"," "))
