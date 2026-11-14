# Sound design target — the help, the seam breach, the symbol voices (round 2)

Status: **rendered and measured, not heard.** Everything below was designed by layer and frequency band and verified on
meters (peak, RMS, band energy, spectrograms). Nobody has listened to it. The last section lists what only an ear can
settle. Since round 3 the cues are wired into the game by `slot_engine/static/canvas/audio_moments.js`, from clips cut by
`scripts/ai/assetgen/sfx_pack.py`; section 1 says what lines up with the game's timings and what does not.

- Generator: `scripts/ai/assetgen/moments.py` (numpy + Pillow only; `python scripts/ai/assetgen/moments.py --sheet`, about 6 s)
- Output: `generated/sfx/moments/` (git-ignored): 79 WAVs (48 kHz, 16-bit, mono), `manifest.json` (source, licence,
  sha256 and measurements per file), `report.json` (the help and win checks)
- Sheets: `artifacts/targets/sound_help_sheet.png` (full), `sound_help_short_sheet.png`, `sound_win_sheet.png`, `sound_symbols_sheet.png`
- Determinism: two renders in separate processes, 79 WAVs + both JSON files byte-identical
  (`help_full_mix.wav` sha256 `a18e20999d3cda7049b0f9fe763913f9fdee28c5e7e242541418ccb0f78df4c0`). Seeds come from SHA-256 of each sound's name;
  depth and cue length do not change a seed. Verified on one machine only.

## 0. What changed in round 2 (`docs/targets/review_round1.md`, fix item 15, and the timing decision)

| # | Asked | Done | Measured |
| --- | --- | --- | --- |
| 1 | Re-time the help: a 3.1 s FULL and a 1.7 s SHORT, transformation straight after the impact, the creature receding underneath | `BEATS_FULL` and `BEATS_SHORT`; `help_full_*` and `help_short_*` (six stems + `_mix` each). H2 is now TARGETING (pupil lock, churn over the cell, glass bowing), not a hull creak. The recede runs under H4 and the drain starts at H5. The old code-timing and 2.4 s storyboard renders are dropped. | section 2 |
| 2 | Phone speakers: body and transient for APEX / WILD, a dread layer above 300 Hz, a 200 Hz-4 kHz check | APEX and WILD rebuilt around a 150-400 Hz body and a mid-band knock; the dread carries a bowed-metal layer at 294 Hz-1.2 kHz. The check is in `report.json` and on the help sheets. It also showed something the review did not ask about: in that band the impact was *quieter* than three other beats. Rebalanced so it leads. | APEX / WILD sub share 91-95 % -> 16-23 %; no beat flagged at depth 2; the impact leads the next beat by 3.1 dB (full), 3.0 dB (short) |
| 3 | Transformation rises and resolves; the last cell has weight | Cells climb the minor scale by step (B6, C#7, D7) and the last lands a fifth above the first, doubled a fifth below itself (an open fifth: resolved, neither major nor minor), 1.7x the ring, +4 dB, on a low-mid "seat" thud. Still inharmonic glass with a 6 ms soft onset. | still > 99.99 % above 1.5 kHz |
| 4 | Win: the weight on W2; water under pressure, no zap | The jet is the loudest stem at every step. It is now a broadband slap + a 420 Hz body + a short low push, broad spray per column, then run-off that keeps falling under the implosion. The swept whine and the fast narrow sweeps (the "zap") are gone. The implosion is lighter. | jet vs implode peak: -3.1 / -8.4 (step 1), -1.7 / -6.0 dBFS (step 5); W2 RMS 2.8-3.5 dB over W3 |
| 5 | Stones differ a little; 3 round-robin lands each | Each stone has its own partial spacing, damping, grit band and one detail (dry, double knock, ringing second partial, scrape, slab with an octave-down partial). Every symbol has `_land_v1..v3` (own seed, 0 / +0.6 / -0.7 semitones, 0 / -1.2 / -0.6 dB). | land centroids 444 / 402 / 456 / 319 / 248 Hz (were 398 / 347 / 307 / 300 / 263) |
| 6 | Sheets, doc, determinism | Four sheets rebuilt, this document rewritten, 80 files byte-identical across two processes | above |

Not asked, changed anyway: every symbol file now starts with 5 ms of silence so the fade cannot eat its transient (two
viper takes failed the fade check without it); both help mixes fade over their last 200 ms so nothing is cut off ringing.

## 0b. Round 3 (`docs/targets/review_round2.md`): the loudness ladder is now set in the band a phone plays

The symbol voices used to be levelled by peak, which let a sub-heavy APEX stinger sit under two HIGH stingers at
200 Hz-4 kHz. Level is now set by **RMS in 200 Hz-4 kHz**, 2 dB a tier (`MID_TARGET`, `to_ladder()` in `moments.py`).
Peaks follow from that and all stay at or below -1.5 dBFS.

| Tier | Lands (three takes each), lowest to highest | Step up to the next tier | Stingers | Step up to the next tier |
| --- | --- | --- | --- | --- |
| LOW stone | -27.5 to -27.0 | +1.5 dB | -25.0 | +2.0 dB |
| MID brass | -25.5 to -25.0 | +1.5 dB | -23.0 | +2.0 dB |
| HIGH living | -23.5 to -23.0 | +1.5 dB | -21.0 | +2.0 dB |
| APEX | -21.5 to -21.0 | +1.5 dB | -19.0 | +2.0 dB |
| WILD | -19.5 to -19.0 | top | -17.0 | top |

- Every step is at least 1.5 dB (lands, counting all three takes: the takes now differ by 0 / -0.5 / -0.3 dB instead
  of 0 / -1.2 / -0.6) and exactly 2.0 dB between stingers. `report.json` carries this table as `symbol_ladder`.
- No recipe was changed and no voice needed its mid band re-weighted. Two click-heavy voices could not reach their rung
  under the peak limit by gain alone, so their tallest peaks are folded on a soft knee: `sym_high_viper_stinger` (2.6 dB), `sym_wild_maw_stinger` (2.0 dB). Everything else is
  gain only.
- The price: the ladder holds in that band, not in full-band peak. The viper's lands peak at -2.0 to -2.5 dBFS (its
  click is mostly above 4 kHz), higher than the APEX lands' -5.4 to -7.5. The stones are now 3-6 dB quieter than in round 2.
