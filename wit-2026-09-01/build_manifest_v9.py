"""Build a timing-locked Weekly In Tech manifest from final ASR word timings."""
import json
from pathlib import Path

ROOT = Path("/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-09-01")
words = json.loads((ROOT / "captions/words_raw.json").read_text())
words = [{"start": float(w["start"]), "end": float(w["end"]), "word": str(w["word"])} for w in words]

# Boundaries are first-word indices for the approved spoken blocks, checked against final ASR.
blocks = [
    ("intro", 0),
    ("chatgpt-ads-expansion", 5),
    ("aws-nvidia-gpu-expansion", 27),
    ("gemma-billion-downloads", 48),
    ("mit-crysvcd-materials", 63),
    ("model-eval-security", 79),
    ("recap", 94),
]
if len(words) < 100:
    raise SystemExit(f"ASR unexpectedly short: {len(words)} words")
segments = []
for index, (story_id, start_index) in enumerate(blocks):
    end_index = blocks[index + 1][1] if index + 1 < len(blocks) else len(words)
    start = words[start_index]["start"]
    end = words[end_index]["start"] if index + 1 < len(blocks) else 55.0
    segments.append({
        "story_id": story_id,
        "cut_start": round(start, 3),
        "cut_end": round(end, 3),
        "assets": [],
        "payoff": {"type": "title" if story_id == "intro" else "recap" if story_id == "recap" else "fact"},
    })
manifest = {
    "edition": "wit-2026-09-01",
    "script_path": "audio/narration_script.txt",
    "voice_id": "fb43143e46f44cc6ad7d06230215bab6",
    "wav": "audio/narration_master.wav",
    "duration": 55.0,
    "segments": segments,
    "word_timing": [{"start": round(w["start"], 3), "end": round(w["end"], 3), "word": w["word"]} for w in words],
    "word_timing_source": "captions/words_raw.json",
    "visual_rights": "Original Pillow editorial graphics and local editorial-identification logos only; no publisher photography reused.",
}
out = ROOT / "research/render_manifest.json"
out.write_text(json.dumps(manifest, indent=2) + "\n")
print(f"wrote {out}: {len(segments)} segments, {len(words)} ASR words, {manifest['duration']:.3f}s")
for seg in segments:
    print(f"{seg['story_id']:28} {seg['cut_start']:6.2f}–{seg['cut_end']:6.2f}")
