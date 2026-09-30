#!/usr/bin/env python3
"""Composition builder for the Daily Digest — flat pop-retro, two-line lower third.

Split from daily_digest.py so the layout can be edited without touching pipeline
logic. Reads voice-timing.json + words.json, writes composition/index.html.

Vertical budget (720x1280) — every band is accounted for, nothing floats:

    40   top header
    104  kicker
    134  headline            (40px, up to 2 lines)
    230  subhead             (21px cyan)
    286  visual container    -> 846  (560px)
    866  detail              (24px)
    944  source              (14px, uppercase)
    1040 caption plate       -> 1192 (152px, TWO lines, bottom:88)
    1274 progress bar

The earlier single-line plate left ~86px of empty plate and 242px (19% of the
frame) of dead space below it. The two-line form fills both.
"""
import html
import json
import os

# ---- layout constants -----------------------------------------------------
CANVAS_W, CANVAS_H = 720, 1280
MARGIN = 44

HEADLINE_PX = 40          # Gate 7: <=6 words at 40px
SUBHEAD_PX = 21
DETAIL_PX = 24
SOURCE_PX = 14
KICKER_PX = 17

VISUAL_TOP = 286
VISUAL_H = 560            # was 496 before the caption rework
DETAIL_TOP = 866
SOURCE_TOP = 944

PLATE_BOTTOM = 88
PLATE_H = 152             # MUST be explicit: .cap children are position:absolute
PLATE_PAD = 24
CAP_CUR_PX = 34           # line being spoken
CAP_NXT_PX = 27           # upcoming line, dimmed
CAP_BUDGET = 34           # max chars per caption line

# ---- palette --------------------------------------------------------------
BG = "#101820"
PLATE = "#F6F3EB"
INK = "#F6F3EB"
AMBER = "#FFD080"
CYAN = "#76E4EA"
CORAL = "#FF6B6B"
CRIMSON = "#A61E4D"
TEAL = "#087F5B"
SLATE = "#202D3A"
BORDER = "#3E4F5D"
BORDER_HI = "#4A5F70"
MUTED = "#9AAAB5"
HILITE = "#C8102E"        # karaoke word highlight

esc = html.escape

# Per-scene visual bodies, keyed by scene id. Gate 7: one focal idea per frame.
VISUALS = {
    1: f"""
      <div class="big-stat">
        <div class="big-stat-v">$518B</div>
        <div class="big-stat-k">MINIMUM &middot; OVER TEN YEARS</div>
        <div class="big-stat-s">AI infrastructure, six partners</div>
      </div>
      <div class="metric-row">
        <div class="metric"><div class="metric-k">NON-CANCELLABLE</div><div class="metric-v alt">80%</div></div>
        <div class="metric"><div class="metric-k">PARTNERS</div><div class="metric-v">6</div></div>
      </div>
    """,
    2: """
      <div class="deal">
        <div class="deal-row"><span class="deal-name">GOOGLE</span><span class="deal-v">$111.1B</span></div>
        <div class="deal-bar"><div class="deal-fill" style="width:100%"></div></div>
        <div class="deal-row"><span class="deal-name">AMAZON</span><span class="deal-v">$110B</span></div>
        <div class="deal-bar"><div class="deal-fill" style="width:99%"></div></div>
        <div class="deal-row"><span class="deal-name">MICROSOFT</span><span class="deal-v">$31.4B</span></div>
        <div class="deal-bar"><div class="deal-fill" style="width:28%"></div></div>
        <div class="deal-note">Payable over 7&ndash;10 years &mdash; regardless of usage</div>
      </div>
    """,
    3: """
      <div class="hero-wrap">
        <img class="hero" src="assets/img/openai-dots.jpg" alt="Dots agent driving a desktop" />
        <div class="hero-cap">Dots agent driving a desktop &mdash; &ldquo;take over&rdquo; control bar</div>
      </div>
      <div class="tagline">RUNS AFTER YOU CLOSE THE CHAT</div>
    """,
    4: """
      <div class="grid2">
        <div class="mini"><div class="mini-k">PER USER</div><div class="mini-v">1</div></div>
        <div class="mini"><div class="mini-k">ACCESS</div><div class="mini-v sm">PRO ONLY</div></div>
      </div>
      <div class="chan">
        <div class="chan-tag">SLACK</div>
        <div class="chan-tag">TEAMS</div>
        <div class="chan-tag dim">SMS SOON</div>
      </div>
    """,
    5: f"""
      <div class="accord">
        <div class="hero-wrap">
          <img class="hero" src="assets/img/whitehouse.jpg" alt="White House luncheon with AI executives" />
          <div class="hero-cap">White House luncheon, Sept 29 &mdash; CBS News</div>
        </div>
        <div class="quote">&ldquo;I think it&rsquo;s morally binding.&rdquo;</div>
        <div class="tag-badge warn">VOLUNTARY &middot; NO AUDITOR NAMED</div>
      </div>
    """,
    6: """
      <div class="outro-card">
        <div class="outro-k">THE ONE NUMBER</div>
        <div class="outro-v">$518B</div>
        <div class="outro-s">Locked in. Non-cancellable. Held by nobody&rsquo;s accountant.</div>
      </div>
    """,
}