- The help and win files were byte-identical to round 2 at that point (the help changed again in round 4, section 1).
- **The game is still playing the round-2 symbol clips** until `python scripts/ai/assetgen/sfx_pack.py` is re-run: it
  writes under `slot_engine/static/canvas/assets/sfx/`, which this task may not touch.

## 1. Timings

### The help: target beats (the engine is being re-timed to these)

| Beat | FULL (3.1 s, first time) | SHORT (1.7 s, repeats, xBet) | Stem that starts here |
| --- | --- | --- | --- |
| H1 dread | 0-900 | 0-350 | `dread` (runs to the dip) |
| H2 targeting | 900-1500 | 350-700 | `targeting` |
| dip | 1420-1500 (80 ms) | 640-700 (60 ms) | `vacuum`: suction from 1280 / 500, then silence |
| H3 impact | 1500 | 700 | `impact` |
| H4 transformation | 1700, 1810, 1920, 2030 (bite + 200 ms, four cells, 110 ms apart: the game's offsets) | 850, 920, 990, 1060 (bite + 150 ms, 70 ms apart) | `transform`; `aftermath` (recede) from 1760 / 910 |
| H5 aftermath | 2300-3100 | 1250-1700 | drain inside `aftermath` |

Four cells is an assumption (`cells=4` in the beat table). The hit-stop is treated as picture only: the sound does not stop.

### The help: what the game does now, and what no longer lines up

Read from `slot_engine/static/canvas/index.html` (`strikePace`, `levPreStrike`, `strikeSeq`; the file was being edited
while this was written, so no line numbers), `audio_moments.js` and `sfx_pack.py`.

| | Game, FULL | Stems, FULL | Game, SHORT | Stems, SHORT | Lines up? |
| --- | --- | --- | --- | --- | --- |
| Lead starts | start of the hush (`helpLead` in `levPreStrike`) | 0 | same | 0 | yes |
| Lunge starts (H2) | 900 ms | targeting at 900 | 350 ms | targeting at 350 | yes |
| Dip | lead clip is cut at 1500 ms; its last 80 ms are silent | 1420-1500 | cut at 700 ms; last 60 ms silent | 640-700 | yes |
| Bite (`helpImpact`, on the hit-stop line) | hush 900 + lunge 600 = 1500 ms, clock-gated | 1500 | 350 + 350 = 700 ms | 700 | yes on a healthy frame rate; a late bite lengthens the dip |
| First cell (`cellTurn`) | bite + 200 ms | bite + 200 | bite + 150 ms | bite + 150 | yes since round 4 |
| Cell spacing | 110 ms (**70** at level 4-5) | 110 | 70 ms | 70 | yes, except full at levels 4-5 (mix only) |
| Recede (`helpRecede`) | bite + 260 ms (`turn` + 60) | bite + 260 | bite + 210 ms | bite + 210 | yes since round 4 |
| Sequence ends | last cell + 600 ms | 1600 ms after the bite | last cell + 300 ms | 1000 ms after the bite | **no**, see 3 |

1. **Fixed in round 4:** the mixes and both help sheets now lay the cells out at the game's offsets (bite + 200 ms and
   110 ms apart, full; bite + 150 ms and 70 ms apart, short), so they describe what plays for a four-cell strike.
2. **Fixed in round 4:** the seat thud is out of the `aftermath` stem and lives only in the `help_cell_last` clips, so
   it plays once. The mixes and sheets therefore do not contain the seat at all.
3. **Partly fixed in round 4:** `help_cell_last_short` (700 ms) exists for the short version, so its ring ends about
   0.4 s after the short sequence does instead of 1.3 s. It is not used until the packer and `cellTurn` pick it up.
   The full version's last cell (1583 ms) still rings about 1.0 s past the end of the full sequence.
4. **A one-cell strike never gets the weighted cell.** `cellTurn` plays `help_cell_last` only when `n > 1`.
5. **The drain inside the recede clip** starts 540 ms into it (full) and 340 ms (short): bite + 800 / + 550 ms in the
   game. That is after the last of four cells in both versions, but it does not move with the cell count.
6. **The bed duck under the bite is -24 dB**, not the -60 dB the dip was designed around, and nothing ducks the bed
   during the dip itself (the hush holds it at -12 dB). The dip will be audible as "quieter", not as a hole.
7. **`symLand` keeps the first land inside any 60 ms window, not the most valuable one**, so when a Wild and a stone
   land together the stone can win. The ladder above is only heard when the valuable symbol is first.
8. Clip gains in the runtime are uniform within a kind (lands -3 dB, stingers -2 dB, master trim -8 dB), so the ladder
   survives them.

