#!/usr/bin/env python3
"""Emit play3d.html: Meowdoku 3D (slice variant) for phones and the web.

Two tabs: Slices (one board per layer) and Cube (three.js, rotate/zoom, legend
focuses a colour and ghosts the rest).  Levels come from pack3d.json.
"""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = json.load(open(os.path.join(HERE, "pack3d.json")))
CAT = "data:image/png;base64," + base64.b64encode(open(os.path.join(HERE, "cat.png"), "rb").read()).decode()

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1">
<meta name="theme-color" content="#F7F2EF">
<title>Meowdoku Cube</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:wght@400;700&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
:root{
  --ground:#F7F2EF; --card:#FFFFFF; --ink:#4A3434; --mauve:#8C5C5C; --line:#EADDD7;
  --chip:#FFFFFF; --chip-on:#4A3434; --chip-on-ink:#FFFFFF; --bad:#E14646; --good:#3F9F5E; --star:#F5B400;
  --shadow:0 2px 10px rgba(120,80,80,.10);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#241D1F; --card:#312729; --ink:#F3E9E5; --mauve:#D9A9A9; --line:#4A3B3E;
    --chip:#3A2F31; --chip-on:#F3E9E5; --chip-on-ink:#241D1F; --shadow:0 2px 12px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --ground:#241D1F; --card:#312729; --ink:#F3E9E5; --mauve:#D9A9A9; --line:#4A3B3E;
  --chip:#3A2F31; --chip-on:#F3E9E5; --chip-on-ink:#241D1F; --shadow:0 2px 12px rgba(0,0,0,.35);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{margin:0;background:var(--ground);color:var(--ink);font-family:"Nunito",system-ui,sans-serif;font-size:16px;line-height:1.4;
  touch-action:manipulation;-webkit-user-select:none;user-select:none;overscroll-behavior:none;
  padding:env(safe-area-inset-top) env(safe-area-inset-right) 0 env(safe-area-inset-left)}
