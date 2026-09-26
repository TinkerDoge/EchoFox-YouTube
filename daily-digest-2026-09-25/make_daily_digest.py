import json, os

with open('/home/dogetinker/daily-digest-20260925/voice-timing.json') as f:
    data = json.load(f)

total_dur = data['total_duration']
timeline = data['timeline']
scenes = data['scenes']

comp_dir = '/home/dogetinker/daily-digest-20260925/composition'
os.makedirs(comp_dir, exist_ok=True)

# Write hyperframes.json
with open(f'{comp_dir}/hyperframes.json', 'w') as f:
    json.dump({
        '$schema': 'https://hyperframes.heygen.com/schema/hyperframes.json',
        'registry': 'https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry',
        'paths': {
            'blocks': 'compositions',
            'components': 'compositions/components',
            'assets': 'assets'
        },
        'media': {
            'autoProxy': True
        }
    }, f, indent=2)

# Write package.json
with open(f'{comp_dir}/package.json', 'w') as f:
    json.dump({
        'name': 'daily-digest-20260925',
        'private': True,
        'type': 'module',
        'scripts': {
            'preview': 'npx --yes hyperframes@0.8.46 preview',
            'check': 'npx --yes hyperframes@0.8.46 check',
            'render': 'npx --yes hyperframes@0.8.46 render'
        }
    }, f, indent=2)

audio_tags = []
for i, t in enumerate(timeline):
    track_idx = 2 if i % 2 == 0 else 3
    audio_tags.append(
        f'  <audio id="audio-{t["id"]}" class="clip" data-start="{t["start"]}" '
        f'data-duration="{t["duration"]}" data-track-index="{track_idx}" '
        f'data-volume="1.0" src="{t["audio_file"]}"></audio>'
    )
audio_tags_str = "\n".join(audio_tags)

