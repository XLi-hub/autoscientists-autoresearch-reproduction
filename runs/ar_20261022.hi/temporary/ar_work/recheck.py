import json, os, yaml, requests, subprocess
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
AGENT_NAME = "ar_20261022hi_analyst2"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "032e5282-1362-4eef-9226-3d40299116aa"
def gf(ws,p):
    r=requests.get(f"{API}/workspaces/{ws}/files/{p}", headers=HEADERS, timeout=30)
    return (r.json().get("content","") if r.ok else f"<<{r.status_code}>>"), (r.json().get("version",0) if r.ok else 0)
def pf(txt):
    p=txt.split("---"); return yaml.safe_load(p[1]) if len(p)>=3 else {}
c,_=gf(MAIN_WS_ID,"champion.md"); fm=pf(c)
print("CHAMP:", fm.get("experiment_id"), fm.get("val_bpb"), fm.get("timestamp"))
q,qv=gf(TEAM_WS_ID,"queue.md"); qfm=pf(q)
print("QUEUE v",qv,"claims:",qfm.get("claims"))
for it in qfm.get("pending",[]): print(" PEND:",it.get("id"),"|",it.get("priority"),"|",it.get("axis"),"|",it.get("direction"),"| dp:",it.get("discussion_pending"),"| by",it.get("proposed_by"))
for it in qfm.get("completed",[])[-6:]: print(" DONE:",it.get("id"),"|",it.get("outcome"),"|",it.get("val_score"))
print("\nRESULTS FILES:")
mf=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files", headers=HEADERS, timeout=30).json().get("files",[])
for f in mf:
    if f["path"].startswith("results/"): print(" ",f["path"],"| v",f.get("version"),"|",f.get("updatedAt"))
print("\nEXPERIMENTS TAIL:")
print(subprocess.run(["bash","-lc","tail -c 1600 /root/autodl-tmp/ar_20261022.hi/logs/experiments.jsonl"],capture_output=True,text=True).stdout)
print("\nNEW POSTS BODIES:")
for pid,label in [("a935d3ee-27c4-4c97-990d-ea1a1a090e88","2e16 RESULT"),
                  ("3292d69f-4c8b-4775-b06e-9029139b7ac3","gpu2 SUGGESTION"),
                  ("eadcb5fd-edfd-478e-b066-868c65424058","analyst1 unembedding"),
                  ("6c84e454-b57e-49a9-a7c6-24182787f013","ve_none"),
                  ("941a2318-e719-4a2e-b962-2f5089b49642","depth_6_w512"),
                  ("a1018d68-44ba-4f45-aff9-b27e246ec223","gqa_kv1")]:
    r=requests.get(f"{API}/posts/{pid}", headers=HEADERS, timeout=30).json()
    cs=requests.get(f"{API}/posts/{pid}/comments", headers=HEADERS, timeout=30).json().get("data",[])
    print(f"\n##### {label} ({pid}) comments={len(cs)}")
    print((r.get("content") or "")[:1700])
print("\nMY POSTS comments:")
for pid,label in [("c093a9b1-cfc0-49b4-90d4-f1f9260cd100","my muon_beta2"),("f7ce4fd9-7c55-44c4-8511-790351fdcbb4","my unembedding")]:
    cs=requests.get(f"{API}/posts/{pid}/comments", headers=HEADERS, timeout=30).json().get("data",[])
    print(label, len(cs), [ (x.get("author") or x.get("agent_name")) for x in cs])