CSS = f"""
    @font-face {{ font-family:'News'; src:url('assets/fonts/regular.ttf'); font-weight:400; }}
    @font-face {{ font-family:'News'; src:url('assets/fonts/bold.ttf'); font-weight:700; }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ width:{CANVAS_W}px; height:{CANVAS_H}px; overflow:hidden; background:{BG};
      color:{INK}; font-family:'News',sans-serif; -webkit-font-smoothing:antialiased; }}
    #root {{ position:relative; width:{CANVAS_W}px; height:{CANVAS_H}px; overflow:hidden; background:{BG}; }}

    .top-header {{ position:absolute; left:{MARGIN}px; top:40px; right:{MARGIN}px; height:44px;
      display:flex; justify-content:space-between; align-items:center;
      border-bottom:2px solid {BORDER}; font-size:19px; letter-spacing:2px;
      font-weight:700; color:#C7D0D5; z-index:20; }}
    .top-header b {{ color:{AMBER}; }}
    .live-tag {{ display:flex; align-items:center; gap:6px; background:#4A1A22; color:#FF8787;
      padding:2px 10px; border-radius:4px; font-size:14px; font-weight:700; border:1px solid {CORAL}; }}
    .live-dot {{ width:8px; height:8px; border-radius:50%; background:{CORAL}; }}

    .scene {{ position:absolute; inset:0; opacity:0; pointer-events:none; }}
    .kicker {{ position:absolute; left:{MARGIN}px; top:104px; font-size:{KICKER_PX}px; font-weight:700;
      letter-spacing:2.5px; color:{AMBER}; text-transform:uppercase; }}
    .headline {{ position:absolute; left:{MARGIN}px; top:134px; width:632px; font-size:{HEADLINE_PX}px;
      font-weight:700; line-height:1.12; letter-spacing:-1px; color:{INK}; }}
    .subhead {{ position:absolute; left:{MARGIN}px; top:230px; width:632px; font-size:{SUBHEAD_PX}px;
      line-height:1.25; color:{CYAN}; font-weight:700; }}

    .visual-container {{ position:absolute; left:{MARGIN}px; top:{VISUAL_TOP}px; width:632px;
      height:{VISUAL_H}px; background:#17212B; border:2px solid {BORDER}; border-radius:12px;
      padding:20px; display:flex; flex-direction:column; gap:14px; overflow:hidden; }}

    .hero-wrap {{ position:relative; flex:1 1 auto; min-height:0; border-radius:8px;
      overflow:hidden; border:1.5px solid {BORDER_HI}; background:#0C141B; }}
    .hero {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .hero-cap {{ position:absolute; left:0; right:0; bottom:0; background:rgba(16,24,32,0.88);
      color:#D3DEE5; font-size:12px; font-weight:700; padding:6px 10px; }}

    .big-stat {{ flex:1 1 auto; display:flex; flex-direction:column; justify-content:center;
      align-items:center; text-align:center; gap:6px; }}
    .big-stat-v {{ font-size:112px; font-weight:700; color:{AMBER}; line-height:1; letter-spacing:-5px; }}
    .big-stat-k {{ font-size:15px; font-weight:700; color:{CYAN}; letter-spacing:2.5px; }}
    .big-stat-s {{ font-size:16px; font-weight:700; color:#D3DEE5; }}

    .metric-row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:0 0 auto; }}
    .metric {{ background:{SLATE}; border:1.5px solid {BORDER_HI}; border-radius:8px;
      padding:12px 14px; text-align:center; }}
    .metric-k {{ font-size:12px; color:#D3DEE5; letter-spacing:1px; font-weight:700; }}
    .metric-v {{ font-size:44px; font-weight:700; color:{AMBER}; line-height:1.1; margin-top:2px; }}
    .metric-v.alt {{ color:{CORAL}; }}

    .deal {{ display:flex; flex-direction:column; gap:9px; justify-content:center; height:100%; }}
    .deal-row {{ display:flex; justify-content:space-between; align-items:baseline; }}
    .deal-name {{ font-size:19px; font-weight:700; color:{INK}; letter-spacing:1.5px; }}
    .deal-v {{ font-size:27px; font-weight:700; color:{AMBER}; }}
    .deal-bar {{ height:12px; background:{BG}; border:1px solid {BORDER}; border-radius:3px; overflow:hidden; }}
    .deal-fill {{ height:100%; background:{AMBER}; }}
    .deal-note {{ margin-top:6px; font-size:14px; color:{CYAN}; font-weight:700; text-align:center; }}

    .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:1 1 auto; }}
    .mini {{ background:{SLATE}; border:1.5px solid {BORDER_HI}; border-radius:8px;
      display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px; }}
    .mini-k {{ font-size:13px; color:#D3DEE5; letter-spacing:1.5px; font-weight:700; }}
    .mini-v {{ font-size:72px; font-weight:700; color:{AMBER}; line-height:1; }}
    .mini-v.sm {{ font-size:34px; color:{CYAN}; }}
    .chan {{ display:flex; gap:10px; flex:0 0 auto; }}
    .chan-tag {{ flex:1; text-align:center; background:{SLATE}; border:1.5px solid {BORDER_HI};
      border-radius:6px; padding:12px 6px; font-size:16px; font-weight:700; color:{INK}; letter-spacing:1px; }}
    .chan-tag.dim {{ color:#7C8B96; border-color:{BORDER}; }}

    .tagline {{ flex:0 0 auto; text-align:center; font-size:19px; font-weight:700;
      color:{BG}; background:{AMBER}; border-radius:8px; padding:13px; }}
    .accord {{ display:flex; flex-direction:column; gap:12px; height:100%; }}
    .quote {{ font-size:29px; font-weight:700; color:{INK}; line-height:1.2; flex:0 0 auto; }}
    .tag-badge {{ align-self:flex-start; padding:7px 13px; border-radius:5px; font-size:14px;
      font-weight:700; letter-spacing:1px; }}
    .tag-badge.warn {{ background:#4A1A22; color:#FF8787; border:1.5px solid {CORAL}; }}

    .outro-card {{ display:flex; flex-direction:column; justify-content:center; align-items:center;
      gap:8px; height:100%; text-align:center; }}
    .outro-k {{ font-size:15px; letter-spacing:3px; font-weight:700; color:{CYAN}; }}
    .outro-v {{ font-size:104px; font-weight:700; color:{AMBER}; line-height:1; letter-spacing:-4px; }}
    .outro-s {{ font-size:19px; color:{INK}; font-weight:700; max-width:520px; line-height:1.3; }}

    .detail {{ position:absolute; left:{MARGIN}px; top:{DETAIL_TOP}px; width:632px; font-size:{DETAIL_PX}px;
      line-height:1.3; font-weight:700; color:{INK}; }}
    .source {{ position:absolute; left:{MARGIN}px; top:{SOURCE_TOP}px; width:632px; font-size:{SOURCE_PX}px;
      letter-spacing:1px; color:{MUTED}; font-weight:700; text-transform:uppercase; }}

    /* ---- two-line lower third ------------------------------------------------
       The .cap children are position:absolute so GSAP can fade them, which means
       they contribute NO height to the plate. The plate must declare its own
       height or it collapses to bare padding and the lines overflow. */
    .caption-box {{ position:absolute; left:40px; right:40px; bottom:{PLATE_BOTTOM}px;
      height:{PLATE_H}px; background:{PLATE}; border:2px solid #647480; border-radius:12px;
      padding:{PLATE_PAD}px 20px; z-index:30; box-shadow:0 10px 28px rgba(0,0,0,0.45); }}
    .speaker-pill {{ position:absolute; top:-13px; left:16px; padding:3px 12px; border-radius:4px;
      font-size:13px; font-weight:700; letter-spacing:1px; color:#FFFFFF; background:{TEAL};
      text-transform:uppercase; }}
    .cap {{ position:absolute; left:20px; right:20px; opacity:0; pointer-events:none; }}
    .cap .cur {{ font-size:{CAP_CUR_PX}px; line-height:1.28; font-weight:700; color:{BG}; }}
    .cap .nxt {{ margin-top:9px; padding-top:9px; border-top:2px solid #C9D2D8;
      font-size:{CAP_NXT_PX}px; line-height:1.28; font-weight:700; color:{BORDER}; }}
    .cap .w {{ border-radius:3px; padding:0 2px; }}
    .cap .cur .w.on {{ background:{HILITE}; color:#FFFFFF;
      box-shadow:0 0 0 2px rgba(200,16,46,0.35); }}

    .progress-bar {{ position:absolute; left:0; bottom:0; width:{CANVAS_W}px; height:6px;
      background:{AMBER}; transform-origin:left center; transform:scaleX(0); z-index:40; }}
"""


