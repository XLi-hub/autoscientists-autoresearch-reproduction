import json, requests
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/ar_20261024_gpu2/credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": "ar_20261024_gpu2"}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
TEAM_WS_ID = "005cb9ec-6fce-4bba-9340-21c08ab914c5"
for ws, name in ((MAIN_WS_ID,"main"),(TEAM_WS_ID,"team")):
    r = requests.get(f"{API}/workspaces/{ws}/search?q=muon", headers=HEADERS).json()
    print(f"=== search muon in {name} ===")
    for h in r.get("results", [])[:10]:
        print(" ", h.get("path"))
p = requests.get(f"{API}/posts/c0f6c228-eccf-488e-afb6-24b342684e02", headers=HEADERS).json()
print("=== proposal content ===")
print(p.get("content","")[:3000])
cm = requests.get(f"{API}/posts/c0f6c228-eccf-488e-afb6-24b342684e02/comments", headers=HEADERS).json().get("data", [])
print("=== comments ===")
for c in cm: print("-", str(c.get("content",""))[:300])
