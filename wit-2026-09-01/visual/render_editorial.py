#!/usr/bin/env python3
"""Weekly In Tech v8 — source-first editorial renderer.

A reusable 720×1280/30fps clean-master template. It deliberately trades the
retro poster grid for one mobile-readable story per beat:

  signal number → what changed → one proof → why it matters → source/status

Inputs stay contract-owned: research/render_manifest_v8.json locks segment
cuts to ASR timing; research/stories.json holds edition facts. Captions are
burned separately into the reserved lane (y >= 1150).
"""
import json
import math
import os
import subprocess
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "research", "render_manifest.json")
STORIES_PATH = os.path.join(ROOT, "research", "stories.json")
FPS, W, H = 30, 720, 1280
SAFE_X0, SAFE_X1 = 52, 668
CAPTION_Y = 1150

# Calm editorial base; the series gets energy from evidence and timed motion,
# not from decorative panels competing with every fact.
PAPER = (247, 244, 239)
INK = (23, 33, 43)
MUTED = (94, 108, 119)
RULE = (217, 223, 226)
DARK = (17, 27, 37)
WHITE = (255, 255, 255)
ACCENTS = [(255, 90, 95), (23, 107, 135), (233, 162, 59), (96, 70, 180), (30, 155, 120)]

with open(MANIFEST) as f:
    MANIFEST_DATA = json.load(f)
with open(STORIES_PATH) as f:
    STORIES = {s["slug"]: s for s in json.load(f)["stories"]}
SEGMENTS = MANIFEST_DATA["segments"]
DURATION = MANIFEST_DATA["duration"]

FONT_DIR = os.path.join(ROOT, "assets", "fonts")

@lru_cache(maxsize=32)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"{name}.ttf"), size)

def text_w(draw, text, f):
    return draw.textlength(text, font=f)

def wrap(draw, text, f, width, max_lines=None):
    lines, line = [], ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if text_w(draw, candidate, f) <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while text_w(draw, lines[-1] + "…", f) > width and len(lines[-1]) > 1:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines

def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3

def reveal(t, start=0.0, duration=0.35):
    return ease_out((t - start) / duration)

def lerp(a, b, p):
    return int(a + (b - a) * p)

def alpha_color(rgb, alpha):
    return tuple(rgb) + (max(0, min(255, int(alpha))),)

def base_canvas(accent, progress):
    im = Image.new("RGB", (W, H), PAPER).convert("RGBA")
    d = ImageDraw.Draw(im)
    # Subtle vertical editorial grid: structure, not a fake UI dashboard.
    for x in range(56, W, 72):
        d.line([(x, 0), (x, 1125)], fill=(231, 234, 235, 120), width=1)
    for y in range(120, 1126, 96):
        d.line([(SAFE_X0, y), (SAFE_X1, y)], fill=(231, 234, 235, 100), width=1)
    d.rectangle([0, 0, 13, 1128], fill=accent)
    d.rectangle([SAFE_X0, 92, SAFE_X1, 95], fill=accent)
    # Dedicated caption safe lane, left intentionally calm for final ASS burns.
    d.rectangle([0, CAPTION_Y, W, H], fill=(238, 241, 241))
    d.line([(SAFE_X0, CAPTION_Y), (SAFE_X1, CAPTION_Y)], fill=RULE, width=2)
    # Progress never enters captions.
    d.rounded_rectangle([SAFE_X0, 1110, SAFE_X1, 1117], 4, fill=(221, 226, 228))
    d.rounded_rectangle([SAFE_X0, 1110, SAFE_X0 + int((SAFE_X1-SAFE_X0)*progress), 1117], 4, fill=accent)
    return im

def centered(draw, text, y, f, fill, width=W, x0=0):
    draw.text((x0 + (width - text_w(draw, text, f)) / 2, y), text, font=f, fill=fill)

def source_status(story):
    source = story.get("source", "Source pending")
    if source.lower().endswith("listing"):
        return "LISTING / VERIFY BEFORE PUBLISH"
    if source.lower() in {"google", "nvidia", "alibaba / tongyi lab", "meta superintelligence labs"}:
        return "PRIMARY-CLAIM / CHECK LINKED RELEASE"
    return story.get("claim_status", "SOURCE REVIEW REQUIRED").upper()

