/* Stage v2 — 2.5D layered Three.js stage (art_bible.md §5). Three.js r128 (global THREE).
   Layers: 0 trench planes + caustics, 1 creature + key light, 2 procedural frame with meters,
   3 lit symbol quads, 5 post (vignette + depth grade), 6 DOM (index.html).
   All colors from the art bible palette. Custom shaders work in linear space; post does ACES + sRGB. */
(function () {
  'use strict';
  var M = window.STAGE_MANIFEST;
  var Q = new URLSearchParams(location.search);
  var PAL = { abyss: '#02060A', trench: '#0B1418', silt: '#1E2C31', bone: '#F2E6CF', mist: '#C3D1D4',
    bio: '#3FE0D0', brass: '#B8874A', brass2: '#D9B77E', sulfur: '#E8B04A', blood: '#E0314B' };
  function lin(hex) { return new THREE.Color(hex).convertSRGBToLinear(); }

  // ---------- grid geometry constants (world units, 1 = one cell) ----------
  var CELL = 1, GAP = 0.06, N = 5;
  var GW = N * CELL + (N - 1) * GAP, HALF = GW / 2, LIP = 0.12;
  var PORTRAIT = window.innerWidth / window.innerHeight < 0.8; // frame variant picked at boot (no rebuild on rotate)
  var FR = PORTRAIT ? { L: HALF + LIP + 0.4, R: HALF + LIP + 0.2, T: HALF + LIP + 0.95, B: HALF + LIP + 0.95 }
                    : { L: HALF + LIP + 0.75, R: HALF + LIP + 0.42, T: HALF + LIP + 0.95, B: HALF + LIP + 0.95 };
  var FW = FR.L + FR.R, FH = FR.T + FR.B;
  var FCX = (FR.R - FR.L) / 2, FCY = (FR.T - FR.B) / 2;
  var KEY_POS = new THREE.Vector3(-2.4, 3.6, 3.4); // shared by creature glow + symbol/frame lighting
  var FOV = 38, DOM_PX = 84;

  // ---------- renderer / scene ----------
  var canvas = document.getElementById('stage');
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputEncoding = THREE.LinearEncoding;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.localClippingEnabled = true;
  var scene = new THREE.Scene();
  scene.background = lin(PAL.abyss);
  var camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 200);
  var camBase = new THREE.Vector3(), camTarget = new THREE.Vector3(FCX, FCY, 0);

  var hdr = renderer.capabilities.isWebGL2 && !!renderer.extensions.get('EXT_color_buffer_float');
  var rt = new THREE.WebGLRenderTarget(4, 4, { type: hdr ? THREE.HalfFloatType : THREE.UnsignedByteType,
    minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: true });
  if (renderer.capabilities.isWebGL2 && THREE.WebGLMultisampleRenderTarget) {
    rt = new THREE.WebGLMultisampleRenderTarget(4, 4, { type: hdr ? THREE.HalfFloatType : THREE.UnsignedByteType });
    rt.samples = 4;
  }

  // ---------- state + shared uniforms ----------
  var state = { depth: parseFloat(Q.get('depth') || '1650'), ritual: parseFloat(Q.get('ritual') || '0.62'), seals: parseInt(Q.get('seals') || '2', 10) };
  var U = { uRes: { value: new THREE.Vector2(1, 1) }, uTime: { value: 0 }, uGrade: { value: lin(PAL.bio) }, uFill: { value: 0 }, uRitual: { value: state.ritual } };
  function depthToFill(m) { // non-linear gauge: 0-2k / 2k-5k / 5k-11k each take a third
    if (m <= 2000) return m / 2000 / 3;
    if (m <= 5000) return 1 / 3 + (m - 2000) / 3000 / 3;
    return Math.min(1, 2 / 3 + (m - 5000) / 6000 / 3);
  }
  function depthGrade(m) {
    var a = lin(PAL.bio), b = lin(PAL.sulfur), c = lin(PAL.blood);
    if (m <= 2000) return a.clone();
    if (m <= 5000) return a.clone().lerp(b, (m - 2000) / 3000);
    return b.clone().lerp(c, Math.min(1, (m - 5000) / 6000));
  }

  // ---------- texture loading with v2 -> placeholder fallback ----------
  THREE.Cache.enabled = true; // trench placeholder is shared by 3 planes: fetch once
  var texLoader = new THREE.TextureLoader();
  function loadTex(url, srgb) {
    return new Promise(function (res, rej) {
      texLoader.load(url, function (t) { if (srgb) t.encoding = THREE.sRGBEncoding; t.anisotropy = 4; res(t); }, undefined, rej);
    });
  }
  function loadArt(entry, srgb) {
    if (Q.has('placeholders')) return loadPlaceholder(entry, srgb);
    return loadTex(entry.v2, srgb).then(function (t) { t.isV2 = true; return t; },
      function () { return loadPlaceholder(entry, srgb); });
  }
  function loadPlaceholder(entry, srgb) {
    if (entry.placeholder.indexOf('glyph:') === 0) return Promise.resolve(glyphTexture(entry.placeholder.slice(6)));
    return loadTex(entry.placeholder, srgb);
  }

  // ---------- procedural canvas textures ----------
  function mkCanvas(w, h) { var c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
  function hash(x, y, s) { var h = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453; return h - Math.floor(h); }
  function vnoise(x, y, s, p) { // tileable value noise, period p
    var xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    var u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    function g(a, b) { return hash(((a % p) + p) % p, ((b % p) + p) % p, s); }
    return (g(xi, yi) * (1 - u) + g(xi + 1, yi) * u) * (1 - v) + (g(xi, yi + 1) * (1 - u) + g(xi + 1, yi + 1) * u) * v;
  }
  function surfaceTex(base, dark, light, scale, streak) { // basalt / steel / brass albedo
    var S = 256, c = mkCanvas(S, S), ctx = c.getContext('2d'), img = ctx.createImageData(S, S);
    var b = new THREE.Color(base), d = new THREE.Color(dark), l = new THREE.Color(light);
    for (var y = 0; y < S; y++) for (var x = 0; x < S; x++) {
      var n = 0, a = 0.5, f = scale;
      for (var o = 0; o < 4; o++) { n += a * vnoise(x / S * f, (streak ? y / S * f * 0.25 : y / S * f), o, f); a *= 0.5; f *= 2; }
      var col = n < 0.5 ? d.clone().lerp(b, n * 2) : b.clone().lerp(l, (n - 0.5) * 2);
      if (hash(x, y, 9) > 0.985) col.lerp(l, 0.5); // mineral flecks
      var i = (y * S + x) * 4; img.data[i] = col.r * 255; img.data[i + 1] = col.g * 255; img.data[i + 2] = col.b * 255; img.data[i + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    var t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.encoding = THREE.sRGBEncoding; return t;
  }
  function glyphTexture(label) { // carved basalt glyph on transparent ground (low tier placeholder)
    var S = 256, c = mkCanvas(S, S), ctx = c.getContext('2d');
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = '700 ' + (label.length > 1 ? 150 : 190) + 'px Georgia, "Times New Roman", serif';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = PAL.abyss; ctx.lineWidth = 22; ctx.strokeText(label, S / 2, S / 2 + 8);
    var g = ctx.createLinearGradient(0, 30, 0, 230); g.addColorStop(0, '#5b6a6c'); g.addColorStop(0.5, '#2d3a3d'); g.addColorStop(1, '#151e21');
    ctx.fillStyle = g; ctx.fillText(label, S / 2, S / 2 + 8);
    ctx.globalCompositeOperation = 'source-atop'; // chisel noise + biolume rim from key light (upper-left)
    for (var i = 0; i < 900; i++) { ctx.fillStyle = 'rgba(0,0,0,' + (Math.random() * 0.35) + ')'; ctx.fillRect(Math.random() * S, Math.random() * S, 2 + Math.random() * 5, 1 + Math.random() * 2); }
    ctx.globalCompositeOperation = 'source-over';
    ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(63,224,208,0.55)'; ctx.save(); ctx.translate(-2, -3); ctx.strokeText(label, S / 2, S / 2 + 8); ctx.restore();
    var t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.isGlyph = true; return t;
  }
  function runeTexture(seed) { // rune-seal face glyph (white strokes; tinted by material)
    var S = 128, c = mkCanvas(S, S), ctx = c.getContext('2d');
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 7; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(64, 26); ctx.lineTo(64, 102);
    for (var i = 0; i < 3; i++) { var y = 34 + hash(seed, i, 2) * 50, dir = hash(seed, i, 3) > 0.5 ? 1 : -1;
      ctx.moveTo(64, y); ctx.lineTo(64 + dir * (16 + hash(seed, i, 4) * 14), y + (hash(seed, i, 5) > 0.5 ? 18 : -18)); }
    ctx.stroke();
    return new THREE.CanvasTexture(c);
  }
  function plaqueTexture(text) {
    var c = mkCanvas(256, 64), ctx = c.getContext('2d');
    ctx.fillStyle = '#0b1418'; ctx.fillRect(0, 0, 256, 64);
    ctx.strokeStyle = 'rgba(217,183,126,.6)'; ctx.lineWidth = 2; ctx.strokeRect(4, 4, 248, 56);
    ctx.fillStyle = PAL.bone; ctx.font = '600 32px Georgia, serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 34);
    var t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t;
  }

  // ---------- LAYER 0: trench backdrop (3 parallax planes + caustics/fog) ----------
  var BG_VS = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }';
  var BG_FS = [
    'uniform sampler2D tMap; uniform float uTime, uDim, uKey, uCaustic, uFeather; uniform vec2 uOff, uScale, uRes; uniform vec3 uFog, uBio;',
    'varying vec2 vUv;',
    'float cau(vec2 p){ float c=0.0; for(int i=0;i<3;i++){ p = p*1.7 + vec2(sin(p.y*1.3+uTime*0.35), cos(p.x*1.1-uTime*0.27)); c += abs(sin(p.x)+sin(p.y)); } return pow(max(0.0, 1.0 - c/3.2), 3.0); }',
    'void main(){',
    '  vec2 uv = uOff + (vUv - 0.5) * uScale + 0.5;',
    '  vec3 c = pow(texture2D(tMap, uv).rgb, vec3(2.2));',
    '  float lum = dot(c, vec3(0.3,0.59,0.11));',
    '  c = mix(vec3(lum), c, 0.4) * uDim;', // desaturate toward trench
    '  float h = smoothstep(0.0, 1.0, vUv.y);',
    '  c += uBio * cau(vUv * vec2(9.0, 5.0)) * uCaustic * h;',
    '  c = mix(uFog, c, mix(0.55, 1.0, h));', // depth fog rises from the floor
    '  float edge = smoothstep(0.0, uFeather, vUv.x) * smoothstep(0.0, uFeather, 1.0-vUv.x) * smoothstep(0.0, uFeather, vUv.y) * smoothstep(0.0, uFeather, 1.0-vUv.y);',
    '  float a = uKey > 0.5 ? smoothstep(0.004, 0.05, lum) * edge : 1.0;', // mid/near planes: keyed by luminance
    '  float sx = gl_FragCoord.x / uRes.x; c *= mix(1.0, 0.28, smoothstep(0.4, 1.0, sx));', // falloff away from the key (left)
    '  gl_FragColor = vec4(c, a);',
    '}'].join('\n');
  function bgPlane(z, opts) {
    var mat = new THREE.ShaderMaterial({ vertexShader: BG_VS, fragmentShader: BG_FS, transparent: opts.key, depthWrite: false,
      uniforms: { tMap: { value: null }, uTime: U.uTime, uRes: U.uRes, uDim: { value: opts.dim }, uKey: { value: opts.key ? 1 : 0 }, uCaustic: { value: opts.caustic },
        uFeather: { value: 0.2 }, uOff: { value: new THREE.Vector2(opts.off[0], opts.off[1]) }, uScale: { value: new THREE.Vector2(opts.scale, opts.scale) },
        uFog: { value: lin('#06141a') }, uBio: { value: lin(PAL.bio) } } });
    var m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat); m.position.z = z; m.renderOrder = -10 + z * 0.01; m.userData.z = z;
    scene.add(m); return m;
  }
  var bgFar = bgPlane(-34, { dim: 0.55, key: false, caustic: 0.35, off: [0, 0], scale: 1.0 });
  var bgMid = bgPlane(-20, { dim: 0.7, key: true, caustic: 0.0, off: [0.18, -0.08], scale: 0.55 });
  var bgNear = bgPlane(-11, { dim: 0.45, key: true, caustic: 0.0, off: [-0.3, -0.25], scale: 0.4 });
  var bgPlanes = [bgFar, bgMid, bgNear];

  // ---------- LAYER 1: creature + key light ----------
  var creatureMat = new THREE.ShaderMaterial({ vertexShader: BG_VS, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { tMap: { value: null }, uTime: U.uTime, uDim: { value: 0.55 }, uAlpha: { value: 0.0 } },
    fragmentShader: [
      'uniform sampler2D tMap; uniform float uTime, uDim, uAlpha; varying vec2 vUv;',
      'void main(){ vec3 c = pow(texture2D(tMap, vUv).rgb, vec3(2.2));',
      '  float l = dot(c, vec3(0.3,0.59,0.11));',
      '  c = mix(vec3(l)*vec3(0.55,0.9,0.95), c, 0.75);',
      '  float r = length((vUv-0.5)*vec2(1.1,1.3)); float m = smoothstep(0.62, 0.15, r);',
      '  gl_FragColor = vec4(c * uDim * m * (0.85 + 0.15*sin(uTime*0.8)), 1.0); }'].join('\n') });
  var creature = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), creatureMat);
  var creatureBase = new THREE.Vector3(0, 0, -6); creature.renderOrder = -5; scene.add(creature);

  var keyLight = new THREE.PointLight(lin(PAL.bio), 2.6, 16, 1.6); keyLight.position.copy(KEY_POS); scene.add(keyLight);
  var keyFill = new THREE.DirectionalLight(lin(PAL.mist), 0.2); keyFill.position.copy(KEY_POS); scene.add(keyFill); // same direction, neutral, so albedo reads
  scene.add(new THREE.HemisphereLight(lin('#163a40'), lin(PAL.abyss), 0.15)); // cold teal ambient, low
  var glowTex = (function () { var c = mkCanvas(128, 128), x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.35, 'rgba(255,255,255,.25)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
  var keyGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, color: lin(PAL.bio), blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.55 }));
  keyGlow.scale.set(9, 9, 1); keyGlow.position.set(KEY_POS.x, KEY_POS.y, -4.5); keyGlow.renderOrder = -4; scene.add(keyGlow);

  // ---------- LAYER 2: frame ----------
  var mats = {
    basalt: new THREE.MeshStandardMaterial({ map: surfaceTex('#0B1418', '#02060A', '#26363b', 6, false), roughness: 0.95, metalness: 0.0 }),
    steel: new THREE.MeshStandardMaterial({ map: surfaceTex('#2c3437', '#11191c', '#5a6669', 10, true), roughness: 0.4, metalness: 0.6 }),
    brass: new THREE.MeshStandardMaterial({ map: surfaceTex('#94552C', '#43220e', '#C98A55', 12, true), roughness: 0.32, metalness: 0.6, emissive: lin('#5a2a10'), emissiveIntensity: 0.45 }), // red-copper bias: cyan key x yellow brass reads olive
    recess: new THREE.MeshStandardMaterial({ color: lin(PAL.abyss), roughness: 1 }),
    back: new THREE.MeshStandardMaterial({ color: lin('#070d10'), roughness: 0.9, metalness: 0.0 })
  };
  mats.basalt.map.repeat.set(1.5, 1.5); // world-unit UVs on extrudes (see SKILL "bubble wrap")
  function frameShade(mat, cavity) { // AO into the grid cavity + inner corners, floor darkening, falloff to near-black lower-right
    mat.onBeforeCompile = function (sh) {
      sh.vertexShader = 'varying vec3 vWP;\n' + sh.vertexShader.replace('#include <project_vertex>', '#include <project_vertex>\n vWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = 'varying vec3 vWP;\n' + sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n' +
        ' vec2 q = abs(vWP.xy) - vec2(' + IN.toFixed(3) + ');\n' +
        ' float dIn = max(q.x, q.y), corner = length(max(q, 0.0));\n' +
        ' float ao = mix(' + cavity + ', 1.0, smoothstep(0.0, 0.45, dIn)) * mix(0.6, 1.0, smoothstep(0.0, 0.7, corner));\n' +
        ' ao *= mix(0.55, 1.0, smoothstep(' + (-FR.B).toFixed(2) + ', ' + FR.T.toFixed(2) + ', vWP.y));\n' +
        ' ao *= mix(1.0, 0.1, smoothstep(-1.5, 6.0, vWP.x - vWP.y));\n' +
        ' diffuseColor.rgb *= ao;');
    };
  }
  frameShade(mats.basalt, '0.35'); frameShade(mats.steel, '0.6'); frameShade(mats.brass, '0.8');

  mats.steel.map.repeat.set(0.35, 0.35); mats.brass.map.repeat.set(0.5, 0.5);
  function rectPath(p, x0, y0, x1, y1) { p.moveTo(x0, y0); p.lineTo(x1, y0); p.lineTo(x1, y1); p.lineTo(x0, y1); p.lineTo(x0, y0); return p; }
  function ring(x0, y0, x1, y1, t, depth, bevel, mat, z) { // rectangular extruded ring, inner hole x0..x1, thickness t
    var s = rectPath(new THREE.Shape(), x0 - t, y0 - t, x1 + t, y1 + t);
    s.holes.push(rectPath(new THREE.Path(), x0, y0, x1, y1));
    var g = new THREE.ExtrudeGeometry(s, { depth: depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2 });
    var m = new THREE.Mesh(g, mat); m.position.z = z; scene.add(m); return m;
  }
  function box(w, h, d, mat, x, y, z) { var m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); scene.add(m); return m; }
  function cyl(r, h, mat, x, y, z, rotX) { var m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 32), mat); m.position.set(x, y, z); if (rotX) m.rotation.x = Math.PI / 2; scene.add(m); return m; }

  var IN = HALF + LIP;
  // basalt body (asymmetric: wide left pillar, deep lintel)
  (function () {
    var s = rectPath(new THREE.Shape(), -FR.L, -FR.B, FR.R, FR.T);
    s.holes.push(rectPath(new THREE.Path(), -IN, -IN, IN, IN));
    var g = new THREE.ExtrudeGeometry(s, { depth: 0.42, bevelEnabled: true, bevelThickness: 0.1, bevelSize: 0.1, bevelSegments: 3 });
    var m = new THREE.Mesh(g, mats.basalt); m.position.z = -0.1; scene.add(m);
  })();
  box(GW + 0.4, GW + 0.4, 0.1, mats.back, 0, 0, -0.3); // reel backplane
  ring(-IN, -IN, IN, IN, 0.13, 0.2, 0.03, mats.steel, 0.36); // steel bezel around grid
  ring(-FR.L, -FR.B, FR.R, FR.T, 0.12, 0.12, 0.07, mats.brass, 0.28); // brass outer trim, fat bevel catches the key
  for (var ci = 1; ci < N; ci++) box(0.035, GW, 0.04, mats.steel, -HALF + ci * (CELL + GAP) - GAP / 2, 0, -0.2); // reel separators
  // rivets on the bezel
  (function () {
    var g = new THREE.CylinderGeometry(0.045, 0.05, 0.05, 10); g.rotateX(Math.PI / 2);
    var pts = []; for (var i = 0; i <= 10; i++) { var t = -IN - 0.065 + (2 * IN + 0.13) * i / 10; pts.push([t, IN + 0.065], [t, -IN - 0.065], [IN + 0.065, t], [-IN - 0.065, t]); }
    var im = new THREE.InstancedMesh(g, mats.brass, pts.length), o = new THREE.Object3D();
    pts.forEach(function (p, i) { o.position.set(p[0], p[1], 0.6); o.updateMatrix(); im.setMatrixAt(i, o.matrix); });
    scene.add(im);
  })();

  // plate seams: carved dark grooves with a lit upper-left lip, splitting pillars/lintel/top band into bevelled panels
  (function () {
    var groove = new THREE.MeshStandardMaterial({ color: lin(PAL.abyss), roughness: 1 }), Z = 0.425, W = 0.03;
    function seamH(x0, x1, y) { box(x1 - x0, W, 0.012, groove, (x0 + x1) / 2, y, Z); box(x1 - x0, 0.012, 0.012, mats.steel, (x0 + x1) / 2, y + W * 0.7, Z + 0.002); }
    function seamV(x, y0, y1) { box(W, y1 - y0, 0.012, groove, x, (y0 + y1) / 2, Z); box(0.012, y1 - y0, 0.012, mats.steel, x - W * 0.7, (y0 + y1) / 2, Z + 0.002); }
    var e = 0.1, ox = -FR.L + e, rx = FR.R - e, by = -FR.B + e, ty = FR.T - e;
    seamV(-IN - 0.16, -IN - 0.16, IN + 0.16);           // pillar inner panel edge
    seamH(ox, -IN - 0.16, IN * 0.35); seamH(ox, -IN - 0.16, -IN * 0.45); // pillar plates
    seamH(-IN - 0.16, IN + 0.16, -IN - 0.2);           // lintel top edge
    seamV(-IN - 0.16, by, -IN - 0.2);
    seamV(IN + 0.16, by, -IN - 0.2); seamV(IN + 0.16, IN + 0.16, ty);
    seamH(-IN - 0.16, IN + 0.16, IN + 0.16);           // top band lower edge
    seamV(-IN - 0.16, IN + 0.16, ty);
  })();

  // depth gauge tube in the left pillar
  var GR = PORTRAIT ? 0.07 : 0.11, GX = PORTRAIT ? -IN - 0.25 : -IN - 0.46, GH = GW * 0.86, GY = 0.18, TS = PORTRAIT ? -1 : 1; // TS: tick side
  box(GR * 4, GH + 0.3, 0.2, mats.recess, GX, GY, 0.32);
  var gaugeMat = new THREE.ShaderMaterial({ uniforms: { uTime: U.uTime, uFill: U.uFill, uGrade: U.uGrade, uGlass: { value: lin(PAL.silt) } },
    vertexShader: 'varying vec2 vUv; varying vec3 vN; void main(){ vUv=uv; vN=normalize(normalMatrix*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: [
      'uniform float uTime, uFill; uniform vec3 uGrade, uGlass; varying vec2 vUv; varying vec3 vN;',
      'float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453); }',
      'void main(){ float rim = pow(1.0 - abs(vN.z), 2.0);',
      '  float lvl = uFill + 0.006*sin(vUv.x*25.0 + uTime*2.0);',
      '  float inF = step(vUv.y, lvl);',
      '  vec2 g = vec2(vUv.x*10.0, vUv.y*64.0 - uTime*2.5); vec2 id = floor(g), f = fract(g) - 0.5;',
      '  float b = step(0.86, h(id)) * smoothstep(0.32, 0.08, length(f + 0.15*vec2(h(id+1.7)-0.5, 0.0))) * inF * smoothstep(lvl, lvl-0.05, vUv.y);',
      '  vec3 liquid = uGrade * (0.75 + 0.35*smoothstep(lvl-0.06, lvl, vUv.y)) + (uGrade*0.6 + 0.25)*b;',
      '  vec3 glass = uGlass*0.25 + uGrade*0.05;',
      '  float men = smoothstep(0.012, 0.0, abs(vUv.y - lvl + 0.006));',
      '  vec3 c = mix(glass, liquid, inF) + rim*0.08 + (uGrade*0.8 + 0.6) * men;',
      '  gl_FragColor = vec4(c, 1.0); }'].join('\n') });
  cyl(GR, GH, gaugeMat, GX, GY, 0.46);
  cyl(GR * 1.3, GH, new THREE.MeshStandardMaterial({ color: lin(PAL.mist), transparent: true, opacity: 0.12, roughness: 0.1, metalness: 0.0, depthWrite: false }), GX, GY, 0.46).renderOrder = 5;
  cyl(GR * 1.7, 0.16, mats.brass, GX, GY + GH / 2 + 0.08, 0.48); cyl(GR * 1.7, 0.2, mats.brass, GX, GY - GH / 2 - 0.1, 0.48);
  [0, 1 / 3, 2 / 3, 1].forEach(function (f, i) { // tier ticks: 0 / 2,000 / 5,000 / 11,000 m
    box(i % 3 === 0 ? 0.1 : 0.15, 0.035, 0.04, mats.brass, GX + TS * (GR + 0.09), GY - GH / 2 + GH * f, 0.5); });
  for (var tk = 1; tk < 12; tk++) if (tk % 4) box(0.06, 0.02, 0.03, mats.brass, GX + TS * (GR + 0.08), GY - GH / 2 + GH * tk / 12, 0.5);
  var depthPlaque = new THREE.Mesh(new THREE.PlaneGeometry(PORTRAIT ? 0.5 : 0.62, PORTRAIT ? 0.125 : 0.155), new THREE.MeshBasicMaterial({ map: plaqueTexture('0 M'), toneMapped: false }));
  depthPlaque.position.set(GX, GY - GH / 2 - 0.1, 0.5 + GR * 1.7); scene.add(depthPlaque); // mounted on the lower brass cap

  // ritual bar channel + 5 rune seal sockets in the bottom lintel
  var RY = -IN - 0.42, RW = GW * 0.66, RX = PORTRAIT ? 0.1 : 0.35;
  box(RW + 0.16, 0.22, 0.2, mats.recess, RX, RY, 0.36);
  box(RW + 0.24, 0.05, 0.08, mats.brass, RX, RY + 0.135, 0.48); box(RW + 0.24, 0.05, 0.08, mats.brass, RX, RY - 0.135, 0.48);
  var ritualMat = new THREE.ShaderMaterial({ uniforms: { uTime: U.uTime, uFill: U.uRitual, uA: { value: lin(PAL.bio) }, uB: { value: lin(PAL.sulfur) } },
    vertexShader: BG_VS,
    fragmentShader: [
      'uniform float uTime, uFill; uniform vec3 uA, uB; varying vec2 vUv;',
      'void main(){ float on = step(vUv.x, uFill);',
      '  float flow = 0.6 + 0.4*sin(vUv.x*40.0 - uTime*4.0) * sin(vUv.x*13.0 + uTime*1.3);',
      '  float core = 1.0 - abs(vUv.y-0.5)*2.0;',
      '  vec3 col = mix(uA, uB, smoothstep(0.85, 1.0, uFill)) * (0.6 + 1.4*core*flow);',
      '  float head = smoothstep(0.006, 0.0, abs(vUv.x-uFill+0.003)) * 3.0;',
      '  gl_FragColor = vec4(col*on + uA*head*core + vec3(0.01,0.02,0.025)*(1.0-on), 1.0); }'].join('\n') });
  var ritual = new THREE.Mesh(new THREE.PlaneGeometry(RW, 0.13), ritualMat); ritual.position.set(RX, RY, 0.465); scene.add(ritual);
  var seals = [];
  for (var si = 0; si < 5; si++) {
    var sx = RX - RW / 2 + RW * (si + 0.5) / 5, sy = -IN - 0.76;
    var sock = new THREE.Mesh(new THREE.TorusGeometry(0.14, 0.035, 10, 32), mats.brass); sock.position.set(sx, sy, 0.52); scene.add(sock);
    var face = new THREE.Mesh(new THREE.CircleGeometry(0.125, 32), new THREE.MeshStandardMaterial({ color: lin('#141c1f'), roughness: 0.8,
      emissive: lin(PAL.bio), emissiveMap: runeTexture(si + 1), emissiveIntensity: 0 }));
    face.position.set(sx, sy, 0.5); scene.add(face); seals.push(face);
  }
  // sonar dial top-right
  var SR = 0.27, SX = IN - 0.5, SY = IN + 0.13 + SR + 0.11; // clears rivet row; SY+SR+0.09 < FR.T
  var sonarMat = new THREE.ShaderMaterial({ uniforms: { uTime: U.uTime, uC: { value: lin(PAL.bio) } }, vertexShader: BG_VS,
    fragmentShader: [
      'uniform float uTime; uniform vec3 uC; varying vec2 vUv;',
      'void main(){ vec2 p = vUv*2.0-1.0; float r = length(p); float a = atan(p.y, p.x);',
      '  float sw = mod(-uTime*1.6 - a, 6.2831853); float beam = exp(-sw*2.2);',
      '  float rings = smoothstep(0.03, 0.0, abs(fract(r*3.0)-0.5)-0.46);',
      '  float cross = smoothstep(0.02,0.0,abs(p.x))+smoothstep(0.02,0.0,abs(p.y));',
      '  vec2 bp = vec2(0.42, 0.28); float blip = smoothstep(0.08, 0.0, length(p-bp)) * exp(-mod(-uTime*1.6 - atan(bp.y,bp.x), 6.2831853)*0.8);',
      '  vec3 c = uC*(0.02 + beam*0.5 + (rings+cross)*0.12 + blip*2.5);',
      '  gl_FragColor = vec4(c*step(r,1.0), 1.0); }'].join('\n') });
  cyl(SR + 0.04, 0.15, mats.recess, SX, SY, 0.36, true);
  var sonar = new THREE.Mesh(new THREE.CircleGeometry(SR, 48), sonarMat); sonar.position.set(SX, SY, 0.47); scene.add(sonar);
  var sonarRing = new THREE.Mesh(new THREE.TorusGeometry(SR + 0.03, 0.06, 12, 48), mats.brass); sonarRing.position.set(SX, SY, 0.5); scene.add(sonarRing);
  // title plaque on the top band
  var title = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 0.5), new THREE.MeshStandardMaterial({ map: (function () {
    var c = mkCanvas(512, 96), x = c.getContext('2d'); x.fillStyle = PAL.bone; x.font = '600 44px Georgia, serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillText('T H E   D E S C E N T', 256, 50); var t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; return t; })(),
    transparent: true, roughness: 0.6, metalness: 0.3, color: lin(PAL.brass2) }));
  title.position.set(-0.9, IN + 0.47, 0.54); scene.add(title);

  // ---------- LAYER 3: symbols ----------
  var clipTop = new THREE.Plane(new THREE.Vector3(0, -1, 0), IN), clipBot = new THREE.Plane(new THREE.Vector3(0, 1, 0), IN);
  var symMats = {}, symbols = [], board = M.board.map(function (r) { return r.slice(); });
  function cellPos(r, c) { return new THREE.Vector2(-HALF + CELL / 2 + c * (CELL + GAP), HALF - CELL / 2 - r * (CELL + GAP)); }
  function buildSymbolMats(texs) {
    Object.keys(M.symbols).forEach(function (id, i) {
      var e = M.symbols[id], t = texs[i * 2], n = texs[i * 2 + 1];
      var isV2 = !!t.isV2, glyph = !!t.isGlyph;
      if (!isV2 && !glyph) { var ins = M.uvInsetPlaceholder; t.offset.set(ins, ins); t.repeat.set(1 - 2 * ins, 1 - 2 * ins); if (n) { n.offset.copy(t.offset); n.repeat.copy(t.repeat); } }
      var mat = new THREE.MeshStandardMaterial({ map: t, normalMap: n || null, bumpMap: glyph ? t : null, bumpScale: 0.04,
        roughness: e.tier === 'low' ? 0.85 : 0.55, metalness: e.tier === 'mid' ? 0.35 : 0.1, transparent: isV2 || glyph, alphaTest: 0.02,
        emissive: lin('#ffffff'), emissiveMap: t, emissiveIntensity: { low: 0.04, mid: 0.16, high: 0.34, special: 0.42 }[e.tier], clippingPlanes: [clipTop, clipBot] });
      if (n) mat.normalScale.set(0.6, -0.6);
      symMats[id] = { mat: mat, scale: (isV2 || glyph) ? e.scale : M.scalePlaceholder, tier: e.tier };
    });
  }
  var quad = new THREE.PlaneGeometry(CELL, CELL);
  function placeBoard(fromAbove) {
    var now = clock.getElapsedTime();
    symbols.forEach(function (s) { s.leaving = true; s.t0 = now + s.c * 0.06; s.y0 = s.mesh.position.y; });
    for (var r = 0; r < N; r++) for (var c = 0; c < N; c++) {
      var d = symMats[board[r][c]], m = new THREE.Mesh(quad, d.mat), p = cellPos(r, c);
      m.position.set(p.x, fromAbove ? p.y + GW + 1.5 : p.y, d.tier === 'high' ? 0.14 : 0.1);
      m.scale.setScalar(d.scale); scene.add(m);
      symbols.push({ mesh: m, r: r, c: c, base: d.scale, yT: p.y, yS: m.position.y, t0: now + 0.25 + c * 0.09 + (N - 1 - r) * 0.035, landed: !fromAbove });
    }
  }
  function animSymbols(now) {
    var busy = false;
    symbols = symbols.filter(function (s) {
      var t = Math.max(0, now - s.t0), m = s.mesh;
      if (s.leaving) { m.position.y = s.y0 - 14 * t * t; if (m.position.y < -IN - 1) { scene.remove(m); return false; } busy = true; return true; }
      if (!s.landed) {
        var fall = 16 * t * t, y = Math.max(s.yT, s.yS - fall); m.position.y = y; busy = true;
        if (y === s.yT) { s.landed = true; s.tl = now; }
      } else if (s.tl !== undefined) { // squash & stretch landing spring
        var k = now - s.tl, a = Math.exp(-k * 9) * Math.cos(k * 28) * 0.16;
        m.scale.set(s.base * (1 + a), s.base * (1 - a), 1); m.position.y = s.yT - a * 0.5 * s.base * CELL;
        if (k > 0.6) { m.scale.setScalar(s.base); m.position.y = s.yT; delete s.tl; } else busy = true;
      }
      return true;
    });
    return busy;
  }

  // ---------- LAYER 5: post (vignette + depth grade + ACES + grain) ----------
  var postScene = new THREE.Scene(), postCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  var postMat = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false,
    uniforms: { tScene: { value: rt.texture }, uTime: U.uTime, uGrade: U.uGrade, uExposure: { value: 1.0 }, uAspect: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }',
    fragmentShader: [
      'uniform sampler2D tScene; uniform float uTime, uExposure, uAspect; uniform vec3 uGrade; varying vec2 vUv;',
      'vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14), 0.0, 1.0); }',
      'void main(){ vec3 c = texture2D(tScene, vUv).rgb * uExposure;',
      '  float l = dot(c, vec3(0.2126,0.7152,0.0722));',
      '  c = mix(c, c * (0.75 + 0.6*uGrade/max(max(uGrade.r,uGrade.g),uGrade.b)), 0.18);', // depth tint
      '  c += uGrade * 0.012 * (1.0 - smoothstep(0.0, 0.2, l));', // lift shadows toward grade colour
      '  vec2 q = (vUv-0.5)*vec2(uAspect,1.0); float v = smoothstep(1.05, 0.35, length(q)*1.15);',
      '  c *= mix(0.25, 1.0, v);',
      '  c = aces(c); c = pow(c, vec3(1.0/2.2));',
      '  float g = fract(sin(dot(vUv*vec2(1733.0,977.0)+uTime, vec2(12.9898,78.233)))*43758.5453);',
      '  c += (g-0.5)*0.025;',
      '  gl_FragColor = vec4(c, 1.0); }'].join('\n') });
  postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));
  var usePost = !Q.has('nopost');

  // ---------- layout ----------
  function coverPlane(mesh, texAspect, dist) {
    var h = 2 * dist * Math.tan(THREE.MathUtils.degToRad(FOV / 2)) * 1.18, w = h * camera.aspect * 1.0;
    if (w / h > texAspect) h = w / texAspect; else w = h * texAspect;
    mesh.scale.set(w, h, 1);
  }
  function resize() {
    var W = window.innerWidth, H = window.innerHeight;
    renderer.setSize(W, H, false);
    var pr = renderer.getPixelRatio(); rt.setSize(Math.floor(W * pr), Math.floor(H * pr));
    camera.aspect = W / H; postMat.uniforms.uAspect.value = camera.aspect;
    var tan = Math.tan(THREE.MathUtils.degToRad(FOV / 2)), avail = (H - DOM_PX) / H;
    var portrait = camera.aspect < 0.8, tx = FCX;
    var needH = FH * 1.05 / avail, needW = portrait ? FW + 0.4 : FW * 1.06; // portrait: whole frame incl. trim, ~62px cells
    var d = Math.max(needH / (2 * tan), needW / (2 * tan * camera.aspect)) + (portrait ? 0 : 0.6);
    var visH = 2 * d * tan, shift = (DOM_PX / H) * visH / 2;
    var ty = Math.max(FCY - shift, -FR.B - 0.3 - 2 * shift + visH / 2); // seat frame just above the DOM bar
    camTarget.set(tx, ty, 0); camBase.set(tx - 0.25, ty + 0.35, d); U.uRes.value.set(W * pr, H * pr);
    camera.updateProjectionMatrix();
    bgPlanes.forEach(function (p) { coverPlane(p, 1376 / 768, d - p.userData.z); p.position.x = tx; p.position.y = ty; });
    var ch = portrait ? FH * 1.5 : FH * 1.9; creature.scale.set(ch * (1376 / 768), ch, 1);
    var head = portrait ? new THREE.Vector3(-1.0, FR.T + 1.5, 0) : new THREE.Vector3(-IN - 2.0, IN - 0.1, 0); // where the head reads on screen
    var onRay = function (z) { var C = camBase, k = (C.z - z) / C.z; return new THREE.Vector3(C.x + (head.x - C.x) * k, C.y + (head.y - C.y) * k, z); };
    creatureBase.copy(onRay(-6)); creatureBase.y -= 0.15 * ch; keyGlow.position.copy(onRay(-4.5));
  }
  window.addEventListener('resize', resize);
  var mouse = new THREE.Vector2();
  window.addEventListener('pointermove', function (e) { mouse.set(e.clientX / window.innerWidth * 2 - 1, e.clientY / window.innerHeight * 2 - 1); });

  // ---------- public API (for state snapshots / future wiring) ----------
  function setDepth(m) {
    state.depth = m; U.uFill.value = depthToFill(m); U.uGrade.value.copy(depthGrade(m));
    keyLight.color.copy(U.uGrade.value); keyGlow.material.color.copy(U.uGrade.value);
    depthPlaque.material.map.dispose(); depthPlaque.material.map = plaqueTexture(Math.round(m).toLocaleString('en-US') + ' M');
  }
  function setRitual(f) { state.ritual = f; U.uRitual.value = f; }
  function setSeals(n) { state.seals = n; seals.forEach(function (s, i) { s.material.emissiveIntensity = i < n ? 2.2 : 0.06; }); }
  window.STAGE = { setDepth: setDepth, setRitual: setRitual, setSeals: setSeals, state: state, scene: scene, camera: camera };

  // ---------- DOM (layer 6) ----------
  var balance = 1000, bets = [0.2, 0.5, 1, 2, 5, 10], bi = 2;
  function fmt(v) { return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  var $ = function (id) { return document.getElementById(id); };
  $('betUp').onclick = function () { bi = Math.min(bets.length - 1, bi + 1); $('bet').textContent = fmt(bets[bi]); };
  $('betDown').onclick = function () { bi = Math.max(0, bi - 1); $('bet').textContent = fmt(bets[bi]); };
  $('spin').onclick = function () {
    if (balance < bets[bi]) return;
    balance -= bets[bi]; $('balance').textContent = fmt(balance); $('spin').disabled = true;
    var ids = Object.keys(M.symbols); board = board.map(function (r) { return r.map(function () { return ids[Math.floor(Math.random() * ids.length)]; }); });
    placeBoard(true); setDepth(state.depth + 150 + Math.random() * 400); setRitual(Math.min(1, state.ritual + 0.08));
    setTimeout(function () { $('spin').disabled = false; }, 1600);
  };

  // ---------- loop ----------
  var clock = new THREE.Clock(), introDone = false;
  function frame() {
    var t = clock.getElapsedTime(); U.uTime.value = t;
    var px = mouse.x * 0.35 + Math.sin(t * 0.21) * 0.12, py = -mouse.y * 0.2 + Math.sin(t * 0.17) * 0.06;
    camera.position.set(camBase.x + px, camBase.y + py, camBase.z); camera.lookAt(camTarget);
    creature.position.set(creatureBase.x + Math.sin(t * 0.13) * 0.35, creatureBase.y + Math.sin(t * 0.19) * 0.2, -6);
    keyLight.intensity = 2.6 + Math.sin(t * 0.8) * 0.25;
    sonarRing.rotation.z = t * 0.05;
    var busy = animSymbols(t);
    if (!busy && !introDone && symbols.length) {
      introDone = true;
      requestAnimationFrame(function () { requestAnimationFrame(function () { window.__RENDER_READY = true; }); });
    }
    if (usePost) { renderer.setRenderTarget(rt); renderer.render(scene, camera); renderer.setRenderTarget(null); renderer.render(postScene, postCam); }
    else renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }

  // ---------- boot ----------
  var L = M.layers, symIds = Object.keys(M.symbols), jobs = [loadArt(L.trench_far), loadArt(L.trench_mid), loadArt(L.trench_near), loadArt(L.creature)];
  symIds.forEach(function (id) { var e = M.symbols[id]; var art = loadArt(e, true); jobs.push(art);
    jobs.push(art.then(function (t) { return t.isV2 && e.normal ? loadTex(e.normal, false).catch(function () { return null; }) : null; })); });
  Promise.all(jobs).then(function (t) {
    bgFar.material.uniforms.tMap.value = t[0]; bgMid.material.uniforms.tMap.value = t[1]; bgNear.material.uniforms.tMap.value = t[2];
    creatureMat.uniforms.tMap.value = t[3];
    buildSymbolMats(t.slice(4));
    setDepth(state.depth); setRitual(state.ritual); setSeals(state.seals); resize();
    placeBoard(!Q.has('nodrop'));
    frame();
  }).catch(function (e) { console.error('stage_v2 boot failed', e); window.__RENDER_ERROR = String(e); });
})();
