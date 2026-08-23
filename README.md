# The Tensor Foundry — YouTube Works

Project space for The Tensor Foundry (tech & AI channel) video production.
Created 2026-08-23 at SUMI's request; visible to Doge via Buzz.

## Editions
- `wit-2026-08-23-test/` — WIT test edition (5-story August model wave, 66s, Megan/Fish Audio).
  Status: review candidate awaiting Doge approval. Final: `weekly_in_tech_tensor_foundry_FINAL.mp4`
  SHA-256: 0ea76673a0c5f1076fe643c9b7511fdbb9a11958a9e061eeba2be16dc8ba716f

## Pipeline (reusable template)
1. Research & lock 5 stories → `research/stories.json` (each story carries a payoff type: counter/comparison/bar/statcard)
2. Narration script → Fish Audio Megan (`fb43143e46f44cc6ad7d06230215bab6`) → clean → master
3. Scene cuts from faster-whisper anchors (`derive_scene_times.py`, use ep02 venv for faster_whisper/numpy)
4. Visual master via data-driven Pillow renderer (`visual/render_visual_master.py`)
5. Captions from word timing → ASS, MarginV≈110 + pos(360,1170) on every line
6. Mix + QA via weekly-in-tech-production kit scripts
