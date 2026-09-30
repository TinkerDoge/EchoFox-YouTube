#!/usr/bin/env python3
"""Rebuild polished clips from the clean *_raw.mp3 stems.

Stage 1 (this file): two-pass loudnorm only. The second pass is given the pass-1
measurements so ffmpeg's linear corrector lands accurately.
Stage 2 (skill script): exact measured static gain -> true -16.0 LUFS.
  python3 ~/.hermes/skills/media/tech-news-shorts-production/scripts/polish_loudness.py

Do NOT fold the static gain in here. Doing loudnorm + volume in one chain stacks
the correction and drove true peak to +8 dBFS (audible clipping).
"""
import json
import os
import subprocess

EP = os.path.expanduser("~/hf-codedoctor/daily-digest-2026-09-30")
NARR = os.path.join(EP, "narration")
TARGET = -16.0

script = json.load(open(os.path.join(EP, "script.json")))

for seg in script["segments"]:
    sid = seg["id"]
    raw = os.path.join(NARR, f"{sid}_raw.mp3")
    out = os.path.join(NARR, f"{sid}.mp3")
    if not os.path.exists(raw):
        raise SystemExit(f"missing raw stem: {raw}")

    # pass 1: measure
    p1 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", raw,
         "-af", f"loudnorm=I={TARGET}:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    blk = p1[p1.rfind("{"): p1.rfind("}") + 1]
    m = json.loads(blk)

    # pass 2: apply measured, linear
    af = (f"loudnorm=I={TARGET}:TP=-1.5:LRA=11:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"linear=true")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-i", raw, "-af", af,
         "-ar", "48000", "-ac", "2", out],
        capture_output=True, check=True,
    )
    print(f"{sid}: loudnorm pass1 input_i={m['input_i']} -> wrote {os.path.basename(out)}")
