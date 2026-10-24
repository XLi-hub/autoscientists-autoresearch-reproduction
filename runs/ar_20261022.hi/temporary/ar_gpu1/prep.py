import shutil, filecmp, re
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
rep=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/repo"); rep.mkdir(parents=True,exist_ok=True)
for f in ("train.py","prepare.py","pyproject.toml","uv.lock"):
    src=Path(f"{FOCUS_ROOT}/champion")/f
    if not src.exists(): src=Path(f"{FOCUS_ROOT}/task/repo")/f
    shutil.copy(src, rep/f)
    print("copied",f,"<-",src)
p=rep/"train.py"; code=p.read_text()
old="        n_layer=depth, n_head=num_heads, n_kv_head=num_heads, n_embd=model_dim,"
new="        n_layer=depth, n_head=num_heads, n_kv_head=max(1, num_heads // 4), n_embd=model_dim,"
assert code.count(old)==1, f"old line count={code.count(old)}"
code=code.replace(old,new)
p.write_text(code)
print("EDIT APPLIED; new line present:", new in p.read_text())
same=filecmp.cmp(str(p), f"{FOCUS_ROOT}/champion/train.py", shallow=False)
print("train.py identical to champion:", same)
import subprocess
print(subprocess.run(["diff","-u",f"{FOCUS_ROOT}/champion/train.py",str(p)],capture_output=True,text=True).stdout)