Before the re-time the bite sat at 1700 ms and the cells at 3060 ms; that description is in git history (round 2 of
this file).

### The win: `WIN_EVALUATION` (`index.html:1925`) then `CASCADE_DROP` (`:1990`) — unchanged, the cue follows the code

Crack `prog` 0 -> 1 in 240 ms (`engSeam` `:1936`, `:4547`); jets from 240 ms, one per winning column, 20 ms apart,
340 ms each (`:4588`); highlight held to 750 ms (`feel.js:22`, `:1960`); then `engDissolve(..., implode)` `:1999`,
`engSeamScar()` `:2000`, `aud.fizz()` `:2001` over `explodeMs` 480 ms x `chainFactor` (1.0 for steps 1-3, 0.84 at 5);
`aud.absorb()` `:2003`; lands via `onLand` (`:4112`, `aud.land()` `:4406`). So **W1 0-240, W2 240-750, W3 750-1230**,
not the sheet's 0-150 / 150-500 / 500-900.

## 2. The help cue

Six stems that sum to the mix (one shared gain; measured error 2 LSB of 16-bit rounding). Each stem is padded to the
cue length; `beat_offset_s` in the manifest says where it really starts.

| Stem | Intention | Layers and bands |
| --- | --- | --- |
| `dread` | The eye opens; you feel it and, on a phone, still hear it. | Sub swell 36 + 37.4 Hz. Eye: 147 + 156 Hz minor second. **New:** bowed metal at 294, 311, 587, 810 and 1195 Hz, each partial breathing at its own rate (1.7-5.3 Hz); lid noise band-pass opening 300 -> 1300 Hz. Cut dead at the dip. |
| `targeting` | The pupil locks on, the water over the cell churns, the glass bows. | Lock: a 3 ms click and a damped 620 / 930 / 1480 Hz knock at the first frame. Churn: pink noise band-pass 350 -> 1400 Hz under a slow random (not periodic) level curve, rising. Glass: a saw 196 -> 262 Hz through a Q12 band-pass climbing 700 -> 1500 Hz, stick-slip gaps 120 ms apart closing to 30 ms, a 1.8-3.2 kHz glass tick on each. A 55 -> 98 Hz groan under it. |
| `vacuum` | The breath in. | Up to 140 ms of suction (high-pass 600 Hz -> 7 kHz, plus a 70 -> 210 Hz rising tone), then the dip. Pre-impact stems are gated shut across it; the file is digitally silent there. |
| `impact` | The sea comes in. | 8 ms click; sub 64 -> 30 Hz; punch 125 -> 46 Hz; **new:** a 520 Hz slap (200 ms) for small speakers; water closing 5.2 kHz -> 170 Hz in **350 ms** (was 500) so the transformation has clear air; rumble under 110 Hz; plates at 187 / 311 / 523 / 742 / 1180 Hz; throat (saw 45 x sine 31 Hz). |
| `transform` | Relief turning into appetite: cold glass that climbs and lands. | Per cell: glass-bar partials 1 : 2.756 : 5.404 with a beating twin, 6 ms soft onset, a breath of frost above 5-6 kHz. Cells 1-3 at 1976, 2217, 2349 Hz; the last at 2960 Hz doubled at 1976 Hz, 1.7x as long, +4 dB. High-passed at 1.5 kHz (6th order). |
| `aftermath` | It goes down under the transformation; then the water leaves. | From the recede: tone falling 84 -> 33 Hz, its throat, and a moan four and six times higher (roughly 330 -> 130 Hz and up) that a phone can carry. From H5: drain, pink noise band-pass falling 1500 -> 260 Hz with a turbulent level, no bubbles; plates still ringing. |

Pitches are as written, at depth 0. The default render is depth 2, one semitone lower on everything but the transformation.

### Measured, FULL (depth 2)

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz | 200 Hz-4 kHz share | 200 Hz-4 kHz RMS dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `help_full_dread.wav` | 3.10 | -12.6 | -27.9 | 366 | 15.0% | 67.5% | -29.6 |
| `help_full_targeting.wav` | 3.10 | -11.8 | -34.3 | 1116 | 2.0% | 93.8% | -34.6 |
| `help_full_vacuum.wav` | 3.10 | -14.6 | -42.4 | 2248 | 0.1% | 6.6% | -54.2 |
| `help_full_impact.wav` | 3.10 | -1.5 | -17.3 | 119 | 84.8% | 5.1% | -30.3 |
| `help_full_transform.wav` | 3.10 | -11.3 | -28.6 | 2788 | 0.0% | 95.6% | -28.7 |
| `help_full_aftermath.wav` | 3.10 | -15.2 | -31.9 | 572 | 26.4% | 70.9% | -33.4 |
| `help_full_mix.wav` | 3.10 | -1.5 | -16.4 | 335 | 71.8% | 17.8% | -23.9 |

### Measured, SHORT (depth 2)

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz | 200 Hz-4 kHz share | 200 Hz-4 kHz RMS dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `help_short_dread.wav` | 1.70 | -12.7 | -28.6 | 343 | 12.9% | 63.0% | -30.7 |
| `help_short_targeting.wav` | 1.70 | -12.4 | -33.4 | 1094 | 1.5% | 93.7% | -33.7 |
| `help_short_vacuum.wav` | 1.70 | -14.6 | -39.8 | 2248 | 0.1% | 6.6% | -51.6 |
| `help_short_impact.wav` | 1.70 | -1.5 | -14.9 | 122 | 85.5% | 5.1% | -27.8 |
| `help_short_transform.wav` | 1.70 | -10.6 | -29.2 | 2836 | 0.0% | 93.5% | -29.5 |
| `help_short_aftermath.wav` | 1.70 | -13.9 | -31.7 | 464 | 33.0% | 64.2% | -33.6 |
| `help_short_mix.wav` | 1.70 | -1.5 | -14.5 | 249 | 76.6% | 13.4% | -23.2 |

