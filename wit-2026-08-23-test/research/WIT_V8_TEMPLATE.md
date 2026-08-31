# Weekly In Tech v8 — Source-First Editorial Template

## Decision

**Replace the retro-comic poster system with a mobile-first editorial sequence.**

The prior v6 look used dense multi-panel composition, outlined display faces, starbursts, oversized logo plates, and repeated fact pills. Frame inspection found that those decorations received more attention than the editorial takeaway, while sources and benchmark context were comparatively tiny.

v8 is intentionally quieter and more informative:

1. **One story per timed segment** — never a poster grid.
2. **One complete headline** — no decorative truncation or ellipses.
3. **One “why it matters” sentence** — the editorial interpretation.
4. **One evidence module** — a single metric or readable comparison, not a duplicate claim stack.
5. **A visible credibility line** — source, date, and claim/review status stay on-frame.
6. **A dedicated caption lane** — y=1150–1280; story content ends before it.
7. **One takeaway card** — summarizes the signal; it does not become a branding splash screen.

This follows accessible visualization guidance: make comparisons easy, provide the relevant context, prioritize accuracy and simplicity, use readable familiar charts, and label what the data represents.[1]

## Design contract

- **Canvas:** 720×1280, 30fps (source), H.264/yuv420p, AAC 48kHz.
- **Content safe zone:** x=52–668; story content ends at y≈1117.
- **Caption lane:** y≥1150. Captions are built separately from approved script text; ASR supplies timings only.
- **Type:** Archivo only in the current reference renderer. This prevents display-font decoration from undermining mobile scanability.
- **Colour:** warm paper, charcoal ink, a single per-story accent. Accent colour is never the sole data encoding.
- **Motion:** segment cuts are locked to `word_timing[]`; individual content elements reveal in the segment, with no timeline-ratio remapping.
- **Progress:** uses actual story index (01/05–05/05); outro is intentionally unnumbered.

## Editorial source gate — before a public render

The included August test edition remains a **template preview**. Its claims and story sources must be re-researched for a fresh episode. Never carry them forward as current news.

For every story, complete this before render lock:

- `headline`: a concise, complete claim.
- `why_it_matters`: one audience-facing implication.
- `payoff`: one metric, status, or comparison that materially supports the story.
- `source`: publisher or primary organization.
- `date`: original publication/update date.
- `url`: direct primary release, benchmark, documentation, or filing—not a search result.
- `claim_status`: `primary-claim`, `third-party-benchmark`, `independently-reproduced`, or `unverified`.
- `methodology_note`: required for benchmarks/comparisons; specify benchmark version and conditions.
- asset ledger row: asset file, owner, license, source URL, attribution text, and usage note.

### Render policy

- A vendor metric must say **“company-reported”** if not independently reproduced.
- An external listing or rumor must be labeled **“unverified”** and cannot be the lead claim until a primary source exists.
- A chart must show its unit in the title (for example, `DeepSWE Pass@1 (%)`) and use like-for-like values only.
- Keep full URL/methodology/asset details in the description and edition ledger; the on-frame source line stays short and legible.
- Do not imply a brand relationship with a logo. Logos are editorial identification only.

## Files

- `research/render_manifest_v8.json` — validated ASR-locked v3 manifest.
- `visual/render_v8_editorial.py` — clean visual master renderer.
- `build_captions_v8.py` — script-text captions with ASR timing.
- `weekly_in_tech_v8_editorial_captioned_preview.mp4` — current rendered reference preview; **not a publish candidate**.
- `qa/v8/` — representative full-resolution QA frames and montage.

## Rebuild

```bash
cd ~/projects/tensor-foundry-youtube/wit-2026-08-23-test
python3 research/validate_manifest.py research/render_manifest_v8.json .
.venv/bin/python visual/render_v8_editorial.py
.venv/bin/python build_captions_v8.py

ffmpeg -y -v error -i visual/visual_master_v8.mp4 \
  -i audio/narration_v6_master.wav -i audio/weekly_in_tech_editorial_bed_v1.wav \
  -filter_complex "[1:a]aresample=48000[narr];[2:a]aloop=loop=-1:size=2e+09,volume=0.045,atrim=0:55.18[bed];[narr][bed]amix=inputs=2:duration=first:normalize=0,aresample=48000[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  weekly_in_tech_v8_editorial_preview.mp4

ffmpeg -y -v error -i weekly_in_tech_v8_editorial_preview.mp4 \
  -vf "subtitles=captions/captions_v8.ass:fontsdir=assets/fonts" \
  -c:v libx264 -preset medium -crf 19 -c:a copy -movflags +faststart \
  weekly_in_tech_v8_editorial_captioned_preview.mp4
```

## Verified template QA (2026-08-31)

- Manifest gate: **PASS** — 7 tiled ASR-locked segments, 155 timing words.
- Caption builder: **PASS** — 164 approved script words conserved into 44 caption events.
- Encoded preview: **PASS** — H.264 720×1280/30fps; AAC 48kHz; 55.174s; full FFmpeg decode clean.
- Full-frame visual samples: intro/story 01/story 02/story 03/story 04/story 05/recap inspected. Story 03 (Gemini) is present at 28s; apparent repeated `02/05` montage states are the intentional chart reveal, not duplicate stories.
- Caption-band pixel samples: mixed dark/light pixel populations at y=1150–1260 across all six QA frames; captions are rendered in the reserved lane, not over source/evidence content.

## Sources

[1] Material Design, *Top Tips for Data Accessibility* — https://m3.material.io/blog/data-visualization-accessibility