def caption_groups(words, seg_id, budget=CAP_BUDGET):
    """Break a segment's words into short runs, never splitting a word."""
    ws = [w for w in words if w["seg"] == seg_id]
    groups, cur, chars = [], [], 0
    for w in ws:
        n = len(w["w"])
        if cur and chars + n > budget:
            groups.append(cur)
            cur, chars = [], 0
        cur.append(w)
        chars += n + 1
    if cur:
        groups.append(cur)
    return groups


def _spans(g):
    return " ".join(
        f'<span class="w" data-s="{w["s"]}" data-e="{w["e"]}">{esc(w["w"])}</span>'
        for w in g)


def caption_html(words, seg_id):
    """Each line shows the words being spoken now plus the line that follows."""
    out, gs = [], caption_groups(words, seg_id)
    for i, g in enumerate(gs):
        s, e = g[0]["s"], g[-1]["e"] + 0.18
        body = f'<div class="cur">{_spans(g)}</div>'
        if i + 1 < len(gs):
            body += f'<div class="nxt">{_spans(gs[i + 1])}</div>'
        out.append(f'<div class="cap clip" data-start="{s:.3f}" '
                   f'data-duration="{e - s:.3f}">{body}</div>')
    return "\n      ".join(out)


def build(ep, script, bed_volume=0.62):
    data = json.load(open(os.path.join(ep, "voice-timing.json")))
    words = json.load(open(os.path.join(ep, "words.json")))
    total = data["total_duration"]
    timeline, scenes = data["timeline"], data["scenes"]

    missing = [s["id"] for s in scenes if s["id"] not in VISUALS]
    if missing:
        raise SystemExit(
            f"No visual defined for scene(s) {missing}. Add a VISUALS entry in "
            f"build_html.py — every scene needs a visual or a deliberate reason "
            f"it has none (title/outro cards only).")

    scene_html, cap_html = [], []
    for sc, t in zip(scenes, timeline):
        scene_html.append(f"""
  <div id="scene-{sc['id']}" class="scene clip" data-start="{sc['start']}" data-duration="{sc['duration']}">
    <div class="kicker">{esc(sc['kicker'])}</div>
    <div class="headline">{esc(sc['headline'])}</div>
    <div class="subhead">{esc(sc['subhead'])}</div>
    <div class="visual-container">{VISUALS[sc['id']]}</div>
    <div class="detail">{esc(sc['detail'])}</div>
    <div class="source">{esc(sc['source'])}</div>
  </div>""")
        cap_html.append(f"""
  <div class="cap-group" data-seg="{t['id']}">
      {caption_html(words, t['id'])}
  </div>""")

    audio = "\n".join(
        f'  <audio id="audio-{t["id"]}" class="clip" data-start="{t["start"]}" '
        f'data-duration="{t["duration"]}" data-track-index="{2 if i % 2 == 0 else 3}" '
        f'data-volume="1.0" src="{t["audio_file"]}"></audio>'
        for i, t in enumerate(timeline))

    out = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width={CANVAS_W}, height={CANVAS_H}" />
  <title>Daily Digest</title>
  <script src="assets/gsap.min.js"></script>
  <style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-width="{CANVAS_W}"
     data-height="{CANVAS_H}" data-fps="30" data-duration="{total}">

  <div class="top-header">
    <span>DAILY DIGEST <b>&middot; MORNING</b></span>
    <div class="live-tag"><div class="live-dot"></div>ROSE INTEL</div>
  </div>

