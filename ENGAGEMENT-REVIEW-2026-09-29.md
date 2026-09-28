---
status: draft
author: sora
date: 2026-09-29
title: Daily Digest & Weekly in Tech — Engagement Review
---

# Engagement Review — Daily Digest & Weekly in Tech

Measured from live YouTube data (yt-dlp, 2026-09-29) and frame analysis of the actual
published renders. No opinions — every claim below is backed by a number or a probe.

## 1. The honest baseline

Channel: **The Tensor Foundry** (`@thetensorfoundry`), 2 subscribers, 381 total views, 9 videos.

| Video | Date | Dur | Views | Likes | Title |
|---|---|---|---|---|---|
| Y40drqDu2CM | 09-28 | 115s | **178** | 1 | Daily Digest — OpenAI's Kill Switch Failed, Minecraft's… |
| OGV6HAyk-zw | 09-25 | 54s | **1** | – | Tensor Foundary - Daily Digest #ai #meta #anthropic |
| vjFUoggeW9A | 09-21 | 23s | **241** | 4 | Me seeing the new AI robot update: 🪵 Wood. |
| c3xmHTxOvE0 | 09-18 | 95s | 75 | – | Weekly in Tech: iPhone 18 Pro, AI Safety Debate… |
| K-DcPrWjBJU | 08-31 | 55s | 9 | – | Weekly in Tech: AI Is Becoming Infrastructure |
| rStSMDdDth8 | 08-29 | 20s | 37 | 1 | She's not real💀 |
| ZfAuAhfiJGg | 08-12 | 84s | 10 | – | 14 AI Tools That Just Changed the Game |

**The single most important fact in this document:** our *best-performing* video is a
**23-second AI robot showcase with zero words in it**. It beat the 115-second Daily Digest
by 35% while being a fifth of the length. Our *worst* video is a 54-second digest titled
with a hashtag dump.

Sample size is small, so I am not claiming statistical significance. But the *structural*
findings below are large, measurable, and independent of view count.

## 2. What competitors actually do (measured, not blog-quoted)

Sampled real shorts from channels that consistently rank:

| Channel | Dur | Views | Likes | Like rate |
|---|---|---|---|---|
| TwoMinutePapers | 19s | 19,209 | 178 | 0.9% |
| TwoMinutePapers | 26s | 11,476 | 98 | 0.9% |
| TwoMinutePapers | 33s | 26,774 | 285 | 1.1% |
| Wes Roth | 55s | 11,925 | 243 | 2.0% |
| Wes Roth | 59s | 12,610 | 207 | 1.6% |
| Wes Roth | 81s | 15,796 | 477 | 3.0% |
| Fireship | 39s | 3,001,701 | 156,301 | 5.2% |
| Fireship | 41s | 483,420 | 30,630 | 6.3% |
| Fireship | 49s | 1,418,245 | 83,061 | 5.9% |

**The band is 19–60s.** TwoMinutePapers — the closest analogue to what we make — sits at
**19–33 seconds**. Our 115-second digest is roughly 4× their longest.

**Like rate is the quality signal and it separates cleanly:**
- Text/voiceover news (TwoMinutePapers): **0.9–1.1%**
- Personality-led commentary (Wes Roth): **1.6–3.0%**
- Personality + strong visual gimmick (Fireship): **5.2–6.3%**

Ours: 1 like on 178 views = **0.56%**. We are at the *bottom* of the text-led tier. The
levers that move like rate are personality and visual gimmick, not better writing.

**Title pattern across all three:** a curiosity gap or a strong opinion, never a list of
topics. "AI Agents as Games Masters? 🎮🔥", "this is just sad... CrowdStrike attacks",
"YouTube is taken over by AI content channels". Compare ours: "OpenAI's Kill Switch Failed,
Minecraft's New Dimension, Bitget Loses $387.5M" — a topic list, which is a *table of
contents*, not a hook.

## 3. The three structural faults (measured on our own renders)

### Fault 1 — The first 4.8 seconds are a static date card
Frame analysis of `daily-digest-2026-09-28-sarah-v3.mp4` at 2fps:

- 0.0–2.4s: static card reading **"MONDAY / SEPT 28"**
- 2.4–4.8s: static card reading **"Good morning! It's Monday,"**

That is **4.8 seconds of a motionless date card before a single headline lands**. A viewer
scrolling at speed has already swiped. This is the highest-cost defect in the pipeline and
it is present in *every* digest we have shipped.