Also rendered: the depth ladder's two ends (full mix only) and the per-cell one-shots the game fires. Both last-cell
clips carry the seat thud (no stem does); `help_cell_last_short` is the same voice with a 0.75x ring, cut to 700 ms,
for the short version.

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz | 200 Hz-4 kHz share | 200 Hz-4 kHz RMS dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `help_full_mix_d0.wav` | 3.10 | -1.5 | -20.0 | 433 | 74.6% | 17.1% | -27.6 |
| `help_full_mix_d5.wav` | 3.10 | -1.5 | -14.9 | 331 | 69.8% | 17.1% | -22.5 |
| `help_cell.wav` | 1.03 | -10.0 | -27.4 | 2309 | 0.0% | 92.7% | -27.7 |
| `help_cell_last.wav` | 1.58 | -6.0 | -24.7 | 2528 | 0.1% | 88.1% | -25.3 |
| `help_cell_last_short.wav` | 0.70 | -6.0 | -24.4 | 2200 | 0.1% | 77.3% | -25.5 |

### Small-speaker check: 200 Hz-4 kHz RMS per beat window (dBFS), and the distance to the impact

A beat is flagged when it is more than 12 dB under the impact in this band (the dip is exempt). Each window is
filtered on its own, so nothing leaks across a beat line. The impact window is impact -> first cell, which since round 4
is the game's own 200 ms (full) and 150 ms (short).

| Render | H1 dread | H2 targeting | H3 impact | H4 transformation | H5 aftermath | Flagged | Impact lead |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FULL, depth 2 | -29.1 (-8.2) | -21.9 (-1.0) | -20.9 (+0.0) | -22.9 (-2.1) | -23.8 (-2.9) | none | +1.0 dB |
| SHORT, depth 2 | -29.5 (-9.6) | -21.9 (-2.0) | -19.9 (+0.0) | -21.7 (-1.8) | -24.1 (-4.3) | none | +1.8 dB |
| FULL, depth 0 | -33.2 (-11.1) | -26.0 (-3.8) | -22.1 (+0.0) | -27.0 (-4.8) | -28.2 (-6.1) | none | +3.8 dB |
| FULL, depth 5 | -28.8 (-7.6) | -22.3 (-1.2) | -21.1 (+0.0) | -20.8 (+0.4) | -20.8 (+0.3) | none | -0.4 dB |

- No beat is flagged in any of the four renders.
- **The impact's lead has shrunk to 1.0 dB (full) and 1.8 dB (short), and at depth 5 it is gone (-0.4 dB).** The audio
  of the hit did not change in round 4; its window did (it was 80 / 70 ms, an average over the first transient, and is
  now 200 / 150 ms of a decaying hit). So on this meter the impact is the loudest beat in the phone band by a small
  margin at best. Its first 80 ms still measure about 3 dB over everything else (round 2 and 3 figures).
- This is a band-limited meter, not a phone. It says the energy exists at 200 Hz-4 kHz; it does not say it sounds good.

### Engineering targets

| Render | Mix peak dBFS | Sub 30-80 Hz peak (50 ms RMS) | vs anything before the dip | vs every other stem | vs the cue 0.9 s later | Dip | Transform vs rest above 1.5 kHz | Stems-sum error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FULL, depth 2 | -1.50 | -7.9 dBFS at 1.695 s | +18.5 dB | +18.0 dB | +11.2 dB | 80 ms, silent (before: -19.0 dBFS) | +11.6 dB | 2 LSB |
| SHORT, depth 2 | -1.50 | -8.0 dBFS at 0.895 s | +19.0 dB | +19.5 dB | +24.0 dB | 60 ms, silent (before: -19.8 dBFS) | +9.8 dB | 2 LSB |
| FULL, depth 0 | -1.50 | -10.8 dBFS at 1.725 s | +19.0 dB | +19.9 dB | +13.6 dB | 80 ms, silent (before: -23.0 dBFS) | +12.1 dB | 2 LSB |
| FULL, depth 5 | -1.50 | -7.1 dBFS at 1.645 s | +24.1 dB | +19.3 dB | +6.6 dB | 80 ms, silent (before: -19.2 dBFS) | +11.0 dB | 2 LSB |

- **Peak <= -1 dBFS:** all 79 files and both summed cues peak at or below -1.5 dBFS. Sample peak, not true peak.
- **No DC:** worst |mean| 0.00024 (7.8 LSB, on a stinger whose peaks were folded in round 3; 0.00001 on everything else). **Fades:** every file starts and ends at zero inside a linear 4 ms ramp to its own
  peak. The generator exits non-zero if any file misses peak, DC or fade.
- **Impact sub is the strongest moment:** the 30-80 Hz peak is inside the impact window in all four renders, about 18 dB
  or more above anything before the dip and above every other stem. At depth 5 the impact's own tail is only 6.3 dB down
  0.9 s later (longer ring, heavier drive).
