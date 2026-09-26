#!/usr/bin/env python3
"""Synthesize each script line individually, verify, and assemble a master."""
import json, os, subprocess, time, shutil
from pathlib import Path

ROOT = Path("/home/dogetinker/projects/tensor-foundry-youtube/wit-2026-09-01")
WORK = ROOT / "audio_lines"
WORK.mkdir(exist_ok=True)

# Each tuple: (filename stem, text)
LINES = [
    ("s01", "Weekly in Tech, September first."),
    ("s02", "OpenAI says ChatGPT Ads reached a one-billion-dollar annualized revenue run rate in under two hundred days."),
    ("s03", "Self-service buying is expanding across India, Europe, the Middle East, and North Africa."),
    ("s04", "OpenAI says ads remain labeled and separate from answers."),
    ("s05", "NVIDIA says its Vera CPU is shipping for agentic AI."),
    ("s06", "AWS received its first Vera server and Vera Rubin GPU."),
    ("s07", "NVIDIA lists eighty-eight custom cores and up to one-point-eight times faster per-core agentic performance."),
    ("s08", "Google says the Gemma family passed one billion downloads, with more than one hundred thousand community variants."),
    ("s09", "It also launched the Awesome Gemma directory for projects and tools."),
    ("s10", "Finally, OpenAI and Hugging Face published further findings from their model-evaluation security incident."),
    ("s11", "OpenAI says it is strengthening containment, monitoring, access controls, and evaluation practices."),
    ("s12", "The pattern: AI is moving into distribution, infrastructure, and operational security."),
]

FISH_VOICE = "9cebbe29ca334dba9252187b0c958412"
FISH_MODEL = "s2.1-pro-free"
BRIDGE = "/home/dogetinker/.hermes/scripts/fish_tts.sh"

def synth(stem, text):
    in_file = WORK / f"{stem}.txt"
    out_file = WORK / f"{stem}.mp3"
    in_file.write_text(text)
    env = os.environ.copy()
    env["FISH_VOICE"] = FISH_VOICE
    env["FISH_MODEL"] = FISH_MODEL
    subprocess.run([BRIDGE, "--in", str(in_file), "--out", str(out_file), "--format", "mp3"],
                   env=env, check=True, capture_output=True, text=True)
    return out_file

def duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def volumedetect(path):
    r = subprocess.run(["ffmpeg","-v","error","-i", str(path), "-af","volumedetect",
                        "-f","null","-"], capture_output=True, text=True)
    out = r.stderr
    mean = None; maxv = None
    for line in out.splitlines():
        if "mean_volume" in line:
            mean = line.split(":",1)[1].strip()
        if "max_volume" in line:
            maxv = line.split(":",1)[1].strip()
    return mean, maxv

start = time.time()
for stem, text in LINES:
    print(f"[{stem}] synthesizing...")
    outfile = synth(stem, text)
    dur = duration(outfile)
    mean, maxv = volumedetect(outfile)
    print(f"  -> {dur:.2f}s  mean_volume={mean}  max_volume={maxv}")
    if dur < 0.5:
        print(f"  !! too short, possible failure")
print(f"done synth in {time.time()-start:.1f}s")
