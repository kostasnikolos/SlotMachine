# Prompt for continuing on another computer

## One-time setup on the new computer

1. Clone the repository on its working branch, and install the Python packages:

   ```bash
   git clone -b feat/rebalance-and-descent-frontend https://github.com/kostasnikolos/SlotMachine.git
   ```

   ```bash
   cd SlotMachine && pip install -r requirements.txt
   ```

2. Set up the Gemini API key. Get it from aistudio.google.com/apikey. **Do not paste it into the chat.** Run this in a terminal:

   ```bash
   read -s "k?Paste key, then Enter: " && echo "export GEMINI_API_KEY=\"$k\"" >> ~/.zshrc && unset k && echo saved
   ```

   Restart the Claude app afterwards.

3. Open the `SlotMachine` folder in Claude Code. Start a Design session if you want the canvas artifact, or a normal Code session. Then paste the prompt below.

---

## Prompt to paste

You're continuing work on **The Descent: Abyssal Leviathan**, a deep-sea horror slot in this repository (branch `feat/rebalance-and-descent-frontend`). Before doing anything, read `README.md` and `docs/ARCHITECTURE.md`, then `docs/big_win_and_sound_design.md` and `docs/undertow_feature.md`.

### Ground rules

- **The frontend source of truth** is `slot_engine/static/descent/design/Main.dc.html`, a Claude Design canvas artboard.
  - After every change, rebuild with `python3 scripts/descent/dc_to_web.py`.
  - Never hand-edit the generated `slot_engine/static/descent/index.html` or `app.js`.
- **Running the game.** Use `.claude/launch.json`, config "descent" (uvicorn on 127.0.0.1:8090). Use `/?director=1` for the QA Director bar, which forces levels, STRIKE, UNDERTOW and big wins.
- **The engine owns all maths** (about 96% RTP). The frontend only plays back the event timeline. Don't change the maths without a simulation run, and keep `pytest tests/` green.
- **Never delete existing features or visuals.** Extend them.
- **Big or parallel changes.** Give each builder agent its own copy of the design under `slot_engine/static/work/<name>/`. Tell each builder to study and reuse the techniques already in the file. Then:
  1. three-way merge the copies with `git merge-file` against the snapshot they started from;
  2. run a reviewer agent;
  3. fix what it finds;
  4. rebuild and verify in the browser preview with no console errors.
- **The user cares most about visuals.** It must look real, dark and terrifying, not fake. Don't use boxes or panels for effects.
- **Usage limits.** If they hit, stop and wait for my message.
- **Commits.** Only commit or push when I ask.
- **Gemini key.** `GEMINI_API_KEY` is in the shell env (read it with `zsh -ic` if needed). Never print it.
  - Available image models: `gemini-3-pro-image` (best) and `gemini-3.1-flash-image` (fast).
  - Image calls may be billed per image.

### State at hand-off (2026-10-28)

**Done and merged:**
- **Engine:** the 96% rebalance and the Undertow help (2 or 4 symbols sink, foam covers them, new symbols appear).
- **HUD:** the abyss gauge, which fills and drains.
- **Big wins:** the 3D falling big win that crashes when the count stops (tiers 50×, 100×, 500×, 1,000× and max).
- **Leviathan strike:** the jaw-bite strike.
- **Sound:** a procedural sound redesign. The background ambience is liked.
- **Reels:** continuous reel water (`wbg*` methods) in place of boxed cells.
- **Help telegraphs without boxes,** from the `telegraph` builder.

**Needs review:** the merged `telegraph` work. Its builder was stopped during visual checks.
- Check the STRIKE and UNDERTOW Director buttons at L0, L3 and L5 (6×5).
- Check the strike sound and animation are in sync and that there's no leftover orange box.
- Check alignment at the grid edges.
- Make sure the gap around each round symbol reads as water.

### To do, in this order

1. **Review pass** on the water and telegraph merge, as described above.
2. **Leviathan realism.** He still looks fake. Add:
   - skin texture and detail normals, and a wet specular sheen;
   - ambient occlusion and soft shadows;
   - caustic light moving over the body;
   - a better face (eyes, mouth and teeth, where the head meets the neck);
   - slower, heavier swimming with gill breathing.

   `scripts/descent/build_leviathan.py` already has an untested hi-poly normal, AO and thinness bake (needs pymeshlab). Finish it or replace it. If the assets change, update the `ASSETS` id map in `dc_to_web.py` and the design's `levUrls`. Don't break the strike choreography (`strikeSeq`, `levStrike`, and the strike branch of `levPath`).
3. **Gemini art pass.** Write a reproducible `scripts/descent/gen_art.py` that reads the prompts from a file and saves to `slot_engine/static/assets/descent/gen/`. Show me a few test images before generating whole batches. In priority order:
   1. **The left depth column** (the "Sunlight Zone" shaft). It looks flat and fake; give it painted trench walls per depth zone.
   2. **Leviathan skin and scar textures.**
   3. **A consistent painted symbol set.** Keep the atlas pipeline in `build_symbol_atlas.py` and derive the normal and emissive maps from the art.
   4. **Per-level layered water backgrounds.**
4. **Near-miss anticipation (crucial).** When the pressure meter is close to the next level, it shudders and the tension builds, in visuals and sound.
5. **Bioluminescent bloom.** Random multiplier spores on symbols, with beautiful visuals.
6. **Sound.** Keep the procedural, reactive layer, and add real samples for the key moments: roar, bite, chain, big wins and the ambience bed. ElevenLabs Sound Effects is a good source, or Freesound with the licence checked. List what's needed and write the generation prompts; I'll generate the files.
7. **Minor items:**
   - The L5 gauge stays full.
   - The radar calls `setState` too often.
   - Clean out the old work folders and the root-level one-off scripts, but ask me first.