- **Transformation above 1.5 kHz:** more than 99.99 % of its energy. In its window it is 11.6 dB (full) and 9.8 dB
  (short) above the rest of the mix above 1.5 kHz, with the cells at the game's offsets. The review expected 5.6 dB once it moved onto the impact's tail;
  closing the water in 350 ms bought the difference, without ducking anything.
- **The dip:** 80 ms (full) and 60 ms (short) of digital silence in the file, against -19 dBFS RMS just before it. In
  the game the bed and any reverb tail will fill it unless the bed is ducked (section 5).

### Depth 0-5

One argument (`Depth`, `--depth`), applied to every sound here: body pitch -0.5 semitone per level; tanh drive
1 + 0.2 per level (none at 0); top-end low-pass 16 kHz x 0.82 per level (5.9 kHz at 5); sub weight +7 % per level; room
+0.03 wet per level; ring length +6 % per level. The transformation is never driven and never sinks in pitch; it gains a
61 Hz ring-modulation (7 % per level) and so turns rough, never warm. Measured on the full mix: RMS -20.0 dBFS at depth
0, -16.3 at 2, -15.0 at 5 at the same peak; transformation centroid 3310 -> 2789 -> 2650 Hz.

## 3. The win seam cue

Intention: water under pressure breaching toward the viewer, then running off. The weight is on W2.

| Stem | Intention | Layers and bands | At (code) |
| --- | --- | --- | --- |
| `crack` | A hairline runs through the winning cells. | 8-20 dry fracture clicks above ~3 kHz, sparse then crowding; a tiny damped glass ping (2.2-4.5 kHz, 8 ms) on each; one low tick 160 -> 110 Hz. Nothing sweeps. | 0-240 ms |
| `jet` | The seam tears and the water comes through, at us; then it runs off. | Tear click; a broadband slap closing 7 kHz -> 1.4 kHz in 140 ms; the body of the water at 420 Hz (160 ms); a short push 105 -> 60 Hz; 3-7 broad needles of spray (Q 0.8, 2.6 kHz easing to 1.8 kHz, 20 ms apart, 340 ms each); run-off: pink noise, low-pass falling 3.6 kHz -> 500 Hz under a turbulent level, lasting 0.86-1.18 s, so it is still falling under the implosion. | 240 ms onward |
| `implode` | The symbols are pulled inward; the seam stays as a scar. | 70 ms suction; a short crush (sub 110 -> 46 Hz, a dull crunch 900 -> 250 Hz, brass dust at 420 / 660 / 990 Hz); scar hum at 73 / 147 / 156 / 220 / 294 Hz for 0.9-1.7 s. Deliberately the lighter half. | 750 ms, crush at 820 ms |

Cascade step 1..5: pitch drops 1.5 semitones a step (the spray one semitone); clicks 8 -> 20, needles 3 -> 7, more water
and more push; run-off and scar hum lengthen; reverb send rises. One gain is shared across the ladder (set by step 5).
The ladder still goes *down* in pitch as the chain grows; the review questioned that and it is left for a listen
(section 6).

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz | 200 Hz-4 kHz share | 200 Hz-4 kHz RMS dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `win_s1_crack.wav` | 2.17 | -9.2 | -38.2 | 4750 | 0.2% | 39.7% | -42.2 |
| `win_s1_jet.wav` | 2.17 | -3.1 | -19.8 | 553 | 29.2% | 20.9% | -26.6 |
| `win_s1_implode.wav` | 2.17 | -8.4 | -25.4 | 100 | 59.1% | 4.3% | -39.1 |
| `win_s1_full.wav` | 2.17 | -3.2 | -18.7 | 500 | 35.1% | 17.6% | -26.2 |
| `win_s3_crack.wav` | 2.57 | -7.5 | -35.7 | 4377 | 0.5% | 49.4% | -38.8 |
| `win_s3_jet.wav` | 2.57 | -2.2 | -17.9 | 436 | 64.5% | 21.4% | -24.6 |
| `win_s3_implode.wav` | 2.57 | -6.3 | -23.7 | 85 | 79.9% | 4.1% | -37.5 |
| `win_s3_full.wav` | 2.57 | -2.2 | -16.9 | 415 | 66.3% | 18.1% | -24.3 |
| `win_s5_crack.wav` | 2.97 | -6.5 | -34.6 | 3869 | 2.1% | 50.4% | -37.6 |
| `win_s5_jet.wav` | 2.97 | -1.7 | -16.6 | 356 | 71.3% | 19.4% | -23.7 |
| `win_s5_implode.wav` | 2.97 | -6.0 | -22.1 | 78 | 77.0% | 3.8% | -36.4 |
| `win_s5_full.wav` | 2.97 | -1.5 | -15.5 | 342 | 71.3% | 16.8% | -23.3 |

Where the weight sits (mix RMS in the W2 window 240-750 ms and the W3 window 750-1230 ms):

| Step | Crack peak | Jet peak | Implode peak | Loudest stem | W2 RMS | W3 RMS |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -9.2 | -3.1 | -8.4 | jet | -14.2 | -17.7 |
| 3 | -7.5 | -2.2 | -6.3 | jet | -11.7 | -15.2 |
| 5 | -6.5 | -1.7 | -6.0 | jet | -10.0 | -12.8 |

## 4. Symbol voices

One family, by construction: every land sits on the same short pressure thud (80 -> 44 Hz, 90 ms, scaled by tier); every
pitch is from D minor, with the flat second reserved for the creature; every stinger bends downward at the end;
everything is in the same 0.55 s steel room. Worth more means lower, heavier and louder, where
"louder" is RMS in 200 Hz-4 kHz (land / stinger: LOW -27 / -25, MID -25 / -23, HIGH -23 / -21, APEX -21 / -19,
WILD -19 / -17 dBFS; section 0b).

