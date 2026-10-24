import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone
AGENT_NAME = "ar_20261022hi_gpu5"
FOCUS_ROOT = "/root/autodl-tmp/ar_20261022.hi"
ws  = Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep = ws/"repo"
EXP_ID = "exp_activation_silu"
out = ws / f"train_{EXP_ID}_seed43.stdout"; err = ws / f"train_{EXP_ID}_seed43.stderr"
prior = json.loads((ws/"result_latest.json").read_text())
prior.update({"status":"running","posted_to_workshop":False,"stdout_path":str(out),"stderr_path":str(err),
              "second_seed_run":43,"pid":os.getpid(),"val_score":None,
              "launched_at":datetime.now(timezone.utc).isoformat()})
(ws/"result_latest.json").write_text(json.dumps(prior, indent=2, default=str))
print("[SEED43] launched", flush=True)
env = {**os.environ,"CUDA_VISIBLE_DEVICES":"0","HF_HOME":f"{FOCUS_ROOT}/.cache/huggingface",
       "HF_HUB_OFFLINE":"1","TORCH_HOME":f"{FOCUS_ROOT}/.cache/torch"}
t0=datetime.now(timezone.utc)
r = subprocess.run(["/root/autodl-tmp/envs/ar/bin/python3","train.py"], cwd=str(rep),
                   capture_output=True, text=True, timeout=1200, env=env)
out.write_text(r.stdout or ""); err.write_text(r.stderr or "")
prior["status"]="complete" if r.returncode==0 else "failed"; prior["returncode"]=r.returncode
prior["wall_sec"]=(datetime.now(timezone.utc)-t0).total_seconds()
(ws/"result_latest.json").write_text(json.dumps(prior, indent=2, default=str))
print(f"[TRAIN43] rc={r.returncode} wall={prior['wall_sec']:.0f}s")
print("\n".join((r.stdout or "").splitlines()[-14:]))
print("=== STDERR ===")
print("\n".join((r.stderr or "").splitlines()[-8:]))
