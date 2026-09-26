#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-09-01")

m = json.load(open(ROOT/"research/render_manifest.json"))
m["duration"] = 70.347755

# ASR word timings (cleaned)
words = [{"start": float(w["start"]), "end": float(w["end"]), "word": str(w["word"])} 
         for w in json.load(open(ROOT/"captions/words_raw.json"))]

# Story boundary indices (from ASR timing)
boundaries = {
    "intro":    (0,   5),      # 0.00 - 3.28
    "openai":   (5,  44),      # 3.28 - 20.78
    "nvidia":   (44, 83),      # 20.78 - 38.96
    "google":   (83, 110),     # 38.96 - 49.60
    "security": (110,136),     # 49.60 - 64.34
    "recap":    (136, len(words))  # 64.34 - end
}

slugs = {
    "openai": "chatgpt-ads-expansion",
    "nvidia": "nvidia-vera-shipping",
    "google": "gemma-billion-downloads",
    "security": "model-eval-security",
}

logos = {
    "openai": "openai_logo.png",
    "nvidia": "nvidia_logo.png",
    "google": "google_logo.png",
    "security": "openai_logo.png",
}

payoffs = {
    "openai":   {"type": "statcard", "value": "$1B", "label": "annualized run rate"},
    "nvidia":   {"type": "statcard", "value": "88", "label": "custom CPU cores"},
    "google":   {"type": "statcard", "value": "1B", "label": "Gemma downloads"},
    "security": {"type": "statcard", "value": "AUG 26", "label": "findings update"},
}

segments = []
for sid, (s_idx, e_idx) in boundaries.items():
    if sid == "intro":
        seg = {"story_id": "intro", "cut_start": 0.0, 
               "cut_end": round(words[e_idx]["start"], 2) if e_idx < len(words) else 3.28,
               "assets": [], "payoff": {"type": "title"}}
    elif sid == "recap":
        seg = {"story_id": "recap", 
               "cut_start": round(words[s_idx]["start"], 2),
               "cut_end": round(words[-1]["end"], 2),
               "assets": [], "payoff": {"type": "recap"}}
    else:
        seg = {"story_id": slugs[sid],
               "cut_start": round(words[s_idx]["start"], 2),
               "cut_end": round(words[e_idx]["start"], 2) if e_idx < len(words)-1 else round(words[-1]["end"], 2),
               "assets": [f"assets/real/{logos[sid]}.png"],
               "payoff": payoffs[sid]}
    segments.append(seg)

m["segments"] = segments
m["word_timing"] = [{"start": round(w["start"], 2), "end": round(w["end"], 2), "word": w["word"]} for w in words]
m["word_timing_source"] = "captions/words_raw.json"

Path(ROOT/"research/render_manifest.json").write_text(json.dumps(m, indent=2))
print(f"Updated manifest: {len(segments)} segments, duration={m['duration']}")
for i, s in enumerate(segments):
    gap = "" if i == 0 else f"  gap={s['cut_start']-segments[i-1]['cut_end']:+.2f}"
    print(f"  {i+1}. {s['story_id']:25s} {s['cut_start']:6.2f} - {s['cut_end']:6.2f}{gap}")