| Symbol | Land (three takes, <= 250 ms) | Win stinger (<= 700 ms) |
| --- | --- | --- |
| LOW 10 (A4) | Smallest pebble: partials 1 : 1.58 : 2.21 : 3.31, shortest damping (x0.75), grit at 2.6 kHz, lightest thud. | Knock, 170 ms of stone dragged on stone, a heavier knock a fourth lower with a dull ring that sinks (same shape for all five, each with its own knock). |
| LOW J (G4) | 1 : 1.47 : 2.09 : 3.10, grit 2.1 kHz, a **double knock** 14 ms apart. | as above |
| LOW Q (F4) | 1 : 1.62 : 2.40 : 3.50, grit 1.7 kHz, the **second partial rings on** 2.6x longer. | as above |
| LOW K (E4) | 1 : 1.35 : 2.21 : 2.90, damping x1.2, grit 1.35 kHz, lands with a **40 ms scrape**. | as above |
| LOW A (D4) | A slab: 1 : 1.50 : 2.00 : 2.76, damping x1.45, grit 1.1 kHz, an **octave-down partial** under it, heaviest thud. | as above |
| MID helmet | Struck brass at 196 Hz with bell partials, half through a 420 Hz resonance (you hear the inside). | The strike ringing three times longer and sinking 3 %, air moving inside (Q5 at 380 Hz). |
| MID compass | A small FM brass tap on D5 (1 : 1.41) under 3.5 kHz with a 6 ms needle tick. | Three ticks slowing (0, 110, 260 ms), then a D4 ring with a tremolo slowing 9 -> 4 Hz. |
| HIGH viper | Jaw snap: click, 45 ms band-pass 2800 -> 1100 Hz, its wet double 11 ms later. | Seven clicks accelerating, then a hiss falling 5.2 -> 1.7 kHz over a throat tone. |
| HIGH angler | The lure: Bb4 with a 14 Hz waver under 1.8 kHz. | The lure hum (A3 + F4 + Bb4) throbbing at 5.5 Hz, then the trap shuts. |
| HIGH squid | The mantle pulses once: soft noise under 900 Hz, F3 sliding to D3. | One long breath out (band-pass 500 -> 1900 -> 420 Hz) with a moan; no transient. |
| APEX Leviathan | **Rebuilt.** A mid-band knock (650 Hz, 16 ms) and click; a body falling 240 -> 150 Hz; the throat in two bands (saw 45 x 31 Hz under 500 Hz, and saw 110 x 31 Hz through a 260 Hz band-pass, the louder of the two); sub 62 -> 32 Hz at a quarter of its old level. | The same knock and body, the two-band throat for 620 ms, D against Eb at 147 / 156 Hz (an octave up from before) with 73 Hz under it. |
| WILD Maw | **Rebuilt.** 30 ms breath in, click and an 800 Hz knock, a jaw body at 300 Hz (140 ms), plates at 187 / 311 / 523 Hz, water closing 3 kHz -> 200 Hz, sub 70 -> 36 Hz at a third of its old level. | 200 ms inhale, 25 ms of nothing, then the snap with the same body, plates and knock. The help cue in miniature. |

Land take 1 and the stinger per symbol (the last column is the one the ladder is set in):

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz | 200 Hz-4 kHz share | 200 Hz-4 kHz RMS dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `sym_low_10_land_v1.wav` | 0.20 | -12.6 | -26.1 | 444 | 16.1% | 81.4% | **-27.0** |
| `sym_low_10_stinger.wav` | 0.42 | -12.0 | -24.4 | 385 | 10.9% | 86.7% | **-25.0** |
| `sym_low_j_land_v1.wav` | 0.20 | -13.8 | -26.2 | 402 | 14.0% | 83.7% | **-27.0** |
| `sym_low_j_stinger.wav` | 0.42 | -11.7 | -23.5 | 395 | 13.7% | 71.0% | **-25.0** |
| `sym_low_q_land_v1.wav` | 0.20 | -15.6 | -26.4 | 456 | 10.6% | 88.0% | **-27.0** |
| `sym_low_q_stinger.wav` | 0.42 | -12.7 | -24.2 | 401 | 7.9% | 84.2% | **-25.0** |
| `sym_low_k_land_v1.wav` | 0.20 | -12.9 | -25.8 | 319 | 22.2% | 75.2% | **-27.0** |
| `sym_low_k_stinger.wav` | 0.42 | -10.1 | -23.0 | 304 | 15.5% | 63.7% | **-25.0** |
| `sym_low_a_land_v1.wav` | 0.20 | -14.8 | -24.7 | 248 | 14.0% | 59.4% | **-27.0** |
| `sym_low_a_stinger.wav` | 0.42 | -13.3 | -23.3 | 246 | 7.8% | 68.0% | **-25.0** |
| `sym_mid_helmet_land_v1.wav` | 0.20 | -10.8 | -23.1 | 320 | 15.7% | 64.8% | **-25.0** |
| `sym_mid_helmet_stinger.wav` | 0.62 | -9.4 | -22.0 | 351 | 6.6% | 79.1% | **-23.0** |
| `sym_mid_compass_land_v1.wav` | 0.20 | -9.6 | -23.3 | 666 | 26.0% | 68.1% | **-25.0** |
| `sym_mid_compass_stinger.wav` | 0.62 | -9.1 | -22.5 | 320 | 10.0% | 88.7% | **-23.0** |
| `sym_high_viper_land_v1.wav` | 0.15 | -2.0 | -18.2 | 1743 | 28.8% | 33.0% | **-23.0** |
| `sym_high_viper_stinger.wav` | 0.62 | -1.6 | -15.7 | 2218 | 17.3% | 29.2% | **-21.0** |
| `sym_high_angler_land_v1.wav` | 0.21 | -7.9 | -20.5 | 290 | 37.0% | 56.8% | **-23.0** |
| `sym_high_angler_stinger.wav` | 0.65 | -7.7 | -19.7 | 283 | 21.3% | 74.0% | **-21.0** |
| `sym_high_squid_land_v1.wav` | 0.21 | -7.2 | -18.8 | 260 | 24.2% | 38.3% | **-23.0** |
| `sym_high_squid_stinger.wav` | 0.62 | -8.1 | -19.8 | 1114 | 0.0% | 76.0% | **-21.0** |
| `sym_apex_leviathan_land_v1.wav` | 0.23 | -5.9 | -17.6 | 231 | 19.6% | 45.2% | **-21.0** |
| `sym_apex_leviathan_stinger.wav` | 0.65 | -2.0 | -13.5 | 184 | 17.9% | 27.9% | **-19.0** |
| `sym_wild_maw_land_v1.wav` | 0.23 | -2.6 | -14.5 | 533 | 15.8% | 35.6% | **-19.0** |
| `sym_wild_maw_stinger.wav` | 0.65 | -1.6 | -12.0 | 509 | 21.0% | 31.7% | **-17.0** |

