import json,os,requests
from pathlib import Path
FOCUS=Path("/root/autodl-tmp/ar_20261022.hi")
creds=json.load(open(FOCUS/"agents/ar_20261022hi_analyst1/credentials.json"))
H={"Authorization":f"Bearer {creds['api_key']}","Content-Type":"application/json","X-Agent-Name":creds.get("agent_name")}
API=os.environ.get("CLAWINSTITUTE_API","http://localhost:3000/api/v1")
MAIN="50594c0f-9a3a-4401-b2d6-c4fb60a9cca5"
WS=open(FOCUS/"WORKSHOP_NAME").read().strip()

# verify comments landed
for pid,label in [("12f100e1-bc46-41a0-aa5e-af4cd5cef0b4","KEEP"),("d913abef-8c5c-4b65-9fc3-daf38b478722","DBQ"),("ff2578ae-14b9-44db-848d-24767546d204","ACT")]:
    d=requests.get(f"{API}/posts/{pid}/comments",headers=H).json()["data"]
    mine=[c for c in d if "analyst1" in json.dumps(c).lower()]
    print(f"verify {label}: {len(d)} comments, latest by {d[-1].get('agent_name','?') if d else '-'} :: {d[-1]['content'][:60].replace(chr(10),' ') if d else ''}")

p="knowledge/unqueued_axes.md"
for attempt in range(4):
    r=requests.get(f"{API}/workspaces/{MAIN}/files/{p}",headers=H).json()
    body=r["content"]; ver=r.get("version")
    if "| softcap |" in body or "softcap" in body.split("##")[-1]:
        pass
    add=""
    if "| softcap " not in body:
        add+="""
| softcap | logit softcap (final logit squashing) | 15 | 30 (raise to half of |logit| ~ 30-40) | UP, 2x | unqueued | analyst1 c4 | gradient-quality lens only; NOT measured in this run; above-band candidate only if logits are being clipped at 15 | closed-form tanh, no extra params/FLOPs, but runs counter to nanoChat's tuned value | yes | yes - one literal `softcap = 15` | `softcap = 15` -> `softcap = 30` |
"""
    if "| tied_embeddings " not in body:
        add+="""
| tied_embeddings | tie lm_head weight to token embedding | untied | tied | REPLACE (structural) | QUEUED exp_embedding_tied (high, bold) | analyst1 c4 | capacity/regularization lens: 16.8M params removed, lm_head grad signal flows into wte | nanoChat deliberately leaves it untied (needs the unembedding_lr=0.004 to be tunable at all); tying forces one LR on two opposing jobs | yes | yes - 4 coordinated edits, listed in the proposal | `self.lm_head.weight = self.transformer.wte.weight`; drop the lm_head init, the lm_head AdamW group, and `len(lm_head_params)` from the assert |
"""
    if not add: print("ledger: both rows already present at v",ver); break
    body2=body.rstrip()+"\n"+add
    hh=dict(H)
    if ver is not None: hh["If-Match"]=str(ver)
    put=requests.put(f"{API}/workspaces/{MAIN}/files/{p}",headers=hh,json={"content":body2,"message":"analyst1 c4: add softcap + tied_embeddings rows (canonical ledger v10 -> v11)"})
    print("ledger PUT",put.status_code,"from v",ver)
    if put.status_code<300: break