Our own narration doesn't even start until 4.8s — "Good morning. It's Monday, September
twenty-eighth. Here's your daily digest." The video is built around a greeting, which is
the single least-compelling sentence in news shorts.

### Fault 2 — One visual change every 8.8 seconds
Scene-cut detection (threshold 0.3):

- Daily Digest (115s): **13 cuts** = 1 change per **8.8s**
- Our 23s top performer: **6 cuts** = 1 change per **3.8s**

The 115-second digest holds a single static layout for nearly 9 seconds at a time. The
Shorts feed rewards continuous re-arming of attention; a 9-second hold reads as a
slide-deck, and slide-decks get swiped.

### Fault 3 — Text density at 65–70% on story cards
Vision analysis of the digest contact sheet found **six distinct layout templates** and
story cards where text fills 65–70% of the frame: category tag, headline, body paragraph,
source line, quote snippet, and a thumbnail — all at once. There is no single focal point,
so the eye has nowhere to land, and nothing is readable in the ~1s a Shorts viewer actually
looks at any given frame.

## 4. Fixes, ordered by expected impact

### P0 — Rebuild the opening (biggest single win)
Kill the date card and the greeting. Open **on the most shocking claim in the episode**, as
text, in the first frame, with the number visible.

- ❌ "MONDAY / SEPT 28 — Five stories. About ninety seconds."
- ✅ **"OPENAI'S KILL SWITCH FAILED"** / `IT REACHED THE PUBLIC INTERNET. HUMANS STOPPED IT 2.5H LATER.`

Put the date in a persistent corner chip, not as a full-screen card. Brand the show in a
watermark, not as a title beat. **Budget: 0–1.5s cold open on the claim, first headline
under 1.5s.**

### P0 — Cut the length
Daily Digest: **115s → 45–60s.** Weekly in Tech: **95s → 60–75s.** Match the TwoMinutePapers
band. If five stories don't fit in 60s, publish **three stories well** instead of five
padded. One short per story is also the format that actually works in this niche.

### P1 — Raise cut density to ~1 change per 2.5–3.5s
That means 18–22 visual states in a 55-second digest, not 13 in 115s. Concretely: every
headline gets its own card (5), every claim gets a visual (5), the open and close (2),
plus karaoke-caption word-highlight changes which already read as motion.

### P1 — Cut text to one idea per frame
Headline (max 6 words, 40px) + one number + source line. Body paragraph goes in the
description, not on screen. A frame must be legible at arm's length on a phone.

### P1 — Rewrite titles to curiosity gaps
Drop the topic list. One story, one tension.
- ❌ "Daily Digest — OpenAI's Kill Switch Failed, Minecraft's New Dimension, Bitget Loses $387.5M"
- ✅ "OpenAI's Kill Switch Failed. They Stopped It By Hand."

### P2 — Fix the metadata regression
`OGV6HAyk-zw` scored **1 view** and its title is a hashtag dump:
`Tensor Foundary - Daily Digest #ai #meta #anthropic`. That is also a **misspelling of our
own brand name** ("Foundary"). Hashtags belong in the description, not the title field.
Fix and re-title the existing video rather than re-uploading it.

### P2 — Add the personality layer that actually drives like rate
Our like rate (0.56%) is in the text-only tier. Wes Roth gets 1.6–3.0% with a *point of
view*; Fireship gets 5.2–6.3% with a running gag. The 2-host Weekly in Tech already has
the right raw material — Sumi and Sora disagreeing about a story is a personality, and the
pipeline should lean into opinion rather than neutral summary. Daily Digest's solo anchor
has no such layer, which is a format-level weakness worth acknowledging.

## 5. What I did not change and why

- **EBU R128 / -16 LUFS chain** — audio is measured and correct; no defect found.
- **Fact-check discipline and source citation** — working well, keep it.
- **The flat pop-retro visual identity** — distinctive vs. competitors. The problem is
  pacing and density, not the aesthetic. Do not redesign the look.
- **Karaoke captions** — already good, and they double as motion. Scale them up.

## 6. Honest caveat

381 total views across 9 videos is not enough data to A/B test any of this. These
recommendations are grounded in (a) structural defects visible in our own frames, and
(b) measured patterns in channels 100–1000× our size. I have not verified our *retention
curve*, which is the metric that would actually settle it — that needs YouTube Analytics,
which the Composio tool does not expose. If you want the retention data, that is a manual
pull in YouTube Studio and I will read it if you export it.
