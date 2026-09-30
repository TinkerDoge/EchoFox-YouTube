#!/usr/bin/env python3
"""Align narration to word-level timestamps for karaoke captions.

Transcribes the composition-time narration stem with faster-whisper and snaps every
recognised word onto the segment boundaries in segs.json, so a caption line can never
straddle a scene change.

Requires a narration stem built at composition time (see
references/karaoke-captions.md step 1) and a faster-whisper install:

    uv venv wv --python 3.12
    uv pip install --python ./wv/bin/python faster-whisper
    ./wv/bin/python align_words.py <segs.json> <narration_stem.wav> [words.json]

Re-run after ANY narration re-synthesis: a corrected line shifts every later segment's
start, and a stale words.json silently mis-times every caption after it.
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    segs_path, audio_path = sys.argv[1], sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else "words.json"

    segs = json.load(open(segs_path))["segments"]
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."

    from faster_whisper import WhisperModel

    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio_path, language="en", word_timestamps=True,
        beam_size=5, vad_filter=False,
    )

    words = []
    for seg in segments:
        for w in (seg.words or []):
            tok = w.word.strip()
            if not tok:
                continue
            words.append({"w": tok, "s": round(w.start, 3), "e": round(w.end, 3)})
    print(f"aligned {len(words)} words")

    # Snap each word to a segment: containing span wins, else nearest centre.
    for word in words:
        mid = (word["s"] + word["e"]) / 2
        best, best_d = None, 1e9
        for s in segs:
            if s["start"] <= word["e"] and word["s"] <= s["start"] + s["dur"]:
                best, best_d = s["id"], 0
                break
            d = abs(mid - (s["start"] + s["dur"] / 2))
            if d < best_d:
                best, best_d = s["id"], d
        word["seg"] = best

    # A segment with no words means the aligner missed it (usually a silent take).
    # Investigate rather than shipping a scene with no captions.
    for s in segs:
        n = sum(1 for w in words if w["seg"] == s["id"])
        flag = "  <-- NO WORDS, investigate" if n == 0 else ""
        print(f"  {s['id']:16} {n:3d} words{flag}")

    with open(os.path.join(out_dir, os.path.basename(out_path)), "w") as f:
        json.dump(words, f, indent=1)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
