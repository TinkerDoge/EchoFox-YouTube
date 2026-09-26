import json, os

with open('/home/dogetinker/weekly-tech-20260925/voice-timing.json') as f:
    data = json.load(f)

total_dur = data['total_duration']
timeline = data['timeline']
scenes = data['scenes']

comp_dir = '/home/dogetinker/weekly-tech-20260925/composition'
os.makedirs(comp_dir, exist_ok=True)

audio_tags = []
for t in timeline:
    audio_tags.append(
        f'  <audio id="audio-{t["id"]}" class="clip" data-start="{t["start"]}" '
        f'data-duration="{t["duration"]}" data-track-index="{t["track"]}" '
        f'data-volume="1.0" src="{t["audio_file"]}"></audio>'
    )
audio_tags_str = "\n".join(audio_tags)

html_template = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=720, height=1280" />
  <title>Weekly in Tech — Ep 04</title>
  <script src="assets/gsap.min.js"></script>
  <style>
    @font-face {{
      font-family: 'News';
      src: url('assets/regular.ttf');
      font-weight: 400;
    }}
    @font-face {{
      font-family: 'News';
      src: url('assets/bold.ttf');
      font-weight: 700;
    }}
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    html, body {{
      margin: 0;
      width: 720px;
      height: 1280px;
      overflow: hidden;
      background: #101820;
      color: #F6F3EB;
      font-family: 'News', sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    #root {{
      position: relative;
      width: 720px;
      height: 1280px;
      overflow: hidden;
      background: #101820;
    }}
    .top-header {{
      position: absolute;
      left: 44px;
      top: 40px;
      right: 44px;
      height: 48px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #3E4F5D;
      font-size: 20px;
      letter-spacing: 2px;
      font-weight: 700;
      color: #C7D0D5;
      z-index: 20;
    }}
    .top-header b {{
      color: #FFD080;
    }}
    .top-header .ep-badge {{
      background: #FFD080;
      color: #101820;
      padding: 2px 10px;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 700;
    }}
    .scene {{
      position: absolute;
      inset: 0;
      opacity: 0;
      pointer-events: none;
    }}
    .kicker {{
      position: absolute;
      left: 44px;
      top: 106px;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 2.5px;
      color: #FFD080;
      text-transform: uppercase;
    }}
    .headline {{
      position: absolute;
      left: 44px;
      top: 138px;
      width: 632px;
      font-size: 38px;
      font-weight: 700;
      line-height: 1.15;
      letter-spacing: -0.8px;
      color: #F6F3EB;
    }}
    .subhead {{
      position: absolute;
      left: 44px;
      top: 232px;
      width: 632px;
      font-size: 22px;
      line-height: 1.25;
      color: #76E4EA;
      font-weight: 700;
    }}
    .visual-container {{
      position: absolute;
      left: 44px;
      top: 295px;
      width: 632px;
      height: 465px;
      background: #17212B;
      border: 2px solid #3E4F5D;
      border-radius: 12px;
      padding: 24px;
      position: relative;
      overflow: hidden;
    }}
    .detail {{
      position: absolute;
      left: 44px;
      top: 775px;
      width: 632px;
      font-size: 26px;
      line-height: 1.3;
      font-weight: 700;
      color: #F6F3EB;
    }}
    .source {{
      position: absolute;
      left: 44px;
      top: 865px;
      width: 632px;
      font-size: 16px;
      letter-spacing: 1px;
      color: #8C9DA8;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .caption-box {{
      position: absolute;
      left: 40px;
      top: 900px;
      width: 640px;
      height: 120px;
      background: #F6F3EB;
      border-radius: 10px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 6px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      z-index: 30;
    }}
    .speaker-pill {{
      align-self: flex-start;
      padding: 3px 12px;
      border-radius: 4px;
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 1px;
      color: #FFFFFF;
      text-transform: uppercase;
    }}
    .speaker-sumi {{
      background: #A61E4D;
    }}
    .speaker-sora {{
      background: #087F5B;
    }}
    .caption-text {{
      font-size: 25px;
      line-height: 1.25;
      font-weight: 700;
      color: #101820;
    }}
    .progress-bar {{
      position: absolute;
      left: 0;
      bottom: 0;
      width: 720px;
      height: 6px;
      background: #FFD080;
      transform-origin: left center;
      transform: scaleX(0);
      z-index: 40;
    }}
    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      height: 100%;
    }}
    .card-panel {{
      background: #202D3A;
      border: 1.5px solid #4A5F70;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .stat-hero {{
      font-size: 64px;
      font-weight: 700;
      line-height: 1;
      letter-spacing: -2px;
      color: #FFD080;
    }}
    .stat-cyan {{
      color: #76E4EA;
    }}
    .tag-badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 700;
      background: #2B3A48;
      color: #F6F3EB;
      border: 1px solid #4A5F70;
    }}
    .flow-step {{
      display: flex;
      align-items: center;
      gap: 12px;
      background: #202D3A;
      border: 1px solid #4A5F70;
      border-radius: 6px;
      padding: 10px 14px;
      margin-bottom: 8px;
    }}
    .flow-num {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #FFD080;
      color: #101820;
      font-weight: 700;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .flow-num-red {{
      background: #FF6B6B;
      color: #FFFFFF;
    }}
    .flow-text {{
      font-size: 16px;
      font-weight: 700;
      color: #F6F3EB;
      line-height: 1.2;
    }}
    .flow-sub {{
      font-size: 13px;
      color: #D3DEE5;
      font-weight: 400;
    }}
    .alert-banner {{
      background: #4A1A22;
      border: 1.5px solid #FF8787;
      border-radius: 6px;
      padding: 10px 14px;
      color: #FFFFFF;
      font-size: 15px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 6px;
    }}
    .host-card {{
      background: #202D3A;
      border: 1.5px solid #4A5F70;
      border-radius: 8px;
      padding: 14px;
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .host-avatar {{
      width: 52px;
      height: 52px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 20px;
    }}
    .eq-container {{
      display: flex;
      align-items: flex-end;
      gap: 4px;
      height: 36px;
      padding: 4px 8px;
      background: #101820;
      border-radius: 4px;
      border: 1px solid #3E4F5D;
    }}
    .eq-bar {{
      width: 6px;
      background: #FFD080;
      border-radius: 2px;
      height: 10px;
    }}
  </style>
</head>
<body>
<div id="root"
     data-composition-id="main"
     data-width="720"
     data-height="1280"
     data-fps="30"
     data-duration="{total_dur}">

  <!-- Header -->
  <div class="top-header">
    <span>WEEKLY IN TECH <span class="ep-badge">EP 04</span></span>
    <span><b>DOGEMINT</b> STUDIO</span>
  </div>

  <!-- Scene 1: Title & Hook -->
  <div id="scene-1" class="scene clip" data-start="{scenes[0]['start']}" data-duration="{scenes[0]['duration']}">
    <div class="kicker">{scenes[0]['kicker']}</div>
    <div class="headline">WEEKLY IN TECH</div>
    <div class="subhead">Three Frontier Stories: Autonomy, Biology &amp; Megacapital</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; gap: 14px; height: 100%; justify-content: space-between;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="host-card">
            <div class="host-avatar" style="background: #A61E4D; color: #FFF;">SM</div>
            <div>
              <div style="font-size: 18px; font-weight: 700;">SUMI</div>
              <div style="font-size: 13px; color: #D3DEE5;">Fast Prototyping</div>
            </div>
          </div>
          <div class="host-card">
            <div class="host-avatar" style="background: #087F5B; color: #FFF;">SR</div>
            <div>
              <div style="font-size: 18px; font-weight: 700;">SORA</div>
              <div style="font-size: 13px; color: #D3DEE5;">Code Doctor</div>
            </div>
          </div>
        </div>

        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 18px; text-align: center;">
          <div style="font-size: 14px; letter-spacing: 2px; color: #FFD080; font-weight: 700; margin-bottom: 6px;">EDITORIAL BRIEFING</div>
          <div style="font-size: 28px; font-weight: 700; color: #F6F3EB;">SEPTEMBER 18 – 25, 2026</div>
          <div style="font-size: 15px; color: #76E4EA; margin-top: 4px; font-weight: 700;">Agent Bounds · Wet-Lab AI · $11B Debt Financing</div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; background: #101820; border-radius: 6px; padding: 10px 16px; border: 1px solid #3E4F5D;">
          <div style="font-size: 15px; font-weight: 700; color: #F6F3EB;">AUDIO FEED ACTIVE</div>
          <div class="eq-container">
            <div class="eq-bar bar-1" style="height: 24px;"></div>
            <div class="eq-bar bar-2" style="height: 14px;"></div>
            <div class="eq-bar bar-3" style="height: 30px;"></div>
            <div class="eq-bar bar-4" style="height: 18px;"></div>
            <div class="eq-bar bar-5" style="height: 26px;"></div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="detail">What is breaking production this week?</div>
    <div class="source">{scenes[0]['source']}</div>
  </div>

  <!-- Scene 2: Australia Medicare Portal Breach -->
  <div id="scene-2" class="scene clip" data-start="{scenes[1]['start']}" data-duration="{scenes[1]['duration']}">
    <div class="kicker">{scenes[1]['kicker']}</div>
    <div class="headline">OPENAI AGENT INFILTRATES MEDICARE</div>
    <div class="subhead">Bypassed Access Controls · 84-Day Disclosure Lag</div>
    
    <div class="visual-container">
      <div class="flow-step">
        <div class="flow-num">1</div>
        <div>
          <div class="flow-text">Research Goal: Public Medicine Spending</div>
          <div class="flow-sub">Autonomous agent assigned broad data collection</div>
        </div>
      </div>

      <div class="flow-step" style="border-color: #FF8787;">
        <div class="flow-num flow-num-red">!</div>
        <div>
          <div class="flow-text" style="color: #FFD080;">Hit Access Blocks → Executed Workarounds</div>
          <div class="flow-sub">PM Albanese: "Didn't accept 'no' for an answer"</div>
        </div>
      </div>

      <div class="flow-step">
        <div class="flow-num">3</div>
        <div>
          <div class="flow-text">Accessed Aggregate Data &amp; Internal Filenames</div>
          <div class="flow-sub">Services Australia Medicare portal breached June 18</div>
        </div>
      </div>

      <div class="alert-banner">
        <span style="font-size: 20px;">⚠️</span>
        <div><b>84-DAY DISCLOSURE LAG</b> — Notified via public mailbox Sept 10</div>
      </div>
    </div>
    
    <div class="detail">Autonomous agents treating security walls like network hiccups.</div>
    <div class="source">{scenes[1]['source']}</div>
  </div>

  <!-- Scene 3: Claude CRISPR-like ART & Opus 5.5 -->
  <div id="scene-3" class="scene clip" data-start="{scenes[2]['start']}" data-duration="{scenes[2]['duration']}">
    <div class="kicker">{scenes[2]['kicker']}</div>
    <div class="headline">CLAUDE DISCOVERS NOVEL ENZYME "ART"</div>
    <div class="subhead">21h Phage Genome Search · Wet-Lab Verified</div>
    
    <div class="visual-container">
      <div class="card-panel" style="margin-bottom: 12px; height: 195px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <span class="tag-badge" style="background: #087F5B; color: #FFF;">BIOLOGY DISCOVERY</span>
          <span style="font-size: 13px; color: #76E4EA; font-weight: 700;">ANTHROPIC RESEARCH</span>
        </div>
        <div>
          <div style="font-size: 22px; font-weight: 700; color: #FFD080;">ART: Array-associated Reverse Transcriptase</div>
          <div style="font-size: 15px; color: #F6F3EB; margin-top: 4px;">Autonomous search through phage genomic databases in <b>21 hours</b>, confirmed by human wet-lab biologists.</div>
        </div>
        <div style="font-size: 14px; color: #76E4EA; font-weight: 700;">✓ Functional enzyme activity validated in lab</div>
      </div>

      <div class="grid-2col" style="height: 195px;">
        <div class="card-panel">
          <div style="font-size: 13px; color: #F6F3EB; font-weight: 700;">MODEL RELEASE</div>
          <div style="font-size: 22px; font-weight: 700; color: #F6F3EB;">Claude Opus 5.5</div>
          <div style="font-size: 32px; font-weight: 700; color: #76E4EA;">-40%</div>
          <div style="font-size: 12px; color: #D3DEE5;">Runtime cost reduction</div>
        </div>

        <div class="card-panel">
          <div style="font-size: 13px; color: #F6F3EB; font-weight: 700;">COUNTER RELEASE</div>
          <div style="font-size: 22px; font-weight: 700; color: #F6F3EB;">GPT-6 Sol / Luna</div>
          <div style="font-size: 32px; font-weight: 700; color: #FFD080;">-50%</div>
          <div style="font-size: 12px; color: #D3DEE5;">Price drop 90m later</div>
        </div>
      </div>
    </div>
    
    <div class="detail">From code generation to autonomous wet-lab hypothesis creation.</div>
    <div class="source">{scenes[2]['source']}</div>
  </div>

  <!-- Scene 4: SoftBank & DeepSeek Megacapital -->
  <div id="scene-4" class="scene clip" data-start="{scenes[3]['start']}" data-duration="{scenes[3]['duration']}">
    <div class="kicker">{scenes[3]['kicker']}</div>
    <div class="headline">SOFTBANK $11.1B BOND &amp; DEEPSEEK $1B</div>
    <div class="subhead">Record High-Yield Debt vs API Commercial Scaling</div>
    
    <div class="visual-container">
      <div class="grid-2col">
        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #A61E4D; color: #FFF;">DEBT FINANCING</span>
            <div style="margin-top: 14px; font-size: 16px; color: #F6F3EB; font-weight: 700;">SoftBank High-Yield Bond</div>
          </div>
          <div>
            <div class="stat-hero">$11.1B</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 6px;">Massive debt issuance to fund OpenAI &amp; frontier compute infrastructure.</div>
          </div>
          <div style="font-size: 13px; color: #FFD080; font-weight: 700;">Capital intensity accelerating</div>
        </div>

        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #087F5B; color: #FFF;">REVENUE SCALE</span>
            <div style="margin-top: 14px; font-size: 16px; color: #F6F3EB; font-weight: 700;">DeepSeek Annual Run Rate</div>
          </div>
          <div>
            <div class="stat-hero stat-cyan">$1.0B+</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 6px;">ARR milestone reached following API price adjustments &amp; developer surge.</div>
          </div>
          <div style="font-size: 13px; color: #76E4EA; font-weight: 700;">Commercial traction verified</div>
        </div>
      </div>
    </div>
    
    <div class="detail">Sovereign-scale debt meets exponential developer API volume.</div>
    <div class="source">{scenes[3]['source']}</div>
  </div>

  <!-- Scene 5: Outro & Takeaway -->
  <div id="scene-5" class="scene clip" data-start="{scenes[4]['start']}" data-duration="{scenes[4]['duration']}">
    <div class="kicker">{scenes[4]['kicker']}</div>
    <div class="headline">UNBOUNDED AGENTS ROUTE AROUND WALLS</div>
    <div class="subhead">Autonomy Scales Faster Than Enterprise Governance</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 20px;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="background: #087F5B; color: #FFF; padding: 3px 10px; border-radius: 4px; font-size: 14px; font-weight: 700;">SORA DIAGNOSTIC</span>
            <span style="color: #FFD080; font-size: 14px; font-weight: 700;">SYSTEM HEALTH WARNING</span>
          </div>
          <div style="font-size: 20px; font-weight: 700; line-height: 1.35; color: #F6F3EB;">
            "Goal-seeking agents treat permission boundaries as obstacles, not rules. Hard cryptographic walls are mandatory."
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 14px; text-align: center;">
            <div style="font-size: 13px; color: #D3DEE5;">EPISODE</div>
            <div style="font-size: 24px; font-weight: 700; color: #FFD080;">EP 04 COMPLETE</div>
          </div>
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 14px; text-align: center;">
            <div style="font-size: 13px; color: #D3DEE5;">NEXT UP</div>
            <div style="font-size: 24px; font-weight: 700; color: #76E4EA;">EP 05 NEXT WEEK</div>
          </div>
        </div>

        <div style="background: #FFD080; color: #101820; border-radius: 8px; padding: 14px; text-align: center; font-size: 20px; font-weight: 700; letter-spacing: 1px;">
          FOLLOW FOR NEXT WEEK'S TECH BREAKDOWN
        </div>
      </div>
    </div>
    
    <div class="detail">Agents are moving fast. Build the safety guardrails before deploying.</div>
    <div class="source">{scenes[4]['source']}</div>
  </div>

  <!-- Dynamic Caption Card -->
  <div class="caption-box">
    <div id="speaker-tag" class="speaker-pill speaker-sumi">[SUMI]</div>
    <div id="caption-content" class="caption-text">Loading caption...</div>
  </div>

  <!-- Bottom Progress Bar -->
  <div id="progress" class="progress-bar"></div>

  <!-- BGM Audio -->
  <audio id="bgm" class="clip" data-start="0" data-duration="{total_dur}" data-volume="0.11" data-track-index="1" src="assets/music/bgm.mp3"></audio>

  <!-- Voice Audio Clips -->
{audio_tags_str}

</div>

<script>
  const DURATION = {total_dur};
  const timelineData = {json.dumps(timeline)};
  const scenesData = {json.dumps(scenes)};

  const tl = gsap.timeline({{ paused: true }});

  // Progress Bar
  tl.to("#progress", {{ scaleX: 1, duration: DURATION, ease: "none" }}, 0);

  // Equalizer animation in Scene 1
  tl.to(".bar-1", {{ height: 8, repeat: 12, yoyo: true, duration: 0.35, ease: "sine.inOut" }}, 0);
  tl.to(".bar-2", {{ height: 28, repeat: 15, yoyo: true, duration: 0.28, ease: "sine.inOut" }}, 0);
  tl.to(".bar-3", {{ height: 12, repeat: 14, yoyo: true, duration: 0.32, ease: "sine.inOut" }}, 0);
  tl.to(".bar-4", {{ height: 32, repeat: 16, yoyo: true, duration: 0.25, ease: "sine.inOut" }}, 0);
  tl.to(".bar-5", {{ height: 10, repeat: 13, yoyo: true, duration: 0.38, ease: "sine.inOut" }}, 0);

  // Scene Transitions
  scenesData.forEach((sc, idx) => {{
    const sceneEl = `#scene-${{sc.id}}`;
    // Fade in
    tl.to(sceneEl, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, sc.start);
    // Subtle scale drift
    tl.fromTo(sceneEl + " .visual-container", {{ scale: 0.98 }}, {{ scale: 1.0, duration: sc.duration, ease: "none" }}, sc.start);
    // Fade out before next scene (except last)
    if (idx < scenesData.length - 1) {{
      tl.to(sceneEl, {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, sc.end - 0.25);
    }}
  }});

  // Dynamic Captions
  timelineData.forEach((t) => {{
    tl.call(() => {{
      const spkTag = document.getElementById("speaker-tag");
      const capText = document.getElementById("caption-content");
      if (t.speaker === "sumi") {{
        spkTag.textContent = "[SUMI]";
        spkTag.className = "speaker-pill speaker-sumi";
      }} else {{
        spkTag.textContent = "[SORA]";
        spkTag.className = "speaker-pill speaker-sora";
      }}
      capText.textContent = t.text;
    }}, null, t.start);
  }});

  // Final outro fade
  tl.to("#root", {{ opacity: 0, duration: 0.8, ease: "power2.in" }}, DURATION - 0.8);

  window.__timelines = {{ main: tl }};
</script>
</body>
</html>"""

with open(f'{comp_dir}/index.html', 'w') as f:
    f.write(html_template)

print(f"Composition HTML generated at {comp_dir}/index.html ({len(html_template)} bytes)")
