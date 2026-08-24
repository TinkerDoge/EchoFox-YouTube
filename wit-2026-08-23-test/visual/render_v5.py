#!/usr/bin/env python3
"""Tensor Foundry WIT v5 — RETRO COMIC / POP PRINT renderer.
Reads research/render_manifest_v5.json. Cream newsprint base, Ben-Day halftone
dots, thick ink outlines, pop-red/yellow/cyan, starburst callouts, comic
caption-boxes. Locked to ASR cuts. Clean master (captions burned separately).
"""
import json, math, os, random, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
W, H = 720, 1280
random.seed(42)

# ---- retro pop palette -------------------------------------------------
PAPER   = (244, 233, 211)   # cream newsprint
PAPER2  = (238, 224, 198)
INK     = (20, 18, 16)      # near-black ink
RED     = (230, 51, 41)
YELLOW  = (255, 198, 26)
CYAN    = (40, 181, 200)
BLUE    = (43, 80, 200)
CREAM   = (250, 244, 228)

with open(f"{ROOT}/research/render_manifest_v5.json") as f:
    MAN = json.load(f)
SEGS = MAN["segments"]
DUR = MAN["duration"]
CUTS = [s["cut_start"] for s in SEGS]
RECAP_END = SEGS[-1]["cut_end"]

with open(f"{ROOT}/captions/words_v6.json") as f:
    WORDS = json.load(f)

STORIES = {s["slug"]: s for s in json.load(open(f"{ROOT}/research/stories.json"))["stories"]}

_fd = f"{ROOT}/assets/fonts"
_fc = {}
def font(name, sz):
    k = (name, sz)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(f"{_fd}/{name}.ttf", sz)
    return _fc[k]

def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 if x >= 1 else 1 - math.pow(2, -10 * x)

