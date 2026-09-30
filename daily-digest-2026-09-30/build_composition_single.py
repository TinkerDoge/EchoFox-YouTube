#!/usr/bin/env python3
"""Build the single-narrator composition + karaoke word-highlight captions.

Supersedes build_composition.py (the 51s MEGAN-SKIENDEL cut) for the
2026-09-28-style single-narrator read. Follows references/karaoke-captions.md:
  - caption lines grouped on a ~34-char budget, never mid-word
  - each .cap timed first_word.start -> last_word.end + 0.18
  - highlight driven as a pure function of timeline position (seek-safe)
"""
import html
import json
import os

EP = os.path.expanduser("~/hf-codedoctor/daily-digest-2026-09-30")
COMP = os.path.join(EP, "composition")
os.makedirs(os.path.join(COMP, "assets", "img"), exist_ok=True)

data = json.load(open(os.path.join(EP, "voice-timing.json")))
WORDS = json.load(open(os.path.join(EP, "words.json")))
total = data["total_duration"]
timeline = data["timeline"]
scenes = data["scenes"]

esc = html.escape


def caption_groups(seg_id, budget=34):
    """Break a segment's words into short runs, never splitting a word."""
    ws = [w for w in WORDS if w["seg"] == seg_id]
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


def caption_html(seg_id):
    out = []
    for g in caption_groups(seg_id):
        s, e = g[0]["s"], g[-1]["e"] + 0.18
        spans = " ".join(
            f'<span class="w" data-s="{w["s"]}" data-e="{w["e"]}">{esc(w["w"])}</span>'
            for w in g
        )
        out.append(
            f'<div class="cap clip" data-start="{s:.3f}" data-duration="{e - s:.3f}">'
            f'{spans}</div>'
        )
    return "\n      ".join(out)


