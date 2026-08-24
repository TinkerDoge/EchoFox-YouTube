# Edition Checkpoint — wit-2026-08-24 v6 (retro comic)

## Status
**QA-passed review candidate → published (public)** — see `publish/youtube_upload_receipt.json`.

## Final artifact
- `weekly_in_tech_v6.mp4` — 55.17s, 720×1280@30, H.264 yuv420p +faststart, AAC 48k stereo
- SHA-256: `142dd5b37b8757d93a7f422cc21fd27bdd7cf538bc57d99971f847788cbb24f8`
- Full decode clean (`ffmpeg -f null -` exit 0)

## What defines v6
1. **Retro comic / pop print restyle**: cream newsprint base (#f4e9d3) with halftone Ben-Day dots,
   thick ink outlines, hard offset shadows, pop palette (red/yellow/cyan/blue), Bangers +
   Luckiest Guy display type, starburst infographic callouts, whip-panel transitions.
2. **Natural narration**: no spoken interjections; emotion carried by Fish inline tags only
   ([delighted] [amused] [impressed] [curious] [pleased]). Voice = Megan, Fish s2.1-pro-free.
   Raw 58.5s → silence-trimmed master 55.17s.
3. **Captions from script text**: ASR supplies timing only. difflib alignment maps script words
   to ASR word spans; ASR spellings ("Quinn", "60", "name atron") never reach captions.
4. **Headline style**: yellow/cream text w/ thick ink stroke — always readable over any panel.
5. **Rank badge fix**: paper ring behind badge + numeral drawn at badge-center
   (draw_center() centers on canvas width — never use it for badge-local text).
6. Caption lane: solid cream box ASS BorderStyle=3 (PrimaryColour=text ink,
   OutlineColour=box cream #F4E9D3), pos(360,1176), MarginV irrelevant when \pos used.
   Chips end by y≈1141; caption top ≈1147.

## Key files
- Renderer: `visual/render_v5.py` (reads `research/render_manifest_v5.json`)
- Captions: `build_captions_v6.py` → `captions/captions_v6.ass`
- Script: `audio/narration_script_v5.txt`; voice master `audio/narration_v6_master.wav`
- Word timing: `captions/words_v6.json`
- Metadata: `publish/youtube_metadata_v6.json`
- Source ledger: `research/source_ledger.md`

## Pipeline gotchas learned (v5→v6)
- ASS BorderStyle=3: OutlineColour IS the box fill; setting Primary=Outline=ink renders black-on-black.
- silenceremove filter can't reach sub-0.35s gaps reliably; use silencedetect + atrim/concat piecewise trim.
- faster-whisper writes np.float64 in word dicts — round before json.dump.
- .venv moved between dirs breaks shebangs in bin/pip* — sed the pyvenv path back.
- Music bed is 59.7s mono-source looped via `aloop` for >59s editions; fixed-level −27dB, fades only.

## Rejected/superseded
- v5 (73s→69.6s cut): rigged-sounding narration, black-on-black captions, ASR-spelling captions.
  Kept as `weekly_in_tech_v5.mp4` for diffing; do not publish.