The three land takes (peak dBFS / centroid Hz / 200 Hz-4 kHz RMS dBFS):

| Symbol | v1 | v2 | v3 |
| --- | --- | --- | --- |
| low_10 | -12.6 / 444 / -27.0 | -11.5 / 455 / -27.5 | -12.7 / 439 / -27.3 |
| low_j | -13.8 / 402 / -27.0 | -14.4 / 394 / -27.5 | -11.9 / 402 / -27.3 |
| low_q | -15.6 / 456 / -27.0 | -14.0 / 420 / -27.5 | -13.9 / 393 / -27.3 |
| low_k | -12.9 / 319 / -27.0 | -14.2 / 315 / -27.5 | -13.4 / 293 / -27.3 |
| low_a | -14.8 / 248 / -27.0 | -12.0 / 231 / -27.5 | -14.9 / 247 / -27.3 |
| mid_helmet | -10.8 / 320 / -25.0 | -11.7 / 326 / -25.5 | -11.1 / 299 / -25.3 |
| mid_compass | -9.6 / 666 / -25.0 | -9.6 / 645 / -25.5 | -11.1 / 637 / -25.3 |
| high_viper | -2.0 / 1743 / -23.0 | -2.2 / 1658 / -23.5 | -2.5 / 1824 / -23.3 |
| high_angler | -7.9 / 290 / -23.0 | -8.7 / 306 / -23.5 | -7.8 / 284 / -23.3 |
| high_squid | -7.2 / 260 / -23.0 | -7.3 / 255 / -23.5 | -7.9 / 270 / -23.3 |
| apex_leviathan | -5.9 / 231 / -21.0 | -7.5 / 228 / -21.5 | -5.4 / 228 / -21.3 |
| wild_maw | -2.6 / 533 / -19.0 | -4.2 / 559 / -19.5 | -3.0 / 560 / -19.3 |

Read this honestly: the ladder is now exact on the meter, in one band, for files played alone. It says nothing about
how heavy a voice *feels*: the squid's stinger is a breath with no transient and the viper's is mostly clicks, and equal
band RMS does not make them equally present. And 2 dB a tier is a small step; whether a player hears five rungs or two
is a listening question.

## 5. Wiring (done since round 3 in `audio_moments.js`, by the sample route; kept here as the design it was built from)

`audio_dark.js` is all-procedural today: there is no sample player. Two honest routes.

