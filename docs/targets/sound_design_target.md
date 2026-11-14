# Sound design target — the help, the seam breach, the symbol voices

Status: **rendered and measured, not heard.** Everything below was designed by layer and frequency band and verified on
meters (peak, RMS, band energy, spectrograms). Nobody has listened to it. The last section lists what only an ear can
settle. Nothing here is wired into the game.

- Generator: `scripts/ai/assetgen/moments.py` (numpy + Pillow only; `python scripts/ai/assetgen/moments.py --sheet`, about 5 s)
- Output: `generated/sfx/moments/*.wav` (48 kHz, 16-bit, mono; git-ignored), `manifest.json` (source, licence, sha256,
  measurements per file), `report.json` (the help cue's engineering checks)
- Sheets: `artifacts/targets/sound_help_sheet.png`, `sound_help_sheet_storyboard.png`, `sound_win_sheet.png`, `sound_symbols_sheet.png`
- Determinism: two renders in separate processes, 53 WAVs + both JSON files byte-identical
  (`help_full.wav` sha256 `7902f948fd72bfac78d39be3e46ced4dcbbba2d456a53541b575a1481e4b3869`). Seeds come from SHA-256 of each sound's name; depth
  and timing profile do not change a seed, so a diff means a design value changed. Verified on one machine only.

## 1. The real timings in the code (and where the beat sheet disagrees)

### The help: `strikeSeq` (`slot_engine/static/canvas/index.html:2148`), event `CREATURE_LIFELINE_STRIKE` (dispatch `:2012`)

The strike is paced by `waitK(k)` (`:2136`), which waits for a fraction of the creature's strike path. `levStrike`
sets `strikeAnim.dur = 10` (`:5230`) and the swim clock runs at 2x during a strike (`:5299`), so **`waitK(k)` = k x 5.0 s**
of real time on a healthy frame rate (later on a slow one: it is clock-gated, not timer-gated).

| Real time (t = 0 at `levStrike`, `:2170`) | Code | What happens | Sound today (dark set) |
| --- | --- | --- | --- |
| -2400..-1500 ms (random) | `levPreStrike(1500 + rnd*900)` `:2165`, body `:2300` | stillness; `A.hush(-12 dB)` | bed -12 dB |
| -100 ms | `:2306` `levSfx('roar', 1)` | | `A.roar` (`audio_dark.js:345`): 1.5 s riser, 300 ms hole, impact +6 dB. Its impact lands at **+1740 ms** |
| 0 | `:2166-2175` | other cells dim, creature rushes in | — |
| 800 ms | `waitK(0.16)` `:2184`, `:2186` | jaws gape | `jawOpen` is skipped when `roar` already fired |
| 1620 ms | `waitK(0.324)` `:2212` | (empty step) | — |
| **1700 ms** | `waitK(0.34)` `:2214`, `chomp` `:2215`, `heavyImpact` `:2218` | bite, hit-stop 67 ms (`feel.js:29`), shake 250 ms | `A.chomp` (`audio_dark.js:341`): -30 dB duck, 40 ms hole, hit at **+1740 ms**, stacked on the roar's impact |
| 1960 ms | `waitK(0.392)` `:2222`, `plunge` `:2228` | creature tears away downward | `A.plunge` (base set, `index.html:1065`; the dark set does not replace it) |
| 2810 / 3060 ms | `waitRaw(850)` `:2229`, `waitRaw(250)` `:2231` | | — |
| **3060 ms + i x 110 ms** (70 ms at level >= 4) | `:2233-2242` `engSurface` per struck cell | struck cells surface as their new symbols | `A.shimmer` once, `A.wildRise` per cell (`audio_dark.js:358`, `:368`) |
| + 1100 ms, then 150 + 250 ms | `:2257-2265` | hold, undim, done | — |

So the sequence is about **4.9 s** for four cells, not 2.4 s, and its order is different from the beat sheet:

| Beat | Storyboard sheet | Code today | Note |
| --- | --- | --- | --- |
| H0 settle | 0 | the 1.5-2.4 s hush *before* t = 0 | the hush is the bed duck; the cue does not own it |
| H1 dread | 0-600 | 0-800 | |
| H2 approach | 600-1100 | 800-1700 | |
| vacuum | ~1020-1100 | 1620-1700 | the code already has an 80 ms step here (`waitK(0.324)` to `waitK(0.34)`) |
| H3 impact | 1100 | **1700** | hit-stop is 67 ms in code, not 80 |
| H4 transformation | 1180-1700 | **3060 onward**, one cell every 110 ms | in code it comes *after* the creature has gone |
| H5 aftermath | 1700-2400 | **1960-3060** (recede), then the hold to ~4900 | in code the recede comes *before* the transformation |

**Decision:** the recipes are written against a table of beat times, and both tables are rendered. `help_*.wav` follows
the code (`BEATS_CODE`), `help_sb_*.wav` follows the storyboard (`BEATS_STORYBOARD`). Same recipes, same seeds. If the
picture is re-timed to the storyboard, the audio is a one-line change. The H4/H5 order needs a decision from whoever
owns `strikeSeq`: the storyboard's "transformation straight after the impact" is the stronger read, and it costs the
transformation 3.7 dB of clearance because it sits on the impact's tail (measured below).

### The win: `WIN_EVALUATION` (`index.html:1925`) then `CASCADE_DROP` (`:1990`)

| Real time | Code | What happens | Sound today |
| --- | --- | --- | --- |
| 0 | `engSeam(idx)` `:1936` (body `:4042`), `aud.win(x)` `:1948` | crack starts: `prog` 0 -> 1 in **240 ms** (`:4547`) | `A.win` (`audio_dark.js:352`) |
| 240 ms + q x 20 ms | `:4588` | one jet per winning column, each **340 ms**; silt flow in 140 ms (`:4548`) | — |
| **750 ms** (`highlightMs`, `feel.js:22`, never compressed) | `:1960`, then `engDissolve(..., implode)` `:1999`, `engSeamScar()` `:2000`, `aud.fizz()` `:2001` | symbols implode over `explodeMs` = **480 ms x chainFactor** (`feel.js:23`, `:73`); the scar glows 2.6 s (`:4549`) | `A.fizz` = `A.dissolve` (`audio_dark.js:331`) |
| 750 + 480f ms | `aud.absorb()` `:2003` | drop: `dropMs` 520 x f, then `pauseMs` 200 x f | `A.absorb` (base set, `index.html:1043`), then `A.land()` per symbol (`:4406`) |

`chainFactor` is 1.0 for steps 1-3, 0.92 at 4, 0.84 at 5, floor 0.7. The beat sheet says W1 0-150, W2 150-500, W3 500-900;
the code is **W1 0-240, W2 240-750, W3 750-1230**. The cue is designed to the code. Because W1/W2 and W3 hang off two
different events, they are separate stems on purpose.

## 2. The help cue

One cue, six stems that sum to the full mix (one shared gain; measured error 3 LSB of 16-bit rounding). Each stem is
padded to the cue length so they line up by simply starting together; `beat_offset_s` in the manifest says where each
one really begins, for trimming into a sprite.

| Stem | Intention | Layers and bands | Starts (code / storyboard) |
| --- | --- | --- | --- |
| `dread` | You feel it before you see it; the eye opens. | Sub swell: two sines 36 + 37.4 Hz (1.4 Hz beat), rising. Eye: 147 + 156 Hz minor-second pair with a faint 220 Hz, gliding up 2 %, slow 0.9 Hz pulse. Lid: pink noise through a low-pass opening 150 -> 750 Hz. Holds under the approach, cut dead at the vacuum. | 0 / 0 |
| `approach` | The frame strains as the shadow crosses. | Bowed-metal creak: saw 62 -> 150 Hz through a Q9 band-pass sweeping 260 -> 1100 Hz, stick-slip gaps 130 ms apart tightening to 30 ms; a rivet ping (420 -> 1500 Hz, 30 ms) on each slip; pink pressure noise band-passed 200 -> 2200 Hz; a 48 -> 92 Hz groan underneath. Pitch and density both rise. | 800 / 600 |
| `vacuum` | The breath in, so the hit lands harder. | 140 ms of suction (white noise, high-pass sweeping 600 Hz -> 7 kHz, cubic swell, plus a 70 -> 210 Hz rising tone), then **80 ms of nothing**. Every pre-impact stem is gated shut over the dip. | 1480 (dip 1620-1700) / 880 (dip 1020-1100) |
| `impact` | The sea comes in. | 8 ms click above 2.5 kHz; sub thump 64 -> 30 Hz (0.95 s); punch 125 -> 46 Hz (120 ms); water mass: white noise low-pass closing 5.2 kHz -> 170 Hz in 0.5 s; brown rumble under 110 Hz for 1.4 s; struck plates at 187 / 311 / 523 / 742 / 1180 Hz; throat: saw 45 Hz ring-modulated by 31 Hz under 600 Hz. | 1700 / 1100 |
| `transform` | Cold, glassy, not a reward chime. | Per struck cell: glass-bar partials 1 : 2.756 : 5.404 on 2349 Hz with a beating twin (x1.004), 6 ms soft onset, a 30 ms breath of frost above 6 kHz. **Each next cell is a semitone lower** (2349, 2217, 2093, 1976 Hz): never an arpeggio up. High-passed at 1.5 kHz, 10th order in total. | 3060 + i x 110 / 1180 + i x 100 |
| `aftermath` | The water leaves, the plates ring, it goes down. | Drain: pink noise band-pass falling 1500 -> 220 Hz (a wash, no bubbles); plates still ringing at 311 / 523 / 742 Hz; recede tone falling 84 -> 33 Hz with 4 Hz waver, and the throat faint behind it. | 1960 / 1700 |

(Pitches are as written, at depth 0. The default render is depth 2, one semitone lower on everything but the transformation.)

### Measured (depth 2, code timings)

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz share |
| --- | --- | --- | --- | --- | --- |
| `help_dread.wav` | 4.90 | -15.5 | -31.4 | 94 | 50.7% |
| `help_approach.wav` | 4.90 | -11.6 | -35.0 | 948 | 4.5% |
| `help_vacuum.wav` | 4.90 | -14.9 | -44.0 | 1636 | 0.1% |
| `help_impact.wav` | 4.90 | -1.5 | -18.6 | 77 | 89.0% |
| `help_transform.wav` | 4.90 | -14.9 | -35.6 | 2650 | 0.0% |
| `help_aftermath.wav` | 4.90 | -11.5 | -26.9 | 957 | 15.2% |
| `help_full.wav` | 4.90 | -1.5 | -17.7 | 244 | 75.5% |

Storyboard timings (`help_sb_*`):

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz share |
| --- | --- | --- | --- | --- | --- |
| `help_sb_dread.wav` | 2.60 | -17.4 | -32.2 | 97 | 50.0% |
| `help_sb_approach.wav` | 2.60 | -13.4 | -35.8 | 898 | 4.6% |
| `help_sb_vacuum.wav` | 2.60 | -15.1 | -41.5 | 1636 | 0.1% |
| `help_sb_impact.wav` | 2.60 | -1.8 | -16.1 | 77 | 88.9% |
| `help_sb_transform.wav` | 2.60 | -14.2 | -33.1 | 2658 | 0.0% |
| `help_sb_aftermath.wav` | 2.60 | -11.2 | -29.8 | 880 | 16.0% |
| `help_sb_full.wav` | 2.60 | -1.5 | -15.7 | 168 | 82.5% |

Also rendered: the two ends of the depth ladder (full mix only) and the single-cell one-shot the runtime would fire.

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz share |
| --- | --- | --- | --- | --- | --- |
| `help_full_d0.wav` | 4.90 | -1.5 | -20.1 | 327 | 77.2% |
| `help_full_d5.wav` | 4.90 | -1.5 | -15.8 | 224 | 73.6% |
| `help_transform_cell.wav` | 1.03 | -9.0 | -25.7 | 2714 | 0.0% |

### Engineering targets

| Render | Full peak dBFS | Sub 30-80 Hz peak (50 ms RMS, dBFS) | vs anything before the dip, dB | vs every other stem, dB | vs the cue from 0.9 s after, dB | Dip RMS dBFS | Transform: energy >1.5 kHz / centroid | Transform vs rest >1.5 kHz in its window, dB | Stems-sum error, LSB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| help | -1.50 | -6.9 at 1.885 s | +16.4 | +17.2 | +11.6 | -90.6 (before: -19.3) | 100.0% / 2650 Hz | +9.3 | 3 |
| help_sb | -1.50 | -7.2 at 1.285 s | +18.3 | +18.5 | +12.3 | -104.8 (before: -21.7) | 100.0% / 2658 Hz | +5.6 | 3 |
| help_d0 | -1.50 | -8.4 at 1.775 s | +18.9 | +19.1 | +15.9 | -98.7 (before: -22.1) | 100.0% / 3553 Hz | +9.5 | 3 |
| help_d5 | -1.50 | -6.4 at 1.845 s | +18.3 | +17.5 | +7.1 | -82.4 (before: -19.0) | 100.0% / 2366 Hz | +9.2 | 3 |

- **Peak <= -1 dBFS:** every file, and the summed cue, peaks at or below -1.5 dBFS. Sample peak, not true peak.
- **No DC:** |mean| <= 0.00002 (0.6 LSB) on every file. **Fades:** all files start and end at zero inside a linear 4 ms ramp to
  their own peak (4.5-5 ms applied). The generator exits non-zero if any file misses peak, DC or fade.
- **Impact sub is the strongest moment:** the 30-80 Hz band peaks inside the impact window in all four renders, at least
  16 dB above anything before the dip and at least 17 dB above every other stem. The measured peak sits 75-185 ms after
  the hit because a 50 ms RMS window on a 30-60 Hz tone reads the body of the thump, not its first cycle. At depth 5 the
  impact's own tail is only 7.1 dB down 0.9 s later (longer ring, heavier drive): a deliberate depth effect, but check it.
- **Transformation above 1.5 kHz:** more than 99.99 % of its energy is above 1.5 kHz. In its window it is 9.3 dB above
  everything else in the mix above 1.5 kHz with the code's timings, 5.6 dB with the storyboard's.
- **Nothing masks the dip:** the 80 ms dip measures -90 dBFS (about one LSB) against -19 dBFS in the 100 ms before it.
  That is the file. In the game the ambience bed and any reverb tail will fill it unless the bed is ducked (section 5).

### Depth 0-5

One argument (`Depth`, `--depth`), applied to every sound in this document:

| | 0 (surface) | 2 (default render) | 5 (the Core) |
| --- | --- | --- | --- |
| Body pitch | as written | -1 semitone | -2.5 semitones |
| Drive (tanh pre-gain) | none: clean | 1.4 | 2.0: peaks fold over, the sub grows harmonics |
| Top end (low-pass) | open, 16 kHz | 10.8 kHz | 5.9 kHz |
| Sub weight | x1.0 | x1.14 | x1.35 |
| Room (wet) | as written | +0.06 | +0.15 |
| Ring / tail length | x1.0 | x1.12 | x1.3 |
| Transformation | pure glass | 61 Hz ring-mod at 14 % | ring-mod at 35 %: the glass turns rough, never warmer |

Measured on the full help cue: RMS -20.1 dBFS at depth 0, -17.7 at 2, -15.8 at 5 (same peak, so it gets denser, not
louder); transformation centroid 3553 -> 2650 -> 2366 Hz. The transformation is never driven and its pitch does not sink:
it stays the one cold thing in the cue. `strikeSeq` clamps the level to 1-5, so depth 0 is for the other cues.

## 3. The win seam cue

Intention: a win is the hull admitting the sea. It should feel like damage that happens to pay.

| Stem | Intention | Layers and bands | At (code) |
| --- | --- | --- | --- |
| `crack` | A hairline runs through the winning cells. | 8-20 fracture clicks of 1.5-4 ms above ~3.5 kHz, sparse then crowding toward the breach; a glass-stress whine falling 3.8 -> 2.9 kHz at very low level; one low tick at 160 -> 110 Hz. | 0-240 ms |
| `jet` | The seam tears and pressurised water comes through. | A 6 ms tear click; 3-7 needles of white noise, band-pass falling 2600 -> 900 Hz, 20 ms apart, 340 ms each (the picture's own numbers); pressure drop 140 -> 60 Hz; a pink hiss near 1.2 kHz that holds until the implosion. | 240-750 ms |
| `implode` | The symbols are crushed inward; the seam stays as a glowing scar. | 70 ms of suction (low-pass opening 300 -> 2400 Hz); crush: sub 110 -> 46 Hz inside the explode budget, a dull crunch band-pass 900 -> 250 Hz, brass dust at 420 / 660 / 990 Hz for 50 ms; scar hum: 147 + 156 Hz minor second with 73 Hz under it, 0.9-1.7 s. | 750 ms, crush at 820 ms |

Cascade step 1..5 (`win_seam_raw(step)`), **heavier, never brighter**: pitch drops 1.5 semitones a step (the jets' band
one semitone a step); fracture clicks 8 -> 20, jets 3 -> 7, more sub under the breach and the crush; the scar hum lasts
0.9 -> 1.7 s so later steps overlap their own past; reverb send rises. The crush itself gets *shorter* at steps 4-5
because the game's explode budget does (`chainFactor`). One gain is shared across the ladder, so step 5 is 4 dB louder
than step 1 on the meter rather than normalised to the same peak. Depth changes it as in the table above.

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz share |
| --- | --- | --- | --- | --- | --- |
| `win_s1_crack.wav` | 2.17 | -9.7 | -39.7 | 5778 | 0.4% |
| `win_s1_jet.wav` | 2.17 | -7.3 | -26.4 | 758 | 1.4% |
| `win_s1_implode.wav` | 2.17 | -5.2 | -20.5 | 82 | 66.6% |
| `win_s1_full.wav` | 2.17 | -5.5 | -19.5 | 274 | 52.6% |
| `win_s3_crack.wav` | 2.57 | -7.6 | -37.6 | 5295 | 1.1% |
| `win_s3_jet.wav` | 2.57 | -6.1 | -23.9 | 475 | 8.5% |
| `win_s3_implode.wav` | 2.57 | -3.1 | -18.6 | 70 | 87.4% |
| `win_s3_full.wav` | 2.57 | -2.8 | -17.4 | 208 | 70.0% |
| `win_s5_crack.wav` | 2.97 | -7.2 | -37.0 | 4325 | 4.8% |
| `win_s5_jet.wav` | 2.97 | -5.0 | -22.6 | 377 | 44.8% |
| `win_s5_implode.wav` | 2.97 | -1.9 | -17.3 | 64 | 87.5% |
| `win_s5_full.wav` | 2.97 | -1.5 | -16.0 | 166 | 76.6% |

Read across steps 1 / 3 / 5: peak -5.5 / -2.8 / -1.5 dBFS, RMS -19.5 / -17.4 / -16.0, centroid 274 / 208 / 166 Hz,
length 2.17 / 2.57 / 2.97 s. The centroid falling while the level rises is the "not cheerful" part, measured.

## 4. Symbol voices

One family, by construction: every land sits on the same short pressure thud (80 -> 44 Hz, 90 ms, scaled by tier); every
pitch is from D minor, with the flat second (Eb against D) reserved for the creature; every stinger bends downward at the
end; everything is in the same 0.55 s steel room. Worth more means lower, heavier and louder (peak targets: LOW -10 / -8,
MID -8.5 / -6.5, HIGH -7 / -5, APEX -4 / -2.5, WILD -3 / -1.5 dBFS for land / stinger).

| Symbol | Land (<= 250 ms) | Win stinger (<= 700 ms) |
| --- | --- | --- |
| LOW 10 / J / Q / K / A (stone) | A dead stone knock: four heavily damped partials (1 : 1.58 : 2.21 : 3.31, 12-45 ms), a 12 ms grit click near 1.8 kHz. One voice at five pitches: A4 G4 F4 E4 D4 (440 -> 294 Hz), the A lowest. | Knock, 170 ms of stone dragged on stone (gated pink noise 520 -> 950 Hz), a second heavier knock a fourth lower with a dull ring that sinks. |
| MID helmet (brass, hollow) | Struck brass at 196 Hz with bell partials (2.0, 2.41, 3.02, 4.53, 5.9), half of it through a 420 Hz resonance so you hear the inside. | The same strike ringing three times longer and sinking 3 %, with air moving inside the helmet (pink noise, Q5 at 380 Hz). |
| MID compass (instrument) | A small FM brass tap on D5 (ratio 1 : 1.41, index 2.5 -> 0) under 3.5 kHz, with a 6 ms needle tick at 2.2 kHz. | The needle swings: three ticks slowing (0, 110, 260 ms; 1800 / 1500 / 1250 Hz), then a D4 ring with a tremolo slowing 9 -> 4 Hz. |
| HIGH viper (click) | A jaw snap: 2.5 ms click, 45 ms band-pass 2800 -> 1100 Hz, and its wet double 11 ms later. The lightest thud of the set. | Teeth: seven clicks accelerating (60 -> 18 ms apart), then a hiss falling 5.2 -> 1.7 kHz over a throat tone G3 -> D3. |
| HIGH angler (lure) | The lure: a Bb4 sine with a fast 14 Hz waver under 1.8 kHz, 200 ms. | The lure hum (A3 + F4 + Bb4) swelling and throbbing at 5.5 Hz for half a second, then the trap shuts: click, 60 ms snap 1500 -> 500 Hz, thud. |
| HIGH squid (breath) | The mantle pulses once: soft pink noise under 900 Hz with a 50 ms swell, and F3 sliding to D3. | One long breath out through the siphon (pink noise band-pass 500 -> 1900 -> 420 Hz) with a moan F3 -> G3 -> D3, roughened by 60 Hz. No transient at all. |
| APEX Leviathan | Sub 62 -> 32 Hz and the throat (saw 45 x sine 31 Hz, under 500 Hz). | The throat for 620 ms over sub 55 -> 30 Hz, and D2 against Eb2 in triangle waves under 400 Hz. |
| WILD Maw | 30 ms breath in, then a click, a 150 ms body closing 3 kHz -> 200 Hz and sub 70 -> 36 Hz. | 200 ms inhale (band-pass 400 -> 3200 Hz, tone 60 -> 150 Hz), 25 ms of nothing, then the snap: click, body 3.5 kHz -> 160 Hz, sub 64 -> 30 Hz, plates at 187 / 311 / 523 Hz. The help cue in miniature. |

| File | s | Peak dBFS | RMS dBFS | Centroid Hz | Sub 30-80 Hz share |
| --- | --- | --- | --- | --- | --- |
| `sym_low_10_land.wav` | 0.20 | -10.0 | -22.4 | 398 | 17.2% |
| `sym_low_10_stinger.wav` | 0.42 | -8.0 | -19.7 | 366 | 9.1% |
| `sym_low_j_land.wav` | 0.20 | -10.0 | -23.8 | 347 | 23.8% |
| `sym_low_j_stinger.wav` | 0.42 | -8.0 | -20.8 | 343 | 9.5% |
| `sym_low_q_land.wav` | 0.20 | -10.0 | -24.1 | 307 | 28.0% |
| `sym_low_q_stinger.wav` | 0.42 | -8.0 | -21.1 | 296 | 10.0% |
| `sym_low_k_land.wav` | 0.20 | -10.0 | -23.4 | 300 | 24.5% |
| `sym_low_k_stinger.wav` | 0.42 | -8.0 | -22.0 | 308 | 13.2% |
| `sym_low_a_land.wav` | 0.20 | -10.0 | -23.9 | 263 | 25.3% |
| `sym_low_a_stinger.wav` | 0.42 | -8.0 | -18.5 | 267 | 6.7% |
| `sym_mid_helmet_land.wav` | 0.20 | -8.5 | -20.8 | 303 | 16.6% |
| `sym_mid_helmet_stinger.wav` | 0.62 | -6.5 | -19.1 | 348 | 6.5% |
| `sym_mid_compass_land.wav` | 0.20 | -8.5 | -22.3 | 624 | 28.0% |
| `sym_mid_compass_stinger.wav` | 0.62 | -6.5 | -19.8 | 317 | 9.9% |
| `sym_high_viper_land.wav` | 0.15 | -7.0 | -23.7 | 1172 | 39.3% |
| `sym_high_viper_stinger.wav` | 0.62 | -5.0 | -21.7 | 2212 | 15.5% |
| `sym_high_angler_land.wav` | 0.21 | -7.0 | -19.7 | 285 | 35.5% |
| `sym_high_angler_stinger.wav` | 0.64 | -5.0 | -17.0 | 283 | 21.6% |
| `sym_high_squid_land.wav` | 0.21 | -7.0 | -18.9 | 249 | 21.7% |
| `sym_high_squid_stinger.wav` | 0.62 | -5.0 | -16.7 | 1114 | 0.0% |
| `sym_apex_leviathan_land.wav` | 0.23 | -4.0 | -12.6 | 54 | 94.8% |
| `sym_apex_leviathan_stinger.wav` | 0.64 | -2.5 | -13.4 | 53 | 94.1% |
| `sym_wild_maw_land.wav` | 0.23 | -3.0 | -13.6 | 188 | 92.4% |
| `sym_wild_maw_stinger.wav` | 0.64 | -1.5 | -12.3 | 173 | 90.8% |

Longest land 230 ms, longest stinger 640 ms. Depth: as the table in section 2. For the symbols the practical reading is:
at the surface they are dry, short and separate; at the Core every land is two and a half semitones heavier, rounder on
top and sits in more room, so a full refill reads as one mass rather than fifteen knocks.

## 5. How to wire it into `audio_dark.js` later (not done)

`audio_dark.js` is all-procedural today: there is no sample player. Two honest routes.

**Route A, samples (fastest, matches these files exactly).**
1. Add a loader inside `install(A)`: `A.loadMoments(baseUrl)` fetches a packed set (OGG/Opus or AAC transcodes of these
   WAVs, or one sprite plus the manifest's offsets), `decodeAudioData`s them into `D.buf[name]`, and never throws.
2. Add `const play = (name, t, gainDb, rate) => { ... }` next to `nburst` / `sub` (`audio_dark.js:70-80`): an
   `AudioBufferSourceNode` -> gain -> `A.sfx`, so it gets the compressor and limiter. `A.sfx` also feeds the shared
   reverb send (`D.send`, `:107`), and these files already contain their own room, so the room will double: either
   route them to a dry bus that skips `D.send`, or re-render with the `verb()` calls at zero and let the game's room do it.
3. New public methods, each guarded by `live()` and listed in `A.darkNames` (`:386`), falling back to today's recipe
   when the buffer is missing:
   - `A.helpLead(level)`: plays `dread` + `approach` + `vacuum` as one buffer at t = 0. Call from `strikeSeq` right
     after `levStrike` (`index.html:2170`). It replaces the `roar(1)` in `levPreStrike` (`:2306`), which must go, or two
     risers and two impacts play.
   - `A.helpImpact(level)`: `duckAt(t, -60, 5, 700)` on the bed (`audio_dark.js:151`), then `impact`. Call where
     `chomp` is called (`index.html:2215`). It must stay a separate trigger: the bite is clock-gated by `waitK(0.34)`
     and arrives late on slow frames, so a single 4.9 s file would drift off the picture. If the lead finishes early the
     dip simply gets longer, which is the safe direction.
   - `A.helpRecede(level)`: `aftermath`. Call where `plunge` is (`index.html:2228`).
   - `A.cellTurn(i, level)`: `help_transform_cell` with `playbackRate = 2^(-i/12)`. Call per cell where `wildRise` is
     (`index.html:2240`); drop the `shimmer` at `:2233` or keep it 12 dB down.
   - `A.seam(step, nCols)`: `crack` + `jet` at t = 0. Call beside `engSeam` (`index.html:1936`) with `ctx.step`, only
     when `!ctx.quiet` (the rule "no win audio at or below stake" stays). `A.win(x)` (`:1948`) then loses its own sub
     thud or it stacks on the jet's.
   - `A.seamImplode(step)`: `implode`. Call where `fizz` is (`index.html:2001`).
   - `A.symLand(sym)` in `onLand` (`index.html:4112`, called from `:4405`) instead of the anonymous `A.land()` at
     `:4406`, keeping `A.land`'s 60 ms rate limit (`audio_dark.js:333`): fifteen symbols land within ~140 ms of each
     other, so play at most the two or three highest-tier voices per column stop and let the rest share one thud.
     `A.symWin(sym)` for the top-paying way of a step, beside `aud.win` (`index.html:1948`); one stinger per step.
4. Depth: either ship depth 0 / 2 / 5 renders and pick by `A.level`, or ship depth 0 and do the depth colour live
   (`playbackRate` for pitch, a per-voice low-pass, a `WaveShaperNode` for drive). The second is smaller and smoother.
5. Cascade step: ship steps 1 / 3 / 5 and use the nearest, or render all five (`win_seams(steps=(1,2,3,4,5))`).

**Route B, procedural port (keeps the "no samples" property).** Every recipe here uses only what `audio_dark.js`
already has: `sub()` for the sweeps, `nburst()` with a scheduled filter sweep for every noise layer, FM and ring-mod
as in `_land` / `_impact`, the shared convolver. The modal partials are a handful of `sub()` calls with a fixed pitch.
The numbers in the tables above are the port spec. The result will not be byte-identical (`Math.random` noise, real
biquads instead of block-wise ones) and would need its own measurement pass through the existing `OfflineAudioContext` lab.

Either way: the bed duck is the runtime's job (`A.hush` before, `duckAt(-60 dB)` across the dip, release 600-700 ms),
and the master chain (compressor at -18 dB 4:1, a 30 Hz high-pass, **-7 dB shelf above 4.2 kHz**, limiter at -6 dB)
will change every number in this document. Files at -1.5 dBFS are far hotter than the dark set's present voices and
need a trim on the way in; how much is a listening decision.

## 6. Needs a human ear

Nothing in this list can be answered by a meter. In rough order of risk:

1. **Does it sound like anything?** Synthesis by recipe can measure perfectly and still sound like a test tone and a
   hiss. The creak (`approach`), the water mass (`impact`) and every "wet, living" voice are the likeliest to sound
   synthetic rather than physical. The honest fallback is to layer real recordings (`docs/audio_sourcing_brief.md`).
2. **Is the dread audible at all?** The pre-impact stems sit 10-14 dB below the impact's peak on purpose, and the sub
   swell is 36 Hz. On a phone speaker the swell does not exist and the eye tone (147 Hz) barely does. The cue may open
   with 1.5 s of near-silence on mobile.
3. **Is the impact's sub real weight or just a number?** 89 % of that stem is 30-80 Hz. Laptop and phone speakers
   reproduce none of it; the game's 30 Hz high-pass and limiter will reshape it. What carries the hit on small speakers
   is the click, the 125 -> 46 Hz punch and the water body. Their balance was set by eye.
4. **Does the 80 ms dip read as a held breath or as a dropout?** Digital silence can sound like a glitch. Try 60, 80,
   100 ms, and a dip to -40 dB instead of to nothing.
5. **Is the transformation cold or just shrill?** Partials at 2.0-2.3 kHz, 6.5 kHz and 12.7 kHz are where ears are most
   sensitive and most easily annoyed. Its level (peak -15 dBFS in the mix) is a guess. Does the semitone descent read as
   ominous or as out of tune? And the master's -7 dB shelf above 4.2 kHz will dull exactly this element.
6. **Not cheerful, not arcade:** the compass ring, the angler lure and the glass cells are the three tonal things here
   and the three that could tip into "reward ding". The descending pitch ladder for cascade steps reverses the genre's
   usual rising one; it may feel like the wins are getting worse.
7. **Bubbles by accident:** the viper's wet double and the squid's breath are filtered noise, which can read as bubbles
   or as white-noise fizz.
8. **Can anyone tell the symbols apart?** The five stones are one voice at five pitches a tone apart and will not be
   told apart in a cascade; that may be right (they are filler) or a waste of five files. Whether viper, angler and
   squid are three animals or three noises is the real test of section 4.
9. **Repetition.** These are single takes. A land sound heard fifteen times a refill, hundreds of times a session,
   needs 3-5 variants (new seeds, +-1 semitone, +-2 dB) or it machine-guns. Not built.
10. **The depth ladder by ear:** tanh at 2.0 on a sub may read as "broken speaker", not "pressure". Depth 0 against 5
    needs an A/B, and the 7 dB tail at depth 5 may make the impact feel smeared rather than heavier.
11. **In the mix:** all of this was measured solo. Against the ambience bed, the drone (24-37 Hz, the same band as the
    dread swell) and a running count-up, masking is unknown. The scar hum (147 / 156 Hz) and the eye tone share a pitch
    by design; over a long cascade that may build into a drone of its own.
12. **Sync.** Beat times come from reading the code, not from a capture. Nobody has watched the picture with this sound.
    Output latency on Bluetooth and mobile (100-250 ms) is larger than the vacuum dip.
13. **Loudness.** Peak and RMS only: no LUFS, no true-peak, no check after lossy encoding (inter-sample overs are
    possible at -1.5 dBFS once transcoded). Mono; no stereo placement of the struck cells was attempted.
