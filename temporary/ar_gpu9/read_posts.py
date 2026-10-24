import json, yaml, requests
from pathlib import Path
AGENT_NAME = "ar_20261024_gpu9"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()
recent = requests.get(f"{API}/posts?workshop={WORKSHOP}&limit=40", headers=HEADERS, timeout=30).json().get("data",[])
want = ["MATRIX_LR 0.04", "seed43", "champion_seed43"]
for p in recent:
    t = p.get("title","")
    if any(w in t for w in want):
        print("="*100)
        print("ID:", p["id"], "| created:", p.get("createdAt"), "|", t)
        d = requests.get(f"{API}/posts/{p['id']}", headers=HEADERS, timeout=30).json()
        print(d.get("content","")[:3000])