**Route A, samples (fastest, matches these files exactly).**
1. Add a loader inside `install(A)`: `A.loadMoments(baseUrl)` fetches a packed set (OGG/Opus or AAC transcodes, or one
   sprite plus the manifest's offsets), `decodeAudioData`s into `D.buf[name]`, and never throws.
2. Add `const play = (name, t, gainDb, rate) => { ... }` next to `nburst` / `sub` (`audio_dark.js:70-80`): an
   `AudioBufferSourceNode` -> gain -> `A.sfx`. `A.sfx` also feeds the shared reverb send (`D.send`, `:107`) and these
   files already contain their own room, so either route them to a dry bus that skips `D.send`, or re-render with the
   `verb()` calls at zero and let the game's room do it.
3. New public methods, each guarded by `live()`, listed in `A.darkNames` (`:386`), falling back to today's recipe when
   a buffer is missing. `v` is `'full'` the first time in a session and `'short'` for repeats, xBet and turbo:
   - `A.helpLead(v, level)`: `dread` + `targeting` + `vacuum` as one buffer, at the sequence's first frame (H1). It
     replaces the `roar(1)` in `levPreStrike` (`index.html:2306`), which must go or two risers and two impacts play.
     The short version has no hush before it.
   - `A.helpImpact(v, level)`: `duckAt(t, -60, 5, 700)` on the bed (`audio_dark.js:151`), then `impact`. Fire it from
     the same line that starts the hit-stop (today `chomp` at `index.html:2215`), **not** from a timer at 1500 / 700 ms:
     the bite is clock-gated by `waitK`, and a late frame should lengthen the dip, not put the hit before the picture.
   - `A.cellTurn(i, n, level)`: `help_cell` at `playbackRate = 2^(semi/12)` with semi = 0, 2, 3, 5, ... for
     i < n - 1, and `help_cell_last` (already a fifth up, with its seat) for i = n - 1. Fire per cell from the surfacing
     loop (today `wildRise` at `index.html:2240`, re-timed to start 80 ms after the impact). Drop the `shimmer` at `:2233`.
   - `A.helpRecede(v, level)`: `aftermath`, 220 ms (full) or 180 ms (short) after the impact, under the cells. Today's
     `plunge` call (`index.html:2228`) is the nearest hook. Its drain is timed for four cells; for other counts split
     the stem at `drain` and fire that half when the last cell has turned.
   - `A.seam(step, nCols)`: `crack` + `jet`, beside `engSeam` (`index.html:1936`) with `ctx.step`, only when
     `!ctx.quiet`. `A.win(x)` (`:1948`) then loses its own sub thud or it stacks on the jet's push.
   - `A.seamImplode(step)`: `implode`, where `fizz` is (`index.html:2001`).
   - `A.symLand(sym)` in `onLand` (`index.html:4112`) instead of the anonymous `A.land()` at `:4406`: pick
     `_land_v1..v3` round-robin per symbol (never the same take twice running), keep `A.land`'s 60 ms rate limit
     (`audio_dark.js:333`), and voice at most the two or three highest-tier symbols per column stop.
     `A.symWin(sym)` for the top-paying way of a step, beside `aud.win` (`index.html:1948`); one stinger per step.
4. Depth: ship depth 0 / 2 / 5 renders and pick by `A.level`, or ship depth 0 and do the colour live (`playbackRate`,
   a per-voice low-pass, a `WaveShaperNode`). The second is smaller, but re-check the small-speaker flags if depth 0 ships.
5. Cascade step: ship steps 1 / 3 / 5 and use the nearest, or render all five (`win_seams(steps=(1,2,3,4,5))`).

**Route B, procedural port (keeps the "no samples" property).** Every recipe uses only what `audio_dark.js` already
has (`sub()`, `nburst()` with scheduled filter sweeps, FM and ring-mod as in `_land` / `_impact`, the shared
convolver); the modal partials are a handful of `sub()` calls at a fixed pitch. The tables above are the port spec. It
will not be byte-identical and needs its own measurement pass through the existing `OfflineAudioContext` lab.

Either way: the bed duck is the runtime's job, and the master chain (compressor at -18 dB 4:1, a 30 Hz high-pass,
**-7 dB shelf above 4.2 kHz**, limiter at -6 dB) will change every number here. Files at -1.5 dBFS are far hotter than
the dark set's present voices and need a trim on the way in; how much is a listening decision.

## 6. Needs a human ear

Nothing in this list can be answered by a meter. In rough order of risk:

1. **Does it sound like anything?** Synthesis by recipe can measure perfectly and still sound like a test tone and a
   hiss. The new churn and run-off (random-level filtered noise) are the most likely to read as "noise with a fader
   moving"; the bowed glass and the three "living" voices are next. The fallback is to layer real recordings.
2. **Does the new dread layer sound like dread or like an organ?** Five sustained partials at 294-1195 Hz are what make
   it audible on a phone, and exactly what could make it sound like a held chord. It passes the 12 dB check by about 1 dB.
3. **Does the transformation read as relief turning into greed, or as a jingle?** It now rises and lands on an open
   fifth. That is the single most "reward-like" gesture in the set. Whether 2-3 kHz glass with a soft onset keeps it
   cold, and whether the last cell's weight is felt at all on a phone (its seat is 95-300 Hz), needs listening.
4. **Is the breach water or a snare?** A broadband slap with a 420 Hz body and a low push is also the description of a
   drum hit. The zap is gone on paper; whether "water coming at you" replaced it is not measurable.
5. **Phone weight of APEX and WILD:** the ladder now ranks them on top in the 200 Hz-4 kHz band by 2 dB a tier. Is
   2 dB audible as rank, and do the two folded voices (viper and Wild stingers) sound squashed?
6. **The dip:** 80 and 60 ms of digital silence may read as a dropout, and both are shorter than Bluetooth latency.
7. **The short version's pacing:** 350 ms of dread, 350 ms of targeting. Does it still build, or is it just a hit
   with a preamble? Heard dozens of times a session, is 1.7 s still too long?
8. **Falling win ladder:** every cascade step is lower. The help's transformation now rises, the win seam still
   falls. Players may hear their wins getting worse, or the two cues may sound like different games.
9. **Stones:** five different details on paper; in a refill of fifteen lands they may still be one clatter. And the
   round-robin takes differ by a seed, 0.6 semitone and 1 dB: enough to stop machine-gunning, or not?
10. **Depth by ear:** tanh on a sub may read as "broken speaker"; at depth 5 the impact's tail is 6 dB down after 0.9 s
    and may smear. Depth 0 flags the dread.
11. **In the mix:** everything was measured solo, through no master chain. The scar hum and the eye tone share 147 /
    156 Hz by design and may pile up over a long cascade.
12. **Sync:** wired, but never watched with the picture by a person. See section 1 for the
    tails that outlast the sequence and the -24 dB duck.
13. **Loudness:** peak and RMS only. No LUFS, no true-peak, no check after lossy encoding; mono.
