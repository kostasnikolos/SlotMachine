// hero.js - 2.5D Leviathan hero shots for the canvas front end (the Nolimit way: painted close-ups at staged moments,
// no full-body creature in everyday view).
//
// A painting (RGBA cut-out) + its pseudo-depth map (scripts/ai/hero_prep.py) is drawn on its own WebGL canvas
// (data-hero) with: depth parallax driven by the pointer and a slow drift, a breathing scale, depth fog, chromatic
// aberration at the glass, drifting motes, and an alpha envelope. Shots: 'lev_eye' (reaction / near-miss),
// 'lev_jaws' (the bite), 'lev_rise' (level-up), 'lev_maw' (max win). ?hero=0 disables the layer.
//
//   const H = window.HeroShots.install(game);   // game = the canvas component (geo(), mouse, timers, flog)
//   H.play('lev_jaws', { x, y, w, h, dur: 1500, zoomFrom: 0.8, zoomTo: 1.15, z: 7 });
//   H.frame(dt);  // from the render loop
(function (root) {
  'use strict';

  const VS = 'attribute vec2 p; varying vec2 v; void main() { v = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }';
  const FS = [
    'precision mediump float; varying vec2 v;',
    'uniform sampler2D tC; uniform sampler2D tD; uniform vec2 uRes; uniform vec4 uRect; uniform vec2 uPar; uniform float uT;',
    'uniform float uA; uniform float uFog; uniform vec3 uTint; uniform float uScale; uniform vec2 uPivot; uniform float uChrom; uniform float uDark;',
    'float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }',
    'float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);',
    '  return mix(mix(h2(i), h2(i + vec2(1.0, 0.0)), f.x), mix(h2(i + vec2(0.0, 1.0)), h2(i + vec2(1.0, 1.0)), f.x), f.y); }',
    'void main() {',
    '  vec2 uv = (v - uRect.xy) / uRect.zw;',
    '  uv = (uv - uPivot) / uScale + uPivot;',
    '  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { gl_FragColor = vec4(0.0); return; }',
    '  float d = texture2D(tD, uv).r;',
    '  vec2 sway = vec2(sin(uT * 0.7 + uv.y * 5.0), cos(uT * 0.5 + uv.x * 4.0)) * 0.0025 * (1.0 - d);',
    '  vec2 u2 = uv + uPar * (d - 0.5) * 0.05 + sway;',
    '  vec4 c = texture2D(tC, u2);',
    '  float ca = uChrom * 0.0035 * (0.3 + 0.7 * length(v - 0.5));',
    '  c.r = texture2D(tC, u2 + vec2(ca, 0.0)).r; c.b = texture2D(tC, u2 - vec2(ca, 0.0)).b;',
    '  float fog = uFog * (1.0 - d);',
    '  vec3 col = mix(c.rgb, uTint * 0.22, fog * 0.85) * (1.0 - uDark * (1.0 - d) * 0.6);',
    '  vec2 ar = vec2(uRes.x * uRect.z, uRes.y * uRect.w) / 140.0;',
    '  vec2 mp = uv * ar + vec2(0.0, uT * 0.06);',
    '  float m = pow(n2(mp * 3.0) * n2(mp * 7.0 + 3.0), 7.0) * 2.2;',
    '  col += uTint * m * 0.7 * c.a;',
    '  gl_FragColor = vec4(col * c.a, c.a) * uA;',
    '}'
  ].join('\n');

  // '#rrggbb' or the canvas's 'r,g,b' accent strings
  function hex(c) {
    if (!c) c = '#3ff5ff';
    if (c.indexOf(',') > 0) { const v = c.split(',').map((x) => parseFloat(x) / 255); return [v[0] || 0, v[1] || 0, v[2] || 0]; }
    const n = parseInt(c.replace('#', ''), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }

  function install(game) {
    if (game.hero) return game.hero;
    if (/[?&]hero=0(&|$)/.test(root.location.search)) return null;
    const H = {
      game, gl: null, canvas: null, prog: null, loc: {}, tex: {}, manifest: null, cur: null, t: 0, par: [0, 0], ready: false, failed: false, base: 'assets/hero/'
    };

    const ensureGL = () => {
      if (H.gl || H.failed) return !!H.gl;
      const c = document.querySelector('canvas[data-hero]');
      if (!c) return false;
      let gl = null;
      try { gl = c.getContext('webgl', { premultipliedAlpha: true, alpha: true, antialias: false }); } catch (e) { gl = null; }
      if (!gl) { H.failed = true; console.warn('hero: WebGL unavailable'); return false; }
      const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn('hero shader', gl.getShaderInfoLog(s)); return null; } return s; };
      const vs = sh(gl.VERTEX_SHADER, VS), fs = sh(gl.FRAGMENT_SHADER, FS);
      if (!vs || !fs) { H.failed = true; return false; }
      const p = gl.createProgram();
      gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) { H.failed = true; console.warn('hero link', gl.getProgramInfoLog(p)); return false; }
      gl.useProgram(p);
      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      const ap = gl.getAttribLocation(p, 'p');
      gl.enableVertexAttribArray(ap);
      gl.vertexAttribPointer(ap, 2, gl.FLOAT, false, 0, 0);
      for (const u of ['tC', 'tD', 'uRes', 'uRect', 'uPar', 'uT', 'uA', 'uFog', 'uTint', 'uScale', 'uPivot', 'uChrom', 'uDark']) H.loc[u] = gl.getUniformLocation(p, u);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
      H.gl = gl; H.canvas = c; H.prog = p;
      return true;
    };

    const loadTex = (url) => new Promise((res) => {
      const im = new Image();
      im.onload = () => {
        const gl = H.gl, t = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        res({ t, w: im.width, h: im.height });
      };
      im.onerror = () => res(null);
      im.src = url;
    });

    // the manifest and the textures load lazily after the first frame; a shot requested before that just skips
    H.load = async () => {
      if (H.ready || H.failed) return;
      if (!ensureGL()) return;
      H.ready = true;
      try {
        const r = await fetch(H.base + 'hero.json?v=' + Date.now());
        if (!r.ok) throw new Error('manifest ' + r.status);
        H.manifest = await r.json();
      } catch (e) { console.warn('hero: no manifest', e); H.failed = true; return; }
      for (const id in H.manifest) {
        const m = H.manifest[id];
        const [c, d] = await Promise.all([loadTex(H.base + m.file + '?v=' + Date.now()), loadTex(H.base + m.depth + '?v=' + Date.now())]);
        if (c && d) H.tex[id] = { c, d, w: c.w, h: c.h, source: m.source };
      }
      H.loaded = Object.keys(H.tex);
    };

    // play one shot. rect in stage px (x, y, w, h); the painting is fitted into it (contain) unless cover:true.
    H.play = (id, o) => {
      o = o || {};
      if (H.failed || !H.tex[id]) { if (!H.ready) H.load(); if (game.flog) game.flog('heroSkip', { id, reason: H.failed ? 'failed' : 'notLoaded' }); return false; }
      const G = game.geo();
      const T = H.tex[id];
      let x = o.x ?? 0, y = o.y ?? 0, w = o.w ?? G.W, h = o.h ?? G.H;
      // fit the painting's aspect into the rect
      const ar = T.w / T.h, rr = w / h;
      if (o.cover ? ar > rr : ar < rr) { const nw = h * ar; x += (w - nw) / 2; w = nw; } else { const nh = w / ar; y += (h - nh) / 2; h = nh; }
      H.cur = {
        id, x, y, w, h, t0: performance.now(), dur: o.dur || 2000, fadeIn: o.fadeIn ?? 220, fadeOut: o.fadeOut ?? 450,
        zoomFrom: o.zoomFrom ?? 1, zoomTo: o.zoomTo ?? 1.06, pivot: o.pivot || [0.5, 0.5], tint: hex(o.tint), fog: o.fog ?? 0.35,
        chrom: o.chrom ?? 1, dark: o.dark ?? 0.3, alpha: o.alpha ?? 1, par: o.par ?? 1, hold: !!o.hold
      };
      if (o.z != null && game.setState) game.setState({ heroZ: o.z });
      if (game.flog) game.flog('heroPlay', { id, source: T.source, dur: H.cur.dur, rect: [Math.round(x), Math.round(y), Math.round(w), Math.round(h)] });
      return true;
    };
    H.stop = (ms) => { if (H.cur) { H.cur.dur = Math.min(H.cur.dur, performance.now() - H.cur.t0 + (ms ?? 350)); H.cur.fadeOut = ms ?? 350; H.cur.hold = false; } };
    H.active = () => !!H.cur;

    H.frame = (dt) => {
      if (!H.ready) { H.load(); return; }
      const gl = H.gl;
      if (!gl) return;
      const c = H.canvas, G = game.geo();
      if (c.width !== G.W || c.height !== G.H) { c.width = G.W; c.height = G.H; }
      gl.viewport(0, 0, c.width, c.height);
      const S = H.cur;
      if (!S) { if (H.drawn) { gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); H.drawn = false; } return; }
      H.t += dt;
      const el = performance.now() - S.t0;
      let a = 1;
      if (el < S.fadeIn) a = el / S.fadeIn;
      if (!S.hold && el > S.dur - S.fadeOut) a = Math.min(a, Math.max(0, (S.dur - el) / S.fadeOut));
      if (!S.hold && el >= S.dur) { H.cur = null; gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); H.drawn = false; if (game.flog) game.flog('heroEnd', { id: S.id }); return; }
      a = a * a * (3 - 2 * a) * S.alpha;
      // parallax: pointer (normalised to the stage) + a slow drift; eased so it never snaps
      const m = game.mouse, M = game.E && game.E.c;
      let px = Math.sin(H.t * 0.31) * 0.35, py = Math.cos(H.t * 0.23) * 0.25;
      if (m && M && performance.now() - m.t < 4000) { px += (m.x / (M.width || 1) - 0.5) * 1.4; py += (m.y / (M.height || 1) - 0.5) * 1.0; }
      H.par[0] += (px - H.par[0]) * Math.min(1, dt * 2.5);
      H.par[1] += (py - H.par[1]) * Math.min(1, dt * 2.5);
      const k = Math.min(1, el / S.dur), ke = 1 - Math.pow(1 - k, 2);
      const breath = 1 + 0.012 * Math.sin(H.t * 1.7);
      const scale = (S.zoomFrom + (S.zoomTo - S.zoomFrom) * ke) * breath;
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(H.prog);
      const T = H.tex[S.id];
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, T.c.t); gl.uniform1i(H.loc.tC, 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, T.d.t); gl.uniform1i(H.loc.tD, 1);
      gl.uniform2f(H.loc.uRes, c.width, c.height);
      // rect in GL space (origin bottom-left)
      gl.uniform4f(H.loc.uRect, S.x / G.W, 1 - (S.y + S.h) / G.H, S.w / G.W, S.h / G.H);
      gl.uniform2f(H.loc.uPar, H.par[0] * S.par, -H.par[1] * S.par);
      gl.uniform1f(H.loc.uT, H.t);
      gl.uniform1f(H.loc.uA, a);
      gl.uniform1f(H.loc.uFog, S.fog);
      gl.uniform3f(H.loc.uTint, S.tint[0], S.tint[1], S.tint[2]);
      gl.uniform1f(H.loc.uScale, scale);
      gl.uniform2f(H.loc.uPivot, S.pivot[0], 1 - S.pivot[1]);
      gl.uniform1f(H.loc.uChrom, S.chrom);
      gl.uniform1f(H.loc.uDark, S.dark);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      H.drawn = true;
    };

    game.hero = H;
    root.__hero = H;
    return H;
  }

  root.HeroShots = { install, version: 1 };
})(typeof window !== 'undefined' ? window : this);
