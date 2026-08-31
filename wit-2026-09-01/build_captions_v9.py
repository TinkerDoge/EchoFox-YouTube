#!/usr/bin/env python3
"""Build WIT v9 clean editorial captions from approved script + Whisper ASR timings."""
import re, json
from pathlib import Path

ROOT = Path("/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-09-01")
script = ROOT / "audio/narration_script.txt"
asr = ROOT / "captions/words_raw.json"
out = ROOT / "captions/captions_v9.ass"

script_words = re.sub(r"\[[^\]]+\]", "", script.read_text()).split()
asr_words = json.loads(asr.read_text())
asr_words = [{"start": float(w["start"]), "end": float(w["end"]), "word": str(w["word"])} for w in asr_words]

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
matcher = __import__("difflib").SequenceMatcher(None,
    [norm(w) for w in script_words],
    [norm(w["word"]) for w in asr_words], autojunk=False)

timed = []
for tag, i1, i2, j1, j2 in matcher.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            item = asr_words[j1 + k]
            timed.append((script_words[i1 + k], item["start"], item["end"]))
    elif tag == "replace":
        start = asr_words[j1]["start"] if j1 < len(asr_words) else (timed[-1][2] if timed else 0)
        end = asr_words[j2 - 1]["end"] if j2 > 0 else start + 0.3
        for k in range(i2 - i1):
            timed.append((script_words[i1 + k], start, end))
    elif tag == "delete":
        start = timed[-1][2] if timed else 0
        for k in range(i2 - i1):
            timed.append((script_words[i1 + k], start + k * 0.01, start + (k + 1) * 0.05))
    elif tag == "insert":
        continue

events, cur = [], []
def flush():
    if cur:
        events.append((cur[0][1], cur[-1][2], [item[0] for item in cur]))
        cur.clear()
for item in timed:
    cur.append(item)
    if len(cur) >= 4 or (len(cur) >= 2 and item[0].endswith((".", "!", "?"))):
        flush()
flush()
if sum(len(w) for _, _, w in events) != len(script_words):
    raise SystemExit(f"caption word conservation failed: {sum(len(w) for _, _, w in events)} vs {len(script_words)}")

def ts(value):
    return f"0:{int(value // 60):02d}:{value % 60:05.2f}"

header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Editorial,Archivo,34,&H0017212B,&H000000FF,&H00F1F4F5,&H60000000,-1,0,0,0,100,100,0,0,3,5,2,2,44,44,52,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = []
for start, end, words in events:
    text = " ".join(words).replace("{", "").replace("}", "")
    lines.append(f"Dialogue: 0,{ts(start)},{ts(end + 0.05)},Editorial,,0,0,0,,{{\\pos(360,1202)}}{text}")
out.write_text(header + "\n".join(lines) + "\n")
print(f"wrote {out.name} ({len(events)} events, {len(script_words)} approved words)")
print("max caption chars:", max(len(" ".join(w)) for _, _, w in events))
