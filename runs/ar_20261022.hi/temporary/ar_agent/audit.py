import json, requests, yaml, re
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; A="ar_20261022hi_analyst2"
creds=json.load(open(f"{FOCUS_ROOT}/agents/{A}/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":A}
API="http://localhost:3000/api/v1"; MAIN=open(f"{FOCUS_ROOT}/WORKSPACE_ID").read().strip()
print("=== baseline_lock.md ===")
print(requests.get(f"{API}/workspaces/{MAIN}/files/baseline_lock.md",headers=H).json().get("content","")[:2000])
print("=== champion.md ===")
print(requests.get(f"{API}/workspaces/{MAIN}/files/champion.md",headers=H).json().get("content","")[:1500])
code=open(f"{FOCUS_ROOT}/champion/train.py").read()
print("\n=== numeric literal inventory (top-level + dataclass + inline) ===")
for pat,name in [(r"^\s*([A-Z_][A-Z0-9_]*)\s*[:=]\s*([0-9].*?)(?:\s*#|$)", "L1"),]:
    for m in re.finditer(pat, code, re.M):
        print(name, m.group(1), "=", m.group(2).strip()[:40])
print("\n=== dataclass fields ===")
for m in re.finditer(r"^\s{4}(\w+):\s*[\w\[\]]+\s*=\s*(.+)$", code, re.M):
    print(" L2", m.group(1), "=", m.group(2).strip()[:40])
print("\n=== grep candidate axes in code ===")
for tok in ["momentum","ns_steps","beta2","softcap","base=","short_window","ve_gate_channels","1.02","dmodel_lr_scale","x0_lambdas","resid_lambdas"]:
    for i,line in enumerate(code.splitlines(),1):
        if tok in line: print(f"  {tok:18s} L{i}: {line.strip()[:120]}")
