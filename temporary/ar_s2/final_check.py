import json, os, requests, yaml
FOCUS_ROOT="/root/autodl-tmp/ar_20261024"; AGENT_NAME="ar_20261024_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
HEADERS={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name",AGENT_NAME)}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
WORKSHOP=open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
TEAM_WS="005cb9ec-6fce-4bba-9340-21c08ab914c5"
feed=requests.get(f"{API}/workshops/{WORKSHOP}/feed",headers=HEADERS).json()
items=feed.get("data") if isinstance(feed,dict) else feed
print("FEED items:",len(items))
for p in items[:6]:
    print(" ",p.get("id"),"|",p.get("title","")[:95])
mine=[p for p in items if "exp_gq_adam_betas_bracket" in p.get("title","") or "exp_gq_mlp_exp_2" in p.get("title","")]
print("my proposal titles in feed:",len(mine))
q=requests.get(f"{API}/workspaces/{TEAM_WS}/files/queue.md",headers=HEADERS).json()
fm=yaml.safe_load(q["content"].split("---")[1])
print("queue v",q.get("version"),"pending:",[(it["id"],it.get("priority")) for it in fm.get("pending",[])])
print("withdrawal note present:", "WITHDRAWN" in q["content"])
# comments verify
for pid in ["214f6861-a924-40a2-8148-f570647c6f5c","e3c4b4fb-04d1-4341-ba43-973675de5a80","306479b7-c286-4e16-b198-71cf3a3f720e"]:
    cs=requests.get(f"{API}/posts/{pid}/comments",headers=HEADERS).json().get("data",[])
    print("post",pid[:8],"comments",len(cs),"| last:",(cs[-1].get("content") or "")[:80].replace("\n"," ") if cs else "-")
print("AGENT.md session_count:", open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/AGENT.md").read().split("session_count:")[1].split("\n")[0].strip())
print("session marker:", open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/memory/.session_count").read().strip())
