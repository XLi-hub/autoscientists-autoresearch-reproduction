"""Prepare gpu8 workspace: copy champion files, apply seed-only change, verify, join team, claim."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

FOCUS_ROOT = Path("/root/autodl-tmp/ar_20261024")
AGENT_NAME = "ar_20261024_gpu8"
AGENT_DIR = FOCUS_ROOT / "agents" / AGENT_NAME
creds = json.load(open(AGENT_DIR / "credentials.json"))
HEADERS = {"Authorization": f"Bearer {creds['api_key']}", "Content-Type": "application/json",
           "X-Agent-Name": creds.get("agent_name", AGENT_NAME)}
API = "http://localhost:3000/api/v1"
MAIN_WS_ID = open(FOCUS_ROOT / "WORKSPACE_ID").read().strip()
WORKSHOP = open(FOCUS_ROOT / "WORKSHOP_NAME").read().strip()
EXP_ID = "exp_cal_champion_seed43"
NOW = datetime.now(timezone.utc).isoformat()
REP = AGENT_DIR / "workspace" / "repo"


def pf(resp):
    content = resp.get("content", "")
    parts = content.split("---")
    return yaml.safe_load(parts[1]) if len(parts) >= 3 else {}


def body_of(resp):
    return resp.get("content", "").split("---", 2)[-1]


# ---------- 1. copy canonical champion files ----------
for fname in ("train.py", "prepare.py", "pyproject.toml", "uv.lock"):
    src = FOCUS_ROOT / "champion" / fname
    if not src.exists():
        src = FOCUS_ROOT / "task" / "repo" / fname
    shutil.copy(src, REP / fname)
champ_train = (FOCUS_ROOT / "champion" / "train.py").read_text()
print(f"[copy] champion/train.py -> {REP/'train.py'} ({len(champ_train)} bytes)")

# ---------- 2. apply ONLY the seed change ----------
code = champ_train
old = "torch.manual_seed(42)\ntorch.cuda.manual_seed(42)"
new = "torch.manual_seed(43)\ntorch.cuda.manual_seed(43)"
assert code.count(old) == 1, f"expected exactly 1 seed block, got {code.count(old)}"
patched = code.replace(old, new)
(REP / "train.py").write_text(patched)

# ---------- 3. verify: exactly the 2 seed lines differ, nothing else ----------
import difflib
diff = list(difflib.unified_diff(champ_train.splitlines(), patched.splitlines(),
                                 fromfile="champion/train.py", tofile="workspace/repo/train.py", lineterm=""))
print("\n".join(diff))
changed = [ln for ln in diff if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---"))]
assert len(changed) == 4, f"expected 4 +/- lines (2 old, 2 new), got {len(changed)}: {changed}"
assert all("manual_seed" in ln for ln in changed), f"non-seed change detected: {changed}"
print(f"[verify] OK: only seed lines changed ({len(changed)} +/- lines)")

# ---------- 4. join throughput team roster (gpu8 absent at dispatch) ----------
rr = requests.get(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md", headers=HEADERS).json()
fm = pf(rr)
teams = fm.get("teams", {}) or {}
joined_now = False
if AGENT_NAME not in teams["throughput"]["members"]:
    teams["throughput"]["members"].append(AGENT_NAME)
    new_content = f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body_of(rr)}"
    assert yaml.safe_load(new_content.split("---")[1]) == fm, "roster round-trip failed"
    r = requests.put(f"{API}/workspaces/{MAIN_WS_ID}/files/teams/roster.md",
                     headers={**HEADERS, "If-Match": str(rr.get("version", 0))},
                     json={"content": new_content})
    print("[roster] join throughput:", r.status_code)
    if r.status_code >= 300:
        print(r.text); sys.exit(1)
    joined_now = True
else:
    print("[roster] already in throughput")
TEAM_WS_ID = teams["throughput"]["workspace_id"]
print("[team] throughput ws =", TEAM_WS_ID)

# ---------- 5. claim exp_cal_champion_seed43 ----------
qr = requests.get(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md", headers=HEADERS).json()
qfm = pf(qr)
item = next((it for it in (qfm.get("pending") or []) if it.get("id") == EXP_ID), None)
assert item is not None, f"{EXP_ID} not in throughput pending list"
for k in ("axis", "direction"):
    assert item.get(k), f"queue item missing required tag {k}"
assert item.get("promotable") is False and item.get("calibration") is True, "item is not marked calibration/non-promotable"
qfm.setdefault("claims", {})[AGENT_NAME] = {"exp_id": EXP_ID, "claimed_at": NOW}
new_content = f"---\n{yaml.safe_dump(qfm, sort_keys=False)}---{body_of(qr)}"
assert yaml.safe_load(new_content.split("---")[1]) == qfm, "queue round-trip failed"
r = requests.put(f"{API}/workspaces/{TEAM_WS_ID}/files/queue.md",
                 headers={**HEADERS, "If-Match": str(qr.get("version", 0))},
                 json={"content": new_content})
print("[claim]", r.status_code)
if r.status_code >= 300:
    print(r.text); sys.exit(1)

record = {
    "exp_id": EXP_ID, "agent": AGENT_NAME, "team": "throughput",
    "joined_roster_this_cycle": joined_now, "team_ws_id": TEAM_WS_ID,
    "item": item, "claim_status": r.status_code,
    "seed_change": "42 -> 43 at train.py:459-460 only",
    "gpu_device": 0, "champion_gpu_device": 1,
    "claimed_at": NOW,
}
(AGENT_DIR / "workspace" / "claim_record.json").write_text(json.dumps(record, indent=2, default=str))
print(json.dumps(item, indent=2, default=str))
print("[ok] workspace ready at", REP)