{''.join(scene_html)}

  <div class="caption-box">
    <div class="speaker-pill">[{str(script.get('anchor', 'sora')).upper()}]</div>
{''.join(cap_html)}
  </div>

  <div id="progress" class="progress-bar"></div>

  <audio id="bgm" class="clip" data-start="0" data-duration="{total}"
         data-volume="{bed_volume}" data-track-index="1" src="assets/music/bgm.mp3"></audio>
{audio}

</div>

<script>
  const DURATION = {total};
  const scenesData = {json.dumps(scenes)};
  const tl = gsap.timeline({{ paused: true }});
  tl.to("#progress", {{ scaleX: 1, duration: DURATION, ease: "none" }}, 0);

  // Staggered reveals give each scene several visual states (Gate 6: one change
  // every 2.5-3.5s). Elements absent from a scene are skipped silently.
  scenesData.forEach((sc) => {{
    const el = `#scene-${{sc.id}}`;
    tl.to(el, {{ opacity: 1, duration: 0.18, ease: "power2.out" }}, sc.start);
    tl.fromTo(el + " .kicker", {{ y: 14, opacity: 0 }},
      {{ y: 0, opacity: 1, duration: 0.3, ease: "power2.out" }}, sc.start + 0.05);
    tl.fromTo(el + " .headline", {{ y: 18, opacity: 0 }},
      {{ y: 0, opacity: 1, duration: 0.3, ease: "power2.out" }}, sc.start + 0.15);
    tl.fromTo(el + " .visual-container", {{ scale: 0.96, opacity: 0 }},
      {{ scale: 1, opacity: 1, duration: 0.36, ease: "power2.out" }}, sc.start + 0.28);
    tl.fromTo(el + " .detail", {{ y: 12, opacity: 0 }},
      {{ y: 0, opacity: 1, duration: 0.3, ease: "power2.out" }}, sc.start + 0.45);
    tl.fromTo(el + " .source", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, sc.start + 0.6);
    tl.fromTo(el + " .metric-v", {{ scale: 0.9 }}, {{ scale: 1, duration: 0.4, ease: "back.out(2)" }}, sc.start + 0.5);
    tl.fromTo(el + " .big-stat-v", {{ scale: 0.88 }}, {{ scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, sc.start + 0.4);
    tl.fromTo(el + " .deal-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power2.out" }}, sc.start + 0.55);
    tl.fromTo(el + " .mini-v", {{ scale: 0.85 }}, {{ scale: 1, duration: 0.4, ease: "back.out(2)" }}, sc.start + 0.5);
    tl.fromTo(el + " .hero", {{ scale: 1.06 }}, {{ scale: 1, duration: sc.duration, ease: "none" }}, sc.start);
    tl.fromTo(el + " .outro-v", {{ scale: 0.85 }}, {{ scale: 1, duration: 0.5, ease: "back.out(1.7)" }}, sc.start + 0.4);
    if (sc.id < scenesData.length) {{
      tl.to(el, {{ opacity: 0, duration: 0.16, ease: "power2.in" }}, sc.end - 0.16);
    }}
  }});

  // caption line visibility from its own clip window
  document.querySelectorAll(".cap").forEach((c) => {{
    const s = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
    tl.fromTo(c, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08 }}, s);
    tl.to(c, {{ opacity: 0, duration: 0.08 }}, s + d);
  }});

  // karaoke: light the word whose [data-s, data-e] window contains t.
  // Scoped to .cur so the dimmed "next" preview line can never light a stale word
  // during handover. Pure function of t, so any seek reproduces it exactly.
  const spans = Array.from(document.querySelectorAll(".cap .cur .w"));
  const onSpans = new Set();
  function karaoke(t) {{
    for (const sp of spans) {{
      const s = parseFloat(sp.dataset.s), e = parseFloat(sp.dataset.e);
      const should = t >= s && t <= e;
      if (should && !onSpans.has(sp)) {{ sp.classList.add("on"); onSpans.add(sp); }}
      else if (!should && onSpans.has(sp)) {{ sp.classList.remove("on"); onSpans.delete(sp); }}
    }}
  }}
  tl.eventCallback("onUpdate", function () {{ karaoke(tl.time()); }});
  karaoke(0);
  tl.seek(0);

  tl.to("#root", {{ opacity: 0, duration: 0.6, ease: "power2.in" }}, DURATION - 0.6);
  window.__timelines = {{ main: tl }};
</script>
</body>
</html>"""

    comp = os.path.join(ep, "composition")
    os.makedirs(comp, exist_ok=True)
    open(os.path.join(comp, "index.html"), "w").write(out)
    return total


if __name__ == "__main__":
    import sys
    ep = sys.argv[1]
    sc = json.load(open(sys.argv[2]))
    print(f"built {build(ep, sc):.2f}s")
