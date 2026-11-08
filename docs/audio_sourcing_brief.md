# Audio sourcing brief — can generative AI make our sounds?

Written 2026-11-08 from a cited research pass (full report in the session transcript; key sources named inline).
Today: all sound is procedural Web Audio (`slot_engine/static/canvas/audio_dark.js`): impacts, risers, roars, sub drops, ticks.

## The short answer

Yes, but **not ElevenLabs for this product**, and not the free tiers of anything.

- **ElevenLabs Sound Effects**: good tool (0.5–30 s clips, seamless-loop flag, 4 variants per prompt), but its free plan is
  non-commercial by its own terms, and its Prohibited Use Policy §2 (updated 9 Oct 2026) bars "operating or facilitating
  real-money gambling" (elevenlabs.io/use-policy). Whether an SFX supplier to a casino title counts as "facilitating" is
  undefined; without written confirmation from them it is a licence risk for a slot. Skip, or ask them in writing first.
- **Meta AudioGen, AudioLDM2, TangoFlux**: non-commercial licences. Out.
- **Stability AI Stable Audio 3.0 Small SFX / Stable Audio Open 1.0**: open weights, Community License allows commercial use
  under $1M annual revenue (stability.ai/license), trained on licensed and CC data, runs in ComfyUI with native nodes on
  the RTX 5060 (keep clips ≤ 10–20 s at fp16 on 8 GB). **This is the free generative route that is licence-clean.**
- **Adobe Firefly Generate Sound Effects**: royalty-free, licensed training data, no gambling clause found, ~$10/month.
  The cleanest hosted option if we want one.
- **Libraries as the baseline**: Sonniss GDC bundles (commercial, no attribution, games named in the licence), Freesound
  filtered to CC0 (72% of 2025 uploads), Pixabay and Mixkit (no credit needed). Zapsplat free needs a credit line.
  **BBC Sound Effects is non-commercial: never use it.**
- **Music stings**: Soundraw (games allowed on every plan) or Suno Pro ($8/month; free output stays non-commercial).

## Recommendation for The Descent

A hybrid, cheapest first:

1. **Keep procedural** what gains from being parametric and tiny: sub drops, risers, count ticks, UI, the win-ladder
   stack, and the ambient bed's LFO layer. These already pass the feel gates and weigh nothing.
2. **Record-sourced layers from Sonniss + Freesound CC0** for what synthesis does worst: water mass (surges, floods),
   metal (hull creaks, rivet pops), bubbles with body, and the creature's organic layer (a real animal growl pitched down).
3. **Stable Audio 3.0 Small SFX in ComfyUI** for bespoke one-offs we cannot find: bioluminescent shimmers, the pressure
   crush, glass fractures, a few creature vocalisations. Same prompt discipline as the art: palette words, no music.
4. **Ship** as WebM/Opus sprite sheets with an MP3 fallback through Howler.js (industry pattern); the 2–4 min ambience is
   assembled at runtime from short seamless beds, since no generator makes a seamless 4-minute loop.
5. **Provenance log per asset** (source, licence, prompt, human edits) in `docs/audio_provenance.md`: AI output has weak
   copyright in the US and EU, and the EU AI Act Art. 50 and Malta's AI charter point toward disclosure expectations.

What the studios do: Hacksaw, Push Gaming and the iGaming market hire sound designers on Reaper / Pro Tools with Wwise or
FMOD; no job ad mentions generative audio. Hand-made layering is still the norm; generation is a source, not the craft.

## Next step if approved

Install the Stable Audio 3.0 Small SFX checkpoint in ComfyUI (gated download: needs your Hugging Face login, like the
model you used for ControlNet), write `scripts/ai/comfy_sfx.py` (prompt pack → WAV → loudness-normalised Opus), generate
the first six: pressure crush, hull creak, bite impact, bubble burst, shimmer, sonar ping, and A/B them in `audio_lab.html`
against the procedural set with the dark-audio gates.
