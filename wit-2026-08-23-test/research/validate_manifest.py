#!/usr/bin/env python3
"""
validate_manifest.py — Tensor Foundry V3 render_manifest gate.

Enforces the Doge-owned `tensor-foundry-v3-shorts` schema (the single source
of truth) as a HARD pre-render gate. Run BEFORE any renderer touches the manifest.

Contract (from SKILL.md):
  - segments[]: {story_id, cut_start, cut_end, assets[], payoff}   ONLY.
  - top-level: word_timing[], motion{cut_cadence, zoom_punch, easing},
    palette, asset_ledger[] (free-text license), script_path, voice_id, wav.
  - AV sync: segment cuts lock to ASR word_timing anchors (+0.3s pad allowed).
  - NO schema-invalid fields (narration_span / visual_span / cut_pad_s /
    cut_interval_s) — those drifted fields caused the historical AV bug.

Exit code 0 = PASS (safe to render). Non-zero = FAIL (block render, fix first).
"""
import json
import sys
import os

# Fields that must NOT appear anywhere — they were the AV-drift bug.
FORBIDDEN_FIELDS = {"narration_span", "visual_span", "cut_pad_s", "cut_interval_s"}
ALLOWED_PAYOFF_TYPES = {"counter", "comparison", "bar", "statcard", "title", "recap", "multiplier"}

# AV sync tolerance: segment cut may lead the first/last ASR word by up to this.
SYNC_PAD_S = 0.3


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def check(manifest_path, root=None):
    ok = True
    with open(manifest_path) as f:
        m = json.load(f)

    # --- forbidden drift fields ---
    for bad in FORBIDDEN_FIELDS:
        if bad in m:
            ok = fail(f"forbidden field at top level: '{bad}' (schema drift -> AV bug)")
        for seg in m.get("segments", []):
            if bad in seg:
                ok = fail(f"forbidden field in segment {seg.get('story_id')}: '{bad}'")

    # --- required top-level keys ---
    for req in ("edition", "script_path", "voice_id", "wav", "segments",
                "word_timing", "motion", "palette", "asset_ledger"):
        if req not in m:
            ok = fail(f"missing required top-level field: '{req}'")

    # --- word_timing must be top-level list ---
    wt = m.get("word_timing")
    if not isinstance(wt, list) or not wt:
        ok = fail("word_timing must be a non-empty list (top-level ASR anchors)")
    else:
        for i, w in enumerate(wt):
            if not all(k in w for k in ("start", "end", "word")):
                ok = fail(f"word_timing[{i}] missing start/end/word")

    # --- segments shape ---
    segs = m.get("segments", [])
    if not segs:
        ok = fail("segments[] is empty")
    last_end = 0.0
    for seg in segs:
        sid = seg.get("story_id", "<no-id>")
        for req in ("story_id", "cut_start", "cut_end", "assets", "payoff"):
            if req not in seg:
                ok = fail(f"segment '{sid}' missing '{req}'")
        if "cut_start" in seg and "cut_end" in seg:
            if not (seg["cut_end"] > seg["cut_start"]):
                ok = fail(f"segment '{sid}': cut_end <= cut_start")
            if seg["cut_start"] < -SYNC_PAD_S:
                ok = fail(f"segment '{sid}': negative cut_start")
            last_end = max(last_end, seg["cut_end"])
        if "payoff" in seg:
            p = seg["payoff"]
            ptype = p.get("type") if isinstance(p, dict) else None
            if ptype not in ALLOWED_PAYOFF_TYPES:
                ok = fail(f"segment '{sid}': payoff.type '{ptype}' not in allowed set")
        # style fork is explicitly allowed (renderer-specific) -> never gate on it

    # --- AV sync: segments must tile the ASR span without remap drift ---
    if isinstance(wt, list) and wt and segs:
        asr_first = wt[0]["start"]
        asr_last = wt[-1]["end"]
        if abs(segs[0]["cut_start"] - asr_first) > SYNC_PAD_S:
            ok = fail(f"first segment cut ({segs[0]['cut_start']}) not locked to ASR start ({asr_first})")
        if abs(segs[-1]["cut_end"] - asr_last) > SYNC_PAD_S:
            ok = fail(f"last segment cut ({segs[-1]['cut_end']}) not locked to ASR end ({asr_last})")
        # continuity: each segment's cut_start == previous cut_end
        for a, b in zip(segs, segs[1:]):
            if abs(a["cut_end"] - b["cut_start"]) > 0.05:
                ok = fail(f"cut gap between '{a['story_id']}' and '{b['story_id']}' "
                          f"({a['cut_end']} -> {b['cut_start']})")

    # --- motion ---
    mot = m.get("motion", {})
    for req in ("cut_cadence", "zoom_punch", "easing"):
        if req not in mot:
            ok = fail(f"motion missing '{req}'")

    # --- asset_ledger free-text license ---
    for row in m.get("asset_ledger", []):
        if "file" not in row or "license" not in row or "source" not in row:
            ok = fail(f"asset_ledger row missing file/license/source: {row}")

    # --- file existence (if root provided) ---
    if root:
        wav = m.get("wav")
        if wav and not os.path.exists(os.path.join(root, wav)):
            ok = fail(f"wav not found on disk: {wav}")
        for seg in segs:
            for a in seg.get("assets", []):
                if not os.path.exists(os.path.join(root, a)):
                    ok = fail(f"asset not found on disk: {a} (segment {seg['story_id']})")

    if ok:
        print(f"[PASS] {manifest_path} — schema clean, AV-sync locked, "
              f"{len(segs)} segments, {len(wt)} ASR words.")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: validate_manifest.py <manifest.json> [project_root]")
        sys.exit(2)
    path = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else None
    passed = check(path, root)
    sys.exit(0 if passed else 1)
