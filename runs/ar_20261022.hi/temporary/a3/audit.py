import json, re, requests
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/ar_20261022hi_analyst3/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds["agent_name"]}
API="http://localhost:3000/api/v1"
MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip(); WS=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
posts=requests.get(f"{API}/posts?workshop={WS}&limit=60",headers=H).json().get("data",[])
print("total posts",len(posts))
kw=["silu","gelu","activation","relu","window_pattern","SSSS","tie","tying","depth_at_fixed","width","n_embd","aspect"]
blob=[]
for p in posts:
    d=requests.get(f"{API}/posts/{p['id']}",headers=H).json()
    c=d.get("content","") or ""
    cm=requests.get(f"{API}/posts/{p['id']}/comments",headers=H).json().get("data",[])
    blob.append((p["title"],c+"\n".join((x.get("content") or "") for x in cm),len(cm)))
for t,c,n in blob:
    hits=[k for k in kw if k.lower() in c.lower()]
    if hits: print(f"  HIT {hits} | {t[:90]} | comments={n}")
print("\n=== posts with zero comments (candidates to engage) ===")
for t,c,n in blob:
    if n==0: print("  0c:",t[:100])
print("\n=== result files ===")
for f in ["results/exp_depth_10.md","results/exp_ve_all_layers.md","results/exp_aspect_ratio_32.md","results/exp_batch_2e17.md"]:
    d=requests.get(f"{API}/workspaces/{MAIN}/files/{f}",headers=H).json()
    txt=d.get("content","")
    print("\n---",f,"---")
    print(txt[:1800])
print("\n=== main knowledge patterns/exhausted ===")
for f in ["knowledge/patterns.md","knowledge/exhausted.md"]:
    d=requests.get(f"{API}/workspaces/{MAIN}/files/{f}",headers=H).json()
    print("\n---",f,"---")
    print((d.get("content","") or "")[:1200])
