# Prompt pack — edit existing symbols (Gemini app, Nano Banana)

Keep the creatures we already have; strip everything baked around them.

**How:** new Gemini chat per symbol → attach the original from `slot_engine/static/assets/` → paste the prompt → ask for 2–3 versions → save the best as `generated/inbox/p2_edit_existing/<id>_<n>.png`.
If a result drifts, reply in the same chat with only the correction ("Keep the original teeth exactly; only remove the ring.").

Rules baked into every prompt: same subject, same painting style, nothing new added, flat pure black background, square.

---

## high_angler  ← `sym_high_angler.jpg`

```text
Edit this image. Keep the anglerfish exactly as painted — same pose, teeth, eye, glowing cyan lure, skin texture and brushwork. Remove everything else: the ornate brass ring frame, the jewels, the background scene, the game interface buttons and the price label at the bottom. Place the anglerfish alone on a flat pure black background (#000000), centred, filling about 85% of the square, with the lower jaw and the lure allowed to touch the edges. Keep the light coming from the upper left in cyan. Do not add anything new. Square 1:1.
```

## high_squid  ← `sym_high_squid.jpg`

```text
Edit this image. Keep the vampire squid exactly as painted — same body, eye, colours and tentacle shapes. Remove the circular medallion, all lettering ("ABYSSAL", "PHANTOM SQUID"), the anchors and the background. Extend the tentacles naturally where the ring used to cut them off, so they curl outward and slightly past the edges of the square. Flat pure black background (#000000), subject centred, about 85% of the frame. Same painting style and brush texture, cyan rim light from the upper left. Do not add anything new. Square 1:1.
```

## high_viper  ← `sym_high_viper.jpg`

```text
Edit this image. Keep the viperfish exactly as painted — same fangs, eye, body curve, skin and cyan photophores. Remove the copper ring frame and the background. Complete the body and tail where the ring cut them off, matching the existing painting. Flat pure black background (#000000), fish centred and filling about 85% of the square, fangs facing right. Cyan rim light from the upper left. Do not add anything new. Square 1:1.
```

## high_leviathan  ← `sym_high_leviathan.jpg`

```text
Edit this image. Keep the leviathan head exactly as painted — same horns, teeth, red eyes, cyan glowing cracks and texture. Remove the water, spray and all background so the head floats alone on a flat pure black background (#000000). Head centred, filling about 90% of the square, horns may touch the top edge. Slightly darken the lower part of the neck so it fades into the black. Do not add anything new. Square 1:1.
```

## mid_helmet  ← `sym_mid_helmet.jpg`

```text
Edit this image. Keep the brass diving helmet exactly as painted — same dents, rivets, glowing cyan faceplate and corrosion. Remove the circular medallion, all lettering ("VICTORIAN DIVE", "DEEP SEA RICHES"), the anchors and the background. Helmet alone on a flat pure black background (#000000), three-quarter view, centred, filling about 75% of the square. Slightly reduce the yellow saturation of the brass toward an aged, darker copper-brass. Do not add anything new. Square 1:1.
```

## mid_compass  ← `sym_mid_compass.jpg`

```text
Edit this image. Keep the brass compass exactly as painted — its outer ring is part of the object, keep it. Remove only the background around the compass so it sits on a flat pure black background (#000000), centred, filling about 75% of the square. Slightly reduce the yellow saturation of the brass toward an aged, darker copper-brass. Do not add anything new. Square 1:1.
```

## special_wild_maw  ← `sym_wild_maw.jpg`

```text
Edit this image. Keep the maw, its ring of teeth, the rune frame and the word "WILD" exactly as painted. Remove the background outside the frame so the symbol sits on a flat pure black background (#000000). Make the glow deep inside the throat a blood red (#E0314B) instead of teal, keeping the teeth and frame lit cyan from the upper left. Do not add anything new. Square 1:1.
```

---

## Backdrop (optional, P1)  ← `abyssal_trench_bg.jpg`

### trench_far
```text
Edit this image into a background layer. Keep the abyssal trench, fog and cyan light from above. Remove all red and orange rocks and any foreground objects. Darken and simplify the centre of the image into soft black fog, so a game grid can sit there. Keep the painting style. Widescreen 16:9.
```

### trench_mid
```text
From this image, keep only the dark basalt rock formations and vent chimneys at the far left and far right edges, with faint cyan rim light. Replace everything else — the centre, the sky and the fog — with flat pure black (#000000). No red or orange. Keep the painting style. Widescreen 16:9.
```
