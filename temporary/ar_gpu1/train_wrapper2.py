import json, os, subprocess, re, shutil, time, sys
from pathlib import Path
from datetime import datetime, timezone

FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
ws=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep=ws/"repo"
exp_id="exp_wd_0p0"
out=ws/f"train_{exp_id}.stdout"; err=ws/f"train_{exp_id}.stderr"
item={"id":exp_id,"axis":"weight_decay","direction":"decrease","value":"0.0","current_value":"0.2",
      "diff":"WEIGHT_DECAY 0.2 -> 0.0 (Muon matrices only)","diff_applied":True,
      "proposed_by":"ar_20261022hi_analyst1","proposal_post":"d2a434dd-d5ad-4a81-968d-873ccaecf35a"}
description=("exp_wd_0p0: WEIGHT_DECAY 0.2 -> 0.0 (Muon matrices only). At 719 steps the wd timescale "
             "1\/(0.04*0.1)=250 steps = 0.35x the run, so decay removes a large fraction of accumulated weight growth. "
             "Step-neutral, memory-neutral; composes with the 2**17 champion.")
sentinel={"status":"running","posted_to_workshop":False,"exp_id":exp_id,"agent":AGENT_NAME,"item":item,
          "queue_claimed":True,"direction":"minimize","val_score":None,
          "submission_path":None,"train_path":str(rep/f"train_{exp_id}.py"),
          "stdout_path":str(out),"stderr_path":str(err),"pid":None,"monitor_id":None,
          "description":description,"launched_at":datetime.now(timezone.utc).isoformat()}
(ws/"result_latest.json").write_text(json.dumps(sentinel,indent=2,default=str))

env={**os.environ,"CUDA_VISIBLE_DEVICES":"0",
     "HF_HOME":f"{FOCUS_ROOT}/.cache/huggingface","HF_HUB_OFFLINE":"1",
     "TORCH_HOME":f"{FOCUS_ROOT}/.cache/torch"}
t0=time.time(); rc=None; so=""; se=""
try:
    p=subprocess.Popen(["/root/autodl-tmp/envs/ar/bin/python3","train.py"],cwd=str(rep),
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    sentinel["pid"]=p.pid
    (ws/"result_latest.json").write_text(json.dumps(sentinel,indent=2,default=str))
    try:
        so,se=p.communicate(timeout=560); rc=p.returncode
    except subprocess.TimeoutExpired:
        p.kill(); so,se=p.communicate(); rc="TIMEOUT"
except Exception as e:
    se=str(e); rc="LAUNCH_FAIL"
out.write_text(so or ""); err.write_text(se or "")
print("returncode:",rc,"wall_s:",round(time.time()-t0,1))
tail=(so or "")[-1800:]
print("=== STDOUT TAIL ===\n"+tail)
m=re.search(r"val_bpb:\s+([0-9.]+)", so or "")
val=float(m.group(1)) if m else None
sentinel.update({"status":"complete" if rc==0 else "failed","returncode":rc,"val_score":val,
                 "wall_seconds":round(time.time()-t0,1)})
# stamped copies (isolation: agent-local only)
if (rep/"train.py").exists():
    shutil.copy(rep/"train.py", rep/f"train_{exp_id}.py")
(ws/"result_latest.json").write_text(json.dumps(sentinel,indent=2,default=str))
print("PARSED_VAL_BPB:",val)
