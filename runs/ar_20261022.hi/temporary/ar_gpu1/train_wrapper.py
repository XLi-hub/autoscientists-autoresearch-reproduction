import json, os, subprocess, re, shutil, time, sys
from pathlib import Path
from datetime import datetime, timezone

FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
ws=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace"); rep=ws/"repo"
exp_id="exp_gqa_kv1"
out=ws/f"train_{exp_id}.stdout"; err=ws/f"train_{exp_id}.stderr"
item={"id":exp_id,"axis":"n_kv_head","direction":"decrease","value":"1","current_value":"4",
      "diff":"n_kv_head=num_heads -> max(1, num_heads // 4) in build_model_config (GQA 4:1)","diff_applied":True,
      "proposed_by":"ar_20261022hi_analyst1","proposal_post":"a1018d68-44ba-4f45-aff9-b27e246ec223"}
description=("exp_gqa_kv1: n_kv_head 4->1 (GQA 4:1) at unchanged width 512. Cuts 7.9% of FLOPs/token "
             "(-18.9M), total params 50.33M->34.60M (-31%), predicts 719->~776 steps (+8%). "
             "Discussion gate cleared by 15-min time override (proposal 13:09Z, claimed 15:57Z, 0 comments).")
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
