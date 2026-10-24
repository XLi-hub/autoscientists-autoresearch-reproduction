import re
from pathlib import Path
def curve(p):
    txt=Path(p).read_text(errors="ignore").replace("\r","\n")
    out=[]
    for m in re.finditer(r"step (\d+) \(([\d.]+)%\) \| loss: ([\d.]+)",txt):
        out.append((int(m.group(1)),float(m.group(2)),float(m.group(3))))
    return out
mine=curve("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu4/workspace/train_exp_embedding_lr_hi.stdout")
champ=curve("/root/autodl-tmp/ar_20261022.hi/agents/ar_20261022hi_gpu2/workspace/train_exp_batch_2e17.stdout")
print(f"mine steps={len(mine)} champ steps={len(champ)}")
def at(c,f):
    i=min(len(c)-1,int(len(c)*f)); return c[i]
for f in (0.2,0.4,0.5,0.6,0.8,0.9,0.95,0.99):
    a=at(mine,f); b=at(champ,f)
    print(f"  {int(f*100):3d}%: mine step {a[0]:4d} loss {a[2]:.4f} | champ step {b[0]:4d} loss {b[2]:.4f} | diff {a[2]-b[2]:+.4f}")
# loss still decreasing? last 10% window
def slope(c,lo,hi):
    seg=[x for x in c if lo<=x[1]<=hi]
    if len(seg)<2: return float('nan')
    return (seg[-1][2]-seg[0][2])/(seg[-1][0]-seg[0][0])
print("\nmine  loss delta over 80->100%:", round(at(mine,0.99)[2]-at(mine,0.8)[2],4))
print("champ loss delta over 80->100%:", round(at(champ,0.99)[2]-at(champ,0.8)[2],4))
print("mine  loss delta over 60->80%:", round(at(mine,0.8)[2]-at(mine,0.6)[2],4))
print("champ loss delta over 60->80%:", round(at(champ,0.8)[2]-at(champ,0.6)[2],4))
