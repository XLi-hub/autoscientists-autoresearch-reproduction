import json, requests, yaml
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu2"; TEAM_WS_ID="005cb9ec-6fce-4bba-9340-21c08ab914c5"
creds = json.load(open(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": AGENT_NAME}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
q = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=H).json()
c=q.get("content","").split("---"); fm=yaml.safe_load(c[1])
for it in fm["pending"]:
    if it["id"]=="exp_gq_warmdown_025":
        print(json.dumps(it, indent=2))
        pid = it.get("proposal_post")
        if pid:
            p = requests.get(f"{API}/posts/{pid}", headers=H).json()
            print("\n=== proposal ===\n", p.get("content","")[:2000])
            cs = requests.get(f"{API}/posts/{pid}/comments", headers=H).json().get("data",[])
            print("=== comments ===")
            for x in cs: print("-", str(x.get("content",""))[:400])
ch = requests.get(f"{API}/workspaces/{MAIN}/files/champion.md", headers=H).json()
print("\nchampion v", ch.get("version"), "updatedBy", ch.get("updatedBy"))
