// Offline audio lab for makeAudio() in Main.dc.html.
// Renders every A.* sound through an OfflineAudioContext using the SAME synthesis code (the method body is
// extracted from the design file and evaluated), then computes objective metrics.
// Usage (in a page on the dev server):  const L = await import('/static/work/audio/lab/harness.js');
//   await L.run('/static/work/audio/Main.dc.html')  -> returns a text table
const SR = 48000;

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

export async function loadMake(url) {
  const src = await (await fetch(url + '?' + Date.now())).text();
  const i = src.indexOf('makeAudio() {');
  const j = src.indexOf('\n  get aud()', i);
  let body = src.slice(i + 'makeAudio() {'.length, j).trim();
  body = body.slice(0, body.lastIndexOf('}'));
  body = body.replace(/A\.ctx\.state !== 'running'/g, 'false')
    .replace(/setInterval\(/g, '((f,ms)=>0)(')
    .replace('A.startAmbient();', 'if (!A.__noAmb) A.startAmbient();');
  return new Function(body);
}

async function render(make, dur, fn, amb, seed) {
  const off = new OfflineAudioContext(2, Math.ceil(dur * SR), SR);
  const OrigAC = window.AudioContext, OrigR = Math.random;
  window.AudioContext = function () { return off; };
  Math.random = mulberry32(seed || 1234);
  let A;
  try {
    A = make(); A.__noAmb = !amb;
    A.init();
  } finally { window.AudioContext = OrigAC; }
  try {
    await fn(A, off);
    return await off.startRendering();
  } finally { Math.random = OrigR; }
}

function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2;
        const xr = re[b] * cr - im[b] * ci, xi = re[b] * ci + im[b] * cr;
        re[b] = re[a] - xr; im[b] = im[a] - xi; re[a] += xr; im[a] += xi;
        const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr;
      }
    }
  }
}

function biquad(x, b, a) {
  const y = new Float64Array(x.length); let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let i = 0; i < x.length; i++) { const v = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2; x2 = x1; x1 = x[i]; y2 = y1; y1 = v; y[i] = v; }
  return y;
}
const db = (v) => v > 0 ? 20 * Math.log10(v) : -Infinity;

function truePeak(ch) {
  let sp = 0; for (let i = 0; i < ch.length; i++) sp = Math.max(sp, Math.abs(ch[i]));
  let tp = sp; const thr = sp * 0.5, H = 8;
  for (let n = H; n < ch.length - H; n++) {
    if (Math.abs(ch[n]) < thr && Math.abs(ch[n + 1]) < thr) continue;
    for (const f of [0.25, 0.5, 0.75]) {
      let s = 0;
      for (let k = -H + 1; k <= H; k++) { const x = k - f, w = 0.5 + 0.5 * Math.cos(Math.PI * x / H); s += ch[n + k] * (Math.sin(Math.PI * x) / (Math.PI * x)) * w; }
      tp = Math.max(tp, Math.abs(s));
    }
  }
  return { sp, tp };
}

