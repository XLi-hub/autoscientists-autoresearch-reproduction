V=8192
def model(E,depth,mlp,ve_layers,seq=2048,win="SSSL"):
    # params
    wte=V*E; lm=V*E
    per_block=E*E*(4+2*mlp)   # c_q,c_k,c_v,c_proj + mlp fc/proj  (MHA kv_dim=E)
    blocks=depth*per_block
    ve=ve_layers*V*E
    tot=wte+lm+blocks+ve+16
    # flops/token per estimate_flops()
    n_excl=wte+ve+16
    f=6*(tot-n_excl)
    attn=0
    pat=win.upper()
    for i in range(depth):
        c=pat[i%len(pat)]
        w = seq if c=="L" else seq//2
        attn += 12*(E//128)*(128)*min(w,seq)   # h*q = E
    # last layer forced long -> handled by pattern already ending in L
    return tot,f+attn,f,attn,depth*(E*E*(4+2*mlp))
def show(name,E,depth,mlp,ve,steps,win="SSSL",seq=2048):
    tot,fl,fmat,fatt,blk=model(E,depth,mlp,ve,seq,win)
    print(f"{name:34s} E={E} d={depth} mlp={mlp} VE={ve}  params={tot/1e6:6.2f}M  flops/tok={fl/1e8:6.2f}e8  mat6N={fmat/1e8:6.2f}e8 ({100*fmat/fl:4.1f}%)  attn={fatt/1e8:5.2f}e8 ({100*fatt/fl:4.1f}%)  steps={steps}")
    return tot,fl,fmat,fatt
print("=== measured anchors ===")
show("champion AR64 mlp2 2**17",512,8,2,4,956)
show("exp_tput_mlp_exp_2 base(2**18)",512,8,2,4,487)
show("exp_cap_ar48_w384 (mlp3,2**18)",384,8,3,4,None)
print("  ^ reported 30.67M / 1.3684e8 / ~677 est; result had num_steps?")
show("champion-at-mlp3 (2**18)",512,8,3,4,433)
print()
print("=== predictions at 2**17 ===")
_,flc,fc,ac=show("champion",512,8,2,4,956)
print()
print("=== exp_cap_ar48_b2e17 (in flight) ===")
tot,fl,fmat,fatt=show("AR48 mlp2 2**17",384,8,2,4,None)
print(f"   FLOPs ratio vs champion: {fl/flc:.4f} -> raw FLOP model steps ~{956*flc/fl:.0f}")
print(f"   matrix-only (6N) ratio  : {fmat/fc:.4f} -> matrix-only model steps ~{956*fc/fmat:.0f}")
print(f"   attn share  AR48 {100*fatt/fl:.1f}%  vs champion {100*ac/flc:.1f}%")
print()
print("=== window SSLL calibration (measured) ===")
_,fl_ssl,_,at_ssl=show("SSSL mlp3",512,8,3,4,433)
_,fl_ssll,_,at_ssll=show("SSLL mlp3",512,8,3,4,None,win="SSLL")
print(f"   predicted dFLOPs/tok = {100*(fl_ssll/fl_ssl-1):+.2f}%   measured steps 433 -> 429 ({100*(429/433-1):+.2f}%)")
print(f"   => implied attention-term price on step time: {((429/433)-1)/((fl_ssll/fl_ssl)-1)*100:.1f}% of predicted")
print()
print("=== win_short_4 prediction ===")
_,fl_ws,_,_=show("SSSL short=seq//4",512,8,2,4,None,win="SSSL")
def model_ws(E,depth,mlp,ve,seq=2048,short=512):
    wte=V*E;lm=V*E; tot=wte+lm+depth*(E*E*(4+2*mlp))+ve*V*E+16
    f=6*(tot-(wte+ve*V*E+16)); attn=0
    for i in range(depth):
        c="SSSL"[i%4]; w=seq if c=="L" else short
        attn+=12*E*min(w,seq)
    return f+attn
f2=model_ws(512,8,2,4,short=512)
print(f"   champion flops/tok {flc/1e8:.2f}e8 -> short//4 {f2/1e8:.2f}e8  ({100*(f2/flc-1):+.2f}%)")
print(f"   naive prediction {956*flc/f2:.0f} steps; SSLL-calibrated (attn free) -> matrix term unchanged?")
