import json, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/ar_20261022hi_analyst3/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM="3a33313e-18ff-4e17-9c47-66b54cfe576d"
def get(ws,path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}",headers=HEADERS).json()
for name,ws,p in [("dead_ends","team","dead_ends.md"),("strategy","team","strategy.md"),
                  ("noise_floor","team","knowledge/noise_floor.md"),("baseline_coverage","team","knowledge/baseline_coverage.md"),
                  ("axis_priors","team","knowledge/axis_priors.md"),("hypotheses","team","hypotheses.md"),
                  ("unqueued_axes","main","knowledge/unqueued_axes.md")]:
    w=TEAM if ws=="team" else MAIN_WS_ID
    d=get(w,p)
    print("\n"+"="*20,name,"(v",d.get("version"),")","="*20)
    print(d.get("content","")[:4500])
