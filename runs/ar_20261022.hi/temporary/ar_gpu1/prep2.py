import shutil, filecmp, subprocess
from pathlib import Path
FOCUS_ROOT="/root/autodl-tmp/ar_20261022.hi"; AGENT_NAME="ar_20261022hi_gpu1"
rep=Path(f"{FOCUS_ROOT}/agents/{AGENT_NAME}/workspace/repo")
for f in ("train.py","prepare.py","pyproject.toml","uv.lock"):
    src=Path(f"{FOCUS_ROOT}/champion")/f
    if not src.exists(): src=Path(f"{FOCUS_ROOT}/task/repo")/f
    shutil.copy(src, rep/f)
p=rep/"train.py"; code=p.read_text()
old="WEIGHT_DECAY = 0.2      # cautious weight decay for Muon"
new="WEIGHT_DECAY = 0.0      # cautious weight decay for Muon"
assert code.count(old)==1, code.count(old)
p.write_text(code.replace(old,new))
print("identical to champion:",filecmp.cmp(str(p),f"{FOCUS_ROOT}/champion/train.py",shallow=False))
print(subprocess.run(["diff","-u",f"{FOCUS_ROOT}/champion/train.py",str(p)],capture_output=True,text=True).stdout)
