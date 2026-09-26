#!/usr/bin/env python3
"""
Tensor Foundry — Reusable 9:16 Story Frame Layout
=================================================
Canonical zone map for WIT (Weekly In Tech) shorts.

Encodes two transferable lessons from the reaction-short editing study
(@AsmongoldShorts1), adapted to a faceless editorial channel:

  1. DUAL-PANEL SIMULTANEITY
     The source visual and the context/data panel are BOTH on screen at
     once. We never cut away from the source to reveal the stat — the
     viewer reads both in parallel (reactor + the thing reacted to).

  2. CAPTION-ON-SEAM
     The kinetic caption lives in a band that straddles the boundary
     between the two panels, so it stays legible over both backgrounds.

V3 palette: base #0a0a0f, violet (148,102,220), copper (222,138,72).

Renderer-agnostic: import LAYOUT / helpers, draw your content inside the
returned rects. Drop-in for render_v3.py and future renderers.
"""
W, H = 720, 1280          # 9:16 native
FPS = 30
MARGIN_X = 40

# V3 palette
BASE   = (10, 10, 15)
PANEL  = (22, 22, 30)
VIOLET = (148, 102, 220)
COPPER = (222, 138, 72)
TEXT   = (238, 236, 240)
MUTED  = (150, 148, 156)

# Zones: (x0, y0, x1, y1) — upper-left origin
LAYOUT = {
    # channel mark + episode/date, pinned top
    "branding": (MARGIN_X, 24, W - MARGIN_X, 78),
    # source/visual panel — the "thing being reported" (logo, KB image, FLUX)
    "source":   (0, 78, W, 720),
    # caption seam band — straddles source/context boundary
    "seam":     (0, 720, W, 812),
    # context/data panel — payoff (counter, bar, statcard)
    "context":  (MARGIN_X, 824, W - MARGIN_X, 1170),
    # citation + verified chip, pinned bottom
    "footer":   (MARGIN_X, 1182, W - MARGIN_X, 1248),
}

def zone(name):
    return LAYOUT[name]

def zone_rect(name):
    x0, y0, x1, y1 = LAYOUT[name]
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

def zone_center(name):
    x0, y0, x1, y1 = LAYOUT[name]
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)

def source_center():
    """Center point for a centered plate inside the source panel.
    Biased slightly above middle so a headline below it still fits."""
    cx = W / 2.0
    x0, y0, x1, y1 = LAYOUT["source"]
    cy = y0 + (y1 - y0) * 0.42
    return (cx, cy)

def caption_seam_rect():
    """Inner rect available to the kinetic caption (with horizontal pad)."""
    x0, y0, x1, y1 = LAYOUT["seam"]
    return (x0 + 20, y0, x1 - 20, y1)
