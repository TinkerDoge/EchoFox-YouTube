#!/usr/bin/env python3
"""Build v6 comic caption ASS.
TEXT = approved script words (editorially correct). TIMING = ASR word count
alignment only. Fixes v5's mismatch where raw ASR spellings ("Quinn", "60",
"name atron") leaked into captions.
"""
import re, json, difflib

ROOT = "/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-08-23-test"
raw = open(f"{ROOT}/audio/narration_script_v5.txt").read()
script_words = re.sub(r'\[[^\]]+\]', '', raw).split()
asr = json.load(open(f"{ROOT}/captions/words_v6.json"))

norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
sm = difflib.SequenceMatcher(None,
     [norm(w) for w in script_words],
     [norm(w["word"]) for w in asr], autojunk=False)

# assign a time span to each script word via opcodes
timed=[]  # (word, start, end)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=="equal":
        for k in range(i2-i1):
            w=asr[j1+k]
            timed.append((script_words[i1+k], w["start"], w["end"]))
    elif tag=="replace":
        n_s, n_a = i2-i1, j2-j1
        t0 = asr[j1]["start"] if j1 < len(asr) else timed[-1][2]
        t1 = asr[j2-1]["end"] if j2-1 < len(asr) else t0+0.3
        for k in range(n_s):
            timed.append((script_words[i1+k], t0, t1))
    elif tag=="insert":
        continue  # ASR hallucination — no script word to attach
    elif tag=="delete":
        # script word dropped by ASR: interpolate between neighbours
        t0 = timed[-1][2] if timed else 0.0
        for k in range(i2-i1):
            timed.append((script_words[i1+k], t0+0.01*k, t0+0.05*(k+1)))

# group into caption phrases: sentence-ending or max 4 words
events=[]; cur=[]
SENT=('.','!','?')
def flush():
    global cur
    if cur:
        events.append({"start":cur[0][1],"end":cur[-1][2],"words":[w[0] for w in cur]}); cur=[]
for item in timed:
    cur.append(item)
    endw=item[0]
    if len(cur)>=2 and any(endw.endswith(p) for p in SENT): flush(); continue
    if len(cur)>=4: flush()
flush()

merged=[]
for e in events:
    if merged and len(e["words"])==1:
        merged[-1]["words"]+=e["words"]; merged[-1]["end"]=e["end"]
    else:
        merged.append(e)

# verify total word count conservation
n_script=len(script_words); n_cap=sum(len(e["words"]) for e in merged)
print(f"script words {n_script} -> captioned {n_cap}")

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
for e in merged:
    txt=" ".join(e["words"]).replace("{","").replace("}","")
    lines.append(f"Dialogue: 0,{ts(e['start'])},{ts(e['end']+0.05)},Comic,,0,0,0,,{{\\pos(360,1176)}}{txt}")

open(f"{ROOT}/captions/captions_v6.ass","w").write(hdr+"\n".join(lines)+"\n")
print("events:",len(merged),"max chars:",max(len(" ".join(e['words'])) for e in merged))
