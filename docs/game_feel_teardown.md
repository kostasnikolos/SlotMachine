# Game-Feel Teardown: Tunable Numbers for The Descent

Compiled 2026-10-28 from public sources only: rules pages, regulator documents, news and research. It covers mechanics, timings and techniques. No assets, code or art from any game were extracted or described for copying.

**Source labels:** **[REG]** regulator text. **[PUB]** published game sheet, news or research. **[RoT]** industry rule of thumb, widely observed but not formally documented. **[EST]** my own estimate for this game. Studios do not publish frame timings, so most timing numbers below are **[RoT]/[EST]** and should be confirmed against your own frame-stepped captures of demo play.

## Summary

- Regulation sets the floor. In the UK, a game cycle must last at least 2.5 s from start until the next start is possible. Turbo, quick spin, slam stop and autoplay are banned, and so is celebrating any return less than or equal to the stake. Germany sets a 5 s floor per spin. Design every timing so that the UK/DE profile is the default and other profiles are the variant.
- Premium "weight" comes mostly from three things: sound locked to animation frames, short hit-stops on impacts, and escalation that you can earn and skip. Raw spin speed matters much less.
- Cascades are where pacing lives. Hold each step at about 1 s and accelerate long chains slightly, but never compress the step that shows the win amount.

## Tunable parameters

| Parameter | Recommended default | Range | Source/label |
|---|---|---|---|
| Min game cycle (start → next start enabled) | 2.6 s (UK), 5.1 s (DE) | ≥2.5 s UK/ON; ≥5 s DE | [REG] |
| Reel kick-back (wind-up) | 80 ms, −0.15 symbol height | 50–120 ms | [RoT] |
| Reel accel to full speed | 150 ms, ease-in quad | 100–250 ms | [RoT] |
| Full spin speed | 25 symbols/s with motion blur | 15–40 | [EST] |
| Time to first reel stop | 900 ms | 600–1200 | [RoT] |
| Stagger between reel stops | 160 ms | 100–250 | [RoT] |
| Stop overshoot/bounce | 12% symbol height, 120 ms, back-out | 5–20%, 80–180 ms | [RoT] |
| Anticipation extra spin per reel | +900 ms | 600–1500 | [RoT] |
| Anticipation reel slow-down | to 40% speed | 30–60% | [EST] |
| Win highlight (per cascade step) | 450 ms | 300–700 | [EST] |
| Symbol removal/explode | 250 ms | 150–400 | [EST] |
| Drop/refill | 300 ms, ease-in + 1 small bounce | 220–450 | [EST] |
| Inter-step pause | 120 ms | 0–250 | [EST] |
| Long-chain acceleration | −8% per step after step 3, floor 70% | 0–12%, floor 60–80% | [EST] |
| Hit-stop on heavy impact | 60 ms (≈4 frames @60) | 33–100 ms | [RoT] (game-feel talks) |
| Camera shake (Leviathan strike) | 6 px amplitude, 250 ms, decay | 2–12 px | [RoT] |
| Big/Mega/Epic thresholds | 15× / 40× / 100× bet | 10–20 / 25–50 / 75–200 | [RoT] |
| Count-up duration | Big 3 s, Mega 5 s, Epic 8 s | 2–12 s | [RoT] |
| Skip available after | 500 ms | 0–1000 | [EST] |
| Feature intro (trigger → first free spin) | 4 s, skippable after 1.5 s | 3–8 s | [EST] |
| Depth level-up interstitial | 2.5 s | 1.5–4 s | [EST] |
| Return ≤ stake | No celebration; neutral tone only | — | [REG] UK |

## 1. Base spin

- **Cycle.** In the UK, the cycle runs from the player pressing start until the start control becomes available again. A bonus round triggered by the spin counts as part of the same cycle, so cascades fall inside it. https://www.gamblingcommission.gov.uk/consultation-response/online-games-design-and-reverse-withdrawals/summary-of-responses-introducing-speed-of-play-limits [REG]
- **Reel motion.** The usual pattern is a short wind-up, a quick acceleration, a steady spin with blur, then sequential stops with an overshoot and settle. Reels stop one by one to build anticipation. Speed and stop rhythm are tuned in the presentation layer and never change the RNG outcome. https://gimkit.it.com/news/how-online-reel-games-manage-speed-and-timing/ [PUB, low-authority]
- **Numbers.** A typical non-UK base spin with no win reads at about 1.6–2.2 s. That is 900 ms to the first stop, plus 4 × 160 ms of stagger, plus about 150 ms of settle. [RoT]
- **Turbo.** Where turbo is legal, it usually shortens the time to first stop to about 300 ms and the stagger to about 40 ms, or stops all reels together. One affiliate source describes turbo taking a roughly 3 s spin down to under 1 s. [PUB, weak] It is banned in the UK (RTS 14E).
- **5×5 cascade grid.** Instead of spinning reels, the Gates of Olympus and Hacksaw style is to drop the whole grid in column by column, staggered about 60–90 ms per column. That is the better fit for The Descent's ways-grid. [EST]