.app{max-width:640px;margin:0 auto;padding:12px 14px calc(96px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:12px}
h1,h2{font-family:"Fredoka",sans-serif;font-weight:600;margin:0}
h1{font-size:1.15rem;white-space:nowrap}
.top{display:flex;align-items:center;justify-content:space-between;gap:8px}
.top .lvl{font-family:"Fredoka",sans-serif;font-weight:500;color:var(--mauve);font-size:.9rem}
.stat{font-family:"Fredoka",sans-serif;font-weight:500;color:var(--mauve);font-size:.9rem;font-variant-numeric:tabular-nums;display:flex;gap:12px}
.stat b{color:var(--ink);font-weight:600}
.iconbtn{border:0;background:var(--chip);color:var(--ink);border-radius:999px;padding:8px 14px;font-family:"Fredoka",sans-serif;font-weight:500;box-shadow:var(--shadow);cursor:pointer;font-size:.9rem}
.seg{display:flex;background:var(--chip);border-radius:999px;padding:4px;box-shadow:var(--shadow)}
.seg button{flex:1;border:0;background:transparent;color:var(--ink);border-radius:999px;padding:9px;font-family:"Fredoka",sans-serif;font-weight:500;font-size:.95rem;cursor:pointer}
.seg button[aria-selected="true"]{background:var(--chip-on);color:var(--chip-on-ink)}
.view{display:none}.view.on{display:block}
/* slices */
.layers{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.layer{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:8px}
.layer h3{font-family:"Fredoka",sans-serif;font-weight:500;font-size:.8rem;color:var(--mauve);margin:0 0 6px 4px;text-transform:uppercase;letter-spacing:.08em}
.grid{display:grid;gap:4%;aspect-ratio:1}
.cell{position:relative;border:0;border-radius:18%;padding:0;background:var(--cc);aspect-ratio:1;cursor:pointer;display:grid;place-items:center;transition:transform .08s,opacity .15s}
.cell:active{transform:scale(.93)}
.cell svg{width:64%;height:64%;display:none}
.cell.x svg{display:block}
.cell img{width:86%;height:86%;display:none;pointer-events:none}
.cell.cat img{display:block}
.cell.ghost{opacity:.18}
.cell.bad::after{content:"";position:absolute;inset:-5%;border-radius:22%;border:3px solid var(--bad);pointer-events:none}
.cell.hint::after{content:"";position:absolute;inset:-5%;border-radius:22%;border:3px solid var(--star);pointer-events:none}
/* cube */
.cubewrap{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:8px;position:relative}
canvas.cube{display:block;width:100%;aspect-ratio:1;border-radius:16px;touch-action:none}
.cubehint{position:absolute;left:10px;bottom:8px;font-size:.75rem;color:var(--mauve);pointer-events:none}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.legend button{border:0;border-radius:999px;padding:6px 10px 6px 6px;background:var(--chip);box-shadow:var(--shadow);display:flex;align-items:center;gap:6px;font-family:"Fredoka",sans-serif;font-size:.85rem;color:var(--ink);cursor:pointer}
.legend button span.sw{width:18px;height:18px;border-radius:6px;background:var(--cc);display:inline-block}
.legend button[aria-pressed="true"]{outline:2px solid var(--ink)}
.legend button.done span.sw::after{content:"🐱";font-size:12px;display:block;text-align:center;line-height:18px}
.ctrls{display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap;font-size:.85rem;color:var(--mauve)}
.ctrls input[type=range]{flex:1;min-width:120px;accent-color:var(--ink)}
.ctrls label{display:flex;align-items:center;gap:6px}
/* bars */
.bar{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.bar button{border:0;border-radius:14px;padding:10px 4px;background:var(--chip);color:var(--ink);font-family:"Fredoka",sans-serif;font-weight:500;font-size:.9rem;box-shadow:var(--shadow);cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:1px}
.bar button small{font-family:"Nunito",sans-serif;font-size:.68rem;color:var(--mauve);font-weight:400}
.bar button:disabled{opacity:.45}
.toggle{display:flex;align-items:center;justify-content:space-between;background:var(--card);border-radius:14px;padding:9px 14px;box-shadow:var(--shadow)}
.toggle small{display:block;color:var(--mauve);font-size:.76rem}
.switch{position:relative;width:46px;height:26px;border-radius:999px;background:var(--line);border:0;cursor:pointer;flex:none}
.switch::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s}
.switch[aria-checked="true"]{background:var(--good)}
.switch[aria-checked="true"]::after{left:23px}
.tabbar{position:fixed;left:0;right:0;bottom:0;background:var(--card);box-shadow:0 -2px 12px rgba(120,80,80,.12);padding:8px 16px calc(8px + env(safe-area-inset-bottom));display:flex;justify-content:center}
.tabbar .seg{max-width:400px;width:100%;box-shadow:none;background:var(--ground)}
/* overlays */
.ov{position:fixed;inset:0;background:rgba(40,25,25,.5);display:none;place-items:center;padding:20px;z-index:9;overflow:auto}
.ov.show{display:grid}
.sheet{background:var(--card);border-radius:24px;padding:22px 20px;width:min(100%,520px);max-height:90vh;overflow:auto;box-shadow:0 10px 40px rgba(0,0,0,.3)}
.sheet h2{font-size:1.3rem;margin-bottom:8px}
.sheet p{margin:8px 0;color:var(--mauve)}
.sheet .primary{border:0;border-radius:999px;padding:12px 22px;background:var(--chip-on);color:var(--chip-on-ink);font-family:"Fredoka",sans-serif;font-size:1rem;cursor:pointer;width:100%;margin-top:12px}
.levels{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;margin-top:10px}
.levels button{border:0;border-radius:14px;padding:10px 6px;background:var(--ground);color:var(--ink);font-family:"Fredoka",sans-serif;font-weight:500;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:2px}
.levels button.cur{outline:2px solid var(--ink)}
.levels button small{font-size:.7rem;color:var(--mauve);font-family:"Nunito",sans-serif}
.levels button .stars{color:var(--star);font-size:.8rem;letter-spacing:1px}
.won{text-align:center}
.won img{width:88px;height:88px}
.won .stars{font-size:2rem;color:var(--star);letter-spacing:4px}
.tut{display:flex;gap:10px;align-items:flex-start;margin:10px 0}
.tut .n{flex:none;width:28px;height:28px;border-radius:50%;background:var(--chip-on);color:var(--chip-on-ink);display:grid;place-items:center;font-family:"Fredoka",sans-serif}
@media (prefers-reduced-motion:reduce){.cell,.switch::after{transition:none}}
</style>
</head>
<body>
<div class="app">
  <div class="top">
    <button class="iconbtn" id="btnLevels" type="button">☰ Levels</button>
    <div style="text-align:center"><h1>Meowdoku Cube</h1><div class="lvl" id="lvlName">Level 1 · 3×3×3</div></div>
    <div class="stat"><span>🐱 <b id="cats">0</b>/<span id="n">3</span></span><span>⏱ <b id="time">0:00</b></span></div>
  </div>
  <section class="view on" id="viewSlices">
    <div class="layers" id="layers"></div>
  </section>
  <section class="view" id="viewCube">
    <div class="cubewrap">
      <div style="position:relative"><canvas class="cube" id="cube"></canvas>
      <div class="cubehint">drag to rotate · pinch or scroll to zoom · tap a cell</div></div>
      <div class="legend" id="legend"></div>
      <div class="ctrls">
        <label>explode <input type="range" id="explode" min="0" max="100" value="25"></label>
        <label><input type="checkbox" id="hideX"> hide crossed cells</label>
        <button class="iconbtn" id="resetView" type="button">reset view</button>
      </div>
    </div>
  </section>
  <div class="bar">
    <button id="undo" type="button">Undo<small>last move</small></button>
    <button id="hint" type="button">Hint<small>reveal a cat</small></button>
    <button id="check" type="button">Check<small>mark mistakes</small></button>
    <button id="reset" type="button">Reset<small>clear cube</small></button>
  </div>
  <div class="toggle">
    <div>Auto-cross<small>a placed cat crosses out its three slices, its colour and its 26 neighbours</small></div>
    <button class="switch" id="assist" role="switch" aria-checked="true" aria-label="Auto-cross"></button>
  </div>
</div>
<div class="tabbar"><div class="seg" role="tablist">
  <button role="tab" id="tabSlices" aria-selected="true" type="button">▦ Slices</button>
  <button role="tab" id="tabCube" aria-selected="false" type="button">⬢ Cube</button>
</div></div>

<div class="ov" id="ovLevels"><div class="sheet">
  <h2>Levels</h2>
  <p>One cat per layer in each of the three directions, one per colour, and no two cats may touch, not even across a corner. Cats have to be a knight's move apart in at least one of the two other directions.</p>
  <div class="levels" id="levelList"></div>
  <button class="primary" id="closeLevels" type="button">Back to the cube</button>
</div></div>
<div class="ov" id="ovTut"><div class="sheet">
  <h2>How to play</h2>
  <div class="tut"><div class="n">1</div><div>The cube is cut into layers. The <b>Slices</b> tab shows every layer as a board; the <b>Cube</b> tab shows the whole thing. Both edit the same cube.</div></div>
  <div class="tut"><div class="n">2</div><div>Tap a cell once for a cross, again for a cat, again to clear. With auto-cross on, a cat crosses out everything it rules out.</div></div>
  <div class="tut"><div class="n">3</div><div>In the Cube tab, tap a colour in the legend to see only that colour; everything else fades. Drag to rotate, use the explode slider to pull the layers apart.</div></div>
  <div class="tut"><div class="n">4</div><div>A cat sees its whole x-layer, y-layer and z-layer, its colour, and the 26 cells around it. Place one cat per colour so that none of them see each other.</div></div>
  <button class="primary" id="closeTut" type="button">Let's go</button>
</div></div>
<div class="ov" id="ovWin"><div class="sheet won">
  <img src="__CAT__" alt="">
  <h2>Solved!</h2>
  <div class="stars" id="winStars">★★★</div>
  <p id="winText"></p>
  <button class="primary" id="nextLevel" type="button">Next level</button>
</div></div>

<script>
const PACK = __PACK__;
const CAT = "__CAT__";
const PAL = ['#8979DA','#FBD983','#F89BE5','#A86D4A','#FA9D5C','#8BD57D','#2A8C53','#38A9C0','#D36F8F','#CDA400'];
const XSVG = '<svg viewBox="0 0 100 100" aria-hidden="true"><path d="M22 22 L78 78 M78 22 L22 78" stroke="#fff" stroke-width="15" stroke-linecap="round" fill="none"/></svg>';
const $ = id => document.getElementById(id);
const KEY = 'meowdoku3d.v1';

// ---------------------------------------------------------------- state
let store = JSON.parse(localStorage.getItem(KEY) || '{}');
store.done = store.done || {}; store.marks = store.marks || {};
let cur = Math.min(PACK.length - 1, store.cur || 0);
let L, n, marks, undo = [], seconds = 0, timer = null, done = false, hints = 0, focus = -1, assist = store.assist !== false;
const save = () => { store.cur = cur; store.assist = assist; store.marks[L.id] = {m: Array.from(marks), s: seconds, h: hints, d: done}; localStorage.setItem(KEY, JSON.stringify(store)); };
const idx = (x, y, z) => x * n * n + y * n + z;
const cellOf = i => [Math.floor(i / (n * n)), Math.floor(i / n) % n, i % n];
function attacks(i, j) {
  if (i === j) return false;
  const a = cellOf(i), b = cellOf(j);
  return a[0] === b[0] || a[1] === b[1] || a[2] === b[2] || (Math.abs(a[0]-b[0]) <= 1 && Math.abs(a[1]-b[1]) <= 1 && Math.abs(a[2]-b[2]) <= 1);
}
function loadLevel(k) {
  cur = k; L = PACK[k]; n = L.n;
  const saved = store.marks[L.id];
  marks = new Uint8Array(n * n * n); seconds = 0; hints = 0; done = false; undo = []; focus = -1;
  if (saved && saved.m.length === marks.length) { marks = Uint8Array.from(saved.m); seconds = saved.s || 0; hints = saved.h || 0; done = !!saved.d; }
  $('n').textContent = n; $('lvlName').textContent = `Level ${k + 1} · ${n}×${n}×${n}`;
  $('time').textContent = fmt(seconds);
  stopTimer();
  buildSlices(); buildLegend(); buildCube(); render(); save();
}
const fmt = s => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
function startTimer() { if (timer || done) return; timer = setInterval(() => { seconds++; $('time').textContent = fmt(seconds); if (seconds % 5 === 0) save(); }, 1000); }
function stopTimer() { clearInterval(timer); timer = null; }

// ---------------------------------------------------------------- moves
function push() { undo.push(Uint8Array.from(marks)); if (undo.length > 300) undo.shift(); }
function autoCross(i) {
  for (let j = 0; j < marks.length; j++)
    if (marks[j] === 0 && (attacks(i, j) || (L.colour[j] === L.colour[i] && j !== i))) marks[j] = 1;
}
function tap(i) {
  if (done) return;
  if (focus >= 0 && L.colour[i] !== focus) return;
  push();
  marks[i] = (marks[i] + 1) % 3;
  if (marks[i] === 2 && assist) autoCross(i);
  clearHints(); render(); save(); startTimer();
}
function conflicts() {
  const cats = []; for (let i = 0; i < marks.length; i++) if (marks[i] === 2) cats.push(i);
  const bad = new Set();
  for (const a of cats) for (const b of cats) if (a !== b && (attacks(a, b) || L.colour[a] === L.colour[b])) bad.add(a);
  return {cats, bad};
}
function clearHints() { document.querySelectorAll('.cell.hint').forEach(e => e.classList.remove('hint')); hintCell = -1; }
let hintCell = -1;

// ---------------------------------------------------------------- slices view
function buildSlices() {
  const box = $('layers'); box.innerHTML = '';
  for (let x = 0; x < n; x++) {
    const card = document.createElement('div'); card.className = 'layer';
    card.innerHTML = `<h3>layer ${x + 1}</h3>`;
    const g = document.createElement('div'); g.className = 'grid'; g.style.gridTemplateColumns = `repeat(${n},1fr)`;
    for (let y = 0; y < n; y++) for (let z = 0; z < n; z++) {
      const i = idx(x, y, z);
      const b = document.createElement('button'); b.type = 'button'; b.className = 'cell'; b.dataset.i = i;
      b.style.setProperty('--cc', PAL[L.colour[i]]);
      b.innerHTML = XSVG + `<img src="${CAT}" alt="">`;
      b.addEventListener('click', () => tap(i));
      g.appendChild(b);
    }
    card.appendChild(g); box.appendChild(card);
  }
}
function render() {
  const {cats, bad} = conflicts();
  document.querySelectorAll('.cell').forEach(el => {
    const i = +el.dataset.i, m = marks[i];
    el.classList.toggle('x', m === 1); el.classList.toggle('cat', m === 2);
    el.classList.toggle('bad', bad.has(i));
    el.classList.toggle('ghost', focus >= 0 && L.colour[i] !== focus);
    el.classList.toggle('hint', i === hintCell);
    const c = cellOf(i);
    el.setAttribute('aria-label', `layer ${c[0]+1} row ${c[1]+1} column ${c[2]+1}: ${m===2?'cat':m===1?'crossed':'empty'}`);
  });
  $('cats').textContent = cats.length;
  $('undo').disabled = undo.length === 0;
  // legend status
  const doneColours = new Set(cats.map(i => L.colour[i]));
  document.querySelectorAll('#legend button').forEach(b => { b.classList.toggle('done', doneColours.has(+b.dataset.g)); b.setAttribute('aria-pressed', +b.dataset.g === focus); });
  updateCube(bad);
  if (!done && cats.length === n && bad.size === 0) win();
}

// ---------------------------------------------------------------- legend
function buildLegend() {
  const lg = $('legend'); lg.innerHTML = '';
  const names = ['purple','yellow','pink','brown','orange','green','dark green','blue','rose','gold'];
  for (let g = 0; g < n; g++) {
    const b = document.createElement('button'); b.type = 'button'; b.dataset.g = g;
    b.style.setProperty('--cc', PAL[g]);
    const count = L.colour.filter(c => c === g).length;
    b.innerHTML = `<span class="sw"></span>${names[g]} <small style="color:var(--mauve)">${count}</small>`;
    b.addEventListener('click', () => { focus = (focus === g) ? -1 : g; render(); });
    lg.appendChild(b);
  }
}

// ---------------------------------------------------------------- cube view (three.js)
let renderer, scene, camera, group, meshes = [], yaw = 0.7, pitch = 0.5, dist = 0, needs = true;
let xTex, catTex;
function makeXTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  g.strokeStyle = '#fff'; g.lineWidth = 18; g.lineCap = 'round';
  g.beginPath(); g.moveTo(34, 34); g.lineTo(94, 94); g.moveTo(94, 34); g.lineTo(34, 94); g.stroke();
  const t = new THREE.CanvasTexture(c); return t;
}
function buildCube() {
  if (!window.THREE) return;
  const cv = $('cube');
  if (!renderer) {
    renderer = new THREE.WebGLRenderer({canvas: cv, antialias: true, alpha: true});
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dl = new THREE.DirectionalLight(0xffffff, 0.55); dl.position.set(3, 5, 4); scene.add(dl);
    const dl2 = new THREE.DirectionalLight(0xffffff, 0.25); dl2.position.set(-4, -2, -3); scene.add(dl2);
    xTex = makeXTexture();
    catTex = new THREE.TextureLoader().load(CAT, () => { needs = true; });
    bindOrbit(cv);
    window.addEventListener('resize', sizeCube);
    requestAnimationFrame(frame);
  }
  if (group) scene.remove(group);
  group = new THREE.Group(); meshes = [];
  const geo = new THREE.BoxGeometry(0.84, 0.84, 0.84);
  const edges = new THREE.EdgesGeometry(geo);
  for (let i = 0; i < n * n * n; i++) {
    const mat = new THREE.MeshLambertMaterial({color: PAL[L.colour[i]], transparent: true, opacity: 1});
    const m = new THREE.Mesh(geo, mat);
    const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({color: 0xffffff, transparent: true, opacity: 0.35}));
    m.add(line);
    const xs = new THREE.Sprite(new THREE.SpriteMaterial({map: xTex, transparent: true, depthTest: false})); xs.scale.set(0.7, 0.7, 1); xs.visible = false; m.add(xs);
    const cs = new THREE.Sprite(new THREE.SpriteMaterial({map: catTex, transparent: true, depthTest: false})); cs.scale.set(0.9, 0.9, 1); cs.visible = false; m.add(cs);
    const ring = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({color: 0xE14646, linewidth: 2})); ring.scale.set(1.12, 1.12, 1.12); ring.visible = false; m.add(ring);
    m.userData = {i, line, xs, cs, ring};
    group.add(m); meshes.push(m);
  }
  scene.add(group);
  dist = n * 2.6;
  layout(); sizeCube(); needs = true;
}
function layout() {
  const ex = (+$('explode').value) / 100 * 1.6;
  const off = (n - 1) / 2;
  for (const m of meshes) {
    const [x, y, z] = cellOf(m.userData.i);
    // layer index x goes along the vertical axis so layer 1 is on top
    m.position.set((z - off), (off - x) * (1 + ex), (y - off));
  }
  needs = true;
}
function updateCube(bad) {
  if (!meshes.length) return;
  const hideX = $('hideX').checked;
  for (const m of meshes) {
    const {i, line, xs, cs, ring} = m.userData;
    const mk = marks[i], ghost = focus >= 0 && L.colour[i] !== focus;
    m.visible = !(hideX && mk === 1 && !ghost) ;
    if (ghost) { m.material.opacity = 0.07; line.visible = false; xs.visible = false; cs.visible = false; ring.visible = false; m.material.depthWrite = false; continue; }
    m.material.depthWrite = true;
    m.material.opacity = mk === 0 ? 1 : (mk === 1 ? 0.45 : 0.35);
    line.visible = true; xs.visible = mk === 1; cs.visible = mk === 2; ring.visible = bad && bad.has(i);
    m.scale.setScalar(mk === 1 ? 0.62 : 1);
  }
  needs = true;
}
function sizeCube() {
  if (!renderer) return;
  const cv = $('cube'); const w = cv.clientWidth || 300;
  renderer.setSize(w, w, false); camera.aspect = 1; camera.updateProjectionMatrix(); needs = true;
}
function frame() {
  if (needs && renderer && $('viewCube').classList.contains('on')) {
    camera.position.set(dist * Math.cos(pitch) * Math.sin(yaw), dist * Math.sin(pitch), dist * Math.cos(pitch) * Math.cos(yaw));
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera); needs = false;
  }
  requestAnimationFrame(frame);
}
function bindOrbit(cv) {
  let ptrs = new Map(), moved = 0, start = null, pinch0 = 0, dist0 = 0;
  cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]); moved = 0; start = [e.clientX, e.clientY, Date.now()];
    if (ptrs.size === 2) { const p = [...ptrs.values()]; pinch0 = Math.hypot(p[0][0]-p[1][0], p[0][1]-p[1][1]); dist0 = dist; } });
  cv.addEventListener('pointermove', e => {
    if (!ptrs.has(e.pointerId)) return;
    const prev = ptrs.get(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptrs.size === 1) { const dx = e.clientX - prev[0], dy = e.clientY - prev[1]; moved += Math.abs(dx) + Math.abs(dy);
      yaw -= dx * 0.008; pitch = Math.max(-1.4, Math.min(1.4, pitch + dy * 0.008)); needs = true; }
    else if (ptrs.size === 2) { const p = [...ptrs.values()]; const d = Math.hypot(p[0][0]-p[1][0], p[0][1]-p[1][1]); dist = Math.max(n * 1.2, Math.min(n * 6, dist0 * pinch0 / d)); moved += 10; needs = true; }
  });
  const up = e => { ptrs.delete(e.pointerId); if (start && moved < 8 && Date.now() - start[2] < 500 && ptrs.size === 0) pick(e, cv); start = null; };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', e => { e.preventDefault(); dist = Math.max(n * 1.2, Math.min(n * 6, dist * (1 + e.deltaY * 0.001))); needs = true; }, {passive: false});
}
function pick(e, cv) {
  const r = cv.getBoundingClientRect();
  const v = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  const rc = new THREE.Raycaster(); rc.setFromCamera(v, camera);
  const targets = meshes.filter(m => m.visible && !(focus >= 0 && L.colour[m.userData.i] !== focus));
  const hit = rc.intersectObjects(targets, false)[0];
  if (hit) tap(hit.object.userData.i);
}

