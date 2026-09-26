#!/usr/bin/env python3
"""Render reusable-layout previews to PNG (no ffmpeg needed).
Produces two proofs:
  previews/layout_zones.png       — labeled zone diagram
  previews/layout_mock_story.png  — realistic mock story frame using the zones
"""
import os
from PIL import Image, ImageDraw, ImageFont
import layout as L

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "previews")
os.makedirs(OUT, exist_ok=True)

def font(sz, bold=True):
    n = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}", sz)

def zone_diagram():
    img = Image.new("RGB", (L.W, L.H), L.BASE)
    d = ImageDraw.Draw(img)
    cols = {
        "branding": (40, 90, 140),
        "source":   (60, 60, 90),
        "seam":     (140, 100, 40),
        "context":  (60, 90, 60),
        "footer":   (90, 60, 90),
    }
    for name, (x0, y0, x1, y1) in L.LAYOUT.items():
        d.rectangle([x0, y0, x1, y1], outline=cols[name], width=3)
        c = L.zone_center(name)
        label = f"{name}\n{x1 - x0}x{y1 - y0}"
        f = font(22)
        lines = label.split("\n")
        yy = c[1] - (len(lines) * 26) // 2
        for ln in lines:
            tw = d.textlength(ln, font=f)
            d.text((c[0] - tw / 2, yy), ln, font=f, fill=(200, 200, 210))
            yy += 26
    path = os.path.join(OUT, "layout_zones.png")
    img.save(path)
    print("wrote", path)

def mock_story():
    img = Image.new("RGB", (L.W, L.H), L.BASE)
    d = ImageDraw.Draw(img)
    # gradient top wash
    grad = Image.new("L", (1, 300))
    for yy in range(300):
        grad.putpixel((0, yy), int(40 * (1 - yy / 300)))
    img.paste(Image.new("RGB", (L.W, 300), L.VIOLET), (0, 0), grad.resize((L.W, 300)))
    d = ImageDraw.Draw(img)

    # branding
    bx0, by0, bx1, by1 = L.LAYOUT["branding"]
    d.text((bx0, by0), "THE TENSOR FOUNDRY  ·  WIT #12", font=font(24), fill=L.COPPER)

    # source panel: mock logo plate + headline
    cx, cy = L.source_center()
    pw, ph = 360, 360
    pl = Image.new("RGBA", (pw, ph), (255, 255, 255, 235))
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw, ph], 28, fill=255)
    full = img.convert("RGBA")
    full.paste(pl, (int(cx - pw / 2), int(cy - ph / 2)), mask)
    img = full.convert("RGB")
    d = ImageDraw.Draw(img)
    d.text((cx - d.textlength("OPENAI", font=font(48)) / 2, cy - 30), "OPENAI", font=font(48), fill=L.BASE)
    hy = cy + ph / 2 + 30
    for ln in ["OpenAI drops a", "stealth model"]:
        d.text((cx - d.textlength(ln, font=font(40)) / 2, hy), ln, font=font(40), fill=L.TEXT)
        hy += 50
    d.text((cx - d.textlength("OpenAI · Aug 2026", font=font(22)) / 2, hy + 6),
           "OpenAI · Aug 2026", font=font(22), fill=L.MUTED)

    # seam caption (kinetic mock) — straddles the boundary, outlined
    sx0, sy0, sx1, sy1 = L.LAYOUT["seam"]
    caption = "A QUIET RELEASE WITH BIG IMPLICATIONS"
    cf = font(38)
    cyc = (sy0 + sy1) / 2
    tw = d.textlength(caption, font=cf)
    tx = (L.W - tw) / 2
    d.text((tx, cyc - 26), caption, font=cf, fill=L.TEXT, stroke_width=3, stroke_fill=(0, 0, 0))

    # context panel: comparison bar (data visible alongside the source)
    cxx0, cyy0, cxx1, cyy1 = L.LAYOUT["context"]
    cv = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cv)
    cd.rounded_rectangle([cxx0, cyy0, cxx1, cyy1], 20, fill=(30, 30, 42, 220),
                         outline=L.VIOLET + (160,), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), cv).convert("RGB")
    d = ImageDraw.Draw(img)
    rows = [("Stealth", 92), ("Public", 71)]
    maxv = 100
    bx = 230
    for j, (name, v) in enumerate(rows):
        ry = cyy0 + 40 + j * 70
        bw = int((L.W - 300) * (v / maxv))
        col = L.VIOLET if j == 0 else (90, 90, 104)
        d.rounded_rectangle([bx, ry, bx + bw, ry + 46], 8, fill=col)
        d.text((66, ry + 9), name, font=font(20), fill=L.TEXT)
        d.text((bx + bw + 8, ry + 10), f"{v}", font=font(22), fill=L.TEXT)
    d.text((bx, cyy1 - 34), "Stealth-vs-public coverage score", font=font(19), fill=L.MUTED)

    # footer: citation + verified chip
    fx0, fy0, fx1, fy1 = L.LAYOUT["footer"]
    d.text((fx0, fy0), "Source: OpenAI · Aug 2026", font=font(20), fill=L.MUTED)
    d.text((fx1 - d.textlength("✓ verified", font=font(20)), fy0), "✓ verified", font=font(20), fill=(120, 200, 120))

    path = os.path.join(OUT, "layout_mock_story.png")
    img.save(path)
    print("wrote", path)

if __name__ == "__main__":
    zone_diagram()
    mock_story()
