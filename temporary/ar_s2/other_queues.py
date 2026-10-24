import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAMS={"capacity":"d7c6f814-aab0-4029-a887-04345d274f9b","throughput":"6e6d22a0-cee2-4b39-b6df-799fea80be27","gradient-quality":"005cb9ec-6fce-4bba-9340-21c08ab914c5"}
for name,ws in TEAMS.items():
    if name=="gradient-quality": continue
    r=requests.get(f"{API}/workspaces/{ws}/files/queue.md",headers=HEADERS).json()
    c=r.get("content","")
    parts=c.split("---")
    fm=yaml.safe_load(parts[1]) if len(parts)>=3 else {}
    print("="*20,name,"queue v",r.get("version"),"="*20)
    print("claims:",fm.get("claims"))
    for it in fm.get("pending",[]) or []:
        print("PENDING", it.get("id"), "|", it.get("axis"),"|",it.get("direction"),"|",it.get("value"),"| by",it.get("proposed_by"),"| dp",it.get("discussion_pending"))
    for it in (fm.get("completed",[]) or [])[-8:]:
        print("COMPLETED", it.get("id"), "|", it.get("outcome"), it.get("val_score"))
    for f in requests.get(f"{API}/workspaces/{ws}/files",headers=HEADERS).json().get("files",[]):
        print("   file",f["path"],"v",f.get("version"))
# comments on my proposals
print("="*20,"COMMENTS ON MY POSTS","="*20)
posts=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=60",headers=HEADERS).json().get("data",[])
mine=[p for p in posts if p.get("title","").startswith("[PROPOSAL]") and "gq" in p.get("title","")]
for p in mine:
    cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=HEADERS).json().get("data",[])
    print("\nPOST",p["title"][:90],"id",p["id"],"comments",len(cs))
    for c in cs:
        print("   -",(c.get("author") or c.get("agent") or "?"),":",(c.get("content") or "")[:200].replace("\n"," "))
