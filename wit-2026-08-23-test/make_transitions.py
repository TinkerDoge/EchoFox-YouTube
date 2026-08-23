#!/usr/bin/env python3
"""Generate abstract V3 transition plates procedurally."""
import math, random, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = "/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-08-23-test"
os.makedirs(f"{ROOT}/assets/transitions", exist_ok=True)
random.seed(42)
W, H = 720, 1280
VIOLET = (148, 102, 220)
COPPER = (222, 138, 72)
BG = (10, 10, 15)

# Plate 1: neural sphere particles
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im, "RGBA")
cx, cy, R = W / 2, H / 2 - 60, 260
for i in range(900):
    th = random.uniform(0, 2 * math.pi)
    ph = math.acos(random.uniform(-1, 1))
    r = R * (random.uniform(0.55, 1.0) ** 0.7)
    x = cx + r * math.sin(ph) * math.cos(th)
    y = cy + r * math.cos(ph) * 0.92
    depth = (math.sin(ph) * math.sin(th) + 1) / 2
    c = VIOLET if i % 3 else COPPER
    a = int(60 + 150 * depth)
    s = random.choice([1, 1, 2])
    d.ellipse([x - s, y - s, x + s, y + s], fill=c + (a,))
for i in range(60):
    a2, b2 = random.sample(range(24), 2)
    th1, ph1 = a2 / 24 * 2 * math.pi, math.acos(2 * (a2 % 12) / 12 - 1)
    th2, ph2 = b2 / 24 * 2 * math.pi, math.acos(2 * (b2 % 12) / 12 - 1)
    x1 = cx + R * math.sin(ph1) * math.cos(th1); y1 = cy + R * math.cos(ph1) * 0.92
    x2 = cx + R * math.sin(ph2) * math.cos(th2); y2 = cy + R * math.cos(ph2) * 0.92
    d.line([x1, y1, x2, y2], fill=VIOLET + (28,))
im = im.filter(ImageFilter.GaussianBlur(0.5))
im.save(f"{ROOT}/assets/transitions/sphere.png")

# Plate 2: fiber streaks converging to copper line
im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im, "RGBA")
for i in range(140):
    y0 = random.randint(-100, H + 100)
    ln = random.randint(120, 600)
    x0 = random.randint(-200, W)
    c = VIOLET if i % 4 else COPPER
    a = random.randint(30, 110)
    wdt = random.choice([1, 1, 2, 3])
    d.line([x0, y0, x0 + ln, y0 + random.randint(-8, 8)], fill=c + (a,), width=wdt)
d.rectangle([int(W / 2 - 2), H // 2 - 260, int(W / 2 + 2), H // 2 + 260], fill=COPPER + (255,))
glow = Image.new("RGB", (W, H), BG)
gd = ImageDraw.Draw(glow)
gd.rectangle([int(W / 2 - 14), H // 2 - 280, int(W / 2 + 14), H // 2 + 280], fill=COPPER)
glow = glow.filter(ImageFilter.GaussianBlur(40))
im = Image.blend(im, glow, 0.35)
im.save(f"{ROOT}/assets/transitions/fiber.png")
print("transition plates done")
