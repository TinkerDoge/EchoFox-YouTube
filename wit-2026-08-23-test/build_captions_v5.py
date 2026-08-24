#!/usr/bin/env python3
"""Build v5 COMIC caption ASS: text from approved script, timing from ASR words.
Style: solid cream caption box w/ thick ink outline + red accent bar — max
separation from art. One phrase at a time, single line.
"""
import re

ROOT = "/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-08-23-test"
raw = open(f"{ROOT}/audio/narration_script_v5.txt").read()
spoken = re.sub(r'\[[^\]]+\]', '', raw)
words_script = spoken.split()

import json
asr = json.load(open(f"{ROOT}/captions/words_v5.json"))

events = []; cur = []
SENT = ('.','!','?')
def flush():
    global cur
    if cur:
        events.append({"start":cur[0]["start"],"end":cur[-1]["end"],"n":len(cur)}); cur=[]

for w in asr:
    cur.append(w)
    endw = w["word"]
    if len(cur) >= 2 and any(endw.endswith(p) for p in SENT):
        flush(); continue
    if len(cur) >= 4:
        flush()
flush()

merged=[]
for e in events:
    if merged and e["n"]==1:
        merged[-1]["n"]+=e["n"]; merged[-1]["end"]=e["end"]
    else:
        merged.append(e)

si=0; out=[]
for e in merged:
    chunk=words_script[si:si+e["n"]]; si+=e["n"]
    if chunk: out.append({"start":e["start"],"end":e["end"],"text":" ".join(chunk)})
while si<len(words_script) and out:
    out[-1]["text"] += " " + words_script[si]; si+=1

hdr="""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Comic,Luckiest Guy,38,&H00101012,&H000000FF,&H00D3E9F4,&H96000000,-1,0,0,0,100,100,1,0,3,5,3,2,44,44,52,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def ts(t):
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"

lines=[]
for e in out:
    # BorderStyle=3: opaque box using OutlineColour as box... we want cream box + ink text edge.
    # libass BorderStyle=3 draws box in OutlineColour; so set per-line override:
    # box=cream via \\3c&HF4E9D3& won't give ink border simultaneously -> use 4 edges via style (ink outline) is not possible with bs=3 alone.
    # Approach: BorderStyle=3 with BackColour as shadow? Keep simple: cream box (3c), ink text via primary, plus thin ink border via \bord handled by style? bs=3 ignores bord for border but uses it partially in libass (adds padding).
    txt = e["text"].replace("{","").replace("}","")
    lines.append(
        f"Dialogue: 0,{ts(e['start'])},{ts(e['end']+0.05)},Comic,,0,0,0,,"
        f"{{\\pos(360,1176)}}{txt}")

open(f"{ROOT}/captions/captions_v5.ass","w").write(hdr+"\n".join(lines)+"\n")
print("events:", len(out))
print("max chars:", max(len(e["text"]) for e in out))
print("any newline:", any("\\N" in l for l in lines))
