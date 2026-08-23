#!/usr/bin/env python3
"""Tensor Foundry WIT v3 — dark kinetic renderer per tensor-foundry-v3-shorts grammar.
Reads research/render_manifest.json. Locked ASR cuts, word-synced kinetic type,
Ken-Burns imagery, zoom-punch motion, 9:16 native. Clean master (no captions).
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
W, H = 720, 1280
BASE = (10, 10, 15)
PANEL = (22, 22, 30)
VIOLET = (148, 102, 220)
COPPER = (222, 138, 72)
TEXT = (238, 236, 240)
MUTED = (150, 148, 156)

with open(f"{ROOT}/research/render_manifest.json") as f:
    MAN = json.load(f)

CUTS = [0.0] + [s["cut_end"] for s in MAN["segments"][:-1]]
RECAP = CUTS[-1] + 0.5
OUTRO = RECAP + 4.0
DUR = MAN["duration"]
SEGS = MAN["segments"]

# word timing for kinetic captions baked into clean master (kinetic reveal IS the visual)
try:
    with open(f"{ROOT}/captions/words.json") as f:
        WORDS = json.load(f)
except FileNotFoundError:
    WORDS = []

_fc = {}
def font(sz, bold=True):
    k = (sz, bold)
    if k not in _fc:
        n = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _fc[k] = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}", sz)
    return _fc[k]

def ease_out_expo(x):
    x = max(0.0, min(1.0, x))
    return 1 if x >= 1 else 1 - math.pow(2, -10 * x)

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

_logos = {}
def logo(name):
    p = os.path.join(ROOT, "assets/real", name)
    if name not in _logos:
        _logos[name] = Image.open(p).convert("RGBA")
    return _logos[name]

_plate = {}
def kenburns(img_path):
    """Pre-render an oversized Ken-Burns source image."""
    if img_path in _plate:
        return _plate[img_path]
    im = logo(img_path)  # reuse cache loader
    _plate[img_path] = im
    return im

def draw_kinetic(d, t):
    """Word-by-word kinetic reveal of narration near time t."""
    if not WORDS: return
    active = []
    for i, w in enumerate(WORDS):
        if w["start"] <= t <= w["end"] + 0.35 and w["end"] > t - 2.2:
            active.append((i, w))
    if not active: return
    # group into a phrase window around the latest words
    idxs = [i for i, _ in active]
    lo, hi = min(idxs), max(idxs)
    phrase_words = WORDS[lo:hi+1]
    txt = " ".join(w["word"] for w in phrase_words)
    fK = font(44)
    lines = wrap(d, txt.upper(), fK, W - 100)[:3]
    y = H - 320
    for ln in lines:
        lw = d.textlength(ln, font=fK)
        d.text(((W - lw) / 2, y), ln, font=fK, fill=TEXT)
        y += 56

def zoompunch(scale, img):
    if scale == 1.0:
        return img
    w2, h2 = int(W / scale), int(H / scale)
    x0 = (img.width - w2) // 2; y0 = (img.height - h2) // 2
    return img.crop((x0, y0, x0 + w2, y0 + h2)).resize((W, H))

def story_frame(idx, local_t, seg_t):
    s_idx = idx
    slug = SEGS[s_idx]["story_id"]
    stories = {s["slug"]: s for s in json.load(open(f"{ROOT}/research/stories.json"))["stories"]}
    st = stories[slug]
    acc = VIOLET if idx % 2 == 0 else COPPER
    appear = ease_out_expo(local_t / 0.45)
    punch_t = max(0.0, seg_t % 2.2 - 1.7) / 0.5  # zoom-pulse every ~2.2s
    punch = 1.0 + 0.06 * math.sin(min(1, punch_t) * math.pi)

    base = Image.new("RGB", (W, H), BASE)
    d = ImageDraw.Draw(base)
    # gradient wash top
    grad = Image.new("L", (1, 300))
    for yy in range(300):
        grad.putpixel((0, yy), int(40 * (1 - yy / 300)))
    tint = Image.new("RGB", (W, 300), acc)
    base.paste(tint, (0, 0), grad.resize((W, 300)))

    # Ken-Burns logo plate
    lg = logo(st.get("logo", "openai_logo.png")).copy()
    r = 340 / lg.width
    lg = lg.resize((340, int(lg.height * r)), Image.LANCZOS)
    kb_scale = 1.05 + 0.05 * (local_t / max(seg_t, 0.01))  # slow push-in
    lw, lh = int(lg.width * kb_scale), int(lg.height * kb_scale)
    lg = lg.resize((lw, lh), Image.LANCZOS)
    ly = 200
    pl = Image.new("RGBA", (lw + 48, lh + 48), (255, 255, 255, 235))
    pmask = Image.new("L", pl.size, 0)
    ImageDraw.Draw(pmask).rounded_rectangle([0, 0, pl.size[0], pl.size[1]], 24, fill=255)
    px = (W - pl.size[0]) // 2
    full = base.convert("RGBA")
    full.paste(pl, (px, ly - 24), pmask)
    full.paste(lg, (px + 24, ly), lg)
    base = full.convert("RGB")
    d = ImageDraw.Draw(base)

    # headline: slide-up snap reveal
    fH = font(52)
    y = ly + lh + 60 - int((1 - appear) * 60)
    for ln in wrap(d, st["headline"], fH, W - 80):
        lw2 = d.textlength(ln, font=fH)
        d.text(((W - lw2) / 2, y), ln, font=fH, fill=TEXT)
        y += 62
    d.text((W / 2 - d.textlength(f'{st["source"]} · {st["date"]}', font=font(22))/2, y + 8),
           f'{st["source"]} · {st["date"]}', font=font(22), fill=MUTED)

    # payoff panel (glass-ish): rounded translucent card
    pay = st.get("payoff", {})
    py0, py1 = 700, 1010
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([50, py0, W - 50, py1], 20, fill=(30, 30, 42, 215),
                         outline=acc + (160,), width=2)
    base = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(base)
    grow = ease_out_expo(max(0.0, local_t - 0.25) / 0.6)
    if pay.get("type") == "counter":
        shown = int(pay["value"] * grow)
        txt = f"{shown:,}"; fB = font(54 if len(txt) > 12 else 72)
        d.text(((W - d.textlength(txt, font=fB)) / 2, py0 + 55), txt, font=fB, fill=acc)
        lb = pay.get("label", "")
        d.text(((W - d.textlength(lb, font=font(26))) / 2, py0 + 165), lb, font=font(26), fill=MUTED)
    elif pay.get("type") in ("comparison", "bar"):
        rows = pay["values"]; maxv = max(v for _, v in rows)
        horiz = len(rows) > 2 or pay["type"] == "comparison"
        if horiz:
            bx = 230
            for j, (name, v) in enumerate(rows):
                ry = py0 + 28 + j * 68
                bw = int((W - 300) * (v / maxv) * grow)
                col = acc if j == 0 else (90, 90, 104)
                d.rounded_rectangle([bx, ry, bx + bw, ry + 44], 8, fill=col)
                d.text((66, ry + 8), name[:12], font=font(20), fill=TEXT)
                d.text((bx + bw + 8, ry + 9), f"{v}", font=font(22), fill=TEXT)
            d.text((bx, py1 - 30), pay.get("label", ""), font=font(19), fill=MUTED)
        else:
            for j, (name, v) in enumerate(rows):
                bh = int(180 * grow * v / maxv)
                col = acc if j == 0 else (90, 90, 104)
                cxp = W / 2 + (j - 0.5) * 220
                d.rectangle([cxp - 70, py1 - 110 - bh, cxp + 70, py1 - 110], fill=col)
                d.text((cxp - 36, py1 - 96), f"{v}", font=font(26), fill=TEXT)
                d.text((cxp - 46, py1 - 58), name, font=font(20), fill=MUTED)
            d.text((64, py0 + 18), pay.get("label", ""), font=font(20), fill=MUTED)
    elif pay.get("type") == "statcard":
        vt = pay["value"]; fB = font(60)
        d.text(((W - d.textlength(vt, font=fB)) / 2, py0 + 60), vt, font=fB, fill=COPPER)
        lb = pay.get("label", "")
        d.text(((W - d.textlength(lb, font=font(26))) / 2, py0 + 170), lb, font=font(26), fill=MUTED)

    # key facts chips
    fy = 1020; fF = font(23)
    for j, claim in enumerate(st["verified_claims"][:2]):
        cp = ease_out_expo(max(0.0, local_t - 0.5 - j * 0.25) / 0.4)
        if cp > 0:
            lines = wrap(d, claim, fF, W - 130)[:1]
            chip_w = min(d.textlength(lines[0], font=fF) + 56, W - 80)
            d.rounded_rectangle([40, fy + j*74, 40 + chip_w, fy + j*74 + 46], 23,
                                fill=PANEL, outline=(70, 70, 84), width=1)
            d.ellipse([58, fy + j*74 + 17, 68, fy + j*74 + 27], fill=acc)
            d.text((82, fy + j*74 + 11), lines[0], font=fF, fill=(205, 203, 208))
    return zoompunch(punch, base)

def recap_frame(local_t):
    base = Image.new("RGB", (W, H), BASE); d = ImageDraw.Draw(base)
    grad = Image.new("L", (1, 400))
    for yy in range(400): grad.putpixel((0, yy), int(50 * (1 - yy / 400)))
    base.paste(Image.new("RGB", (W, 400), VIOLET), (0, 0), grad.resize((W, 400)))
    d = ImageDraw.Draw(base)
    ap = ease_out_expo(local_t / 0.5)
    d.text((60, 120 - int((1-ap)*30)), "THE WEEK IN FIVE", font=font(46), fill=TEXT)
    d.rectangle([60, 190, 60 + 200*ap, 196], fill=COPPER)
    stories = json.load(open(f"{ROOT}/research/stories.json"))["stories"]
    for j, s in enumerate(stories):
        rp = ease_out_expo(max(0.0, local_t - 0.2 - j * 0.28) / 0.35)
        if rp > 0:
            y = 250 + j * 92 + int((1-rp)*24)
            acc = VIOLET if j % 2 == 0 else COPPER
            d.ellipse([60, y+4, 82, y+26], fill=acc)
            short = s["headline"].split(":")[0]
            for ln in wrap(d, short, font(29), W-160)[:1]:
                d.text((102, y), ln[:38], font=font(29), fill=TEXT)
    return base

def outro_frame(local_t):
    base = Image.new("RGB", (W, H), BASE); d = ImageDraw.Draw(base)
    op = ease_out_expo(min(1, local_t / 0.7))
    fT = font(58)
    c = tuple(int(TEXT[i]*op) for i in range(3))
    a2 = ease_out_expo(max(0.0, local_t - 0.4)/0.7)
    c2 = tuple(int(30+(170-30)*a2) for _ in range(3))[:0] or (int(30+(170-30)*a2),)*3
    d.text(((W-d.textlength("THE TENSOR", font=fT))/2, 520), "THE TENSOR", font=fT, fill=c)
    d.text(((W-d.textlength("FOUNDRY", font=fT))/2, 610), "FOUNDRY", font=fT, fill=c)
    sub = "tech & ai, weekly"; fS = font(26)
    d.text(((W-d.textlength(sub, font=fS))/2, 720), sub, font=fS, fill=c2)
    gw = int(140*op)
    d.rectangle([(W-gw)//2, 800, (W+gw)//2, 806], fill=tuple(int(COPPER[i]*op) for i in range(3)))
    return base

def transition_frame(t, kind):
    """Animated transition plate: drift + fade pulse."""
    path = f"assets/transitions/{kind}.png"
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    prog = (t % 4) / 4.0
    sc = 1.08 + 0.10 * prog
    w2, h2 = int(W/sc), int(H/sc)
    x0 = int((im.width-w2)*(0.5 + 0.08*math.sin(prog*6.28)))
    y0 = int((im.height-h2)*0.5)
    frame = im.crop((x0, y0, x0+w2, y0+h2)).resize((W, H), Image.LANCZOS)
    return frame

def is_transition(t):
    """Transition windows: 1.2s before each story cut."""
    for i in range(1, len(SEGS)):
        if CUTS[i]-1.2 <= t < CUTS[i]:
            return True
    return False

def draw_frame(t):
    if t < CUTS[0] + 3.58:  # intro = first cut span
        base = Image.new("RGB", (W, H), BASE); d = ImageDraw.Draw(base)
        p = ease_out_expo(t / 0.8)
        fT = font(72)
        d.text((56, 420-int((1-p)*50)), "THIS WEEK", font=fT, fill=TEXT)
        d.text((56, 516), "IN TECH", font=fT, fill=VIOLET)
        d.rectangle([56, 630, 56+220*p, 637], fill=COPPER)
        d.text((56, 660), "Five signals. One minute.", font=font(28, False), fill=MUTED)
        d.text((56, 1180), "THE TENSOR FOUNDRY · Aug 23, 2026", font=font(22), fill=COPPER)
        draw_kinetic(d, t)
        return zoompunch(1.0+0.04*math.sin(t*1.4), base)
    if is_transition(t):
        return transition_frame(t, "sphere" if int(t/4)%2==0 else "fiber")
    for i in range(len(SEGS)):
        cs = CUTS[i]; ce = CUTS[i+1] if i+1 < len(SEGS) else RECAP
        if cs <= t < ce:
            return story_frame(i, t-cs, ce-cs)
    if RECAP <= t < OUTRO:
        return recap_frame(t-RECAP)
    return outro_frame(t-OUTRO)

def main():
    n = int(DUR*FPS)
    fd = f"{ROOT}/visual/frames_v3"; os.makedirs(fd, exist_ok=True)
    print(f"rendering {n} frames...")
    for i in range(n):
        draw_frame(i/FPS).save(f"{fd}/f{i:05d}.png")
    out = f"{ROOT}/visual/visual_master_v3.mp4"
    subprocess.run(["ffmpeg","-y","-v","error","-framerate",str(FPS),
        "-i",f"{fd}/f%05d.png","-c:v","libx264","-preset","medium","-crf","19",
        "-pix_fmt","yuv420p","-movflags","+faststart",out], check=True)
    print("done:", out)

if __name__ == "__main__":
    main()
