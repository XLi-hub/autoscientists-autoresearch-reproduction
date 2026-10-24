import json, os, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

AGENT_NAME="ar_20261022hi_gpu4"; FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"
EXP_ID="exp_embedding_lr_hi"
ws=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep=ws/"repo"
out, err = ws/f"train_{EXP_ID}.stdout", ws/f"train_{EXP_ID}.stderr"
item=json.load(open("/tmp/claimed_item.json"))

sentinel={
 "status":"running","posted_to_workshop":False,"exp_id":EXP_ID,"agent":AGENT_NAME,
 "item":item,"queue_claimed":True,"direction":"minimize","val_score":None,
 "submission_path":None,"train_path":str(rep/f"train_{EXP_ID}.py"),
 "stdout_path":str(out),"stderr_path":str(err),
 "pid":os.getpid(),"monitor_id":None,
 "description":"EMBEDDING_LR 0.6 -> 1.2 (wte+value_embeds AdamW, 42% of params; 2x per-step movement)",
 "diff_applied":True,"launched_at":datetime.now(timezone.utc).isoformat(),
}
(ws/"result_latest.json").write_text(json.dumps(sentinel,indent=2,default=str))

env={**os.environ,
     "CUDA_VISIBLE_DEVICES":"1",
     "HF_HOME":f"{FOCUS_ROOT}/.cache/huggingface",
     "HF_HUB_OFFLINE":"1",
     "TORCH_HOME":f"{FOCUS_ROOT}/.cache/torch",
     "PYTHONUNBUFFERED":"1"}
t0=time.time()
print(f"[RUN] {EXP_ID} start {sentinel['launched_at']}", flush=True)
with open(out,"w") as fo, open(err,"w") as fe:
    r=subprocess.run(["/root/autodl-tmp/envs/ar/bin/python3","train.py"],
                     cwd=str(rep),stdout=fo,stderr=fe,text=True,timeout=1500,env=env)
el=time.time()-t0
sentinel.update({"status":"complete" if r.returncode==0 else "failed",
                 "returncode":r.returncode,"completed_at":datetime.now(timezone.utc).isoformat(),
                 "elapsed_sec":round(el,1)})
(ws/"result_latest.json").write_text(json.dumps(sentinel,indent=2,default=str))
print(f"[RUN] done rc={r.returncode} elapsed={el:.1f}s", flush=True)
