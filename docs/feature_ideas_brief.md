# Discovery brief — what else the slot could have

Status: phases 0–4 complete, decision pending (owner). Written 2026-11-06 from a cited research pass (sources named inline;
"not found" = no public source). Companion to `docs/leviathan_presentation_brief.md` (the creature) and
`docs/math_calibration.md` (the numbers this brief must not break: the math gate now pins them).

## 0. Problem

The game has one arc (descend, purge lows, bite, vents, Ultra) and three known gaps: the base game hits on 49% of spins
(premium cascade titles sit at 17–40%: Beheaded 27%, Fire in the Hole 26%, Mental 34%, Tombstone RIP 9%, all from
nolimitcity.com game pages), the bonus has no retrigger, no running multiplier and no progressive top end (Standard buys
return more than 5× their price on ~0.03% of rounds), and there is nothing for the player to *decide* (no gamble, no cap
choice). "Solved" = two or three features that give the game a second arc and a real top end, chosen so they can be gated
per jurisdiction, with the hit-frequency problem fixed by a feature rather than by weights alone.

## 1. Needs (owner's words this week)

| # | Need | Priority |
| --- | --- | --- |
| N1 | "check the maths add up every time" — any feature must pass the pinned gate or re-pin deliberately | must |
| N2 | Hit frequency toward ~28–32% without empty seats (the owner's rule: purged seats go to higher symbols, no blockers) | must |
| N3 | A Nolimit-grade top end: rare, large, remembered ("max win hunt") | should |
| N4 | Features that read inside the fiction (depth, pressure, the creature), not bolt-ons | should |
| N5 | Jurisdiction gating already in the feel profiles (mga / ukgc / de) must extend to features | must |

## 2. What premium studios ship (the relevant subset; full report in the session log)

**Nolimit City**: xWays (symbol stacks that add ways; San Quentin), xNudge (stacked wild nudges fully in, +1× per nudge;
Tombstone RIP), xSplit (splits every symbol to its left; xWays Hoarder, Mental), xBomb (wild that removes neighbours and
raises the next collapse's multiplier; Fire in the Hole), Infectious xWays (one symbol spreads to all matching; East Coast
vs West Coast), xZone (+1 multiplier on everything adjacent; Gluttony), Enhancer Cells and Jumping Wilds (San Quentin),
Beheaded's progression bar ("each level converts medium paying symbols to high paying symbols", Tzantza Spins remove all
mediums), Supersized's Germinator (removes the lowest paying symbol per landing, +1 spin; all ten removed = max win),
Tombstone RIP's xRIP ("if the total win is less than the base stake, then there is no payout": 9.08% hit frequency),
tiered buys (70×–3,600×) with "may be removed in some regulated markets", xBet (2× for 3× the bonus odds in Beheaded),
Nolimit Cap (player picks 10,000× or 69,000× max win, "the mathematical model… will alter slightly"), xCrash (bet your
win from 30× up: lose all or max win).

