// Stage v2 art manifest — the ONLY place texture paths live.
// To swap in cleaned Gemini art, drop files at the `v2` path (slot_engine/static/assets/v2/<category>/<id>.png).
// The loader tries `v2` first and silently falls back to `placeholder` if the file is missing.
// Paths are relative to stage_v2/index.html. `placeholder: "glyph:X"` = procedural carved-basalt glyph.
// `scale` = cell coverage (art bible §4: lows ~0.7, mids 1.0, highs overscan 1.1–1.2).
// `normal` is loaded only when that symbol's v2 art exists (keep it <=512px; G7 budget).
// `scalePlaceholder` is used while the old framed JPGs are in place (their baked frames must not overlap).
window.STAGE_MANIFEST = {
  layers: {
    trench_far:  { v2: '../assets/v2/backdrop/trench_far.png',  placeholder: '../assets/abyssal_trench_bg.jpg' },
    trench_mid:  { v2: '../assets/v2/backdrop/trench_mid.png',  placeholder: '../assets/abyssal_trench_bg.jpg' },
    trench_near: { v2: '../assets/v2/backdrop/trench_near.png', placeholder: '../assets/abyssal_trench_bg.jpg' },
    creature:    { v2: '../assets/v2/creature/leviathan_silhouette.png', placeholder: '../assets/leviathan_creature_strike.jpg' }
  },
  symbols: {
    '10':      { tier: 'low',  v2: '../assets/v2/symbols/low_10.png', placeholder: 'glyph:10', scale: 0.72 },
    'J':       { tier: 'low',  v2: '../assets/v2/symbols/low_j.png',  placeholder: 'glyph:J',  scale: 0.72 },
    'Q':       { tier: 'low',  v2: '../assets/v2/symbols/low_q.png',  placeholder: 'glyph:Q',  scale: 0.72 },
    'K':       { tier: 'low',  v2: '../assets/v2/symbols/low_k.png',  placeholder: 'glyph:K',  scale: 0.72 },
    'A':       { tier: 'low',  v2: '../assets/v2/symbols/low_a.png',  placeholder: 'glyph:A',  scale: 0.72 },
    helmet:    { tier: 'mid',  v2: '../assets/v2/symbols/mid_helmet.png',  placeholder: '../assets/sym_mid_helmet.jpg',  normal: '../assets/v2/symbols/mid_helmet_normal.png',  scale: 1.0 },
    compass:   { tier: 'mid',  v2: '../assets/v2/symbols/mid_compass.png', placeholder: '../assets/sym_mid_compass.jpg', normal: '../assets/v2/symbols/mid_compass_normal.png', scale: 1.0 },
    angler:    { tier: 'high', v2: '../assets/v2/symbols/high_angler.png',    placeholder: '../assets/sym_high_angler.jpg',    normal: '../assets/v2/symbols/high_angler_normal.png',    scale: 1.16 },
    squid:     { tier: 'high', v2: '../assets/v2/symbols/high_squid.png',     placeholder: '../assets/sym_high_squid.jpg',     normal: '../assets/v2/symbols/high_squid_normal.png',     scale: 1.16 },
    viper:     { tier: 'high', v2: '../assets/v2/symbols/high_viper.png',     placeholder: '../assets/sym_high_viper.jpg',     normal: '../assets/v2/symbols/high_viper_normal.png',     scale: 1.16 },
    leviathan: { tier: 'high', v2: '../assets/v2/symbols/high_leviathan.png', placeholder: '../assets/sym_high_leviathan.jpg', normal: '../assets/v2/symbols/high_leviathan_normal.png', scale: 1.18 },
    wild:      { tier: 'special', v2: '../assets/v2/symbols/special_wild_maw.png', placeholder: '../assets/sym_wild_maw.jpg', normal: '../assets/v2/symbols/special_wild_maw_normal.png', scale: 1.0 },
    scatter:   { tier: 'special', v2: '../assets/v2/symbols/special_scatter.png',  placeholder: '../assets/token_abyssal_pearl.jpg', scale: 1.0 }
  },
  scalePlaceholder: 0.96,
  uvInsetPlaceholder: 0.05,
  // Hard-coded 5x5 showcase board (rows top -> bottom). No math/API dependency.
  board: [
    ['A',       'angler', 'K',       'wild',      'Q'],
    ['helmet',  'J',      'squid',   '10',        'compass'],
    ['K',       'viper',  'A',       'leviathan', 'J'],
    ['10',      'Q',      'scatter', 'K',         'angler'],
    ['compass', 'A',      'J',       'helmet',    '10']
  ]
};