VISUALS = {
    1: """
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
        <div class="mini">
          <div class="mini-k">PER USER</div>
          <div class="mini-v">1</div>
        </div>
        <div class="mini">
          <div class="mini-k">ACCESS</div>
          <div class="mini-v sm">PRO ONLY</div>
        </div>
      </div>
      <div class="chan">
        <div class="chan-tag">SLACK</div>
        <div class="chan-tag">TEAMS</div>
        <div class="chan-tag dim">SMS SOON</div>
      </div>
    """,
    5: """
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

scene_html, cap_html = [], []
for sc, t in zip(scenes, timeline):
    scene_html.append(f"""
  <div id="scene-{sc['id']}" class="scene clip" data-start="{sc['start']}" data-duration="{sc['duration']}">
    <div class="kicker anim">{esc(sc['kicker'])}</div>
    <div class="headline anim">{esc(sc['headline'])}</div>
    <div class="subhead anim">{esc(sc['subhead'])}</div>
    <div class="visual-container">{VISUALS[sc['id']]}</div>
    <div class="detail anim">{esc(sc['detail'])}</div>
    <div class="source anim">{esc(sc['source'])}</div>
  </div>""")
    cap_html.append(f"""
  <div class="cap-group" data-seg="{t['id']}">
      {caption_html(t['id'])}
  </div>""")

audio_tags = [
    f'  <audio id="audio-{t["id"]}" class="clip" data-start="{t["start"]}" '
    f'data-duration="{t["duration"]}" data-track-index="{2 if i % 2 == 0 else 3}" '
    f'data-volume="1.0" src="{t["audio_file"]}"></audio>'
    for i, t in enumerate(timeline)
]

htmlout = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=720, height=1280" />
  <title>Daily Digest — 30 Sep 2026</title>
  <script src="assets/gsap.min.js"></script>
  <style>
    @font-face {{ font-family:'News'; src:url('assets/fonts/regular.ttf'); font-weight:400; }}
    @font-face {{ font-family:'News'; src:url('assets/fonts/bold.ttf'); font-weight:700; }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    html, body {{ width:720px; height:1280px; overflow:hidden; background:#101820;
      color:#F6F3EB; font-family:'News',sans-serif; -webkit-font-smoothing:antialiased; }}
    #root {{ position:relative; width:720px; height:1280px; overflow:hidden; background:#101820; }}

    .top-header {{ position:absolute; left:44px; top:40px; right:44px; height:44px;
      display:flex; justify-content:space-between; align-items:center;
      border-bottom:2px solid #3E4F5D; font-size:19px; letter-spacing:2px;
      font-weight:700; color:#C7D0D5; z-index:20; }}
    .top-header b {{ color:#FFD080; }}
    .live-tag {{ display:flex; align-items:center; gap:6px; background:#4A1A22; color:#FF8787;
      padding:2px 10px; border-radius:4px; font-size:14px; font-weight:700; border:1px solid #FF6B6B; }}
    .live-dot {{ width:8px; height:8px; border-radius:50%; background:#FF6B6B; }}

    .scene {{ position:absolute; inset:0; opacity:0; pointer-events:none; }}
    .kicker {{ position:absolute; left:44px; top:104px; font-size:17px; font-weight:700;
      letter-spacing:2.5px; color:#FFD080; text-transform:uppercase; }}
    .headline {{ position:absolute; left:44px; top:134px; width:632px; font-size:40px;
      font-weight:700; line-height:1.12; letter-spacing:-1px; color:#F6F3EB; }}
    .subhead {{ position:absolute; left:44px; top:230px; width:632px; font-size:21px;
      line-height:1.25; color:#76E4EA; font-weight:700; }}

    .visual-container {{ position:absolute; left:44px; top:286px; width:632px; height:496px;
      background:#17212B; border:2px solid #3E4F5D; border-radius:12px; padding:18px;
      display:flex; flex-direction:column; gap:14px; overflow:hidden; }}

    .hero-wrap {{ position:relative; flex:1 1 auto; min-height:0; border-radius:8px;
      overflow:hidden; border:1.5px solid #4A5F70; background:#0C141B; }}
    .hero {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .hero-cap {{ position:absolute; left:0; right:0; bottom:0; background:rgba(16,24,32,0.88);
      color:#D3DEE5; font-size:12px; font-weight:700; padding:6px 10px; }}

    .big-stat {{ flex:1 1 auto; display:flex; flex-direction:column; justify-content:center;
      align-items:center; text-align:center; gap:6px; }}
    .big-stat-v {{ font-size:112px; font-weight:700; color:#FFD080; line-height:1; letter-spacing:-5px; }}
    .big-stat-k {{ font-size:15px; font-weight:700; color:#76E4EA; letter-spacing:2.5px; }}
    .big-stat-s {{ font-size:16px; font-weight:700; color:#D3DEE5; }}

    .metric-row {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:0 0 auto; }}
    .metric {{ background:#202D3A; border:1.5px solid #4A5F70; border-radius:8px;
      padding:12px 14px; text-align:center; }}
    .metric-k {{ font-size:12px; color:#D3DEE5; letter-spacing:1px; font-weight:700; }}
    .metric-v {{ font-size:44px; font-weight:700; color:#FFD080; line-height:1.1; margin-top:2px; }}
    .metric-v.alt {{ color:#FF6B6B; }}

    .deal {{ display:flex; flex-direction:column; gap:9px; justify-content:center; height:100%; }}
    .deal-row {{ display:flex; justify-content:space-between; align-items:baseline; }}
    .deal-name {{ font-size:19px; font-weight:700; color:#F6F3EB; letter-spacing:1.5px; }}
    .deal-v {{ font-size:27px; font-weight:700; color:#FFD080; }}
    .deal-bar {{ height:12px; background:#101820; border:1px solid #3E4F5D; border-radius:3px; overflow:hidden; }}
    .deal-fill {{ height:100%; background:#FFD080; }}
    .deal-note {{ margin-top:6px; font-size:14px; color:#76E4EA; font-weight:700; text-align:center; }}

    .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; flex:1 1 auto; }}
    .mini {{ background:#202D3A; border:1.5px solid #4A5F70; border-radius:8px;
      display:flex; flex-direction:column; align-items:center; justify-content:center; gap:4px; }}
    .mini-k {{ font-size:13px; color:#D3DEE5; letter-spacing:1.5px; font-weight:700; }}
    .mini-v {{ font-size:72px; font-weight:700; color:#FFD080; line-height:1; }}
    .mini-v.sm {{ font-size:34px; color:#76E4EA; }}
    .chan {{ display:flex; gap:10px; flex:0 0 auto; }}
    .chan-tag {{ flex:1; text-align:center; background:#202D3A; border:1.5px solid #4A5F70;
      border-radius:6px; padding:12px 6px; font-size:16px; font-weight:700; color:#F6F3EB;
      letter-spacing:1px; }}
    .chan-tag.dim {{ color:#7C8B96; border-color:#3E4F5D; }}

    .tagline {{ flex:0 0 auto; text-align:center; font-size:19px; font-weight:700;
      color:#101820; background:#FFD080; border-radius:8px; padding:13px; }}
    .accord {{ display:flex; flex-direction:column; gap:12px; height:100%; }}
    .quote {{ font-size:29px; font-weight:700; color:#F6F3EB; line-height:1.2; flex:0 0 auto; }}
    .tag-badge {{ align-self:flex-start; padding:7px 13px; border-radius:5px; font-size:14px;
      font-weight:700; letter-spacing:1px; }}
    .tag-badge.warn {{ background:#4A1A22; color:#FF8787; border:1.5px solid #FF6B6B; }}

    .outro-card {{ display:flex; flex-direction:column; justify-content:center; align-items:center;
      gap:8px; height:100%; text-align:center; }}
    .outro-k {{ font-size:15px; letter-spacing:3px; font-weight:700; color:#76E4EA; }}
    .outro-v {{ font-size:104px; font-weight:700; color:#FFD080; line-height:1; letter-spacing:-4px; }}
    .outro-s {{ font-size:19px; color:#F6F3EB; font-weight:700; max-width:520px; line-height:1.3; }}

    .detail {{ position:absolute; left:44px; top:800px; width:632px; font-size:24px;
      line-height:1.3; font-weight:700; color:#F6F3EB; }}
    .source {{ position:absolute; left:44px; top:876px; width:632px; font-size:14px;
      letter-spacing:1px; color:#9AAAB5; font-weight:700; text-transform:uppercase; }}

    /* ---- karaoke captions ---- */
    .caption-box {{ position:absolute; left:40px; top:920px; width:640px; min-height:118px;
      background:#F6F3EB; border:2px solid #647480; border-radius:10px; padding:16px 20px;
      display:flex; flex-direction:column; justify-content:center; z-index:30; }}
    .speaker-pill {{ position:absolute; top:-13px; left:16px; padding:3px 12px; border-radius:4px;
      font-size:13px; font-weight:700; letter-spacing:1px; color:#FFFFFF; background:#087F5B;
      text-transform:uppercase; }}
    .cap {{ position:absolute; left:20px; right:20px; font-size:25px; line-height:1.3;
      font-weight:700; color:#101820; opacity:0; pointer-events:none; }}
    .cap .w {{ border-radius:3px; padding:0 2px; }}
    .cap .w.on {{ background:#C8102E; color:#FFFFFF;
      box-shadow:0 0 0 2px rgba(200,16,46,0.35); }}

    .progress-bar {{ position:absolute; left:0; bottom:0; width:720px; height:6px;
      background:#FFD080; transform-origin:left center; transform:scaleX(0); z-index:40; }}
  </style>
</head>
<body>
<div id="root" data-composition-id="main" data-width="720" data-height="1280"
     data-fps="30" data-duration="{total}">

  <div class="top-header">
    <span>DAILY DIGEST <b>&middot; MORNING</b></span>
    <div class="live-tag"><div class="live-dot"></div>ROSE INTEL</div>
  </div>

{''.join(scene_html)}

  <div class="caption-box">
    <div class="speaker-pill">[SORA]</div>
{''.join(cap_html)}
  </div>

  <div id="progress" class="progress-bar"></div>

  <audio id="bgm" class="clip" data-start="0" data-duration="{total}"
         data-volume="0.62" data-track-index="1" src="assets/music/bgm.mp3"></audio>
{chr(10).join(audio_tags)}

</div>

<script>
  const DURATION = {total};
  const scenesData = {json.dumps(scenes)};
  const tl = gsap.timeline({{ paused: true }});
  tl.to("#progress", {{ scaleX: 1, duration: DURATION, ease: "none" }}, 0);

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
  // Pure function of timeline position, so any seek reproduces it exactly.
  const spans = Array.from(document.querySelectorAll(".cap .w"));
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

open(os.path.join(COMP, "index.html"), "w").write(htmlout)

ngroups = sum(len(caption_groups(t["id"])) for t in timeline)
print(f"wrote {COMP}/index.html ({len(htmlout)} bytes)")
print(f"duration {total}s, {len(scenes)} scenes, {len(WORDS)} words, {ngroups} caption lines")
for t in timeline:
    print(f"  {t['id']:14} {t['start']:6.2f}-{t['end']:6.2f}  "
          f"{len(caption_groups(t['id']))} cap lines")