**Push / Hacksaw / Pragmatic / Print**: Instant Prize symbols 1–5,000× summed on collect (Jammin' Jars 2, Big Bamboo);
collect meters that lift RTP by level (JJ2 96.1→96.6%); wild multipliers +1 per winning cascade (Jammin' Jars, up to 43×);
Mystery stacks that nudge and reveal (Razor Shark); VS/Duel wilds that expand a reel (Wanted Dead or a Wild, 19.4% HF);
summed tumble multipliers with a running free-spins total and uncapped +5 retriggers (Gates of Olympus, 27.9% HF);
respin-until-win on two scatters (Money Train 2); pick-or-gamble at bonus start (Beheaded's Pick A Potion); Hold & Win
respins resetting to 3 (Fire in the Hole's Lucky Wagon).

**Regulation that gates features**: UK RTS 14D/E/F (2.5 s cycle, no turbo/slam, no celebration ≤ stake) and the 2020
feature-buy warning (RTS 3A/14A: products must not encourage stake increases) — buys are "non-UK only" across the market;
UK stake caps £5 / £2 under-25 (2025). Germany §22a: 5 s average game, €1 per game (raised to €3/€5 from 1 July 2026 per
GGL), no accumulation of stakes or wins across games (jackpot/meter risk), autoplay ban. Netherlands treats Bonus Buy as
autoplay (prohibited). Sweden's draft rules: 3 s minimum, "double" must be voluntary and never queued. Ontario: 2.5 s, no
autoplay, no celebrated losses.

## 3. Candidates mapped to The Descent

| # | Feature (fiction name) | What the player sees | Hit freq | Math | Gating | Effort |
| --- | --- | --- | --- | --- | --- | --- |
| A | **Crush depth** (xRIP in our skin): at Level 0 a return below the stake is "crushed by pressure", the symbols implode and pay nothing, but each crushed win adds pressure points | The only lever found that takes a 5×5 ways game from 49% to ~25–30% without blockers; the sub-stake dribbles become descent fuel instead of coins | ↓ large | RTP sink in base (~1.5 pts) that must be returned at depth; descents become more frequent, which the base RTP already lives on | Satisfies UK 14F / Ontario by construction; results must still be shown (Sweden); net position shown (UK) | S (engine + paytable gate re-pin) |
| B | **Pressure multiplier** (Gates model): every win inside a descent adds its cascade count to a running multiplier for the rest of the round; vents multiply it | A number that climbs through the whole descent and makes the last cascade the biggest | — | RTP source inside the feature; gives the "rare 500×+" the calibration doc says is missing | none | M |
| C | **Second breath** (retrigger): a Leviathan bite during free spins awards +2 spins, uncapped | Bonus rounds that can run long; the bite becomes something to hope for | — | RTP source; the top end of Standard/Ultra buys | none | S |
| D | **Germinator-style purge on the bite**: each bite at Level 3+ also removes the lowest remaining symbol for the rest of the round; all lows gone = ascend to Ultra | Visible paytable shrinking, "the deep gets richer" — the owner's existing rule, made a mechanic | ↑ in feature | Strong RTP source and variance; interacts with the Ultra pearl ascension | none | M |
| E | **Sonar near-miss respin** (Money Train 2 / Germinator): when the gauge stops 1–2 points short of a level, one respin of the stalled reel | Anticipation beat tied to the gauge the player is already watching | ↑ small | Small RTP source (more descents); each respin is a stake-free feature step (UK 14E exempt) | none | S |
| F | **Abyssal pearls → instant prizes** (Push): pearls carry 1–100× values collected by the bite | Cash texture inside cascades; makes the pearls that exist today matter | ↑ unless rare | RTP source | none | S |
| G | **Nolimit Cap**: the player chooses the 5,000× or 15,000× model | A choice before play; two volatility profiles from one game | — | Two certified models; the pinned gate per model | Fine everywhere (not a stake increase) | M (two weight sets) |
| H | **Bet the catch** (xCrash): from 30× up, gamble the win: the line snaps (lose) or the Leviathan is landed (max win) | The decision moment the game lacks | — | RTP-neutral if fair | UK RTS 14A exposure; Sweden "double" must be voluntary/unqueued; keep out of ukgc/de profiles | S |
| I | **Depth meter across spins** (JJ2 collect, Beheaded bar) | Persistent progression | — | Small RTP source | Germany §22a Abs. 8 forbids accumulating across games: de profile must reset per round | M |
| J | **Boosters / more buy tiers** | Standard market pattern | — | Each buy its own RTP line | Non-UK, non-NL; Germany's per-game cap excludes 100×+ buys | S |

Weights (owner first): N2 hit frequency 30%, N3 top end 25%, N4 fiction fit 20%, N1 math safety 15%, N5 gating 10%.

## 4. Recommendation

Build **A + B + C** as one package ("the pressure model"), in that order:

1. **A, Crush depth**, is the hit-frequency fix the calibration doc said needed a structural change. It is the one documented
   mechanic that moves a ways grid into the mid-20s (Tombstone RIP) and it turns the 37% of sub-stake spins into descent
   fuel, which is already where this game's RTP lives. It also makes the UK "no celebration ≤ stake" rule a game rule.
2. **B, the pressure multiplier**, puts the RTP that A removes back inside descents and gives the bonus its missing top end.
3. **C, second breath**, is a one-line engine change that lengthens good bonuses and makes the bite something to want.

Then **G** (cap choice) when two models are worth certifying, **H** only for the mga profile, and **D/E/F** as the next
discovery round once A–C are measured. What would change this: if A's sink cannot be returned inside the ±2 pt window
without making descents too frequent (the feel gate's cycle budget), fall back to D (purge-on-bite) plus 4-reel low pays.

Process: every candidate ships as engine config/core change → `python scripts/math_check.py --full` → `--write-pin` in the
same commit → feel gate on the front end → captures → the owner judges by eye.

## 5. Riskiest assumption and its test

"Voiding sub-stake wins at Level 0 and feeding them to the gauge lands the base game near 28% hit frequency while the
descents absorb the sink within the RTP window." Test (~1 hour): implement A behind a config flag, run the fast gate
(deterministic), read base hit frequency and RTP; if hit frequency is 25–32% and base RTP is within reach by depth
thresholds alone, proceed; if the sink needs more than threshold tuning, stop and take the fallback.

## 6. Open questions

- Is a crushed win shown as a win-then-void (Tombstone shows it) or never counted at all? UK net-position display either way.
- Does the Ultra's 2× global multiplier stack with B, or does B replace it at Level 5?
- Which profile gets H: mga only, or also Ontario once that profile exists?
