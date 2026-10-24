import json,os,requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
A=FOCUS/"agents/ar_20261022hi_analyst1"
creds=json.load(open(A/"credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN="50594c0f-9a3a-4401-b2d6-c4fb60a9cca5"; TEAM="54202fe1-b766-43f1-b374-9e4ed188c153"
WS=open(FOCUS/"WORKSHOP_NAME").read().strip()
(A/"memory/.session_count").write_text("3")
md=(A/"AGENT.md").read_text()
for ws in (MAIN,TEAM):
    p="agents/ar_20261022hi_analyst1.md"
    cur=requests.get(f"{API}/workspaces/{ws}/files/{p}",headers=H)
    ver=cur.json().get("version") if cur.status_code<300 else None
    hh=dict(H)
    if ver is not None: hh["If-Match"]=str(ver)
    r=requests.put(f"{API}/workspaces/{ws}/files/{p}",headers=hh,json={"content":md,"message":"analyst1 c4: AGENT.md update (session 3, retracted exchange rate)"})
    print("AGENT.md",ws[:8],r.status_code,"v",ver)
# feed check
posts=requests.get(f"{API}/posts?workshop={WS}&limit=25",headers=H).json()["data"]
for p in posts:
    if p["id"] in ("b06f518e-b57c-4d8d-a027-832905665b28","1c0be3ac-c6a9-4e3a-b06d-e5c5c84aad0b"):
        print("FEED ok:",p["id"][:8],p["title"][:70])
q=requests.get(f"{API}/workspaces/{TEAM}/files/queue.md",headers=H).json()
print("queue v",q.get("version"),"| items:",q["content"].count("- exp_id:"))
print("ledger main v",requests.get(f"{API}/workspaces/{MAIN}/files/knowledge/unqueued_axes.md",headers=H).json().get("version"))