## 2. Cascades/tumbles

- Pragmatic's tumble removes winning symbols, refills the grid and re-evaluates it. In free spins, multipliers accumulate. https://www.pragmaticplay.com/en/games/gates-of-olympus/ [PUB]
- Nolimit's xBomb wild detonates non-winning symbols. The survivors fall and new symbols collapse into place, and each xBomb increases the multiplier. That makes it an explosion → drop → multiplier tick beat. https://europeangaming.eu/portal/latest-news/2025/12/16/198647/nolimit-city-dives-back-into-the-atlantic-in-its-latest-release-das-xboot-2wei/ [PUB]
- **One step lasts about 1.1 s:** 450 ms highlight + 250 ms explode + 300 ms drop + 120 ms pause. [EST]
- **Long chains.** Speed up the explode and drop phases only. Always keep the highlight phase and the running-total update readable, at 300 ms or more. Raise the pitch of the cascade sound about one semitone per step (cap at about 6) so the chain feels like it is climbing. [RoT]
- **Drop easing.** Use ease-in with gravity, then a 1-frame squash and a small bounce. Stagger columns by 30–50 ms so the refill reads as heavy material falling, not a UI tween. [EST]

## 3. Anticipation

- **Trigger.** Start anticipation when the player is one scatter short of a feature with reels still to land (for example, 2 scatters showing with 3 needed). Nolimit/Push Bonus symbols work the same way. [RoT]
- **Layers.**
  1. Remaining reels extend their spin, one at a time, by 0.6–1.5 s each.
  2. The reel slows to about 40%.
  3. A frame or glow appears around the reel.
  4. A rising drone or riser plays, with a heartbeat or tick.
  5. The camera pushes in 3–5%.
  6. Music ducks by −6 dB.

  [RoT/EST]
- **Use it sparingly.** A patent on reel-stop ordering notes that drawn-out reveals bore and discourage players. Reserve anticipation for real feature chances. https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8342934 [PUB]
- **UK budget.** Anticipation time counts toward the game cycle. That is fine, because it only lengthens the cycle.

## 4. Win celebration ladder

- No official cross-studio threshold standard exists in public sources. The tiers in the table (Big 15×, Mega 40×, Epic 100×) are **[RoT]**. Add a fourth "Abyssal" tier at 500× or more for The Descent. [EST]
- **Escalation per tier.** Each tier adds one layer: count-up, then music swell, then particles, then screen flash and shake, then a full-screen takeover. Count-up should ease out so that 80% of the value arrives in the first 60% of the time. Any input skips straight to the final value, then holds that value for 1 s or more. [RoT]
- **Hit-stop.** Freeze on the tier-change frame for 60–100 ms with a white flash of 2 frames or less. The "Juice it or Lose it" (Jonasson & Purho, 2012) and "Art of Screenshake" (Nijman, 2013) talks popularised these techniques. https://www.youtube.com/watch?v=Fy0aCDmgnxg , https://www.youtube.com/watch?v=AJdEqssNZ-U [PUB]
- **Losses disguised as wins (LDWs).** Research found that players' skin-conductance arousal after LDWs was similar to real wins, and that sound amplifies this response. That is the basis for the UK ban. https://uwaterloo.ca/reasoning-decision-making-lab/sites/default/files/uploads/files/DixFugetal_10c.pdf [PUB]

## 5. Feature trigger and level-up

Typical sequence, about 4 s in total and skippable after 1.5 s [EST]:

1. Scatters land.
2. Hit-stop of 80 ms.
3. Each scatter pulses in reel order at about 150 ms per scatter, with ascending tones.
4. The screen dims to about 40%.
5. A title card appears with the number of spins awarded, and the player presses to start.
6. Transition into the feature, with the music key change landing exactly on the cut.

Depth level-up (The Descent):

1. The camera dollies down in the 2.5D stage over about 2.5 s.
2. Ambience gets darker and lower-passed.
3. The new multiplier is stamped with a hit-stop.