def draw_logo(im, story, x, y, size, p):
    path = os.path.join(ROOT, "assets", "real", story["logo"])
    if not os.path.exists(path):
        return
    logo = Image.open(path).convert("RGBA")
    ratio = min(size / logo.width, size / logo.height)
    logo = logo.resize((max(1, int(logo.width * ratio * (0.88 + 0.12*p))), max(1, int(logo.height * ratio * (0.88 + 0.12*p)))), Image.LANCZOS)
    plate = Image.new("RGBA", im.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pad = 18
    pd.rounded_rectangle([x-pad, y-pad, x+size+pad, y+size+pad], 16, fill=(255,255,255,245), outline=(213,220,223,255), width=2)
    im.alpha_composite(plate)
    im.alpha_composite(logo, (x + (size-logo.width)//2, y + (size-logo.height)//2))

def metric_text(story):
    payoff = story.get("payoff", {})
    typ = payoff.get("type")
    if typ == "counter":
        value = payoff.get("value", 0)
        if value >= 1_000_000_000_000:
            return f"{value/1_000_000_000_000:g}T", payoff.get("label", "metric")
        if value >= 1_000_000:
            return f"{value/1_000_000:g}M", payoff.get("label", "metric")
        return f"{value:,}", payoff.get("label", "metric")
    if typ == "multiplier":
        return "4×", "faster agent workloads"
    if typ == "statcard":
        return str(payoff.get("value", "OPEN")), payoff.get("label", "key status")
    return None, payoff.get("label", "comparison")

def metric_card(im, story, accent, local_t):
    d = ImageDraw.Draw(im)
    p = reveal(local_t, 0.35, 0.45)
    y0, y1 = 690 + int((1-p)*20), 900 + int((1-p)*20)
    d.rounded_rectangle([SAFE_X0, y0, SAFE_X1, y1], 22, fill=WHITE, outline=RULE, width=2)
    d.rectangle([SAFE_X0, y0, SAFE_X0+8, y1], fill=accent)
    payoff = story.get("payoff", {})
    kind = payoff.get("type")
    small = font("Archivo", 22)
    bold = font("Archivo", 29)
    if kind in ("comparison", "bar"):
        rows = payoff.get("values", [])
        maximum = max([value for _, value in rows] or [1])
        for j, (label, value) in enumerate(rows[:4]):
            rp = reveal(local_t, 0.45 + j*0.12, 0.32)
            yy = y0 + 30 + j*37
            d.text((80, yy), label[:18], font=small, fill=INK)
            bx0, bx1 = 270, 560
            d.rounded_rectangle([bx0, yy+4, bx1, yy+24], 8, fill=(229,233,234))
            d.rounded_rectangle([bx0, yy+4, bx0+int((bx1-bx0)*(value/maximum)*rp), yy+24], 8, fill=accent if j == 0 else (130,145,153))
            d.text((578, yy-2), f"{value:g}", font=bold, fill=INK)
        centered(d, payoff.get("label", "comparison"), y1-38, small, MUTED, SAFE_X1-SAFE_X0, SAFE_X0)
    else:
        value, label = metric_text(story)
        number_font = font("Archivo", 82 if len(value or "") < 12 else 58)
        d.text((80, y0+44), value or "—", font=number_font, fill=accent)
        d.text((82, y0+148), label.upper(), font=font("Archivo", 25), fill=INK)
        d.text((82, y0+178), "ONE PROOF POINT — READ FULL CONTEXT IN DESCRIPTION", font=font("Archivo", 17), fill=MUTED)

def intro_frame(t):
    accent = ACCENTS[0]
    im = base_canvas(accent, min(1, t/2.88))
    d = ImageDraw.Draw(im)
    p = reveal(t, 0, 0.6)
    d.text((SAFE_X0, 142), "THE TENSOR FOUNDRY", font=font("Archivo", 24), fill=MUTED)
    d.text((SAFE_X0, 208-int((1-p)*30)), "WEEKLY", font=font("Archivo", 82), fill=INK)
    d.text((SAFE_X0, 300-int((1-p)*30)), "IN TECH", font=font("Archivo", 82), fill=INK)
    d.rectangle([SAFE_X0, 412, SAFE_X0+92, 422], fill=accent)
    d.text((SAFE_X0, 458), "5 SIGNALS", font=font("Archivo", 34), fill=INK)
    d.text((SAFE_X0, 506), "what changed · why it matters · where it came from", font=font("Archivo", 23), fill=MUTED)
    d.rounded_rectangle([SAFE_X0, 630, SAFE_X1, 770], 22, fill=DARK)
    d.text((80, 658), "THE WEEK'S THROUGH-LINE", font=font("Archivo", 20), fill=(191,205,212))
    d.text((80, 700), "AI IS BECOMING INFRASTRUCTURE.", font=font("Archivo", 28), fill=WHITE)
    d.text((80, 740), "Each signal includes a visible source/status cue.", font=font("Archivo", 20), fill=(215,225,229))
    d.text((SAFE_X0, 1060), "SOURCE-FIRST EDITORIAL SYSTEM · SEP 01", font=font("Archivo", 17), fill=MUTED)
    return im.convert("RGB")

def story_frame(index, local_t):
    seg = SEGMENTS[index]
    story = STORIES[seg["story_id"]]
    accent = ACCENTS[(index-1) % len(ACCENTS)]
    total = 5
    im = base_canvas(accent, (index-1)/(total+1))
    d = ImageDraw.Draw(im)
    p = reveal(local_t, 0, 0.35)
    # Masthead and position: compact and repeatable, never visually louder than the story.
    d.text((SAFE_X0, 26), "WEEKLY IN TECH", font=font("Archivo", 20), fill=MUTED)
    d.text((SAFE_X1-104, 26), f"{index:02d} / {total:02d}", font=font("Archivo", 20), fill=INK)
    d.text((SAFE_X0, 124), "WHAT CHANGED", font=font("Archivo", 20), fill=accent)
    logo_p = reveal(local_t, 0.1, 0.4)
    draw_logo(im, story, 536, 118, 94, logo_p)
    # Keep the complete claim readable; a headline is not a place for decorative ellipses.
    # Four smaller lines keep every sourced headline complete; ellipses can
    # hide a material qualification in a news claim.
    title_font = font("Archivo", 36)
    y = 168 + int((1-p)*24)
    for line in wrap(d, story["headline"].upper(), title_font, 470, 4):
        d.text((SAFE_X0, y), line, font=title_font, fill=INK)
        y += 50
    # One clear why statement prevents decorative fact-pills.
    why_p = reveal(local_t, 0.25, 0.4)
    why_y = max(382, y + 24) + int((1-why_p)*14)
    d.text((SAFE_X0, why_y), "WHY IT MATTERS", font=font("Archivo", 20), fill=accent)
    claim = story.get("verified_claims", ["Context pending"])[0]
    claim_font = font("Archivo", 28)
    for line in wrap(d, claim, claim_font, SAFE_X1-SAFE_X0, 2):
        why_y += 35
        d.text((SAFE_X0, why_y), line, font=claim_font, fill=INK)
    d.line([(SAFE_X0, 570), (SAFE_X1, 570)], fill=RULE, width=2)
    d.text((SAFE_X0, 594), "EVIDENCE SNAPSHOT", font=font("Archivo", 20), fill=accent)
    d.text((SAFE_X0, 624), "One metric only. Benchmark labels stay visible.", font=font("Archivo", 21), fill=MUTED)
    metric_card(im, story, accent, local_t)
    # Credibility stack: readable on-frame source, date, and review status.
    d.text((SAFE_X0, 936), f"SOURCE  {story.get('source', 'Source pending').upper()}", font=font("Archivo", 19), fill=INK)
    d.text((SAFE_X0, 966), f"DATE  {story.get('date', '—')}  ·  {source_status(story)}", font=font("Archivo", 16), fill=MUTED)
    d.text((SAFE_X0, 1000), "Full link, methodology, and license ledger: video description", font=font("Archivo", 16), fill=MUTED)
    d.text((SAFE_X0, 1040), "LOGO: EDITORIAL IDENTIFICATION · NOT AN ENDORSEMENT", font=font("Archivo", 14), fill=MUTED)
    return im.convert("RGB")

def recap_frame(t):
    im = base_canvas(ACCENTS[4], 1.0)
    d = ImageDraw.Draw(im)
    p = reveal(t, 0, 0.45)
    d.text((SAFE_X0, 142), "THE TAKEAWAY", font=font("Archivo", 21), fill=ACCENTS[4])
    d.text((SAFE_X0, 188), "AI IS BECOMING", font=font("Archivo", 54), fill=INK)
    d.text((SAFE_X0, 258), "INFRASTRUCTURE.", font=font("Archivo", 54), fill=INK)
    d.text((SAFE_X0, 356), "Five signals. One evidence-led thread.", font=font("Archivo", 26), fill=MUTED)
    for j, story in enumerate(STORIES.values()):
        rp = reveal(t, 0.25 + j*0.18, 0.3)
        y = 470 + j*82 + int((1-rp)*18)
        d.ellipse([SAFE_X0, y+6, SAFE_X0+16, y+22], fill=ACCENTS[j])
        d.text((SAFE_X0+32, y), story["headline"].split(":")[0], font=font("Archivo", 22), fill=INK)
        d.text((SAFE_X0+32, y+30), story["source"], font=font("Archivo", 16), fill=MUTED)
    d.rounded_rectangle([SAFE_X0, 950, SAFE_X1, 1042], 18, fill=DARK)
    d.text((80, 974), "NEXT WEEK: FOLLOW THE PRIMARY SOURCES.", font=font("Archivo", 22), fill=WHITE)
    d.text((80, 1008), "Tensor Foundry · weekly research digest", font=font("Archivo", 17), fill=(202,214,219))
    return im.convert("RGB")

def draw_frame(t):
    for index, seg in enumerate(SEGMENTS):
        if seg["cut_start"] <= t < seg["cut_end"]:
            if seg["story_id"] == "intro":
                return intro_frame(t - seg["cut_start"])
            if seg["story_id"] == "recap":
                return recap_frame(t - seg["cut_start"])
            return story_frame(index, t - seg["cut_start"])
    return recap_frame(max(0, t - SEGMENTS[-1]["cut_end"]))

def main():
    frame_dir = os.path.join(ROOT, "visual", "frames_v9")
    os.makedirs(frame_dir, exist_ok=True)
    frame_count = round(DURATION * FPS)
    print(f"Rendering {frame_count} v9 frames at {FPS}fps…")
    for i in range(frame_count):
        draw_frame(i / FPS).save(os.path.join(frame_dir, f"f{i:05d}.png"))
        if i % 300 == 0:
            print(f"frame {i}/{frame_count}")
    output = os.path.join(ROOT, "visual", "visual_master_v9.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
        "-i", os.path.join(frame_dir, "f%05d.png"), "-c:v", "libx264",
        "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", output,
    ], check=True)
    print(output)

if __name__ == "__main__":
    main()
