import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN_WS_ID=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip(); WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
# full ledger tail
r=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/knowledge/unqueued_axes.md",headers=HEADERS).json()
c=r.get("content","")
print("=== LEDGER TAIL ===")
print(c[5500:])
# knowledge files
for p in ["knowledge/patterns.md","knowledge/exhausted.md","task.md"]:
    rr=requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/{p}",headers=HEADERS).json()
    print("\n===",p,"===")
    print(rr.get("content","")[:2500])
# discussion post + all comments
posts=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=60",headers=HEADERS).json().get("data",[])
disc=[p for p in posts if "[DISCUSSION]" in p.get("title","")]
for p in disc:
    full=requests.get(f"{API}/posts/{p['id']}",headers=HEADERS).json()
    print("\n=== DISCUSSION",p["title"],"===")
    print((full.get("content") or "")[:4000])
    cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[])
    for cc in cs:
        print("  -",(cc.get("content") or "")[:800].replace("\n"," "))
# axis mention counts across posts+comments
import re
alltext=[]
for p in posts:
    alltext.append((p.get("id"),p.get("title","")+" "+(requests.get(f"{API}/posts/{p['id']}",headers=HEADERS).json().get("content") or "")))
    for cc in requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[]):
        alltext.append((p.get("id"),cc.get("content") or ""))
for kw in ["MATRIX_LR","matrix_lr","ADAM_BETAS","adam_betas","adam beta","mtp","beta1","beta2","weight_decay","WEIGHT_DECAY"]:
    hits=set(pid for pid,t in alltext if kw.lower() in t.lower())
    print(f"MENTION {kw}: {len(hits)} posts {sorted(hits)}")
