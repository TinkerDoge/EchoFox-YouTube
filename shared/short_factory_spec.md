# Short-Factory Template — Shared Content Contract

**Purpose:** One content contract both TF/WIT surfaces render from. Pre-baked during the
free `stealth/ox-alpha` 1M-token window so the paid period is *execution only*.

**Two surfaces, one spine:**
- **Surface A — YouTube Shorts (9:16):** `v3-modern-dark` grammar. Sora-V3 (editorial) and
  SUMI-V3 (UI/terminal) are deliberate *style forks* of the SAME contract — never merge styles.
- **Surface B — Faceless Doc (16:9):** `ocean-cable` grammar. AI panels + CC0 b-roll + fact cards.

The divergence is the **renderer (skin)**, not the content. A `beat` is the atomic unit both share.

---

## The BEAT (atomic unit)

Every beat carries the same fields regardless of surface:

```
beat = {
  id:           str            # story_id (shorts) or beat label (doc)
  window:       [start, end]   # seconds. SHORTS: locked to ASR word_timing.
                               #   DOC: duration-allocated from script beats.
  assets:       [path]         # visual ref(s); renderer resolves file + ledger rights
  motion:       {zoom, easing} # zoompan (doc) / zoom_punch 1.05-1.1 (shorts)
  text_layers: {
    headline:   str            # kinetic title (shorts) / chapter title (doc)
    caption:    windowed_ASR   # SHORTS ONLY: slice of word_timing[] in window
    factcard:   str            # on-screen verified claim (both surfaces)
  }
  payoff:       {type, ...}    # counter|bar|comparison|statcard|recap|title|null
  rights:       ledger_ref     # matches asset_ledger[].file -> {license, source}
}
```

### Mapping to existing artifacts
| Beat field | v3-shorts render_manifest | ocean-cable build-ep01.sh |
|---|---|---|
| `window` | `segment.cut_start/cut_end` (ASR-locked) | `seg` duration column |
| `assets` | `segment.assets[0]` | `img` column |
| `motion` | `motion.zoom_punch` + `easing` | `zp` zoompan rate |
| `text_layers.headline` | kinetic typography (seam band) | `title` drawtext |
| `text_layers.caption` | windowed `word_timing[]` | (doc: none — VO only) |
| `text_layers.factcard` | payoff HUD / statcard | `card` drawtext |
| `rights` | `asset_ledger[]` | inline (TODO: promote to ledger) |

---

## Cross-project manifest (beat_manifest.json)

Top-level shape consumed by BOTH renderers:

```json
{
  "project":     "string",
  "surface":     "shorts-9x16 | doc-16x9",
  "grammar":     "v3-modern-dark | ocean-cable",
  "script_path": "audio/narration_script.txt",
  "wav":         "audio/narration_master.wav",
  "duration":    0.0,
  "beats":       [ <beat>, ... ],
  "word_timing": [ {start,end,word}, ... ],   // SHORTS: ASR anchor. DOC: optional
  "palette":     {"base":"#0a0a0f","accents":["violet","copper"],"grammar":"..."},
  "motion":      {"cut_cadence":[1.5,2.5],"zoom":[1.05,1.1],"easing":"ease_out_expo"},
  "asset_ledger":[ {"file","license","source"}, ... ],
  "flux_transitions": [],
  "synthetic_label": "string | null"          // DOC: YouTube 2026 AI-disclosure
}
```

**Invariant:** `v3-modern-dark` shorts manifest (render_manifest_v7.json) is a *specialization*
of this — its `segments[]` == `beats[]` with `style:null` per segment to preserve the fork.
The validator in `research/validate_manifest.py` remains the gate for the shorts specialization.

---

## Why this is the "make it worth" artifact
During the free window we:
1. Locked the **drift-free** shorts contract (V7 + validator) — done.
2. Defined the **shared beat contract** so new episodes (WIT ep03+, doc ep02+) are fill-in-the-blanks.
3. Both renderers (Sora-V3 / SUMI-V3 / doc) validate against ONE schema in the paid period.

Result: paid period = research article → populate `beats[]` → one command per surface → ship.
No re-deriving cuts, no schema drift, no per-project hardcoded paths.
