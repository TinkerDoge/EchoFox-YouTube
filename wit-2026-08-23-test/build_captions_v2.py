#!/usr/bin/env python3
"""Build phrase captions: TEXT from the approved script (de-tagged), TIMING from ASR words only."""
import re, sys
from faster_whisper import WhisperModel

ROOT = "/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-08-23-test"
raw = open(f"{ROOT}/audio/narration_script_v2.txt").read()
spoken = re.sub(r'\[[^\]]+\]', '', raw)
words_script = spoken.split()

m = WhisperModel("base", device="cpu", compute_type="int8")
segs, _ = m.transcribe(f"{ROOT}/audio/narration_master.wav", word_timestamps=True)
asr = []
for s in segs:
    for w in s.words:
        asr.append({"start": round(w.start,2), "end": round(w.end,2), "word": w.word.strip()})

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

# merge orphan single-word events into previous
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
Style: Cap,DejaVu Sans,38,&H00FFFFFF,&HAA000000,&H00000000,&H88000000,-1,0,0,0,100,100,0,0,3,2,0,2,40,40,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def ts(t):
    h=int(t//3600); mnt=int(t%3600//60); s=t%60
    return f"{h}:{mnt:02d}:{s:05.2f}"
lines=[]; prev=0
for e in out:
    st=max(e["start"], prev+0.02)
    lines.append(f"Dialogue: 0,{ts(st)},{ts(e['end'])},Cap,,0,0,0,,{{\\pos(360,1170)}}{e['text']}")
    prev=e["end"]
open(f"{ROOT}/captions/captions_v2.ass","w").write(hdr+"\n".join(lines)+"\n")
print(len(out),"events; first:",[o["text"] for o in out[:4]])
