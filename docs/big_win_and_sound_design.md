# Big-win celebrations and sound design

How these work in `slot_engine/static/descent/design/Main.dc.html` (methods `celebrate`, `bwFrame`, `makeAudio`), and the research behind them.

## Big-win screens

### Tiers

The amount is measured against the base bet. Nothing is celebrated unless the win is above what was staked for the round, including any buy cost (UKGC RTS 14F).

| Tier | At | Name | Kicker | Effect |
|---|---|---|---|---|
| — | under 50× | inline win chip only | — | — |
| T1 | 50× | DEEP WIN | THE DEEP STIRS | Bioluminescent bloom: the title rises from below, rings of light open outward, plankton and bubbles drift up |
| T2 | 100× | CRUSH DEPTH | THE HULL GIVES WAY | Pressure implosion: rings crush inward, then a shockwave and sparks burst from the counter; hull creak and chain rattle |
| T3 | 500× | LEVIATHAN WIN | IT HAS SEEN YOU | Creature reveal: red flash, scare sting, burning eyes above the title, the 3D Leviathan swims across behind the counter, screen shake |
| T4 | 1,000× | HADAL WIN | THE TRENCH ERUPTS | Tsunami wipe: a wall of water with a foaming crest floods the screen, light ripples through it as it drains, geyser behind the counter |
| MAX | 15,000× (or engine cap) | THE ABYSS | MAXIMUM WIN | Blackout, crimson pressure rings, the Leviathan passes, a held drone; stays up until the player taps |

### Count-up

- The count runs threshold to threshold with an ease-in-out curve per segment, as Nolimit City does.
- Segment lengths:

  | From → to | Length |
  |---|---|
  | 0 → 50× | 3 s |
  | 50 → 100× | 4 s |
  | 100 → 500× | 4.5 s |
  | 500 → 1,000× | 5 s |
  | 1,000× → final | 6 s |

  A final, partial segment is scaled down, to no less than 1.2 s.
- At each tier the title is swapped in with that tier's own entrance, the counter punches (1 → 1.3 → 1), and a louder tier sting plays.
- The counter jitters during the last 40% of each segment.
- A "depth of win" gauge beside the counter reads 10 m per 1× bet, bottoming out at 11,000 m.

### Skip rules

- Skip is armed 0.5 s after the screen opens.
- First tap jumps to the final amount and final tier. Second tap, at least 1 s later, closes.
- The screen auto-closes 5 s after the count ends. Max win never auto-closes.
- `prefers-reduced-motion` turns off the shake and the jitter.

## Sound

Everything is synthesised live with the Web Audio API. It is rebuilt from `sound.js` and the recipes in `scripts/audio/generate_*.py`. Audio starts on the first tap; the header speaker button mutes it.

### Ambience

Everything below gets deeper with the depth level:
- **Drone:** 45 Hz, dropping 3 Hz per level.
- **Water bed:** low-passed noise with a slow swell.
- **Oxygen-mask breathing:** inhale, valve click, then exhale through regulator bubbles. One cycle every 5 s at Sunlight, every 3 s at the Core.
- **Hull creaks:** more frequent with depth.
- **Heartbeat:** at the Core only.

### Gameplay

| Moment | Sound |
|---|---|
| Swimming | A water rush that follows the Leviathan's on-screen speed and visibility |
| Spin | Chain paying out into the deep |
| Symbols sinking out | Low-passed whoosh and sub drop |
| Each reel landing | The heavy "spank" slap |
| Win | Bubble cluster sized to the win, plus a dark surge |
| Dissolve | Fizz and steam, then the suction "absorb" into the meter |
| Vents | Rumble and hiss |
| Level up | Chain dive and boom. Level 4+ gets the heavy anchor chain and an alarm; the Core adds a roar |
| Lifeline strike | Plunge with bubbles as it dives in; geyser and roar on the breach; shimmer as the wilds surface |
| Feature intro | Roar and boom. Mystery adds a riser |
| 6×5 shatter | Glass crack and boom |
| Pearl | Shimmer |

### Celebration

- **Ambience:** ducked while the screen is up.
- **Under each segment:** a riser.
- **On each tier:** a sub drop and a sting that gets louder per tier.
- **Count ticks:** bubble ticks pitched by progress.
- **Tier extras:**
  - T2: creak and chain
  - T3: scare stab and roar
  - T4: a tsunami swell and crash
- **Ending:** an end sting per tier. Max win holds a drone until the player taps.

## Research summary

Most figures come from the code each studio serves for its public demo games. Durations are in seconds unless stated.

### Nolimit City

Source: `casino.nolimitcdn.com/games/<Game>/<ver>/game.js`.

- **Mental:** tiers at 15 / 25 / 50 / 100 / 250× bet, about 3.5–4 s each.
- **San Quentin:** tiers at 15 / 50 / 100 / 250×, then "Wicked Win" at 1,000× and above, 8.78 s.
- **Fire in the Hole:** uses themed tier names.
- **How a tier lands:** title drops in, an additive "blast" plays, the counter punches 1 → 1.3, and the counter shakes over the last 40% of each segment.
- **Max win:** a black overlay with a held loop until the player continues.

### Print Studios (Darkness)

- **Tiers:** 20 / 60 / 120 / 240 / 480×, with names running from Big Win up to "Printing!".
- **Count:** one continuous roll-up, about 27 s at the top tier.
- **Sound:** a "scare" sting.
- **Skip and close:** skip after 0.5 s; auto-close after 5 s.
- **Compliance:** a `Legal.canCelebrateWin` check blocks wins at or below the bet.

### Hacksaw (Wanted Dead or a Wild)

- **Tiers:** 20 / 50 / 100 / 250× (BIG, MEGA, SUPER MEGA, EPIC).
- **Count:** tier by tier.
- **Effects:** a full-screen shockwave centred on the counter at each tier.
- **Sound:** tier stings getting louder (0.2 → 0.6).
- **Max win:** shown as a modal.

### Stake Engine web-sdk (open source)

- Tier durations of 6 / 18 / 20 / 26 / 32 s.
- First press finishes the count; second press closes.

### Regulation

**UKGC RTS 14:**
- No celebration of a return at or below the stake (14F).
- At least 2.5 s between spins (14D).
- No turbo or slam stop in UK builds (14E).
- Skipping is allowed only after the result is shown.

### Still to do for regulated markets

- **Per-step win sounds:** they currently also play for cascade steps that end at or below the stake. They should be gated for UK builds.
- **Turbo:** it halves animation time, so hide it in UK builds.
