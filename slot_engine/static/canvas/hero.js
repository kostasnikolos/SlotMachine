// hero.js - 2.5D Leviathan hero shots for the canvas front end (the Nolimit way: painted close-ups at staged moments,
// no full-body creature in everyday view).
//
// A painting (RGBA cut-out) + its pseudo-depth map (scripts/ai/hero_prep.py) is drawn on its own WebGL canvas
// (data-hero) by ONE fragment program whose "rig" uniforms give every shot its life:
//   - depth parallax (pointer + drift), breathing scale, depth fog, chromatic aberration weighted to the near glass, motes
//   - feathered painting edges (px, measured from the content bbox), a contact overlay under the painting (dark ellipse + ripple)
//   - eye rig: iris ellipse tracking the pointer, a 2-layer eyelid blink filled with skin sampled above the iris, pupil narrowing
//   - jaw rig: the cut-out split at the mouth midline (feathered), lower/upper region translation (the chomp, the slow threat)
//   - rise rig: nodule pulse (blue > 1.5 red mask), a rotation about the neck, fog at the bottom only
//   - maw rig: radial "swallow" scale about the throat, a lure pulse keyed to the counter ticks
// Every shot is opaque and enters / leaves by moving (translate / zoom) under a short alpha ramp; reduced-motion users get a
// plain cross-fade and no blink / slam. Shots: 'lev_eye' (loss reaction), 'lev_jaws' (the bite), 'lev_rise' (level-up),
// 'lev_maw' (500x). ?hero=0 disables the layer.
//
//   const H = window.HeroShots.install(game);   // game = the canvas component (geo(), mouse, timers, flog, setState)
//   H.play('lev_jaws', { anchor: 'throat', at: [x, y], w: side, h: side, chompMs: 1800 });
//   H.chomp(); H.pulse(); H.stop(ms); H.frame(dt);  // from the choreography / the render loop
(function (root) {
  'use strict';

  const VS = 'attribute vec2 p; varying vec2 v; void main() { v = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }';
  const FS = [
    'precision mediump float; varying vec2 v;',
    'uniform sampler2D tC; uniform sampler2D tD; uniform vec2 uRes; uniform vec4 uRect; uniform vec2 uPar; uniform float uT;',
    'uniform float uA; uniform float uFog; uniform float uFogBot; uniform vec3 uTint; uniform vec3 uFogCol; uniform float uScale; uniform vec2 uPivot; uniform float uChrom; uniform float uDark;',
    'uniform vec4 uFeath; uniform vec4 uCont;',          // feather widths (l, r, b, t) in uv; content bbox (x0, x1, y0, y1)
    'uniform vec4 uIris; uniform vec2 uIrisOff; uniform float uPupil; uniform float uLid; uniform vec2 uLidSkin; uniform vec3 uLidCol;',
    'uniform vec4 uJaw;',                                 // hinge y, feather, upper dy (down), lower dy (up)
    'uniform vec3 uRot; uniform vec3 uNod; uniform vec4 uThroat; uniform float uFlash;',
    'uniform vec4 uShadow; uniform float uShadowA; uniform float uRipple; uniform float uBg;',
    'uniform vec4 uSheet;',                               // flipbook: cols, rows, frame index, on (0/1); frames in reading order from the top
    'vec2 fbUv(vec2 u) { if (uSheet.w < 0.5) return u; float i = uSheet.z; float col = mod(i, uSheet.x); float row = floor(i / uSheet.x);',
    '  return vec2((u.x + col) / uSheet.x, (u.y + (uSheet.y - 1.0 - row)) / uSheet.y); }',
    'float ss(float a, float b, float x) { float t = clamp((x - a) / (b - a), 0.0, 1.0); return t * t * (3.0 - 2.0 * t); }',
    'float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }',
    'float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);',
    '  return mix(mix(h2(i), h2(i + vec2(1.0, 0.0)), f.x), mix(h2(i + vec2(0.0, 1.0)), h2(i + vec2(1.0, 1.0)), f.x), f.y); }',
    'void main() {',
    '  vec2 uvR = (v - uRect.xy) / uRect.zw;',
    '  float asp = (uRes.x * uRect.z) / max(1.0, uRes.y * uRect.w);',
    // contact overlay under the painting: a soft dark ellipse on the symbols + a refraction-looking ripple around the iris
    '  vec4 ov = vec4(0.0);',
    '  if (uBg > 0.0 && uvR.x >= 0.0 && uvR.x <= 1.0 && uvR.y >= 0.0 && uvR.y <= 1.0) {',
    '    vec2 tc = uPivot + (uThroat.xy - uPivot) * uScale;',
    '    float dpx = length((uvR - tc) * vec2(uRes.x * uRect.z, uRes.y * uRect.w)) / uRes.x;',
    '    vec2 ar2 = vec2(uRes.x * uRect.z, uRes.y * uRect.w) / 140.0;',
    '    vec2 mp3 = uvR * ar2 + vec2(0.0, uT * 0.06);',
    '    float fogN = n2(mp3 * 1.5 + uT * 0.03) * 0.6 + n2(mp3 * 4.0 - uT * 0.05) * 0.4;',
    '    float mt = pow(n2(mp3 * 3.0) * n2(mp3 * 7.0 + 3.0), 7.0) * 2.2;',
    '    float lamp = 1.0 - 0.55 * ss(0.25, 0.9, dpx);',
    '    vec3 wash = (vec3(0.043, 0.078, 0.094) * (0.7 + 0.6 * fogN) + uFogCol * 0.08 * fogN) * lamp + uTint * mt * 0.5;',
    '    ov = vec4(wash, 1.0) * uBg;',
    '  }',
    '  if (uShadowA > 0.0) {',
    '    vec2 q = (uvR - uShadow.xy) / uShadow.zw;',
    '    float sh = (1.0 - smoothstep(0.5, 1.1, length(q))) * uShadowA;',
    '    vec2 ic = uPivot + (uIris.xy + uIrisOff - uPivot) * uScale;',
    '    vec2 qi = (uvR - ic) / (uIris.zw * uScale * 1.1 + 1e-4);',
    '    float ri = length(qi);',
    '    float rm = (1.0 - smoothstep(0.75, 1.0, ri)) * uRipple;',
    '    float ring = sin(ri * 26.0 - uT * 4.0) * 0.5 + 0.5;',
    '    sh = min(1.0, sh + rm * 0.35 * ring);',
    '    ov = vec4(uTint * rm * (1.0 - ring) * 0.09, sh);',
    '  }',
    // painting space: zoom about the pivot, rotation about the neck, region translations, the throat swallow
    '  vec2 uv = (uvR - uPivot) / uScale + uPivot;',
    '  if (uRot.z != 0.0) { vec2 d = uv - uRot.xy; d.x *= asp; float cs = cos(uRot.z), sn = sin(uRot.z); d = vec2(d.x * cs - d.y * sn, d.x * sn + d.y * cs); d.x /= asp; uv = uRot.xy + d; }',
    '  if (uJaw.y > 0.0) { float hd = uJaw.x + uJaw.w; float lw = 1.0 - smoothstep(hd - uJaw.y, hd + uJaw.y, uv.y); uv.y += -uJaw.w * lw + uJaw.z * (1.0 - lw); }',
    '  if (uThroat.z != 1.0) uv = uThroat.xy + (uv - uThroat.xy) * uThroat.z;',
    '  float mi = 0.0, me = 0.0; vec2 qe = vec2(0.0);',
    '  if (uIris.z > 0.0) {',
    '    qe = (uv - uIris.xy) / (uIris.zw * 1.22);',
    '    float re = length(qe * 1.22);',
    '    mi = 1.0 - smoothstep(0.8, 1.0, re);',
    '    me = 1.0 - smoothstep(1.2, 1.32, re);',
    '    uv -= uIrisOff * mi;',
    '    float mp = 1.0 - smoothstep(0.25, 0.75, re);',
    '    uv.x = mix(uv.x, uIris.x + (uv.x - uIris.x) / max(0.5, uPupil), mp);',
    '  }',
    '  vec4 pc = vec4(0.0);',
    '  if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {',
    '    float d = texture2D(tD, uv).r;',
    '    vec2 sway = vec2(sin(uT * 0.7 + uv.y * 5.0), cos(uT * 0.5 + uv.x * 4.0)) * 0.0025 * (1.0 - d);',
    '    vec2 u2 = uv + uPar * (d - 0.5) * 0.05 + sway;',
    '    vec4 c = texture2D(tC, fbUv(u2));',
    '    float ca = uChrom * 0.0045 * (1.0 - d) * (0.3 + 0.7 * length(v - 0.5));',
    '    c.r = texture2D(tC, fbUv(u2 + vec2(ca, 0.0))).r; c.b = texture2D(tC, fbUv(u2 - vec2(ca, 0.0))).b;',
    '    vec3 col = c.rgb;',
    // nodule pulse: the bioluminescent dots are the pixels with blue well over red
    '    if (uNod.x > 0.0) { float nm = smoothstep(1.3, 1.6, c.b / max(c.r, 0.02)) * smoothstep(0.3, 0.5, c.b);',
    '      float wave = 0.5 + 0.5 * sin(uv.x * 18.85 - uNod.y); col *= mix(1.0, 0.55 + 0.8 * wave + 0.3 * uNod.z, nm); }',
    // the 2-layer eyelid: an upper cap closing down over the iris, a thinner lower lid rising, filled with skin from above the eye
    '    if (uLid > 0.0 && me > 0.0) {',
    '      float cap = sqrt(max(0.0, 1.0 - qe.x * qe.x));',
    '      float dUp = (qe.y - (1.0 - 2.0 * uLid) * cap) * uIris.w * 1.22;',
    '      float dLo = ((-1.0 + 0.75 * uLid) * cap - qe.y) * uIris.w * 1.22;',
    '      float dE = max(dUp, dLo);',
    '      float lw = ss(-0.01, 0.01, dE) * me;',
    '      vec3 membrane = uLidCol * (1.0 - 0.15 * (1.0 - clamp(dE / 0.08, 0.0, 1.0)));',
    '      float rim = (1.0 - ss(0.0, 0.004, abs(dE))) * me;',
    '      col = mix(col, membrane, lw) + uTint * 0.25 * rim;',
    '    }',
    // lure pulse: Biolume in a small mask around the throat
    '    if (uThroat.w > 0.0) { vec2 ql = (uv - uThroat.xy) * vec2(asp, 1.0); float dl = length(ql); float lm = 1.0 - smoothstep(0.0, 0.11, dl);',
    '      col += uTint * uThroat.w * lm * lm * 1.4 + uTint * 0.15 * min(1.0, uThroat.w / 1.6) * (1.0 - ss(0.0, 0.22, dl)); }',
    '    float fog = clamp(uFog * (1.0 - d) + uFogBot * pow(1.0 - uv.y, 1.5), 0.0, 1.0);',
    '    col = mix(col, uFogCol * 0.22, fog * 0.85) * (1.0 - uDark * (1.0 - d) * 0.6);',
    '    vec2 ar = vec2(uRes.x * uRect.z, uRes.y * uRect.w) / 140.0;',
    '    vec2 mp2 = uv * ar + vec2(0.0, uT * 0.06);',
    '    float m = pow(n2(mp2 * 3.0) * n2(mp2 * 7.0 + 3.0), 7.0) * 2.2;',
    '    col += uTint * m * 0.7 * c.a;',
    '    col = mix(col, vec3(0.0), uFlash);',
    // feathered edges, measured from the content bbox
    '    float fe = ss(uCont.x, uCont.x + uFeath.x, uv.x) * ss(uCont.y, uCont.y - uFeath.y, uv.x)',
    '             * ss(uCont.z, uCont.z + uFeath.z, uv.y) * ss(uCont.w, uCont.w - uFeath.w, uv.y);',
    '    float pa = c.a * fe;',
    '    pc = vec4(col * pa, pa) * uA;',
    '  }',
    '  ov *= uA;',
    '  gl_FragColor = pc + ov * (1.0 - pc.a);',
    '}'
  ].join('\n');
  const UNI = ['uSheet', 'tC', 'tD', 'uRes', 'uRect', 'uPar', 'uT', 'uA', 'uFog', 'uFogBot', 'uTint', 'uFogCol', 'uScale', 'uPivot', 'uChrom', 'uDark', 'uFeath', 'uCont',
    'uIris', 'uIrisOff', 'uPupil', 'uLid', 'uLidSkin', 'uLidCol', 'uJaw', 'uRot', 'uNod', 'uThroat', 'uFlash', 'uShadow', 'uShadowA', 'uRipple', 'uBg'];

  // measured feature anchors, in painting image coordinates (x right, y DOWN, 0..1); flipped to GL (y up) when uploaded.
  // Measured off the PNGs with PIL (scripts: see the review notes): iris = the big cyan blob of lev_eye, the lure / throat = the
  // cyan blob in the gullet, the mouth midline of lev_jaws = the darkest row band of the opening, content = alpha bbox.
  const RIG = {
    lev_eye: {
      iris: [0.661, 0.476], irisR: [0.075, 0.13], lidSkin: [0.661, 0.416], cont: [0.309, 0.932, 0.0, 0.969],
      fog: 0.15, dark: 0.2, chrom: 0.3, feather: { l: 120, b: 120 }, shadow: true
    },
    lev_jaws: {
      throat: [0.48, 0.60], hinge: 0.58, hingeFeather: 0.035, cont: [0.198, 0.711, 0.0, 0.927],
      fog: 0.2, dark: 0.2, chrom: 0.6, feather: { l: 80, r: 80, b: 80, t: 110 }
    },
    // the whole-figure lunge (strike beat 2): head frontal at the throat anchor, the body coiling back; zoomed from far to the glass
    lev_lunge: {
      throat: [0.491, 0.665], hinge: 0.656, hingeFeather: 0.03, cont: [0.18, 0.99, 0.0, 1.0],
      fog: 0.25, dark: 0.15, chrom: 0.4, feather: { l: 90, r: 90, b: 90, t: 90 }
    },
    lev_rise: {
      eye: [0.496, 0.514], eyeR: [0.016, 0.028], lidSkin: [0.496, 0.454], neck: [0.5, 0.30], cont: [0.294, 0.709, 0.331, 0.849],
      fog: 0.0, fogBot: 0.65, dark: 0.2, chrom: 0.5, feather: { l: 60, r: 60, b: 160 }, nodules: true
    },
    lev_maw: {
      throat: [0.535, 0.52], lure: [0.535, 0.496], cont: [0.140, 0.862, 0.0, 0.999],
      fog: 0.2, dark: 0.2, chrom: 0.4, feather: { l: 100, r: 100 }, swallow: true, bg: true
    }
  };

  // '#rrggbb' or the canvas's 'r,g,b' accent strings
  function hex(c) {
    if (!c) c = '#3FE0D0';
    if (c.indexOf(',') > 0) { const v = c.split(',').map((x) => parseFloat(x) / 255); return [v[0] || 0, v[1] || 0, v[2] || 0]; }
    const n = parseInt(c.replace('#', ''), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  const EASE = {
    linear: (k) => k,
    outQuart: (k) => 1 - Math.pow(1 - k, 4),
    outCubic: (k) => 1 - Math.pow(1 - k, 3),
    outQuad: (k) => 1 - (1 - k) * (1 - k),
    inCubic: (k) => k * k * k,
    inQuad: (k) => k * k,
    smooth: (k) => k * k * (3 - 2 * k)
  };
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const BIOLUME = hex('#3FE0D0');

  function install(game) {
    if (game.hero) return game.hero;
    if (/[?&]hero=0(&|$)/.test(root.location.search)) return null;
    const H = {
      game, gl: null, canvas: null, prog: null, loc: {}, tex: {}, manifest: null, cur: null, t: 0, par: [0, 0], ready: false, failed: false, base: 'assets/hero/',
      rm: !!(root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)').matches), RIG
    };

    // the hero clock: real time, or frozen at an offset into the current shot (H.freezeAt(ms) / H.freezeAt(null)) so a capture can
    // step the choreography frame by frame
    H.now = () => (H.frozen != null ? H.frozen : performance.now());
    H.freezeAt = (ms) => { H.frozen = ms == null || !H.cur ? null : H.cur.t0 + ms; };

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
      for (const u of UNI) H.loc[u] = gl.getUniformLocation(p, u);
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
        res({ t, w: im.width, h: im.height, im });
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
        if (c && d && m.sheet) {
          const sh = await loadTex(H.base + m.sheet.file + '?v=' + Date.now());
          if (sh) H.tex[id].sheet = Object.assign({ t: sh.t }, m.sheet);
        }
      }
      H.loaded = Object.keys(H.tex);
    };

    // the mean colour of a 5-tap cross around a painting point (image coords), for the flat eyelid membrane
    const sampleCol = (T, pt, cache) => {
      const key = pt[0].toFixed(3) + ',' + pt[1].toFixed(3);
      if (cache[key]) return cache[key];
      let out = [0.25, 0.3, 0.32];
      try {
        const cv = document.createElement('canvas'); cv.width = cv.height = 5;
        const g = cv.getContext('2d', { willReadFrequently: true });
        const d = 0.012, taps = [[0, 0], [d, 0], [-d, 0], [0, d], [0, -d]];
        let r = 0, gg = 0, b = 0, n = 0;
        for (const [dx, dy] of taps) {
          g.clearRect(0, 0, 5, 5);
          g.drawImage(T.c.im, Math.round((pt[0] + dx) * T.w) - 2, Math.round((pt[1] + dy) * T.h) - 2, 5, 5, 0, 0, 5, 5);
          const px = g.getImageData(0, 0, 5, 5).data;
          for (let i = 0; i < px.length; i += 4) { if (px[i + 3] < 128) continue; r += px[i]; gg += px[i + 1]; b += px[i + 2]; n++; }
        }
        if (n) out = [r / n / 255, gg / n / 255, b / n / 255];
      } catch (e) { /* tainted / no 2d: keep the fallback */ }
      cache[key] = out;
      return out;
    };

    // play one shot. rect in stage px (x, y, w, h): the painting is fitted into it (contain, or cover:true); with anchor (a RIG
    // feature name or [u, v] in image coords) + at [x, y] the painting is placed so that feature sits on that stage point; the
    // rect is then clamped inside the stage with `margin` px. Motion: enter {dx, dy, ms, ease, alphaMs} and exit {...} are moves
    // in stage px; zoomFrom -> zoomTo over zoomMs (ease-out), then the breathing.
    H.play = (id, o) => {
      o = o || {};
      if (H.failed || !H.tex[id]) { if (!H.ready) H.load(); if (game.flog) game.flog('heroSkip', { id, reason: H.failed ? 'failed' : 'notLoaded' }); return false; }
      const G = game.geo();
      const T = H.tex[id];
      const R = RIG[id] || {};
      let x = o.x ?? 0, y = o.y ?? 0, w = o.w ?? G.W, h = o.h ?? G.H;
      // fit the painting's aspect into the rect
      const ar = T.w / T.h, rr = w / h;
      if (o.cover ? ar > rr : ar < rr) { const nw = h * ar; x += (w - nw) / 2; w = nw; } else { const nh = w / ar; y += (h - nh) / 2; h = nh; }
      let anchor = o.anchor;
      if (typeof anchor === 'string') anchor = R[anchor];
      if (anchor && o.at) { x = o.at[0] - anchor[0] * w; y = o.at[1] - anchor[1] * h; }
      if (o.margin != null) {
        const mg = o.margin;
        x = Math.max(mg, Math.min(G.W - mg - w, x)); y = Math.max(mg, Math.min(G.H - mg - h, y));
        if (w > G.W - 2 * mg) x = (G.W - w) / 2;
        if (h > G.H - 2 * mg) y = (G.H - h) / 2;
      }
      if (o.minY != null && y < o.minY) y = o.minY;
      if (o.maxY != null && y > o.maxY) y = o.maxY;
      const pivot = o.pivot || (anchor ? [anchor[0], anchor[1]] : [0.5, 0.5]);
      const fe = Object.assign({}, R.feather || {}, o.feather || {});
      const enter = Object.assign({ dx: 0, dy: 0, ms: 0, ease: 'outQuart', alphaMs: o.fadeIn ?? 220 }, o.enter || {});
      const exit = Object.assign({ dx: 0, dy: 0, ms: 0, ease: 'inCubic', alphaMs: o.fadeOut ?? 250, zoomTo: null }, o.exit || {});
      if (H.rm) {
        // reduced motion: no violence beyond a plain cross-fade
        enter.dx = enter.dy = exit.dx = exit.dy = 0; exit.zoomTo = null;
        enter.alphaMs = Math.max(enter.alphaMs, 350); exit.alphaMs = Math.max(exit.alphaMs, 350);
      }
      const now = H.now();
      H.cur = {
        id, x, y, w, h, t0: now, dur: o.dur || 2000, enter, exit,
        zoomFrom: o.zoomFrom ?? 1, zoomTo: o.zoomTo ?? 1.06, zoomMs: o.zoomMs ?? (o.dur || 2000), pivot, tint: BIOLUME, fogCol: o.tint && o.tint !== 'biolume' ? hex(o.tint) : BIOLUME,
        fog: o.fog ?? R.fog ?? 0.2, fogBot: o.fogBot ?? R.fogBot ?? 0, chrom: o.chrom ?? R.chrom ?? 0.5, dark: o.dark ?? R.dark ?? 0.2, alpha: o.alpha ?? 1,
        par: o.par ?? 1, hold: !!o.hold, feather: fe, cont: R.cont || [0, 1, 0, 1], rig: R,
        breath: o.breath ?? 0.012, hitStopMs: o.hitStopMs ?? 67,
        // live rig state
        irisOff: [0, 0], track: [0, 0], lid: 0, pupil: 1, blink: null, nextBlink: null, lastLid: 0,
        jaw: [0, 0], chompT: null, dropT: null, dropped: false, flash: 0, rot: 0, nod: 1, swallow: 1, lure: 0, shadowA: 0, ox: 0, oy: 0,
        lidCol: [0.25, 0.3, 0.32]
      };
      const S = H.cur;
      if (R.lidSkin) { T.cols = T.cols || {}; S.lidCol = sampleCol(T, R.lidSkin, T.cols).map((v, i) => v * 0.6 + [0.36, 0.42, 0.42][i] * 0.4); }   // 40 % toward a dull skin grey: a lid, not a membrane
      if (id === 'lev_eye' || id === 'lev_rise') {
        const arrive = enter.ms;
        // the eye: a full blink 300 ms after arrival and a half-blink 900 ms into the hold; the rising head: one at 1.26 s
        S.blinks = id === 'lev_eye' ? [[arrive + 300, 1], [arrive + 900, 0.5]] : [[arrive + 1260, 1]];
        S.nextBlink = S.blinks[0][0];
      }
      if (o.z != null && game.setState) game.setState({ heroZ: o.z });
      if (game.flog) game.flog('heroPlay', { id, source: T.source, dur: S.dur, rect: [Math.round(x), Math.round(y), Math.round(w), Math.round(h)] });
      return true;
    };

    // end the shot within ms: by its exit move (drop / recede / sink), the alpha ramp only at the very end
    H.stop = (ms) => {
      const S = H.cur;
      if (!S) return;
      ms = ms ?? 350;
      const el = H.now() - S.t0;
      if (S.id === 'lev_jaws' && !H.rm) {
        if (S.dropT == null) { S.dropT = el; S.dropMs = ms; }
        S.dur = Math.min(S.dur, S.dropT + S.dropMs);
        S.exit.alphaMs = 0;
      } else {
        S.exit.ms = H.rm ? 0 : Math.min(S.exit.ms || ms, ms);
        S.exit.alphaMs = Math.min(S.exit.alphaMs, ms);
        S.dur = Math.min(S.dur, el + ms);
      }
      S.hold = false;
    };
    H.active = () => !!H.cur;
    // the bite: jaws slam shut (70 ms), hold through the hit-stop, a 120 ms overshoot, a 60 ms black flash on impact, then the
    // painting drops off the bottom of the stage within 450 ms
    H.chomp = () => {
      const S = H.cur;
      if (!S || S.chompT != null) return false;
      if (!(H.tex[S.id] && H.tex[S.id].sheet) && S.rig.hinge == null) return false;   // a bite needs frames or a jaw hinge
      S.chompT = H.now() - S.t0;
      S.zoomMs = Math.min(S.zoomMs, S.chompT);
      const sh = H.tex[S.id] && H.tex[S.id].sheet;
      if (sh && !H.rm && !/[?&]flipbook=0(&|$)/.test(root.location.search)) {
        // real frames: play the sheet from the chomp at its fps, hold the last frame through the hit-stop + overshoot, then drop
        S.fb = { t0: S.chompT, fps: sh.fps || 24, count: sh.count, cols: sh.cols, rows: sh.rows };
        const playMs = (sh.count - 1) / (sh.fps || 24) * 1000;
        S.flash = 0; S.dropT = S.chompT + playMs + S.hitStopMs + 120; S.dropMs = 450; S.dur = Math.min(S.dur, S.dropT + S.dropMs); S.exit.alphaMs = 0;
        if (game.flog) game.flog('heroFlipbook', { id: S.id, frames: sh.count, fps: sh.fps, playMs: Math.round(playMs) });
        return true;
      }
      if (!H.rm) { S.flash = 1; S.dropT = S.chompT + 70 + S.hitStopMs + 120; S.dropMs = 450; S.dur = Math.min(S.dur, S.dropT + S.dropMs); S.exit.alphaMs = 0; }
      if (game.flog) game.flog('heroChomp', { id: S.id, el: Math.round(S.chompT), dropAt: S.dropT == null ? null : Math.round(S.dropT) });
      return true;
    };
    // the lure pulses with the big-win counter ticks
    H.pulse = (v) => { const S = H.cur; if (S) S.lure = Math.max(S.lure, v ?? 1.6); };
    // the stage point where a painting feature sits right now (for the churn / the contact cue)
    H.featureAt = (name) => {
      const S = H.cur;
      if (!S) return null;
      const f = S.rig[name];
      if (!f) return null;
      return [S.x + S.ox + f[0] * S.w, S.y + S.oy + f[1] * S.h];
    };

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
      const now = H.now();
      const el = now - S.t0;
      if (!S.hold && el >= S.dur) { H.cur = null; H.frozen = null; gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); H.drawn = false; if (game.flog) game.flog('heroEnd', { id: S.id, el: Math.round(el) }); return; }
      const R = S.rig, EN = S.enter, EX = S.exit;
      // ---- envelope: alpha ramps, enter / exit moves ----
      let a = 1;
      if (EN.alphaMs > 0 && el < EN.alphaMs) a = el / EN.alphaMs;
      const exitStart = S.hold ? Infinity : S.dur - EX.ms;
      let ox = 0, oy = 0, scaleX = null;
      if (el < EN.ms) { const k = 1 - (EASE[EN.ease] || EASE.outQuart)(el / EN.ms); ox += EN.dx * k; oy += EN.dy * k; }
      if (!S.hold && EX.alphaMs > 0 && el > S.dur - EX.alphaMs) a = Math.min(a, Math.max(0, (S.dur - el) / EX.alphaMs));
      if (el >= exitStart && EX.ms > 0) { const k = (EASE[EX.ease] || EASE.inCubic)(clamp01((el - exitStart) / EX.ms)); ox += EX.dx * k; oy += EX.dy * k; if (EX.zoomTo != null) scaleX = k; }
      a = a * a * (3 - 2 * a) * S.alpha;
      // parallax: pointer (normalised to the stage) + a slow drift; eased so it never snaps
      const m = game.mouse, M = game.E && game.E.c;
      let px = Math.sin(H.t * 0.31) * 0.35, py = Math.cos(H.t * 0.23) * 0.25;
      const realNow = performance.now();
      if (m && M && realNow - m.t < 4000) { px += (m.x / (M.width || 1) - 0.5) * 1.4; py += (m.y / (M.height || 1) - 0.5) * 1.0; }
      H.par[0] += (px - H.par[0]) * Math.min(1, dt * 2.5);
      H.par[1] += (py - H.par[1]) * Math.min(1, dt * 2.5);
      const kz = Math.min(1, el / Math.max(1, S.zoomMs));
      const breath = 1 + S.breath * Math.sin(H.t * 1.7);
      let zoom = S.zoomFrom + (S.zoomTo - S.zoomFrom) * EASE.outCubic(kz);
      if (scaleX != null) zoom = zoom + (EX.zoomTo - zoom) * scaleX;
      const scale = zoom * breath;
      // ---- the rig ----
      let iris = null, lidSkin = [0, 0], pupil = 1;
      if (R.iris || R.eye) {
        const ic = R.iris || R.eye, ir = R.irisR || R.eyeR;
        iris = [ic[0], ic[1], ir[0], ir[1]];
        lidSkin = R.lidSkin;
        // eye tracking: the iris drifts up to +-0.012 toward the pointer (or the stage centre) with a 400 ms lag
        if (R.iris) {
          const ix = S.x + ox + ic[0] * S.w, iy = S.y + oy + ic[1] * S.h;
          let tx = G.W / 2, ty = G.H / 2;
          if (m && M && realNow - m.t < 4000 && game.E && game.E.c) { const sc = G.gridW / (M.width || 1); tx = G.frameLeft + 20 + m.x * sc; ty = G.frameTop + 20 + (G.gridTop || 0) + m.y * sc; }
          let dx = tx - ix, dy = ty - iy;
          const l = Math.hypot(dx, dy) || 1;
          const amt = Math.min(1, l / (S.w * 0.6)) * 0.012;
          dx = dx / l * amt; dy = dy / l * amt;
          const f = 1 - Math.exp(-dt / 0.4);
          S.track[0] += (dx - S.track[0]) * f; S.track[1] += (dy - S.track[1]) * f;
        }
        // 2-layer blink: close 90 ms, open 140 ms; once after arrival, then every 4-7 s; one at the exit covers the departure
        if (!H.rm) {
          if (!S.blink && S.nextBlink != null && el >= S.nextBlink) {
            const q = S.blinks && S.blinks.length && S.blinks[0][0] <= el ? S.blinks.shift() : null;
            S.blink = { t: el, amp: q ? q[1] : 1 };
            S.nextBlink = S.blinks && S.blinks.length ? S.blinks[0][0] : el + 4000 + Math.random() * 3000;
          }
          if (!S.blink && R.iris && !S.hold && el >= exitStart - 20 && !S.exitBlinked) { S.blink = { t: el, amp: 1 }; S.exitBlinked = true; }
          if (S.blink) {
            const b = el - S.blink.t, A = S.blink.amp;
            S.lid = A * (b < 110 ? EASE.inQuad(b / 110) : b < 150 ? 1 : b < 310 ? 1 - EASE.outQuad((b - 150) / 160) : 0);
            // the slit pupil narrows ~25% as a full lid opens, then relaxes
            if (A >= 1 && b >= 150 && b < 310) S.pupil = 0.75;
            if (b >= 310) { S.blink = null; S.lid = 0; }
          }
          S.pupil += (1 - S.pupil) * Math.min(1, dt * 1.2);
          pupil = S.pupil;
        }
      }
      // jaws: the chomp / the slow threat
      let jaw = [0, 0, 0, 0];
      if (R.hinge != null) {
        let lo = 0, up = 0;
        if (S.chompT != null && !H.rm) {
          const b = el - S.chompT;
          const hs = S.hitStopMs;
          if (b < 70) { const k = EASE.outCubic(b / 70); lo = 0.18 * k; up = 0.05 * k; }
          else if (b < 70 + hs) { lo = 0.18; up = 0.05; }
          else if (b < 70 + hs + 120) { const k = EASE.outQuad((b - 70 - hs) / 120); lo = 0.18 - 0.02 * k; up = 0.05 - 0.01 * k; }
          else { lo = 0.16; up = 0.04; }
          S.flash = b < 60 ? 1 - b / 60 : 0;
        }
        jaw = [1 - R.hinge, R.hingeFeather, up, lo];
        if (S.fb) { const fi = Math.min(S.fb.count - 1, Math.max(0, Math.floor((el - S.fb.t0) / 1000 * S.fb.fps))); S.fbIndex = fi; jaw = [1 - R.hinge, R.hingeFeather, 0, 0]; S.flash = 0; }
        // the drop: the whole painting falls off the bottom of the stage (ease-in-cubic)
        if (S.dropT != null && el >= S.dropT) {
          if (!S.dropped) { S.dropped = true; if (game.flog) game.flog('heroDrop', { id: S.id, el: Math.round(el), ms: S.dropMs }); }
          const k = EASE.inCubic(clamp01((el - S.dropT) / S.dropMs)); oy += G.H * 0.45 * k + S.h * 0.3 * k;
        }
      } else if (R.swallow) {
        // the maw's slow threat: upper jaw down 0.03 and lower up 0.02 over the screen's life
        const k = clamp01(el / 10000);
        jaw = [0.5, 0.12, 0.06 * k, 0.04 * k];
      }
      // rise: nodules pulse (low band when the audio exposes it), the head sways 1.5 deg on a 7 s sine
      let nod = [0, 0, 0], rot = [0.5, 0.5, 0];
      if (R.nodules) {
        const A = root.__aud;
        let lb = 0;
        if (A && typeof A.lowBand === 'function') { try { lb = Math.min(1, (A.lowBand() || 0) * 1.8); } catch (e) { lb = 0; } }
        S.lbS = (S.lbS ?? lb) + (lb - (S.lbS ?? lb)) * Math.min(1, dt * 8);
        // a wave travelling along the crown (3 turns across the painting) at 1.2 Hz
        nod = [1, el / 1000 * 6.2831853 * 1.2, S.lbS];
        if (!H.rm) rot = [R.neck[0], 1 - R.neck[1], 2.5 * Math.PI / 180 * Math.sin(el / 5000 * 6.2831853)];
      }
      // maw: the gullet swallows (radial scale about the throat at 0.45 Hz); the lure pulses with the count
      let throat = [0, 0, 1, 0];
      if (R.swallow) {
        S.lure *= Math.exp(-dt / 0.22);
        if (S.gulpAt == null) S.gulpAt = 600;
        if (el >= S.gulpAt + 2200) S.gulpAt = el + 2200 + Math.random() * 800;    // the next gulp 2.2-3 s after this one
        const g = el - S.gulpAt;
        const gulp = g < 0 ? 0 : g < 400 ? EASE.outQuad(g / 400) : g < 2200 ? 1 - EASE.smooth((g - 400) / 1800) : 0;
        throat = [R.throat[0], 1 - R.throat[1], 1 + (H.rm ? 0.012 : 0.04) * gulp, S.lure];
      }
      // the eye's contact cue on the symbols under it: a soft shadow under the painting's silhouette + the ripple around the iris
      let shadow = [0.5, 0.5, 0.5, 0.5], shadowA = 0, ripple = 0;
      if (R.shadow) {
        const cx = (R.cont[0] + R.cont[1]) / 2, cy = 1 - (R.cont[2] + R.cont[3]) / 2;
        shadow = [cx, cy, (R.cont[1] - R.cont[0]) * 0.55, (R.cont[3] - R.cont[2]) * 0.55];
        shadowA = 0.25; ripple = H.rm ? 0 : 1;
      }
      S.ox = ox; S.oy = oy;
      // ---- draw ----
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(H.prog);
      const T = H.tex[S.id], L = H.loc;
      const fbOn = !!(S.fb && T.sheet);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, fbOn ? T.sheet.t : T.c.t); gl.uniform1i(L.tC, 0);
      gl.uniform4f(L.uSheet, fbOn ? T.sheet.cols : 1, fbOn ? T.sheet.rows : 1, fbOn ? S.fbIndex || 0 : 0, fbOn ? 1 : 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, T.d.t); gl.uniform1i(L.tD, 1);
      gl.uniform2f(L.uRes, c.width, c.height);
      // rect in GL space (origin bottom-left)
      gl.uniform4f(L.uRect, (S.x + ox) / G.W, 1 - (S.y + oy + S.h) / G.H, S.w / G.W, S.h / G.H);
      gl.uniform2f(L.uPar, H.par[0] * S.par, -H.par[1] * S.par);
      gl.uniform1f(L.uT, H.t);
      gl.uniform1f(L.uA, a);
      gl.uniform1f(L.uFog, S.fog);
      gl.uniform1f(L.uFogBot, S.fogBot);
      gl.uniform3f(L.uTint, S.tint[0], S.tint[1], S.tint[2]);
      gl.uniform3f(L.uFogCol, S.fogCol[0], S.fogCol[1], S.fogCol[2]);
      gl.uniform1f(L.uScale, scale);
      gl.uniform2f(L.uPivot, S.pivot[0], 1 - S.pivot[1]);
      gl.uniform1f(L.uChrom, S.chrom);
      gl.uniform1f(L.uDark, S.dark);
      // feather widths in uv (px / rect size, through the zoom), measured from the content bbox
      const fe = S.feather, ct = S.cont;
      const fx = (p) => Math.max(1e-4, (p || 0) / (S.w * scale)), fy = (p) => Math.max(1e-4, (p || 0) / (S.h * scale));
      gl.uniform4f(L.uFeath, fx(fe.l), fx(fe.r), fy(fe.b), fy(fe.t));
      gl.uniform4f(L.uCont, fe.l ? ct[0] : -1, fe.r ? ct[1] : 2, fe.b ? 1 - ct[3] : -1, fe.t ? 1 - ct[2] : 2);
      if (iris) {
        gl.uniform4f(L.uIris, iris[0], 1 - iris[1], iris[2], iris[3]);
        gl.uniform2f(L.uIrisOff, S.track[0], -S.track[1]);
        gl.uniform1f(L.uPupil, pupil);
        gl.uniform1f(L.uLid, S.lid);
        gl.uniform2f(L.uLidSkin, lidSkin[0], 1 - lidSkin[1]);
        gl.uniform3f(L.uLidCol, S.lidCol[0], S.lidCol[1], S.lidCol[2]);
      } else { gl.uniform4f(L.uIris, 0, 0, 0, 0); gl.uniform2f(L.uIrisOff, 0, 0); gl.uniform1f(L.uPupil, 1); gl.uniform1f(L.uLid, 0); gl.uniform2f(L.uLidSkin, 0, 0); gl.uniform3f(L.uLidCol, 0, 0, 0); }
      gl.uniform4f(L.uJaw, jaw[0], jaw[1], jaw[2], jaw[3]);
      gl.uniform3f(L.uRot, rot[0], rot[1], rot[2]);
      gl.uniform3f(L.uNod, nod[0], nod[1], nod[2]);
      gl.uniform4f(L.uThroat, throat[0], throat[1], throat[2], throat[3]);
      gl.uniform1f(L.uFlash, S.flash || 0);
      gl.uniform4f(L.uShadow, shadow[0], shadow[1], shadow[2], shadow[3]);
      gl.uniform1f(L.uShadowA, shadowA);
      gl.uniform1f(L.uRipple, ripple);
      gl.uniform1f(L.uBg, R.bg ? 1 : 0);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      H.drawn = true;
    };

    game.hero = H;
    root.__hero = H;
    return H;
  }

  root.HeroShots = { install, version: 2, RIG };
})(typeof window !== 'undefined' ? window : this);