## 6. Regulation

- **UK (UKGC RTS, in force 31 Oct 2021) [REG].**
  - RTS 14D: at least 2.5 s per cycle, and the player must release and press again to start each cycle.
  - RTS 14E: nothing may reduce the time to the result. Turbo, quick spin and slam stop are all prohibited.
  - RTS 14F: no celebration of a return less than or equal to the stake. Showing the amount and briefly showing winning lines is permitted, as is a distinct brief sound.
  - RTS 8C: no autoplay.
  - RTS 2E / 13C: show the session's net position and elapsed time.

  https://www.gamblingcommission.gov.uk/manual/online-games-design-and-reverse-withdrawals/ogdrw-annex-1-summary-of-changes-to-rts. The rules were reported in February 2021: https://sbcnews.co.uk/igaming/2021/02/02/ukgc-bans-online-slots-autoplay-and-quickspin-features/. Reports say game-design rules were extended to all online casino products from January 2025; verify this before relying on it.
- **Germany (GlüStV 2021, §22a) [PUB].**
  - At least 5 s per virtual slot spin, and no autoplay.
  - Stake cap of €1. Reports say the cap was relaxed in July 2026 to tiered €3/€5 limits, with the 5 s rule and the autoplay ban unchanged.

  https://www.gaming.net/germany-raises-the-online-slots-max-stake-per-spin-from-1-to-5-euros/. Verify against GGL.
- **Netherlands (KSA) [PUB].** Autoplay is prohibited and enforced: the KSA has sent warnings, and penalties can reach €300k. I found no public minimum cycle. https://sbcnews.co.uk/europe/2025/03/05/ksa-takes-aim-at-banned-autoplay-features/
- **Sweden [PUB].** Spelinspektionen proposed an autoplay ban in 2022. I found no spin-speed rule. https://igamingbusiness.com/legal-compliance/regulation/sweden-ban-autoplay-reverse-withdrawal/
- **Ontario / Alberta.** Both apply a 2.5 s minimum and an autoplay ban, mirroring the UK. [PUB]
- **Implication.** Build a `jurisdictionProfile` with these fields: `{minCycleMs, allowTurbo, allowSlamStop, allowAutoplay, celebrateAtOrBelowStake}`. Measure cycle time from start-press to start re-enabled, and pad the end of the cycle; do not slow the reels.

## 7. What makes Nolimit/Push feel expensive

Public interviews do not spell out frame-level methods, so this section is reviewer consensus plus established game-feel practice **[RoT/EST]**:

1. **Sound locked to frames.** Every stop, explosion and multiplier tick fires its sound on the exact contact frame (within 1 frame). Use layered transients: a sub-thump, a mid crack and a tail.
2. **Weight.** Heavy symbols overshoot less and settle faster, while light FX overshoot more. Squash on landing for 1–2 frames.
3. **Impact frames.** Freeze for 2–6 frames, flash white or additive for 1–2 frames, then shake with exponential decay.
4. **Contrast and silence.** Duck the music before big moments. A short pocket of silence makes the next hit land harder.
5. **Escalating persistence.** Multipliers and modifiers (xBomb-style) stay visible and grow, so the player can always read the current state.
6. **Character reactions.** For The Descent, the Leviathan strike gets a telegraph (about 400 ms of shadow and rumble), then a hit-stop, then the result.
7. **Restraint on losses.** Losing spins resolve quickly and quietly. That keeps intensity meaningful, and in the UK it is mandatory.

## Game-feel gate (check on 60 fps captured video)

1. Start-press to start re-enabled is 2.5 s or more on every UK-profile spin, including cascades. In a 200-spin capture, zero frames violate this.
2. No celebration sound or VFX plays on any return less than or equal to the stake. Spot-check 20 such spins.
3. Every reel or column stop and every explosion has its audio transient within ±1 frame (±17 ms) of the visual contact frame.
4. Cascade steps run 900–1300 ms each. On a chain of 6 or more, the final step is at least 70% of the duration of the first step. The win amount stays visible for 300 ms or more per step.
5. Heavy impacts (Leviathan, Wild Maw, tier changes) show a hit-stop of 3–6 frames, and camera shake decays to zero within 300 ms.
6. Win tiers trigger at the configured bet multiples. Skip responds within 2 frames and lands on the exact final value.
7. Anticipation occurs only on real near-feature states. In a 500-spin capture, its frequency equals the predicted frequency of those states.
