#!/usr/bin/env python3
"""Rebuild voice-timing.json + segs.json from the polished narration clips.

No TTS here -- gen_audio.py owns synthesis. This only re-probes durations and
re-lays the timeline, so a re-loudness pass never desyncs the captions.
"""
import json
import os
import subprocess

EP = os.path.expanduser("~/hf-codedoctor/daily-digest-2026-09-30")
NARR = os.path.join(EP, "narration")

script = json.load(open(os.path.join(EP, "script.json")))


def dur(p):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", p],
        capture_output=True, text=True, check=True).stdout.strip())


timeline, scenes, total = [], [], 0.0
for i, seg in enumerate(script["segments"]):
    d = dur(os.path.join(NARR, f"{seg['id']}.mp3"))
    timeline.append({
        "id": seg["id"], "speaker": "sora", "start": round(total, 3),
        "duration": round(d, 3), "end": round(total + d, 3),
        "track": 2 if i % 2 == 0 else 3,
        "text": seg["text"],
        "audio_file": f"assets/audio/{seg['id']}.mp3",
        "kicker": seg["kicker"], "headline": seg["headline"],
        "subhead": seg["subhead"], "detail": seg["detail"],
        "source": seg["source"], "visual": seg["visual"], "scene": seg["scene"],
    })
    scenes.append({
        "id": seg["scene"], "start": round(total, 3),
        "end": round(total + d, 3), "duration": round(d, 3),
        "kicker": seg["kicker"], "headline": seg["headline"],
        "subhead": seg["subhead"], "detail": seg["detail"],
        "source": seg["source"], "visual": seg["visual"],
    })
    total += d

total = round(total + 1.5, 3)  # outro tail
json.dump({"total_duration": total, "timeline": timeline, "scenes": scenes},
          open(os.path.join(EP, "voice-timing.json"), "w"), indent=2)

# segs.json for the aligner: needs dur as well as start
json.dump({"total": total,
           "segments": [{"id": t["id"], "start": t["start"], "dur": t["duration"]}
                        for t in timeline]},
          open(os.path.join(EP, "segs.json"), "w"), indent=2)

print(f"total {total}s across {len(timeline)} clips\n")
for t in timeline:
    print(f"  {t['id']:14} {t['start']:6.2f}-{t['end']:6.2f} ({t['duration']:5.2f}s) track {t['track']}")
