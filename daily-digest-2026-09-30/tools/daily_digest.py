#!/usr/bin/env python3
"""Daily Digest — end-to-end vertical news short pipeline.

One command, date-parameterized. Takes a content contract (script.json), produces a
rendered, measured MP4. Every stage encodes a failure that actually cost a rebuild.

    ./daily_digest.py --date 2026-10-01 --script script.json
    ./daily_digest.py --date 2026-10-01 --script script.json --from align   # resume
    ./daily_digest.py --date 2026-10-01 --script script.json --dry-run      # plan only

STAGES
  tts      synth narration, then TWO-PASS loudness, then measured static gain
  timing   re-probe durations, lay the timeline, write voice-timing.json + segs.json
  stem     build narration_stem.wav at composition offsets (for the aligner)
  align    faster-whisper word timings -> words.json
  compose  write composition/index.html (two-line lower-third karaoke captions)
  render   hyperframes check + render
  verify   measure the finished MP4: loudness, peak, cut density, dead air, bed level

HARD-WON RULES ENCODED HERE (do not "simplify" these away):

1. Fish `prosody` is a STRUCT. Sending the string "natural" returns HTTP 400, which
   looks like a provider failure but says nothing about balance. Omit the field.
2. Loudnorm and the static gain MUST be separate ffmpeg passes. Chaining
   `loudnorm=...,volume=NdB` stacks the corrections and clips true peak to +8 dBFS
   while polish_loudness.py still reports PASS.
3. Always read the printed true peak. Plausible LUFS + peak above -1 dBFS is broken.
4. `data-volume` on the bed is a LINEAR multiplier, not a dB trim. A -20 LUFS bed at
   0.11 renders at -39.8 LUFS and is inaudible while the bed-only render looks fine.
   Target ~-34 dBFS measured in the finished mix.
5. The bed must cover the full runtime, or the tail is silence.
6. The caption plate MUST declare its own height. Its .cap children are
   position:absolute so GSAP can fade them, so they contribute no height and the
   plate collapses to bare padding.
7. Karaoke highlight is scoped to the .cur line, so the dimmed preview line can never
   light a stale word during handover.
8. Never reuse words.json across a narration change: a corrected line shifts every
   later segment's start. stem -> align -> compose is one atomic chain.
9. The cold open carries a claim and a number. No greeting card, no date card.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import urllib.request

# ---------------------------------------------------------------- config

FISH_URL = "https://api.fish.audio/v1/tts"
CREDIT_URL = "https://api.fish.audio/wallet/self/api-credit"

# Single-narrator voice used by the 2026-09-28 keeper (digest-0928 v3) and every
# Daily Digest since. Override with --voice.
DEFAULT_VOICE = "933563129e564b19a115bedd57b7406a"
DEFAULT_MODEL = "s2.1-pro-free"

BGM_LIB = os.path.expanduser("~/sora/tools/bgm")
BED_SOURCE = "Cymatic.mp3"
BED_SS = 70          # every library track opens sparse; this offset has real level
HYPERFRAMES = "npx --yes hyperframes@0.8.95"
ALIGN_VENV = os.path.expanduser("~/.cache/daily-digest-wv")
ALIGN_PY = os.path.join(ALIGN_VENV, "bin", "python")

TARGET_LUFS = -16.0
MAX_PEAK_DBFS = -1.0     # above this is clipping, regardless of the LUFS reading
TAIL_BED_DBFS = -34.0    # narration-free tail target for audibility

STAGES = ["tts", "timing", "stem", "align", "compose", "render", "verify"]


def log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def head(msg: str) -> None:
    print(f"\n\033[1m== {msg}\033[0m", flush=True)


class Fail(RuntimeError):
    pass


# ---------------------------------------------------------------- helpers

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise Fail(f"{' '.join(cmd[:4])}... failed:\n{r.stderr[-1500:]}")
    return r


def api_key(name="FISH_API_KEY") -> str:
    for line in open(os.path.expanduser("~/.hermes/.env")):
        if line.startswith(name + "="):
            return line.strip().split("=", 1)[1]
    raise Fail(f"{name} not found in ~/.hermes/.env")


def probe_dur(path: str) -> float:
    r = need(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def measure_lufs(path: str) -> tuple[float, float]:
    """Integrated loudness and true peak, from ebur128's final summary block."""
    r = need(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
              "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rfind("Integrated loudness:"):]
    i = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", tail)
    p = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", tail)
    if not i:
        raise Fail(f"could not measure loudness of {path}")
    return float(i[-1]), float(p[-1]) if p else float("nan")


def measure_tail_rms(path: str, start: float, dur: float = 1.2) -> float:
    """RMS dBFS of a window — used on the narration-free outro tail."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", path,
         "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True).stdout
    n = len(raw) // 2
    if n == 0:
        raise Fail(f"no audio in tail window of {path}")
    v = struct.unpack("<%dh" % n, raw[:n * 2])
    return 20 * math.log10(math.sqrt(sum(x * x for x in v) / n) / 32768)


# ---------------------------------------------------------------- stages

def stage_tts(ep, script, voice, model, force=False):
    narr = os.path.join(ep, "narration")
    os.makedirs(narr, exist_ok=True)
    key = api_key()
    targets = [s["id"] for s in script["segments"]]

    if not force:
        missing = [i for i in targets if not os.path.exists(os.path.join(narr, f"{i}.mp3"))]
        if not missing:
            log(f"all {len(targets)} stems present, skipping TTS (--force to redo)")
            return

    for i, seg in enumerate(script["segments"]):
        sid = seg["id"]
        raw = os.path.join(narr, f"{sid}_raw.mp3")
        out = os.path.join(narr, f"{sid}.mp3")
        if os.path.exists(out) and not force:
            log(f"[{i+1}/{len(targets)}] {sid}: cached")
            continue
        log(f"[{i+1}/{len(targets)}] TTS {sid} ...")
        # NOTE: no `prosody` key. It is a struct now; the string form is a 400.
        payload = {"text": seg["text"], "reference_id": voice,
                   "format": "mp3", "model": model}
        req = urllib.request.Request(
            FISH_URL, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            raise Fail(f"TTS HTTP {e.code} on {sid}: {detail}")
        if body[:1] == b"{":
            raise Fail(f"TTS returned JSON not audio for {sid}: {body[:300]!r}")
        open(raw, "wb").write(body)

    # ---- loudness: PASS 1 two-pass loudnorm (its own file) ------------------
    log("loudnorm pass (two-pass, measured) ...")
    for seg in script["segments"]:
        sid = seg["id"]
        raw = os.path.join(narr, f"{sid}_raw.mp3")
        out = os.path.join(narr, f"{sid}.mp3")
        p1 = need(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                   f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json",
                   "-f", "null", "-"]).stderr
        m = json.loads(p1[p1.rfind("{"):p1.rfind("}") + 1])
        need(["ffmpeg", "-y", "-hide_banner", "-i", raw, "-af",
              f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:"
              f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
              f"linear=true", "-ar", "48000", "-ac", "2", out])

    # ---- loudness: PASS 2 measured static gain (SEPARATE invocation) -------
    # Never fold this into the loudnorm chain: stacking them clipped to +8 dBFS.
    log("static gain pass (exact measured offset) ...")
    worst, worst_peak = 0.0, -99.0
    for seg in script["segments"]:
        f = os.path.join(narr, f"{seg['id']}.mp3")
        cur, _ = measure_lufs(f)
        gain = TARGET_LUFS - cur
        if abs(gain) >= 0.1:
            tmp = f + ".gain.mp3"
            need(["ffmpeg", "-y", "-i", f, "-af", f"volume={gain:.2f}dB",
                  "-ar", "48000", "-ac", "2", tmp])
            os.replace(tmp, f)
        now, peak = measure_lufs(f)
        worst = max(worst, abs(now - TARGET_LUFS))
        worst_peak = max(worst_peak, peak)
        flag = "" if peak <= MAX_PEAK_DBFS else "  <-- CLIPPING"
        log(f"    {seg['id']:16} -> {now:6.2f} LUFS  peak {peak:6.2f} dBFS{flag}")

    if worst > 0.5:
        raise Fail(f"loudness off target by {worst:.2f} LU (max 0.5)")
    if worst_peak > MAX_PEAK_DBFS:
        raise Fail(f"true peak {worst_peak:.2f} dBFS exceeds {MAX_PEAK_DBFS} — "
                   f"clipping; do NOT compensate with a volume cut, re-run --force")


def stage_timing(ep, script):
    narr = os.path.join(ep, "narration")
    timeline, scenes, total = [], [], 0.0
    for i, seg in enumerate(script["segments"]):
        d = probe_dur(os.path.join(narr, f"{seg['id']}.mp3"))
        timeline.append({
            "id": seg["id"], "speaker": script.get("anchor", "sora"),
            "start": round(total, 3), "duration": round(d, 3),
            "end": round(total + d, 3),
            # alternate tracks so micro-overlaps don't trip duplicate_audio_track
            "track": 2 if i % 2 == 0 else 3,
            "text": seg["text"], "audio_file": f"assets/audio/{seg['id']}.mp3",
            "kicker": seg["kicker"], "headline": seg["headline"],
            "subhead": seg["subhead"], "detail": seg["detail"],
            "source": seg["source"], "visual": seg.get("visual", ""),
            "scene": seg["scene"],
        })
        scenes.append({
            "id": seg["scene"], "start": round(total, 3), "end": round(total + d, 3),
            "duration": round(d, 3), "kicker": seg["kicker"],
            "headline": seg["headline"], "subhead": seg["subhead"],
            "detail": seg["detail"], "source": seg["source"],
            "visual": seg.get("visual", ""),
        })
        total += d
    total = round(total + 1.5, 3)

    json.dump({"total_duration": total, "timeline": timeline, "scenes": scenes},
              open(os.path.join(ep, "voice-timing.json"), "w"), indent=2)
    json.dump({"total": total,
               "segments": [{"id": t["id"], "start": t["start"], "dur": t["duration"]}
                            for t in timeline]},
              open(os.path.join(ep, "segs.json"), "w"), indent=2)
    log(f"total {total}s / {len(timeline)} clips")
    return total


def stage_stem(ep, segs_path):
    """Lay every clip at its composition offset onto a silent bed.

    The aligner must hear the arrangement the viewer hears, or every word
    timestamp is offset from the voice.
    """
    M = json.load(open(segs_path))
    segs = M["segments"]
    args = ["ffmpeg", "-y", "-f", "lavfi", "-i",
            f"anullsrc=r=48000:cl=stereo:d={M['total']}"]
    for s in segs:
        args += ["-itsoffset", str(s["start"]), "-i",
                 os.path.join(ep, "narration", f"{s['id']}.mp3")]
    fc = "".join(f"[{i+1}:a]adelay={int(s['start']*1000)}|{int(s['start']*1000)}[a{i+1}];"
                 for i, s in enumerate(segs))
    mix = "".join(f"[a{i+1}]" for i in range(len(segs)))
    fc += f"{mix}amix=inputs={len(segs)}:normalize=0[out]"
    args += ["-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2",
             os.path.join(ep, "narration_stem.wav")]
    need(args)
    log(f"stem {probe_dur(os.path.join(ep, 'narration_stem.wav')):.2f}s")


def ensure_aligner():
    """faster-whisper 1.2.x needs PyAV 13.x; 14+ dropped the metadata_errors kwarg."""
    if os.path.exists(ALIGN_PY):
        return ALIGN_PY
    if not shutil.which("uv"):
        raise Fail("uv not found; install it or align words by hand")
    log("building aligner venv (first run only) ...")
    subprocess.run(["uv", "venv", ALIGN_VENV, "--python", "3.12"], check=True,
                   capture_output=True)
    # pin av==13.1.0: av 19 raises TypeError on metadata_errors
    subprocess.run(["uv", "pip", "install", "--python", ALIGN_PY,
                    "faster-whisper", "av==13.1.0"], check=True, capture_output=True)
    return ALIGN_PY


def stage_align(ep, segs_path):
    py = ensure_aligner()
    aligner = os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_words.py")
    need([py, aligner, segs_path, os.path.join(ep, "narration_stem.wav"),
          os.path.join(ep, "words.json")])
    W = json.load(open(os.path.join(ep, "words.json")))
    segs = json.load(open(segs_path))["segments"]
    empty = [s["id"] for s in segs
             if not any(w["seg"] == s["id"] for w in W)]
    if empty:
        raise Fail(f"aligner returned no words for {empty} — silent take or bad stem")
    log(f"{len(W)} words across {len(segs)} segments, none empty")


def build_bed(ep, runtime, out_name="bed.wav"):
    """Compress the library track into a steady band, then size it to the runtime.

    Compressor is not cosmetic: every library track has a sparse intro at every
    offset, and a raw bed measures a plausible integrated LUFS while being
    near-silent under the voice for its first 20s.
    """
    src = os.path.join(BGM_LIB, BED_SOURCE)
    if not os.path.exists(src):
        raise Fail(f"bed source missing: {src}")
    dur = runtime + 1.0
    out = os.path.join(ep, out_name)
    need(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(BED_SS),
          "-i", src, "-t", str(dur), "-af",
          "acompressor=threshold=-28dB:ratio=3:attack=15:release=350:makeup=2dB,"
          "volume=6.5dB,alimiter=limit=-3dB:level=disabled,"
          f"afade=t=out:st={dur-3:.1f}:d=3", "-ar", "48000", "-ac", "2", out])
    i, p = measure_lufs(out)
    log(f"bed {probe_dur(out):.1f}s @ {i:.1f} LUFS, peak {p:.1f} dBFS")
    return out


def stage_compose(ep, script, bed_volume=0.62):
    from build_html import build          # sibling module, kept separate for editing
    total = build(ep, script, bed_volume=bed_volume)
    log(f"composition written, {total:.2f}s")
    return total


def stage_render(ep, out_name):
    comp = os.path.join(ep, "composition")
    r = subprocess.run(f"{HYPERFRAMES} check", shell=True, cwd=comp,
                       capture_output=True, text=True)
    tail = r.stdout + r.stderr
    if "Check failed" in tail:
        raise Fail("hyperframes check FAILED:\n" + tail[-2000:])
    for ln in tail.splitlines():
        if "text checks" in ln or "error(s)" in ln:
            log(ln.strip())
    log("check passed")
    need(f"{HYPERFRAMES} render --output ../{out_name}", shell=True, cwd=comp)
    mp4 = os.path.join(ep, out_name)
    log(f"rendered {out_name} ({os.path.getsize(mp4)/1e6:.1f} MB)")


def stage_verify(ep, out_name, segs_path):
    mp4 = os.path.join(ep, out_name)
    data = json.load(open(os.path.join(ep, "voice-timing.json")))
    segs = json.load(open(segs_path))["segments"]
    total = data["total_duration"]

    i, peak = measure_lufs(mp4)
    ok = "OK" if abs(i - TARGET_LUFS) < 1.5 else "OFF"
    log(f"loudness {i:.2f} LUFS ({ok})   true peak {peak:.2f} dBFS")
    if peak > -0.5:
        log("  WARNING: peak above -0.5 dBFS, possible clipping")

    # Cut density. gt(scene,0.3) reports ZERO for opacity/crossfade compositions,
    # so sweep and report which threshold produced the number.
    for th in (0.3, 0.02, 0.005):
        n = sh(["ffmpeg", "-i", mp4, "-vf", f"select='gt(scene,{th})',showinfo",
                "-f", "null", "-"]).stderr.count("pts_time")
        log(f"visual states @ th={th}: {n}  (one per {total/max(n,1):.2f}s)")

    sil = sh(["ffmpeg", "-i", mp4, "-af", "silencedetect=noise=-45dB:d=0.4",
              "-f", "null", "-"]).stderr.count("silence_start")
    log(f"dead-air gaps >0.4s: {sil}" + ("  OK" if sil == 0 else "  CHECK"))

    # Bed audibility: the outro tail is narration-free, so it holds bed only.
    end = max(s["start"] + s["dur"] for s in segs)
    if total - end > 0.6:
        rms = measure_tail_rms(mp4, end + 0.1)
        verdict = "OK" if TAIL_BED_DBFS - 6 <= rms <= TAIL_BED_DBFS + 6 else "TOO QUIET/LOUD"
        log(f"bed level in outro tail: {rms:.1f} dBFS (target {TAIL_BED_DBFS}) {verdict}")
        if rms < TAIL_BED_DBFS - 6:
            log("  -> raise bed data-volume in the composition and re-render")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="episode date, YYYY-MM-DD")
    ap.add_argument("--script", required=True, help="path to script.json")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--workdir", default=None,
                    help="default ~/hf-codedoctor/daily-digest-<date>")
    ap.add_argument("--from", dest="start", default="tts", choices=STAGES)
    ap.add_argument("--to", dest="end", default="verify", choices=STAGES)
    ap.add_argument("--force", action="store_true", help="re-synthesise narration")
    ap.add_argument("--bed-volume", type=float, default=0.62,
                    help="bed data-volume multiplier (linear, not dB)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ep = args.workdir or os.path.expanduser(f"~/hf-codedoctor/daily-digest-{args.date}")
    script = json.load(open(args.script))
    script.setdefault("anchor", "sora")
    out_name = f"daily-digest-{args.date}-single.mp4"

    lo, hi = STAGES.index(args.start), STAGES.index(args.end)
    plan = STAGES[lo:hi + 1]

    head(f"Daily Digest {args.date}")
    log(f"workdir {ep}")
    log(f"script  {len(script['segments'])} segments")
    log(f"voice   {args.voice}")
    log(f"stages  {' -> '.join(plan)}")
    if args.dry_run:
        return 0

    os.makedirs(ep, exist_ok=True)
    segs_path = os.path.join(ep, "segs.json")

    for st in plan:
        head(st)
        if st == "tts":
            stage_tts(ep, script, args.voice, args.model, force=args.force)
        elif st == "timing":
            stage_timing(ep, script)
        elif st == "stem":
            stage_stem(ep, segs_path)
        elif st == "align":
            stage_align(ep, segs_path)
        elif st == "compose":
            # bed must cover the whole runtime, or the tail is silence
            total = json.load(open(os.path.join(ep, "voice-timing.json")))["total_duration"]
            build_bed(ep, total)
            comp = os.path.join(ep, "composition")
            for sub in ("assets/audio", "assets/music", "assets/fonts", "assets/img"):
                os.makedirs(os.path.join(comp, sub), exist_ok=True)

            # Seed fonts, gsap and hero images from the last good episode.
            # `hyperframes check` treats a missing <img> as an ERROR ("the
            # renderer will silently skip these"), so a scene that loses its
            # photo would ship a blank plate.
            seed = os.path.expanduser(
                "~/projects/tensor-foundry-youtube/daily-digest-2026-09-30/composition")
            for f in ("assets/gsap.min.js",
                      "assets/fonts/bold.ttf", "assets/fonts/regular.ttf",
                      "assets/img/openai-dots.jpg", "assets/img/whitehouse.jpg"):
                src, dst = os.path.join(seed, f), os.path.join(comp, f)
                if os.path.exists(src):
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        log(f"seeded {f}")
                else:
                    log(f"WARN seed missing {f} — supply it in this episode's assets/")

            for seg in script["segments"]:
                shutil.copy2(os.path.join(ep, "narration", f"{seg['id']}.mp3"),
                             os.path.join(comp, "assets/audio", f"{seg['id']}.mp3"))
            shutil.copy2(os.path.join(ep, "bed.wav"),
                         os.path.join(comp, "assets/music/bgm.mp3"))

            stage_compose(ep, script, bed_volume=args.bed_volume)

            # Fail before rendering if a referenced image is still absent.
            html_path = os.path.join(comp, "index.html")
            missing = [m for m in re.findall(r'src="(assets/img/[^"]+)"',
                                             open(html_path).read())
                       if not os.path.exists(os.path.join(comp, m))]
            if missing:
                raise Fail(f"composition references missing images {missing} — "
                           f"add them to assets/img/ or drop the <img> from VISUALS")
        elif st == "render":
            stage_render(ep, out_name)
        elif st == "verify":
            stage_verify(ep, out_name, segs_path)

    head("done")
    log(os.path.join(ep, out_name))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as e:
        print(f"\n\033[31mPIPELINE FAILED: {e}\033[0m", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