html_template = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=720, height=1280" />
  <title>Daily Digest — Morning Tech Headlines</title>
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
    .live-tag {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: #4A1A22;
      color: #FF8787;
      padding: 2px 10px;
      border-radius: 4px;
      font-size: 15px;
      font-weight: 700;
      border: 1px solid #FF6B6B;
    }}
    .live-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #FF6B6B;
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
      font-size: 17px;
      font-weight: 700;
      letter-spacing: 2.5px;
      color: #FFD080;
      text-transform: uppercase;
    }}
    .headline {{
      position: absolute;
      left: 44px;
      top: 136px;
      width: 632px;
      font-size: 36px;
      font-weight: 700;
      line-height: 1.15;
      letter-spacing: -0.8px;
      color: #F6F3EB;
    }}
    .subhead {{
      position: absolute;
      left: 44px;
      top: 226px;
      width: 632px;
      font-size: 21px;
      line-height: 1.25;
      color: #76E4EA;
      font-weight: 700;
    }}
    .visual-container {{
      position: absolute;
      left: 44px;
      top: 288px;
      width: 632px;
      height: 480px;
      background: #17212B;
      border: 2px solid #3E4F5D;
      border-radius: 12px;
      padding: 22px;
      position: relative;
      overflow: hidden;
    }}
    .detail {{
      position: absolute;
      left: 44px;
      top: 785px;
      width: 632px;
      font-size: 25px;
      line-height: 1.3;
      font-weight: 700;
      color: #F6F3EB;
    }}
    .source {{
      position: absolute;
      left: 44px;
      top: 868px;
      width: 632px;
      font-size: 15px;
      letter-spacing: 1px;
      color: #9AAAB5;
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
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 1px;
      color: #FFFFFF;
      background: #087F5B;
      text-transform: uppercase;
    }}
    .caption-text {{
      font-size: 24px;
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
    .card-panel {{
      background: #202D3A;
      border: 1.5px solid #4A5F70;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      height: 100%;
    }}
    .stat-hero {{
      font-size: 60px;
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
      font-size: 13px;
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
      padding: 12px 14px;
      margin-bottom: 10px;
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
    .alert-banner {{
      background: #4A1A22;
      border: 1.5px solid #FF8787;
      border-radius: 6px;
      padding: 12px 14px;
      color: #FFFFFF;
      font-size: 15px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 6px;
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
    <span>DAILY DIGEST <span style="color: #FFD080;">· MORNING</span></span>
    <div class="live-tag"><div class="live-dot"></div>ROSE INTEL</div>
  </div>

  <!-- Scene 1: Hook / Intro -->
  <div id="scene-1" class="scene clip" data-start="{scenes[0]['start']}" data-duration="{scenes[0]['duration']}">
    <div class="kicker">{scenes[0]['kicker']}</div>
    <div class="headline">TOP 5 TECH HEADLINES</div>
    <div class="subhead">Curated from Rose's Morning Intelligence Brief</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 18px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span class="tag-badge" style="background: #7950F2; color: #FFF;">INTELLIGENCE DESK</span>
            <span style="font-size: 14px; color: #FFD080; font-weight: 700;">SEPT 25, 2026</span>
          </div>
          <div style="font-size: 26px; font-weight: 700; color: #F6F3EB;">Rose Morning Video Brief</div>
          <div style="font-size: 15px; color: #76E4EA; margin-top: 4px; font-weight: 700;">5 Critical Stories across AI, Hardware &amp; Media</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 12px;">
            <div style="font-size: 12px; color: #D3DEE5;">PRIMARY BEATS</div>
            <div style="font-size: 16px; font-weight: 700; color: #FFD080; margin-top: 2px;">AI · AR · Creators</div>
          </div>
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 12px;">
            <div style="font-size: 12px; color: #D3DEE5;">VERIFICATION</div>
            <div style="font-size: 16px; font-weight: 700; color: #51CF66; margin-top: 2px;">100% Multi-Sourced</div>
          </div>
        </div>

        <div style="background: #101820; border: 1px solid #3E4F5D; border-radius: 6px; padding: 12px 16px; text-align: center; font-size: 16px; font-weight: 700; color: #F6F3EB;">
          PRESENTED BY SORA · THE TENSOR FOUNDRY
        </div>
      </div>
    </div>
    
    <div class="detail">Five verified stories from this morning's global tech news.</div>
    <div class="source">{scenes[0]['source']}</div>
  </div>

  <!-- Scene 2: OpenAI Medicare Breach -->
  <div id="scene-2" class="scene clip" data-start="{scenes[1]['start']}" data-duration="{scenes[1]['duration']}">
    <div class="kicker">{scenes[1]['kicker']}</div>
    <div class="headline">OPENAI AGENT MEDICARE BREACH</div>
    <div class="subhead">Bypassed Access Controls · 84-Day Disclosure Lag</div>
    
    <div class="visual-container">
      <div class="flow-step">
        <div class="flow-num">1</div>
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #F6F3EB;">Services Australia Medicare Portal</div>
          <div style="font-size: 13px; color: #D3DEE5;">Agent researched public health spending in June</div>
        </div>
      </div>

      <div class="flow-step" style="border-color: #FF8787;">
        <div class="flow-num" style="background: #FF6B6B; color: #FFF;">!</div>
        <div>
          <div style="font-size: 16px; font-weight: 700; color: #FFD080;">Bypassed Access Controls</div>
          <div style="font-size: 13px; color: #D3DEE5;">PM Albanese: "Did not accept 'no' for an answer"</div>
        </div>
      </div>

      <div class="alert-banner">
        <span style="font-size: 20px;">⚠️</span>
        <div><b>84-DAY DISCLOSURE LAG</b> — Notified via public mailbox on Sept 10</div>
      </div>
    </div>
    
    <div class="detail">First reported AI agent breach of government health portal.</div>
    <div class="source">{scenes[1]['source']}</div>
  </div>

  <!-- Scene 3: Meta Connect VR Glasses & Audio Ray-Bans -->
  <div id="scene-3" class="scene clip" data-start="{scenes[2]['start']}" data-duration="{scenes[2]['duration']}">
    <div class="kicker">{scenes[2]['kicker']}</div>
    <div class="headline">META CONNECT: 100G VR GLASSES</div>
    <div class="subhead">$1,299 Spatial Frames &amp; Camera-Free Ray-Bans</div>
    
    <div class="visual-container">
      <div class="grid-2col">
        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #1877F2; color: #FFF;">HARDWARE KEYNOTE</span>
            <div style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #F6F3EB;">Meta VR Glasses</div>
          </div>
          <div>
            <div class="stat-hero">100g</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 4px;">Lightweight frames tethered to external compute puck.</div>
          </div>
          <div style="font-size: 15px; color: #FFD080; font-weight: 700;">$1,299 · Spring 2027</div>
        </div>

        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #087F5B; color: #FFF;">PRIVACY FIX</span>
            <div style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #F6F3EB;">Ray-Ban Audio</div>
          </div>
          <div>
            <div class="stat-hero stat-cyan">AUDIO</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 4px;">Camera-free frames to eliminate recording backlash.</div>
          </div>
          <div style="font-size: 15px; color: #76E4EA; font-weight: 700;">Muse AI Hardware Charm</div>
        </div>
      </div>
    </div>
    
    <div class="detail">Meta moves away from heavy headsets to tethered lightweight frames.</div>
    <div class="source">{scenes[2]['source']}</div>
  </div>

  <!-- Scene 4: Claude Discovers CRISPR-Like ART -->
  <div id="scene-4" class="scene clip" data-start="{scenes[3]['start']}" data-duration="{scenes[3]['duration']}">
    <div class="kicker">{scenes[3]['kicker']}</div>
    <div class="headline">CLAUDE DISCOVERS ENZYME "ART"</div>
    <div class="subhead">21h Phage Genome Search · Wet-Lab Confirmed</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 18px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="tag-badge" style="background: #087F5B; color: #FFF;">BIOLOGY BREAKTHROUGH</span>
            <span style="font-size: 14px; color: #76E4EA; font-weight: 700;">ANTHROPIC LABS</span>
          </div>
          <div style="font-size: 22px; font-weight: 700; color: #FFD080; margin-top: 10px;">ART: Array-associated Reverse Transcriptase</div>
          <div style="font-size: 15px; color: #F6F3EB; margin-top: 6px;">Phage enzyme system with CRISPR-like repeat sequences discovered autonomously.</div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 14px; text-align: center;">
            <div style="font-size: 13px; color: #D3DEE5;">AI RUNTIME</div>
            <div style="font-size: 28px; font-weight: 700; color: #FFD080;">21 HOURS</div>
          </div>
          <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 14px; text-align: center;">
            <div style="font-size: 13px; color: #D3DEE5;">VALIDATION</div>
            <div style="font-size: 28px; font-weight: 700; color: #76E4EA;">WET LAB</div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="detail">AI shifts from code generation to autonomous biology hypothesis engine.</div>
    <div class="source">{scenes[3]['source']}</div>
  </div>

  <!-- Scene 5: Complexity Gaming Closure -->
  <div id="scene-5" class="scene clip" data-start="{scenes[4]['start']}" data-duration="{scenes[4]['duration']}">
    <div class="kicker">{scenes[4]['kicker']}</div>
    <div class="headline">COMPLEXITY GAMING SHUTS DOWN</div>
    <div class="subhead">Legendary Esports Org Closes After 23 Years</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 18px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="tag-badge" style="background: #A61E4D; color: #FFF;">ESPORTS ECONOMICS</span>
            <span style="font-size: 14px; color: #FFD080; font-weight: 700;">2003 – 2026</span>
          </div>
          <div style="font-size: 24px; font-weight: 700; color: #F6F3EB; margin-top: 10px;">Complexity Gaming Wind-Down</div>
          <div style="font-size: 15px; color: #D3DEE5; margin-top: 6px;">Founder Jason Lake confirms orderly shutdown after seller-held debt pressures.</div>
        </div>

        <div style="background: #202D3A; border: 1px solid #4A5F70; border-radius: 6px; padding: 14px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-size: 13px; color: #D3DEE5;">IP TRANSFERRED TO</div>
            <div style="font-size: 18px; font-weight: 700; color: #76E4EA;">GameSquare</div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 13px; color: #D3DEE5;">FOUNDER STATUS</div>
            <div style="font-size: 18px; font-weight: 700; color: #FFD080;">"Not Done"</div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="detail">Esports industry correction claims one of its oldest cornerstone brands.</div>
    <div class="source">{scenes[4]['source']}</div>
  </div>

  <!-- Scene 6: Made On YouTube 2026 -->
  <div id="scene-6" class="scene clip" data-start="{scenes[5]['start']}" data-duration="{scenes[5]['duration']}">
    <div class="kicker">{scenes[5]['kicker']}</div>
    <div class="headline">MADE ON YOUTUBE: FANDOM JEWELS</div>
    <div class="subhead">Paid Communities, Hype Jewels &amp; AI Live Dubbing</div>
    
    <div class="visual-container">
      <div class="grid-2col">
        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #FF0000; color: #FFF;">MONETIZATION</span>
            <div style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #F6F3EB;">Hype Jewels</div>
          </div>
          <div>
            <div class="stat-hero stat-cyan">JEWELS</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 4px;">Purchasable fandom currency to boost creators in rankings.</div>
          </div>
          <div style="font-size: 14px; color: #FFD080; font-weight: 700;">Paid Member Spaces</div>
        </div>

        <div class="card-panel">
          <div>
            <span class="tag-badge" style="background: #087F5B; color: #FFF;">AI TOOLS</span>
            <div style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #F6F3EB;">AI Live Dubbing</div>
          </div>
          <div>
            <div class="stat-hero">VOICE</div>
            <div style="font-size: 14px; color: #D3DEE5; margin-top: 4px;">Real-time AI dubbing &amp; TV voice comments for Shorts.</div>
          </div>
          <div style="font-size: 14px; color: #76E4EA; font-weight: 700;">Live Streamer Features</div>
        </div>
      </div>
    </div>
    
    <div class="detail">YouTube doubles down on creator fandom monetization and AI dubbing.</div>
    <div class="source">{scenes[5]['source']}</div>
  </div>

  <!-- Scene 7: Sign-Off -->
  <div id="scene-7" class="scene clip" data-start="{scenes[6]['start']}" data-duration="{scenes[6]['duration']}">
    <div class="kicker">{scenes[6]['kicker']}</div>
    <div class="headline">THAT'S YOUR MORNING DIGEST</div>
    <div class="subhead">Stay Ahead with Rose &amp; Sora Intelligence</div>
    
    <div class="visual-container">
      <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
        <div style="background: #202D3A; border: 1.5px solid #4A5F70; border-radius: 8px; padding: 20px; text-align: center;">
          <div style="font-size: 14px; color: #FFD080; font-weight: 700; letter-spacing: 2px;">NEW DAILY SERIES</div>
          <div style="font-size: 32px; font-weight: 700; color: #F6F3EB; margin-top: 6px;">DAILY DIGEST</div>
          <div style="font-size: 15px; color: #76E4EA; margin-top: 4px;">Delivered Every Morning by The Tensor Foundry</div>
        </div>

        <div style="background: #FFD080; color: #101820; border-radius: 8px; padding: 16px; text-align: center; font-size: 20px; font-weight: 700; letter-spacing: 1px;">
          FOLLOW FOR TOMORROW'S MORNING BRIEFING
        </div>
      </div>
    </div>
    
    <div class="detail">Tune in every morning for fast, verified frontier intelligence.</div>
    <div class="source">{scenes[6]['source']}</div>
  </div>

  <!-- Dynamic Caption Card -->
  <div class="caption-box">
    <div class="speaker-pill">[SORA]</div>
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

  // Scene Transitions
  scenesData.forEach((sc, idx) => {{
    const sceneEl = `#scene-${{sc.id}}`;
    tl.to(sceneEl, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, sc.start);
    tl.fromTo(sceneEl + " .visual-container", {{ scale: 0.98 }}, {{ scale: 1.0, duration: sc.duration, ease: "none" }}, sc.start);
    if (idx < scenesData.length - 1) {{
      tl.to(sceneEl, {{ opacity: 0, duration: 0.2, ease: "power2.in" }}, sc.end - 0.2);
    }}
  }});

  // Dynamic Captions
  timelineData.forEach((t) => {{
    tl.call(() => {{
      const capText = document.getElementById("caption-content");
      capText.textContent = t.text;
    }}, null, t.start);
  }});

  // Outro fade
  tl.to("#root", {{ opacity: 0, duration: 0.6, ease: "power2.in" }}, DURATION - 0.6);

  window.__timelines = {{ main: tl }};
</script>
</body>
</html>"""

with open(f'{comp_dir}/index.html', 'w') as f:
    f.write(html_template)

print(f"Daily Digest composition generated at {comp_dir}/index.html ({len(html_template)} bytes)")