export function metrics(buf) {
  const L = buf.getChannelData(0), R = buf.getChannelData(1), n = L.length;
  const pL = truePeak(L), pR = truePeak(R);
  const sp = Math.max(pL.sp, pR.sp), tp = Math.max(pL.tp, pR.tp);
  let clip = 0; for (let i = 0; i < n; i++) { if (Math.abs(L[i]) >= 0.999) clip++; if (Math.abs(R[i]) >= 0.999) clip++; }
  // K-weighted loudness (BS.1770, 48 kHz coefficients)
  const kb1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], ka1 = [1, -1.69065929318241, 0.73248077421585];
  const kb2 = [1, -2, 1], ka2 = [1, -1.99004745483398, 0.99007225036621];
  const kL = biquad(biquad(L, kb1, ka1), kb2, ka2), kR = biquad(biquad(R, kb1, ka1), kb2, ka2);
  const W = Math.round(0.4 * SR), S = Math.round(0.1 * SR), blocks = [];
  let maxRms = 0;
  for (let s = 0; s + W <= n; s += S) {
    let e = 0, r = 0;
    for (let i = s; i < s + W; i++) { e += kL[i] * kL[i] + kR[i] * kR[i]; r += (L[i] * L[i] + R[i] * R[i]) / 2; }
    blocks.push(e / W); maxRms = Math.max(maxRms, Math.sqrt(r / W));
  }
  const lufs = (z) => -0.691 + 10 * Math.log10(z);
  const mMax = Math.max(...blocks.map((z) => z > 0 ? lufs(z) : -200));
  const g1 = blocks.filter((z) => z > 0 && lufs(z) > -70);
  let integ = -Infinity;
  if (g1.length) {
    const m1 = g1.reduce((a, b) => a + b, 0) / g1.length, rel = lufs(m1) - 10;
    const g2 = g1.filter((z) => lufs(z) > rel);
    integ = lufs(g2.reduce((a, b) => a + b, 0) / g2.length);
  }
  // spectrum of the mid signal: frames 2048, hop 1024, Hann
  const N = 8192, H = 4096, bins = N / 2, hz = SR / N;
  const tot = new Float64Array(bins); const frames = [];
  const win = new Float64Array(N); for (let i = 0; i < N; i++) win[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / N);
  for (let s = 0; s + N <= n; s += H) {
    const re = new Float64Array(N), im = new Float64Array(N);
    for (let i = 0; i < N; i++) re[i] = 0.5 * (L[s + i] + R[s + i]) * win[i];
    fft(re, im);
    const P = new Float64Array(bins); let e = 0;
    for (let k = 1; k < bins; k++) { P[k] = re[k] * re[k] + im[k] * im[k]; e += P[k]; }
    frames.push({ P, e });
  }
  const emax = Math.max(...frames.map((f) => f.e));
  let fwSum = 0, sfmFull = 0, sfmBand = 0;
  for (const f of frames) {
    if (!(f.e > emax * 1e-4)) continue; // frames within 40 dB of the loudest
    for (let k = 1; k < bins; k++) tot[k] += f.P[k];
    // full-band flatness 40 Hz..12 kHz
    const k0 = Math.ceil(40 / hz), k1 = Math.floor(12000 / hz);
    const flat = (a, b) => { let lg = 0, ar = 0, c = 0; for (let k = a; k <= b; k++) { const p = f.P[k] + 1e-20; lg += Math.log(p); ar += p; c++; } return Math.exp(lg / c) / (ar / c); };
    // in-band flatness: between the 5% and 95% cumulative-energy bins of this frame
    let cum = 0, a = 1, b = bins - 1; const tgt5 = f.e * 0.05, tgt95 = f.e * 0.95;
    for (let k = 1; k < bins; k++) { cum += f.P[k]; if (cum < tgt5) a = k + 1; if (cum <= tgt95) b = k + 1; }
    if (b - a < 4) b = a + 4;
    sfmFull += flat(k0, k1) * f.e; sfmBand += flat(a, Math.min(bins - 1, b)) * f.e; fwSum += f.e;
  }
  let T = 0, C = 0, A2 = 0, A4 = 0, A6 = 0;
  for (let k = 1; k < bins; k++) { const f = k * hz; T += tot[k]; C += tot[k] * f; if (f > 2000) A2 += tot[k]; if (f > 4000) A4 += tot[k]; if (f > 6000) A6 += tot[k]; }
  return {
    tp: db(tp), sp: db(sp), clip, I: integ, Mmax: mMax, crest: db(tp) - db(maxRms),
    cent: C / T, hf2: 100 * A2 / T, hf4: 100 * A4 / T, hf6: 100 * A6 / T,
    sfm: sfmFull / fwSum, sfmB: sfmBand / fwSum
  };
}

const at = (off, t, f) => off.suspend(t).then(() => { f(); off.resume(); });

export function oneShots(A) {
  const list = [
    ['spank(1)', 3, (A) => A.spank(1)], ['land', 3, (A) => A.land()],
    ['chain(false)', 5, (A) => A.chain(false)], ['chain(true)', 10, (A) => A.chain(true)],
    ['sink', 3, (A) => A.sink()], ['boom(1)', 3, (A) => A.boom(null, 1)],
    ['win(2x)', 3, (A) => A.win(2)], ['win(50x)', 3, (A) => A.win(50)],
    ['fizz', 3, (A) => A.fizz()], ['vent', 3, (A) => A.vent()], ['absorb', 3, (A) => A.absorb()],
    ['roar(1)', 4, (A) => A.roar(1)], ['plunge', 3, (A) => A.plunge()], ['geyser', 4, (A) => A.geyser()],
    ['shimmer', 3, (A) => A.shimmer()], ['alarm', 3, (A) => A.alarm()], ['shatter', 4, (A) => A.shatter()],
    ['riser(1.4)', 3, (A) => A.riser(1.4)], ['tsunami', 6, (A) => A.tsunami()],
    ['tick(0.5)', 2, (A) => A.tick(0.5)], ['tierUp(1)', 4, (A) => A.tierUp(1)], ['tierUp(4)', 4, (A) => A.tierUp(4)],
    ['ui', 2, (A) => A.ui()], ['scare', 3, (A) => A.scare()], ['endSting(2)', 5, (A) => A.endSting(2)],
    ['maxLoop 5s', 6, (A, off) => { A.maxLoop(true); at(off, 4, () => A.maxLoop(false)); }],
    ['breath', 5, (A) => A.breath(0.05)], ['creak', 3, (A) => A.creak()], ['heartbeat', 2, (A) => A.heartbeat(0.05)],
    ['chainLurch(1)', 4, (A) => A.chainLurch && A.chainLurch(1)], ['chainLurch(4)', 5, (A) => A.chainLurch && A.chainLurch(4)],
    ['jawOpen', 4, (A) => A.jawOpen && A.jawOpen()], ['chomp', 3, (A) => A.chomp && A.chomp()],
    ['wildRise', 3, (A) => A.wildRise && A.wildRise()],
    ['padSwell', 12, (A) => { if (!A.padSwell) return; A.startAmbient(); A.bedG.disconnect(); A.swimG.disconnect(); A.padSwell(0.05); }], ['moan', 6, (A) => A.moan && A.moan(0.05)],
    ['sonar', 5, (A) => A.sonar && A.sonar(0.05)],
  ];
  return list;
}

