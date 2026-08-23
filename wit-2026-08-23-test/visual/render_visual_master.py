#!/usr/bin/env python3
"""Tensor Foundry WIT v2 — editorial renderer with real logo imagery + richer palette.
720x1280@30, clean master (no captions). Visual grammar: Source-First Editorial Motion V2.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
W, H = 720, 1280

with open(os.path.join(ROOT, "research/scene_times.json")) as f:
    SC = json.load(f)
CUTS = SC["cuts"] + [SC["recap"], SC["outro"], SC["duration"]]
DESIGN = [0.0, 4.5, 14.5, 24.5, 34.5, 44.5, 52.0, 60.0]

def story_local(t, i):
    return (t - CUTS[i]) * (DESIGN[i+1]-DESIGN[i]) / (CUTS[i+1]-CUTS[i])

with open(os.path.join(ROOT, "research/stories.json")) as f:
    STORIES = json.load(f)["stories"]

# ---- Palette: warm charcoal editorial with ember/teal duotone accents ----
PAPER   = (242, 236, 226)   # warm ivory
GRID    = (228, 220, 206)
INK     = (30, 30, 34)
MUTED   = (108, 104, 98)
DARK    = (26, 28, 32)
DARK2   = (38, 41, 47)
ACCENTS = [(196, 74, 63),   # ember red
           (36, 116, 122),  # deep teal
           (198, 124, 40),  # amber
           (52, 96, 150),   # slate blue
           (120, 82, 148)]  # plum
GOLD    = (176, 138, 62)

_fontcache = {}
def font(sz, bold=False):
    k=(sz,bold)
    if k not in _fontcache:
        n="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _fontcache[k]=ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}", sz)
    return _fontcache[k]

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t_=(cur+" "+w_).strip()
        if d.textlength(t_,font=f)<=maxw: cur=t_
        else: lines.append(cur); cur=w_
    if cur: lines.append(cur)
    return lines

def ease(x): x=max(0,min(1,x)); return x*x*(3-2*x)

_logos={}
def logo(name):
    if name not in _logos:
        p=os.path.join(ROOT,"assets/real",name)
        im=Image.open(p).convert("RGBA")
        _logos[name]=im
    return _logos[name]

def paste_logo(img, name, box_w, center_x, y):
    im=logo(name).copy()
    r=box_w/im.width
    im=im.resize((box_w,int(im.height*r)))
    # white plate behind logo for legibility
    pl=Image.new("RGBA",img.size,(0,0,0,0))
    d=ImageDraw.Draw(pl)
    pad=18
    d.rounded_rectangle([center_x-im.width//2-pad, y-pad, center_x+im.width//2+pad, y+im.height+pad],
                        14, fill=(255,255,255,230))
    pl=pl.filter(ImageFilter.GaussianBlur(0))
    img.paste(pl,(0,0),pl)
    img.paste(im,(center_x-im.width//2,y),im)

def draw_frame(t):
    img=Image.new("RGB",(W,H),PAPER)
    d=ImageDraw.Draw(img)
    for gx in range(0,W,48): d.line([(gx,0),(gx,H)],fill=GRID,width=1)
    for gy in range(0,H,48): d.line([(0,gy),(W,gy)],fill=GRID,width=1)
    # top brand rule
    d.rectangle([0,0,W,6],fill=GOLD)

    if t < CUTS[1]:
        p=ease(min(1,t/1.0))
        fT=font(66,True)
        for k,ln in enumerate(["THIS WEEK","IN TECH"]):
            d.text((58,400+k*88-(1-p)*40),ln,font=fT,fill=INK)
        d.rectangle([58,600,58+180*p,606],fill=GOLD)
        d.text((58,630),"Five signals. One minute.",font=font(30),fill=MUTED)
        srcs=["Local AI Zone","OpenRouter","Google","Meta","NVIDIA"]
        fsx=680-((t*160)%(len(srcs)*260+400))
        for i2,s in enumerate(srcs):
            x=fsx+i2*260
            if -200<x<W:
                d.rounded_rectangle([x,780,x+230,840],10,fill=DARK)
                d.text((x+16,796),s,font=font(24),fill=PAPER)
        d.text((58,1180),"THE TENSOR FOUNDRY · Aug 23, 2026",font=font(24,True),fill=(160,50,42))

    elif t < CUTS[5]:
        idx=max(i for i in range(5) if t>=CUTS[i])
        st=story_local(t,idx)
        acc=ACCENTS[idx]; s=STORIES[idx]
        p=ease(min(1,st/0.7))
        # accent spine down left
        d.rectangle([0,0,10,H],fill=acc)
        d.ellipse([48,70,128,150],fill=acc)
        d.text((72,88),str(idx+1),font=font(44,True),fill=PAPER)
        paste_logo(img,s.get("logo","openai_logo.png"),130,W-100,70)
        fH=font(44,True); y=190-int((1-p)*24)
        for ln in wrap(d,s["headline"],fH,W-130):
            d.text((56,y),ln,font=fH,fill=INK); y+=56
        y+=10
        d.text((56,y),f'{s["source"]} · {s["date"]}',font=font(21),fill=MUTED); y+=54
        d.text((56,y),"Logo: Wikimedia Commons",font=font(19),fill=(150,146,140)); y+=50
        pay=s.get("payoff",{}); py=470
        if pay.get("type")=="counter":
            val=pay["value"]; shown=int(val*min(1,max(0,(st-0.3))/1.2))
            txt=f"{shown:,}"; fB=font(58 if len(txt)>12 else 78,True)
            d.text(((W-d.textlength(txt,font=fB))/2,py+50),txt,font=fB,fill=acc)
            lb=pay.get("label",""); fL=font(30)
            d.text(((W-d.textlength(lb,font=fL))/2,py+160),lb,font=fL,fill=MUTED)
        elif pay.get("type")=="comparison":
            rows=pay["values"]; bx=260; maxv=max(v for _,v in rows)
            for j,(name,v) in enumerate(rows):
                ry=py+j*92; grow=ease(min(1,max(0,(st-0.2-j*0.15))/0.5))
                bw=int((W-340)*(v/maxv)*grow)
                col=acc if j==0 else (172,168,160)
                d.rounded_rectangle([bx,ry,bx+bw,ry+56],8,fill=col)
                d.text((60,ry+12),name[:14],font=font(24,True),fill=INK)
                d.text((bx+bw+10,ry+14),f"{v}%",font=font(26,True),fill=INK)
            d.text((bx,py+len(rows)*92+16),pay.get("label",""),font=font(24),fill=MUTED)
        elif pay.get("type")=="bar":
            rows=pay["values"]; maxv=max(v for _,v in rows)
            for j,(name,v) in enumerate(rows):
                ry=py+70+j*140; grow=ease(min(1,max(0,(st-0.2-j*0.2))/0.5))
                bh=int(190*grow*v/maxv)
                col=acc if j==0 else (172,168,160)
                d.rectangle([140+j*230-64,830-bh,140+j*230+64,830],fill=col)
                d.text((140+j*230-42,840),f"{v}%",font=font(28,True),fill=INK)
                d.text((140+j*230-56,876),name,font=font(22),fill=MUTED)
            d.text((80,py),pay.get("label",""),font=font(26),fill=MUTED)
        elif pay.get("type")=="statcard":
            grow=ease(min(1,max(0,(st-0.3))/0.6)); cw=int((W-120)*(0.6+0.4*grow))
            d.rounded_rectangle([(W-cw)//2,py+40,(W+cw)//2,py+250],16,fill=DARK)
            vt=pay["value"]; fB=font(64,True)
            d.text(((W-d.textlength(vt,font=fB))/2,py+95),vt,font=fB,fill=GOLD)
            lb=pay.get("label",""); fL=font(28)
            d.text(((W-d.textlength(lb,font=fL))/2,py+185),lb,font=fL,fill=(205,202,197))
        fy=960; fF=font(25)
        for j,claim in enumerate(s["verified_claims"][:2]):
            fp=ease(min(1,max(0,(st-0.5-j*0.25))/0.4))
            if fp>0:
                lines=wrap(d,claim,fF,W-170)[:2]
                d.ellipse([62,fy+j*62+8,74,fy+j*62+20],fill=acc)
                for k2,ln in enumerate(lines):
                    d.text((92,fy+j*62+k2*30),ln,font=fF,fill=(66,64,62))

    elif t < CUTS[6]:
        d.rectangle([0,0,W,H],fill=DARK)
        d.rectangle([0,0,W,6],fill=GOLD)
        d.text((56,110),"THE WEEK IN FIVE",font=font(40,True),fill=PAPER)
        appear=max(0,t-CUTS[5])
        for j,s in enumerate(STORIES):
            rp=ease(min(1,max(0,(appear-0.15-j*0.35))/0.35))
            if rp>0:
                y=210+j*82+int((1-rp)*20)
                d.ellipse([56,y+6,76,y+26],fill=ACCENTS[j])
                short=s["headline"].split(":")[0]
                for ln in wrap(d,short,font(27,True),W-170)[:1]:
                    d.text((96,y),ln[:40],font=font(27,True),fill=(225,222,216))

    else:
        d.rectangle([0,0,W,H],fill=DARK)
        op=ease(min(1,(t-CUTS[6])/0.8)); fT=font(52,True)
        a2=ease(min(1,max(0,(t-CUTS[6]-0.5)/0.8)))
        c1=tuple(int(PAPER[i]*op) for i in range(3))
        c2=tuple(int(26+(150-26)*a2) for i in range(3))[:0] or (int(26+(150-26)*a2),)*3
        d.text(((W-d.textlength("THE TENSOR",font=fT))/2,520),"THE TENSOR",font=fT,fill=c1)
        d.text(((W-d.textlength("FOUNDRY",font=fT))/2,600),"FOUNDRY",font=fT,fill=c1)
        sub="tech & ai, weekly"; fS=font(26)
        d.text(((W-d.textlength(sub,font=fS))/2,700),sub,font=fS,fill=c2)
        d.rectangle([(W-120)//2,790,(W+120)//2,794],fill=tuple(int(GOLD[i]*op) for i in range(3)))

    prog=t/CUTS[-1]; segs=7
    for si in range(segs):
        x0=40+si*(W-80)/segs; x1=40+(si+1)*(W-80)/segs
        ff=max(0.0,min(1.0,(prog*segs-si)))
        d.line([(x0,1244),(x1,1244)],fill=(206,200,190),width=6)
        if ff>0:
            d.line([(x0,1244),(x0+(x1-x0)*ff,1244)],fill=ACCENTS[min(si,4)],width=6)
    return img

def main():
    dur=CUTS[-1]; n=int(dur*FPS)
    fd=os.path.join(ROOT,"visual/frames"); os.makedirs(fd,exist_ok=True)
    print(f"rendering {n} frames...")
    for i in range(n):
        draw_frame(i/FPS).save(f"{fd}/f{i:05d}.png")
    out=os.path.join(ROOT,"visual/visual_master.mp4")
    subprocess.run(["ffmpeg","-y","-v","error","-framerate",str(FPS),
        "-i",f"{fd}/f%05d.png","-c:v","libx264","-preset","medium","-crf","19",
        "-pix_fmt","yuv420p","-movflags","+faststart",out],check=True)
    print("done:",out)

if __name__=="__main__":
    main()
