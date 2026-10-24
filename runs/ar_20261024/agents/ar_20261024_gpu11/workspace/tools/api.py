import json, os, yaml, requests
from pathlib import Path

FOCUS_ROOT = "/root/autodl-tmp/ar_20261024"
AGENT_NAME = "ar_20261024_gpu11"
AGENT_DIR = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}")
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = os.environ.get("CLAWINSTITUTE_API", "http://localhost:3000/api/v1")
MAIN_WS_ID = open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
WORKSHOP = open(f"{FOCUS_ROOT}/WORKSHOP_NAME").read().strip()

def parse_frontmatter(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

def get_file(ws, path):
    return requests.get(f"{API}/workspaces/{ws}/files/{path}", headers=HEADERS).json()

def list_files(ws):
    return requests.get(f"{API}/workspaces/{ws}/files", headers=HEADERS).json().get("files", [])

def posts(limit=50):
    return requests.get(f"{API}/posts?workshop={WORKSHOP}&limit={limit}", headers=HEADERS).json().get("data", [])

def comments(post_id):
    return requests.get(f"{API}/posts/{post_id}/comments", headers=HEADERS).json().get("data", [])
