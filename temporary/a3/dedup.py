import json, re, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
teams={"throughput":"54202fe1-b766-43f1-b374-9e4ed188c153","gradient-quality":"032e5282-1362-4eef-9226-3d40299116aa","capacity":"3a33313e-18ff-4e17-9c47-66b54cfe576d"}
def pf(c):
    p=(c or "").split("---"); 
    try: return yaml.safe_load(p[1]) or {} if len(p)>=3 else {}
    except Exception: return {}
for name,ws in teams.items():
    q=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=H).json()
    fm=pf(q.get("content",""))
    print(f"\n=== {name} pending ===")
    for it in fm.get("pending",[]) or []:
        print(f"  {it.get('id')} | axis={it.get('axis')} dir={it.get('direction')} val={it.get('value')} | {str(it.get('diff'))[:110]}")
print("\n=== tails / followups ===")
for f in ["results/exp_aspect_ratio_32.md","results/exp_depth_10.md","results/exp_ve_all_layers.md","results/exp_batch_2e17.md","results/exp_batch_2e18.md","results/exp_muon_mom_ramp60.md"]:
    d=requests.get(f"{API}/workspaces/{MAIN}/files/{f}",headers=H).json()
    t=d.get("content","") or ""
    has="FOLLOWUP" in t.upper()
    print(f"\n--- {f} (followup={has}) tail ---")
    print(t[-900:])
