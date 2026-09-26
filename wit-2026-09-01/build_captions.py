#!/usr/bin/env python3
"""Build WIT v8 clean editorial captions.

Caption words always come from the approved script. ASR supplies timings only;
this keeps misspelled model names and raw recognizer artifacts out of the final.
"""
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
raw = (ROOT / "audio/narration_script_v5.txt").read_text()
script_words = re.sub(r"\[[^\]]+\]", "", raw).split()
asr = json.loads((ROOT / "captions/words_v6.json").read_text())
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
matcher = difflib.SequenceMatcher(None, [norm(word) for word in script_words], [norm(item["word"]) for item in asr], autojunk=False)
timed = []
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == "equal":
        for offset in range(i2 - i1):
            item = asr[j1 + offset]
            timed.append((script_words[i1 + offset], item["start"], item["end"]))
    elif tag == "replace":
        start = asr[j1]["start"] if j1 < len(asr) else (timed[-1][2] if timed else 0)
        end = asr[j2 - 1]["end"] if j2 else start + .3
        for offset in range(i2 - i1):
            timed.append((script_words[i1 + offset], start, end))
    elif tag == "delete":
        start = timed[-1][2] if timed else 0
        for offset in range(i2 - i1):
            timed.append((script_words[i1 + offset], start + offset*.01, start + (offset+1)*.05))

# Short 2–4 word phrases make captions readable at feed speed.
events, current = [], []
def flush():
    if current:
        events.append((current[0][1], current[-1][2], [item[0] for item in current]))
        current.clear()
for item in timed:
    current.append(item)
    if len(current) >= 4 or (len(current) >= 2 and item[0].endswith((".", "!", "?"))):
        flush()
flush()
if sum(len(words) for _, _, words in events) != len(script_words):
    raise RuntimeError("caption word conservation failed")

def timestamp(value):
    return f"0:{int(value//60):02d}:{value%60:05.2f}"

header = r'''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Editorial,Archivo,34,&H0017212B,&H000000FF,&H00F1F4F5,&H60000000,-1,0,0,0,100,100,0,0,3,5,2,2,44,44,52,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
lines = []
for start, end, words in events:
    text = " ".join(words).replace("{", "").replace("}", "")
    lines.append(f"Dialogue: 0,{timestamp(start)},{timestamp(end+.05)},Editorial,,0,0,0,,{{\\pos(360,1202)}}{text}")
out = ROOT / "captions/captions_v8.ass"
out.write_text(header + "\n".join(lines) + "\n")
print(f"wrote {out} ({len(events)} events, {len(script_words)} approved words)")
