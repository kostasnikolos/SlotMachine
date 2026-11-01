# Feel design plan — Leviathan presence, dark audio, big-win ladder

Scope: the canvas front end (`slot_engine/static/canvas/index.html`). Research summary 2026-11-01; studios publish no numbers, so the recipes below are our design, informed by how Nolimit / Push / Print Studios are described (rationed creature, stillness + sound carry the threat, escalation toward a finale).

## A. Leviathan presence (make it alive, not a prop)

Today: a procedural spine on a drifting path; `reveal` rises on a slow sine + surge. No eyes/attention, no body breathing, no reaction to game state, no silence before strikes.

| # | Change | Where | Effort |
| --- | --- | --- | --- |
| 1 | **Ration it**: fully visible <15% of base-game time; otherwise a silhouette in fog. 1.5–3s audio drop-out before any strike. | `levUpdate` reveal curve, `strikeSeq` | S |
| 2 | **Look-at**: head yaw/pitch slerps toward the active cascade column or the cursor (300–600ms lag); on a near-miss it snaps to the missing cell and holds. | `levPath` heading, new `attention` target | M |
| 3 | **Breathing**: vertex displacement along normals `0.015·sin(t·0.6)+0.004·sin(t·2.3)`; period 8–12s idle, 3–4s when agitated (anticipation). | Leviathan vertex shader | S |
| 4 | **Spring-chain tendrils/fins**: 6–10 segments, stiffness 40–80, damping 6–10, driven by head velocity. The biggest "alive" signal. | new secondary motion pass | M |
| 5 | **Bioluminescence pulse** = emissive × audio low band (AnalyserNode 40–120Hz) → eyes/lure pulse on every thump. | `levUpdate` uniforms + audio analyser | S |
| 6 | **Reaction shots**: loss streak ≥5 → an eye opens close to the glass 1.2s then recedes; win ≥10× → recoil 400ms then lunge. | `spin()` outcome hooks | S |
| 7 | **Glass-proximity refraction**: when near the glass, UV wobble (0.004–0.01) on the symbol layer instead of material transmission (perf). | symbol shader uniform | M |
| 8 | **Dithered depth fog + grade**: density 0.08–0.15 keyed to level; blue-noise dither; teal → black-green per level. | `BG_FS` / post | S |
| 9 | **Camera**: 2–4% push-in over 600ms during anticipation; slow 0.5°/s idle orbit. | render loop | S |

## B. Dark procedural audio (kill the bubbles)

Today: `A.win` and `A.dissolve` are bubble clouds (Minnaert sines); `A.thump` is a soft triangle drop. Keep the bubble synth for ambience only.

Bus: dry → `ConvolverNode` (IR = 2.5–4s decaying noise, lowpass 4kHz→800Hz over its length, 20ms fade-in) at −12dB send; master `DynamicsCompressor` (−18dB, 4:1, 3ms, 250ms); ambience ducked −9dB in 20ms / back in 600ms on every impact.

| Event | Recipe |
| --- | --- |
| Symbol dissolve | noise burst 60–90ms, bandpass 900→250Hz over 80ms (Q3) + sine 110→55Hz over 120ms. No tonal ding. |
| Cascade landing | sub sine 70→38Hz / 200ms + lowpassed noise 400Hz / 120ms + FM metal (carrier 180Hz, mod 311Hz, index 4→0 / 150ms). Each later cascade −2 semitones, +10% reverb. |
| Wild Maw impact | 40ms silence → 8ms click (noise HP 2kHz) → noise body 500ms LP 3kHz→150Hz → sub 55→28Hz / 600ms → brown rumble 1.5s LP 90Hz. |
| Leviathan strike | 1.5s riser (pink noise BP 200→2.5kHz, Q6) → 300ms total silence → Maw impact +6dB + ring-mod growl (saw 45Hz × sine 31Hz, 900ms, LP 600Hz). |
| Level-up | per-depth drone D1 36.7 → 32.7 → 29.1 → 24.5Hz adding a 1.5× partial per level; transition = 2s glide 110→36Hz under a 600ms noise exhale; ambience LP 1.2kHz→500Hz per level. |
| Big-win tiers | never major-key. T1 sub pulse 45Hz/500ms; T2 + FM bell cluster (1:1.41) 3s reverb; T3 + riser loops + detuned-saw "choir" through 300–900Hz formants; T4 500ms silence then full stack. Count ticks = noise clicks 400→1200Hz. |

Rule: no win audio/presentation when the return ≤ stake (already enforced under ukgc; apply everywhere).

## C. Escalating big-win screens ("more creatures as the win grows")

Uses the existing `bw3d`/`bwfx` layers and the 15/40/100/500× ladder. Tier changes mid-count never restart the count.

| Tier | Name | Duration | Picture | Audio |
| --- | --- | --- | --- | --- |
| T1 15× | Disturbance | 3s | vignette −10%, fog +20%, 2–3 far silhouettes drift past; ticks every 60ms | sub pulse |
| T2 40× | Eyes | 5s | vignette −25%, grade cools, 6–10 bioluminescent eye pairs open 150ms apart and track the number; particles ×2; slam-skip after 1s | + FM bells |
| T3 100× | Breach | 8s | 40% darker except the number, camera push 6%, 3–4 mid creatures lunge at the glass with refraction wobble; count-up with two stutter-stops; number 1.0→1.25 + cracked-glass text | + riser + choir |
| T4 500× | Leviathan | 12s | 500ms blackout + silence, then the Leviathan fills the frame, mouth open behind the number, glass cracks propagate, fog max, 8px shake 300ms; final slam 1.5× | full stack, 3s tail |

Background luminance 0.9 → 0.75 → 0.6 → 0.1; particle density 1/2/4/8×.

## Suggested order
1. **B (audio)** first: smallest change, biggest felt difference, and the Leviathan/bw work syncs to it (bioluminescence pulse, impacts).
2. **A1–A6** (ration, look-at, breathing, tendrils, pulse, reactions).
3. **C** the four-tier screens.
Gate: the G8 feel checks must stay PASS; A/B judged by eye/ear against the canvas with a reviewer pass each.