# ---- pre-rendered textures --------------------------------------------
def make_halftone(w, h, dot=9, gap=22, color=INK, alpha=28):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = color + (alpha,)
    for row, y in enumerate(range(0, h, gap)):
        off = (gap // 2) if row % 2 else 0
        for x in range(off, w, gap):
            d.ellipse([x - dot//2, y - dot//2, x + dot//2, y + dot//2], fill=c)
    return im

HALFTONE = make_halftone(W, H)

def paper_bg():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    # subtle horizontal newsprint streaks
    rnd = random.Random(7)
    for _ in range(140):
        y = rnd.randrange(H); ln = rnd.randrange(30, 260)
        d.line([(rnd.randrange(W), y), (rnd.randrange(W), y)], fill=PAPER2, width=rnd.choice([1,1,2]))
    im.paste(HALFTONE, (0, 0), HALFTONE)
    return im

def ink_rect(d, box, r=14, width=6, outline=INK, fill=None):
    if fill: d.rounded_rectangle(box, r, fill=fill)
    d.rounded_rectangle(box, r, outline=outline, width=width)

def shadow_panel(im, box, r=14, fill=CREAM, offset=8, accent=None):
    """Comic panel: hard ink drop-shadow, thick border."""
    x0,y0,x1,y1 = box
    ov = Image.new("RGBA", im.size, (0,0,0,0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle([x0+offset, y0+offset, x1+offset, y1+offset], r, fill=(*INK, 160))
    if accent:
        d.rounded_rectangle(box, r, fill=accent)
        d.rounded_rectangle([x0+10, y0+10, x1+10, y1+10], r, outline=(*INK,255), width=6)
    im.alpha_composite(ov)
    d2 = ImageDraw.Draw(im)
    d2.rounded_rectangle(box, r, fill=fill, outline=INK, width=6)
    return d2

def starburst(cx, cy, r_out, r_in, n=12, rot=0.0):
    pts = []
    for i in range(n*2):
        ang = rot + i*math.pi/n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r*math.cos(ang), cy + r*math.sin(ang)))
    return pts

_logos = {}
def logo(name):
    if name not in _logos:
        _logos[name] = Image.open(os.path.join(ROOT, "assets/real", name)).convert("RGBA")
    return _logos[name]

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def draw_center(d, txt, y, fill=INK, stroke=0, sfill=CREAM, f=None):
    if f is None: raise ValueError("font required")
    lw = d.textlength(txt, font=f)
    d.text(((W-lw)/2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

# rank badge: circle + number, with cream stroke ring so it never blends into panels
def rank_badge(d, cx, cy, r, num, acc):
    d.ellipse([cx-r-8, cy-r-8, cx+r+8, cy+r+8], fill=PAPER, outline=None)
    d.ellipse([cx-r-8, cy-r-8, cx+r+8, cy+r+8], outline=INK, width=6)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=acc, outline=INK, width=6)

# ---------------- intro ----------------
def intro_frame(t):
    im = paper_bg().convert("RGBA")
    d = ImageDraw.Draw(im)
    p = ease(t/0.5)
    # big title panel tilted slightly (draw straight; tilt via rotation of a sub-im is costly — use skew look via offset lines)
    # top masthead strip
    d.rectangle([0, 0, W, 90], fill=YELLOW, outline=INK, width=0)
    d.rectangle([0, 86, W, 96], fill=INK)
    d.text((36, 22), "THE TENSOR FOUNDRY · WEEKLY", font=font("Archivo", 30), fill=INK)
    # rotating starburst behind THIS WEEK
    sb = starburst(W/2, 430, 300*p, 240*p, n=14, rot=t*0.35)
    d.polygon(sb, fill=RED, outline=INK, width=6)
    sb2 = starburst(W/2, 430, 258*p, 208*p, n=14, rot=-t*0.22+1)
    d.polygon(sb2, fill=YELLOW, outline=INK, width=4)
    draw_center(d, "THIS WEEK", 340, INK, f=font("Bangers", 110))
    draw_center(d, "IN TECH!", 460, CREAM, stroke=6, sfill=INK, f=font("Bangers", 120))
    # subtitle chip
    chip_w = int(d.textlength("FIVE SIGNALS · SIXTY SECONDS", font=font("LuckiestGuy", 30)) + 70)
    shadow_panel(im, ((W-chip_w)//2, 660, (W+chip_w)//2, 730), r=16, fill=CYAN)
    draw_center(d, "FIVE SIGNALS · SIXTY SECONDS", 674, INK, f=font("LuckiestGuy", 30))
    # date tag bottom-left comic stamp
    stamp = Image.new("RGBA", (420, 130), (0,0,0,0))
    sd = ImageDraw.Draw(stamp)
    sd.rounded_rectangle([6,6,410,120], 14, outline=RED, width=8)
    sd.text((30, 34), "AUG 24, 2026", font=font("Bangers", 52), fill=RED)
    stamp = stamp.rotate(-6, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(stamp, (10, H-190))
    # kinetic caption words (comic style handled at caption burn stage too)
    draw_kinetic_hint(d, t)
    return im.convert("RGB")

# ---------------- story ----------------
ACCENTS = [RED, BLUE, CYAN, RED, BLUE]

def story_frame(i, local_t):
    seg = SEGS[i]
    st = STORIES[seg["story_id"]]
    acc = ACCENTS[i % len(ACCENTS)]
    ap = ease(local_t/0.45)
    im = paper_bg().convert("RGBA")
    d = ImageDraw.Draw(im)

    # number badge — big comic circle top-left with rank (paper ring prevents panel overlap)
    bx, by, br = 92, 128, 64
    pulse = 1 + 0.04*math.sin(local_t*3)
    br *= pulse
    rank_badge(d, bx, by, br, str(st["rank"]), acc)
    fR = font("Bangers", 88)
    num = str(st["rank"])
    nw = d.textlength(num, font=fR)
    d.text((bx-nw/2, by-52), num, font=fR, fill=CREAM, stroke_width=4, stroke_fill=INK)
    # story label chip next to badge
    lab = st["source"].split("/")[0].split(",")[0].upper()
    fL = font("LuckiestGuy", 26)
    lw = d.textlength(lab, font=fL)
    shadow_panel(im, (bx+br+24, 84, bx+br+24+lw+56, 148), r=14, fill=YELLOW)
    d.text((bx+br+52, 98), lab, font=fL, fill=INK)

    # logo plate — white comic panel with halftone corner + Ken-Burns-ish scale-in
    lg = logo(seg["assets"][0]).copy()
    target = 300
    r = target/max(lg.size)
    lg = lg.resize((int(lg.width*r), int(lg.height*r)), Image.LANCZOS)
    grow = 0.85 + 0.15*ap
    lw2, lh2 = max(1,int(lg.width*grow)), max(1,int(lg.height*grow))
    lg = lg.resize((lw2, lh2), Image.LANCZOS)
    px, py = (W-lw2)//2, 220+(lh2//2)
    panel_h = max(lh2, 240)+44
    pd = shadow_panel(im, ((W-380)//2, py-120, (W+380)//2, py-120+panel_h), r=18, fill=CREAM)
    # halftone dots in plate corner
    ht = HALFTONE.crop((0,0,180,180))
    im.alpha_composite(ht.crop((0,0,150,90)), ((W-380)//2+14, py-120+panel_h-104))
    im.paste(lg, (px, py-lh2//2), lg)
    d = ImageDraw.Draw(im)

    # headline — Bangers, big, cream with ink outline (comic style, always readable)
    fH = font("Bangers", 54)
    lines = wrap(d, st["headline"], fH, W-100)[:2]
    hy = py-120+panel_h+26
    for j, ln in enumerate(lines):
        draw_center(d, ln, hy+j*62, CREAM if j else YELLOW, stroke=5, sfill=INK, f=fH)
    sy = hy+len(lines)*62+2
    src = f'{st["source"]} · {st["date"]}'
    draw_center(d, src, sy, (90,80,66), f=font("Archivo", 22))

    # ---- payoff infographic: comic panel with starburst accents ----
    pay_y0, pay_y1 = 690, 1005
    pd2 = shadow_panel(im, (48, pay_y0, W-48, pay_y1), r=20, fill=CREAM)
    d = ImageDraw.Draw(im)
    grow = ease(max(0.0, local_t-0.2)/0.6)
    typ = seg["payoff"]
    cxm = W/2
    if typ == "title":
        pass
    elif typ == "counter":
        val = int(pay_value(st) * grow)
        txt = f"{val:,}"
        # mini starburst behind number
        sb = starburst(cxm, pay_y0+120, 150*grow, 118*grow, n=11, rot=local_t*0.5)
        d.polygon(sb, fill=YELLOW, outline=INK, width=4)
        fB = font("Bangers", 78 if len(txt)>10 else 96)
        draw_center(d, txt, pay_y0+72, RED, stroke=4, sfill=INK, f=fB)
        draw_center(d, st["payoff"].get("label","").upper(), pay_y0+218, INK, f=font("LuckiestGuy", 30))
    elif typ in ("comparison","bar"):
        rows = st["payoff"]["values"]; mx = max(v for _,v in rows)
        bx0 = 250; bw_max = W-395
        for j,(name,v) in enumerate(rows):
            ry = pay_y0+30+j*62
            bwd = int(bw_max*(v/mx)*grow)
            col = acc if j==0 else (168,158,140)
            d.rounded_rectangle([bx0, ry, bx0+bwd, ry+44], 8, fill=col, outline=INK, width=3)
            d.text((74, ry+7), name[:13], font=font("LuckiestGuy", 22), fill=INK)
            d.text((bx0+bwd+10, ry+8), f"{v:g}", font=font("Bangers", 30), fill=INK)
        draw_center(d, st["payoff"].get("label","").upper(), pay_y1-46, (90,80,66), f=font("LuckiestGuy", 24))
    elif typ == "statcard":
        vt = st["payoff"]["value"]
        sb = starburst(cxm, pay_y0+130, 170*grow, 138*grow, n=12, rot=-local_t*0.4)
        d.polygon(sb, fill=CYAN, outline=INK, width=5)
        fB = font("Bangers", 76)
        draw_center(d, vt, pay_y0+92, INK, f=fB)
        draw_center(d, st["payoff"].get("label","").upper(), pay_y0+212, (90,80,66), f=font("LuckiestGuy", 28))
    elif typ == "multiplier":
        # big 4x burst
        sb = starburst(cxm, pay_y0+125, 175*grow, 140*grow, n=12, rot=local_t*0.45)
        d.polygon(sb, fill=RED, outline=INK, width=6)
        draw_center(d, "4× FASTER", pay_y0+82, YELLOW, stroke=4, sfill=INK, f=font("Bangers", 68))
        draw_center(d, "AGENTIC WORKLOADS", pay_y0+205, INK, f=font("LuckiestGuy", 26))

    # verified claims — comic caption chips
    fy = 1030
    fF = font("ArchivoBold" if os.path.exists(f"{_fd}/ArchivoBold.ttf") else "Archivo", 24)
    for j, claim in enumerate(st["verified_claims"][:2]):
        cp = ease(max(0.0, local_t-0.4-j*0.25)/0.4)
        if cp <= 0: continue
        lines = wrap(d, claim, fF, W-150)[:1]
        cw = min(d.textlength(lines[0], font=fF)+64, W-70)
        yy = fy + j*58 + int((1-cp)*16)
        shadow_panel(im, (36, yy, 36+cw, yy+48), r=12, fill=CREAM, offset=5)
        d = ImageDraw.Draw(im)
        d.ellipse([56, yy+16, 70, yy+30], fill=acc, outline=INK, width=2)
        d.text((84, yy+10), lines[0], font=fF, fill=INK)

    # attribution micro-text
    d.text((W-16-d.textlength("Logo: Wikimedia Commons", font=font("Archivo", 14)), H-26),
           "Logo: Wikimedia Commons", font=font("Archivo", 14), fill=(140,128,108))
    return im.convert("RGB")

def pay_value(st):
    v = st["payoff"]["value"]
    return v if v < 10**13 else 2_400_000_000_000

# ---------------- recap & outro ----------------
def recap_frame(t):
    im = paper_bg().convert("RGBA")
    d = ImageDraw.Draw(im)
    ap = ease(t/0.4)
    d.rectangle([0, 0, W, 110], fill=RED)
    d.rectangle([0, 106, W, 116], fill=INK)
    d.text((40, 28), "THE WEEK IN FIVE!", font=font("Bangers", 62), fill=YELLOW, stroke_width=3, stroke_fill=INK)
    stories = list(STORIES.values())
    for j, s in enumerate(stories):
        rp = ease(max(0.0, t-0.15-j*0.22)/0.35)
        if rp <= 0: continue
        y = 170 + j*112 + int((1-rp)*26)
        acc = ACCENTS[j % len(ACCENTS)]
        d.ellipse([48, y, 106, y+58], fill=acc, outline=INK, width=4)
        num = str(s["rank"])
        d.text((77-d.textlength(num, font=font("Bangers", 40))/2, y+6), num,
               font=font("Bangers", 40), fill=CREAM, stroke_width=2, stroke_fill=INK)
        short = s["headline"].split(":")[0]
        for k, ln in enumerate(wrap(d, short, font("Archivo", 27), W-190)[:2]):
            d.text((126, y+2+k*32), ln, font=font("Archivo", 27), fill=INK)
    return im.convert("RGB")

def outro_frame(t):
    im = paper_bg().convert("RGBA")
    d = ImageDraw.Draw(im)
    op = ease(t/0.6)
    sb = starburst(W/2, 500, 320*op, 258*op, n=16, rot=t*0.3)
    d.polygon(sb, fill=YELLOW, outline=INK, width=6)
    draw_center(d, "THAT'S YOUR", 400, INK, f=font("Bangers", 72))
    draw_center(d, "WEEK IN TECH!", 490, RED, stroke=4, sfill=INK, f=font("Bangers", 84))
    a2 = ease(max(0.0, t-0.35)/0.6)
    if a2 > 0:
        c = tuple(int(150+(20-150)*a2) for _ in range(3))
        draw_center(d, "see you next week — bye-bye!", 660, c, f=font("LuckiestGuy", 30))
    gw = int(180*op)
    d.rectangle([(W-gw)//2, 760, (W+gw)//2, 768], fill=RED)
    draw_center(d, "THE TENSOR FOUNDRY", 800, INK, f=font("LuckiestGuy", 34))
    return im.convert("RGB")

# ---------------- transition whip-panel ----------------
def transition_frame(t, i):
    acc = ACCENTS[i % len(ACCENTS)]
    im = paper_bg().convert("RGBA")
    d = ImageDraw.Draw(im)
    prog = (t % 1.2)/1.2
    x = int(-W + prog*2*W)  # sweep across
    d.rectangle([x, 0, x+W, H], fill=acc)
    d.rectangle([x-26, 0, x-14, H], fill=INK)
    d.rectangle([x+W+14, 0, x+W+26, H], fill=INK)
    # speed lines
    for k in range(8):
        yy = 100+k*140
        d.line([(x+40, yy), (x+W-40, yy)], fill=CREAM, width=6)
    return im.convert("RGB")

def draw_kinetic_hint(d, t):
    pass  # captions burned in ASS pass, not baked

# ---------------- assembly ----------------
def is_transition(t):
    for i in range(1, len(SEGS)):
        if SEGS[i]["cut_start"]-0.55 <= t < SEGS[i]["cut_start"]:
            return SEGS[i-0]["cut_start"], True
    return None, False

def draw_frame(t):
    # recap/outro after last segment end handled below
    for i, seg in enumerate(SEGS):
        cs, ce = seg["cut_start"], seg["cut_end"]
        if cs <= t < ce:
            nxt_cut, tr = False, False
            if i+1 < len(SEGS) and t >= SEGS[i+1]["cut_start"]-0.55:
                return transition_frame(t, i+1)
            local = t - cs
            if seg["story_id"] == "intro":
                return intro_frame(local)
            if seg["story_id"] == "recap":
                return recap_frame(local)
            return story_frame(i, local)
    if RECAP_END <= t < RECAP_END + 4.2:
        return outro_frame(t - RECAP_END)
    return outro_frame(max(0.0, t - RECAP_END))

def main():
    n = int(DUR*FPS)
    fd = f"{ROOT}/visual/frames_v5"; os.makedirs(fd, exist_ok=True)
    print(f"rendering {n} frames...")
    for i in range(n):
        draw_frame(i/FPS).save(f"{fd}/f{i:05d}.png")
        if i % 300 == 0: print("frame", i)
    out = f"{ROOT}/visual/visual_master_v5.mp4"
    subprocess.run(["ffmpeg","-y","-v","error","-framerate",str(FPS),
        "-i",f"{fd}/f%05d.png","-c:v","libx264","-preset","medium","-crf","19",
        "-pix_fmt","yuv420p","-movflags","+faststart",out], check=True)
    print("done:", out)

if __name__ == "__main__":
    main()