function fmt(name, m) {
  const f = (v, d = 1) => (isFinite(v) ? v.toFixed(d) : '-inf').padStart(6);
  return name.padEnd(20) + f(m.tp) + f(m.I) + f(m.Mmax) + f(m.crest) + f(m.cent, 0).padStart(7) + f(m.hf2) + f(m.hf4) + f(m.hf6) + f(10 * Math.log10(m.sfm), 0) + f(m.sfmB, 3) + String(m.clip).padStart(5);
}
export const HEAD = 'sound'.padEnd(20) + '   TPk  LUFSi  Mmax  crest  centr  >2k%  >4k%  >6k% SFMdB  SFMb clip';

export async function runAmbience(make, level, swimFn, secs, seed) {
  return render(make, secs, (A, off) => {
    A.setLevel(level);
    for (let t = 0.25; t < secs - 0.1; t += 0.25) {
      const tt = t;
      at(off, tt, () => { const v = swimFn(tt); for (let i = 0; i < 15; i++) A.swim(v); A.tickAmbient(); });
    }
  }, true, seed);
}

export async function run(url, only) {
  const make = await loadMake(url);
  const out = [HEAD];
  for (const [name, dur, fn] of oneShots()) {
    if (only && !only.includes(name)) continue;
    const probe = make(); // skip sounds that this version doesn't have
    const key = name.match(/^[a-zA-Z]+/)[0];
    if (!(key in probe) && key !== 'maxLoop') { out.push(name.padEnd(20) + '   (absent)'); continue; }
    try {
      const b = await render(make, dur, (A, off) => fn(A, off), false, 7);
      out.push(fmt(name, metrics(b)));
    } catch (e) { out.push(name.padEnd(20) + ' ERROR ' + e.message); }
  }
  const probe = make();
  if (probe.descentStart) {
    const b = await render(make, 14, (A, off) => {
      A.descentStart();
      for (let t = 0.1; t < 11.95; t += 0.1) { const tt = t; at(off, tt, () => A.descentDepth(Math.min(1, tt / 11))); }
      at(off, 12, () => A.descentStop());
    }, false, 9);
    out.push(fmt('descent bed 0..1', metrics(b)));
  } else out.push('descent bed'.padEnd(20) + '   (absent)');
  {
    const b = await render(make, 20, (A, off) => { A.setLevel(0); }, true, 13);
    out.push(fmt('bed only (no events)', metrics(b)));
  }
  const swims = [[0, (t) => 0.15], [3, (t) => 0.4 + 0.3 * Math.sin(t * 0.5)], [5, (t) => 0.6 + 0.4 * Math.sin(t * 0.7)]];
  for (const [lv, sf] of swims) {
    const b = await runAmbience(make, lv, sf, 30, 11);
    out.push(fmt('AMBIENCE L' + lv + ' 30s', metrics(b)));
  }
  return out.join('\n');
}

// Base64 WAV (16-bit) of a render, for optional export in chunks.
export function wavB64(buf) {
  const n = buf.length, ch = 2, dv = new DataView(new ArrayBuffer(44 + n * ch * 2));
  const ws = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, 'RIFF'); dv.setUint32(4, 36 + n * ch * 2, true); ws(8, 'WAVEfmt '); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true);
  dv.setUint16(22, ch, true); dv.setUint32(24, SR, true); dv.setUint32(28, SR * ch * 2, true); dv.setUint16(32, ch * 2, true); dv.setUint16(34, 16, true);
  ws(36, 'data'); dv.setUint32(40, n * ch * 2, true);
  const L = buf.getChannelData(0), R = buf.getChannelData(1);
  for (let i = 0; i < n; i++) { dv.setInt16(44 + i * 4, Math.max(-1, Math.min(1, L[i])) * 32767, true); dv.setInt16(46 + i * 4, Math.max(-1, Math.min(1, R[i])) * 32767, true); }
  let s = ''; const u = new Uint8Array(dv.buffer); for (let i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
  return btoa(s);
}
export { render };
