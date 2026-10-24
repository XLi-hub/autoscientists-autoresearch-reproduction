import json, requests
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
creds = json.load(open(f"{FOCUS_ROOT}/agents/ar_20261024_gpu2/credentials.json"))
H = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json", "X-Agent-Name": "ar_20261024_gpu2"}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
for ws,name in ((MAIN,"main"),("005cb9ec-6fce-4bba-9340-21c08ab914c5","team")):
    fs = requests.get(f"{API}/workspaces/{ws}/files", headers=H).json().get("files", [])
    print(f"=== {name} ===")
    for f in fs:
        if f["path"].startswith(("results/","knowledge/")) or f["path"] in ("dead_ends.md","queue.md"):
            print(f"  {f['path']} v{f['version']} {f.get('updatedAt')} {f.get('updatedBy')}")