// ---------------------------------------------------------------- tabs, buttons
function showTab(cube) {
  $('viewSlices').classList.toggle('on', !cube); $('viewCube').classList.toggle('on', cube);
  $('tabSlices').setAttribute('aria-selected', !cube); $('tabCube').setAttribute('aria-selected', cube);
  if (cube) { sizeCube(); needs = true; }
}
$('tabSlices').addEventListener('click', () => showTab(false));
$('tabCube').addEventListener('click', () => showTab(true));
$('explode').addEventListener('input', layout);
$('hideX').addEventListener('change', () => render());
$('resetView').addEventListener('click', () => { yaw = 0.7; pitch = 0.5; dist = n * 2.6; needs = true; });
$('assist').addEventListener('click', () => { assist = !assist; $('assist').setAttribute('aria-checked', assist); save(); });
$('undo').addEventListener('click', () => { if (!undo.length || done) return; marks = undo.pop(); clearHints(); render(); save(); });
$('reset').addEventListener('click', () => { if (!confirm('Clear this cube?')) return; stopTimer(); marks = new Uint8Array(n*n*n); undo = []; seconds = 0; hints = 0; done = false; $('time').textContent = '0:00'; clearHints(); render(); save(); });
$('check').addEventListener('click', () => {
  const sol = new Set(L.solution.map(c => idx(...c)));
  let wrong = 0;
  for (let i = 0; i < marks.length; i++) { const isCat = sol.has(i); if ((marks[i] === 2 && !isCat) || (marks[i] === 1 && isCat)) wrong++; }
  const cs = document.querySelectorAll('.cell');
  cs.forEach(el => { const i = +el.dataset.i; const isCat = sol.has(i); el.classList.toggle('bad', (marks[i] === 2 && !isCat) || (marks[i] === 1 && isCat)); });
  alert(wrong ? `${wrong} mistake${wrong > 1 ? 's' : ''} marked in red.` : 'No mistakes so far.');
});
$('hint').addEventListener('click', () => {
  if (done) return;
  const sol = new Set(L.solution.map(c => idx(...c)));
  clearHints();
  for (let i = 0; i < marks.length; i++) if (marks[i] === 2 && !sol.has(i)) { hintCell = i; render(); alert('The ringed cat is in the wrong place.'); return; }
  const missing = [...sol].filter(i => marks[i] !== 2);
  if (!missing.length) return;
  const i = missing[Math.floor(Math.random() * missing.length)];
  push(); hints++; marks[i] = 2; if (assist) autoCross(i); hintCell = i; focus = -1; render(); save(); startTimer();
});
function win() {
  done = true; stopTimer();
  const par = n * n * 6;
  const stars = hints === 0 ? (seconds <= par ? 3 : 2) : 1;
  const prev = store.done[L.id];
  if (!prev || prev.stars < stars) store.done[L.id] = {stars, time: seconds};
  save();
  $('winStars').textContent = '★★★'.slice(0, stars) + '☆☆☆'.slice(0, 3 - stars);
  $('winText').textContent = `${n}×${n}×${n} in ${fmt(seconds)}${hints ? ` with ${hints} hint${hints > 1 ? 's' : ''}` : ''}.`;
  $('nextLevel').textContent = cur + 1 < PACK.length ? 'Next level' : 'Back to levels';
  $('ovWin').classList.add('show');
}
$('nextLevel').addEventListener('click', () => { $('ovWin').classList.remove('show'); if (cur + 1 < PACK.length) loadLevel(cur + 1); else openLevels(); });
function openLevels() {
  const list = $('levelList'); list.innerHTML = '';
  PACK.forEach((p, k) => {
    const b = document.createElement('button'); b.type = 'button'; if (k === cur) b.classList.add('cur');
    const d = store.done[p.id];
    b.innerHTML = `<span>${k + 1}</span><small>${p.n}×${p.n}×${p.n}</small><span class="stars">${d ? '★'.repeat(d.stars) + '☆'.repeat(3 - d.stars) : '·'}</span>`;
    b.addEventListener('click', () => { $('ovLevels').classList.remove('show'); loadLevel(k); });
    list.appendChild(b);
  });
  $('ovLevels').classList.add('show');
}
$('btnLevels').addEventListener('click', openLevels);
$('closeLevels').addEventListener('click', () => $('ovLevels').classList.remove('show'));
$('closeTut').addEventListener('click', () => { $('ovTut').classList.remove('show'); store.tut = true; save(); });

$('assist').setAttribute('aria-checked', assist);
loadLevel(cur);
if (!store.tut) $('ovTut').classList.add('show');
</script>
</body>
</html>
"""

out = PAGE.replace("__PACK__", json.dumps(PACK, separators=(",", ":"))).replace("__CAT__", CAT)
with open(os.path.join(HERE, "play3d.html"), "w") as f:
    f.write(out)
print("wrote play3d.html", len(out), "bytes,", len(PACK), "levels")
