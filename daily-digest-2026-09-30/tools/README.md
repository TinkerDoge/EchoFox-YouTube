# Daily Digest — build tooling

Reusable pipeline for the 9:16 solo-anchor news short. **Read `daily-digest-pipeline`
(skill) for the rules; this is just the map.**

## Run an episode

```bash
# 1. author the content contract (only thing you write per episode)
mkdir -p ~/hf-codedoctor/daily-digest-$(date +%F)
$EDITOR ~/hf-codedoctor/daily-digest-$(date +%F)/script.json

# 2. build, measure, render
python3 ~/hf-codedoctor/tools/daily_digest.py \
  --date $(date +%F) \
  --script ~/hf-codedoctor/daily-digest-$(date +%F)/script.json
```

Output: `~/hf-codedoctor/daily-digest-<date>/daily-digest-<date>-single.mp4`

## Files

| file | role |
|---|---|
| `daily_digest.py` | the pipeline. 7 stages, resumable, hard-fails on known defects |
| `build_html.py` | composition builder. Layout constants at the top; `VISUALS` per scene |
| `align_words.py` | faster-whisper word alignment (unmodified from the skill) |

## Stage resume

```bash
--dry-run            # plan only, no writes
--from align         # skip TTS if narration is already good
--to compose         # stop before the expensive render
--force              # re-synthesise narration
--bed-volume 0.62    # bed multiplier (linear, not dB)
--voice <id>         # override the 28/9 keeper narrator
```

## Per-episode directory

```
daily-digest-<date>/
  script.json            <- the contract you author
  voice-timing.json      <- derived
  segs.json              <- derived (aligner input)
  words.json             <- derived (karaoke timings; NEVER reuse across a narration change)
  narration_stem.wav     <- derived (aligner input)
  bed.wav
  narration/*.mp3        <- raw + polished stems
  composition/           <- index.html + assets
  _superseded/           <- one-off scripts from the 2026-09-30 build, kept for reference
```

## What the pipeline refuses to ship

- true peak above -1.0 dBFS (the loudnorm-stacking clip)
- any clip more than 0.5 LU off -16.0 LUFS
- a composition referencing a missing hero image
- a scene with no `VISUALS` entry
- a segment the aligner returned zero words for
- a dead-air gap over 0.4s

`verify` reports these as measurements rather than assertions — read the numbers, and
remember `hyperframes check` does not audit audio or caption timing at all.
