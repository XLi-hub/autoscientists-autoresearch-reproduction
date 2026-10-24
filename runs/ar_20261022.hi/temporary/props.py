import json, requests
AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":AGENT_NAME}
API="http://localhost:3000/api/v1"; WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
data=requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=40",headers=H).json().get("data",[])
want=["exp_embedding_lr_bracket","exp_muon_beta2_bracket","exp_adam_beta1_bracket","exp_adam_beta2_bracket"]
for p in data:
    t=p.get("title","")
    if any(w in t for w in want):
        print("\n"+"="*100)
        print("TITLE:",t,"| id:",p["id"],"| author:",p.get("author_name"),"| comments:",p.get("comment_count"))
        print(p.get("content","")[:3000])
        cs=requests.get(f"{API}/posts/{p['id']}/comments",headers=H).json().get("data",[])
        print(f"\n-- {len(cs)} comments --")
        for c in cs:
            print("  ",c.get("author_name"),":",str(c.get("content",""))[:300].replace("\n"," "))
