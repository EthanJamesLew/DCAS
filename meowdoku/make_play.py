#!/usr/bin/env python3
"""Emit play.html: a phone-first playable version of the hardest boards found."""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(HERE, "hardest.json")))
CAT = "data:image/png;base64," + base64.b64encode(open(os.path.join(HERE, "cat.png"), "rb").read()).decode()

PUZZLES = []
for N, name in (("10", "Ten"), ("9", "Nine"), ("8", "Eight")):
    e = H[N]["hardest"][0]
    PUZZLES.append({"id": f"h{N}", "name": f"{name} by {name.lower()}", "n": int(N),
                    "grid": e["grid"], "solution": e["solution"], "difficulty": e["difficulty"]})

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1">
<meta name="theme-color" content="#F7F2EF">
<title>Meowdoku Hard Mode</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:wght@400;700&display=swap">
<style>
:root{
  --ground:#F7F2EF; --card:#FFFFFF; --ink:#4A3434; --mauve:#8C5C5C; --line:#EADDD7;
  --chip:#FFFFFF; --chip-on:#4A3434; --chip-on-ink:#FFFFFF; --bad:#E14646; --good:#3F9F5E;
  --shadow:0 2px 10px rgba(120,80,80,.10);
  --c0:#8979DA; --c1:#FBD983; --c2:#F89BE5; --c3:#A86D4A; --c4:#FA9D5C;
  --c5:#8BD57D; --c6:#2A8C53; --c7:#38A9C0; --c8:#D36F8F; --c9:#CDA400;
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
body{margin:0;background:var(--ground);color:var(--ink);font-family:"Nunito",system-ui,sans-serif;
  font-size:16px;line-height:1.4;touch-action:manipulation;-webkit-user-select:none;user-select:none;
  padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}
.app{max-width:560px;margin:0 auto;padding:14px 16px 24px;display:flex;flex-direction:column;gap:12px;min-height:100%}
h1{font-family:"Fredoka",sans-serif;font-weight:600;font-size:1.2rem;margin:0;letter-spacing:.01em;white-space:nowrap}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.stat{font-family:"Fredoka",sans-serif;font-weight:500;color:var(--mauve);font-size:.95rem;
  font-variant-numeric:tabular-nums;display:flex;gap:14px}
.stat b{color:var(--ink);font-weight:600}
.picker{display:flex;gap:8px}
.picker button{flex:1;border:0;border-radius:999px;padding:10px 6px;background:var(--chip);color:var(--ink);
  font-family:"Fredoka",sans-serif;font-weight:500;font-size:.95rem;box-shadow:var(--shadow);cursor:pointer}
.picker button[aria-pressed="true"]{background:var(--chip-on);color:var(--chip-on-ink)}
.picker button:focus-visible,.bar button:focus-visible,.cell:focus-visible{outline:3px solid var(--c0);outline-offset:2px}
.boardwrap{background:var(--card);border-radius:22px;box-shadow:var(--shadow);padding:8px}
.board{display:grid;gap:3.5%;width:100%;aspect-ratio:1;--gap:3.5%}
.cell{position:relative;border:0;border-radius:18%;padding:0;background:var(--cc);aspect-ratio:1;cursor:pointer;
  display:grid;place-items:center;overflow:visible;transition:transform .08s}
.cell:active{transform:scale(.94)}
.cell svg{width:62%;height:62%;display:none}
.cell.x svg{display:block}
.cell img{width:84%;height:84%;display:none;pointer-events:none}
.cell.cat img{display:block}
.cell.bad::after{content:"";position:absolute;inset:-4%;border-radius:22%;border:3px solid var(--bad);pointer-events:none}
.cell.hint::after{content:"";position:absolute;inset:-4%;border-radius:22%;border:3px solid #FFCD3C;pointer-events:none}
.bar{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.bar button{border:0;border-radius:14px;padding:12px 4px;background:var(--chip);color:var(--ink);font-family:"Fredoka",sans-serif;
  font-weight:500;font-size:.95rem;box-shadow:var(--shadow);cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:2px}
.bar button small{font-family:"Nunito",sans-serif;font-size:.7rem;color:var(--mauve);font-weight:400}
.bar button:disabled{opacity:.45;cursor:default}
.toggle{display:flex;align-items:center;justify-content:space-between;background:var(--card);border-radius:14px;padding:10px 14px;box-shadow:var(--shadow)}
.toggle label{font-size:.95rem}
.toggle small{display:block;color:var(--mauve);font-size:.78rem}
.switch{position:relative;width:46px;height:26px;border-radius:999px;background:var(--line);border:0;cursor:pointer;flex:none}
.switch::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s}
.switch[aria-checked="true"]{background:var(--good)}
.switch[aria-checked="true"]::after{left:23px}
.note{color:var(--mauve);font-size:.85rem;margin:0}
.won{position:fixed;inset:0;background:rgba(40,25,25,.45);display:none;place-items:center;padding:24px;z-index:9}
.won.show{display:grid}
.won div{background:var(--card);border-radius:24px;padding:26px 24px;text-align:center;max-width:320px;box-shadow:0 10px 40px rgba(0,0,0,.3)}
.won img{width:84px;height:84px}
.won h2{font-family:"Fredoka",sans-serif;font-weight:600;margin:8px 0 4px}
.won p{margin:0 0 16px;color:var(--mauve)}
.won button{border:0;border-radius:999px;padding:12px 22px;background:var(--chip-on);color:var(--chip-on-ink);font-family:"Fredoka",sans-serif;font-size:1rem;cursor:pointer}
@media (prefers-reduced-motion:reduce){.cell,.switch::after{transition:none}}
</style>
</head>
<body>
<div class="app">
  <div class="top">
    <h1>Meowdoku: hard mode</h1>
    <div class="stat"><span>🐱 <b id="cats">0</b>/<span id="n">10</span></span><span>⏱ <b id="time">0:00</b></span></div>
  </div>
  <div class="picker" id="picker" role="tablist" aria-label="Choose a board"></div>
  <div class="boardwrap"><div class="board" id="board" role="grid" aria-label="Meowdoku board"></div></div>
  <div class="bar">
    <button id="undo" type="button">Undo<small>last move</small></button>
    <button id="hint" type="button">Hint<small>reveal a cat</small></button>
    <button id="check" type="button">Check<small>mark mistakes</small></button>
    <button id="reset" type="button">Reset<small>clear board</small></button>
  </div>
  <div class="toggle">
    <label for="assist">Auto-cross<small>a placed cat crosses out everything it attacks</small></label>
    <button class="switch" id="assist" role="switch" aria-checked="true" aria-label="Auto-cross"></button>
  </div>
  <p class="note">Tap a cell once for a cross, again for a cat, again to clear. One cat per row, per column and per colour; no two cats may touch, not even at a corner. These three boards are the hardest found by a rule-based search: each one reaches a point where the direct rules stall and you must try a cell and follow it to a contradiction.</p>
</div>
<div class="won" id="won"><div><img src="__CAT__" alt=""><h2>Solved!</h2><p id="wontext"></p><button id="wonok" type="button">Nice</button></div></div>
<script>
const PUZZLES = __PUZZLES__;
const CAT = "__CAT__";
const XSVG = '<svg viewBox="0 0 100 100" aria-hidden="true"><path d="M22 22 L78 78 M78 22 L22 78" stroke="#fff" stroke-width="15" stroke-linecap="round" fill="none"/></svg>';
let cur = 0, marks = [], undo = [], seconds = 0, timer = null, assist = true, done = false;
const $ = id => document.getElementById(id);

function key(){ return "meowdoku-hard-" + PUZZLES[cur].id; }
function save(){ localStorage.setItem(key(), JSON.stringify({marks, seconds, done})); }
function load(){
  const s = localStorage.getItem(key());
  const N = PUZZLES[cur].n;
  marks = Array.from({length:N}, () => Array(N).fill(0)); seconds = 0; done = false; undo = [];
  if (s) { try { const o = JSON.parse(s); if (o.marks && o.marks.length === N) { marks = o.marks; seconds = o.seconds || 0; done = !!o.done; } } catch(e){} }
}
function attacks(a, b){ return (a[0]!==b[0]||a[1]!==b[1]) && (a[0]===b[0]||a[1]===b[1]||(Math.abs(a[0]-b[0])<=1&&Math.abs(a[1]-b[1])<=1)); }

function build(){
  const P = PUZZLES[cur], N = P.n, b = $("board");
  b.style.gridTemplateColumns = `repeat(${N},1fr)`;
  b.innerHTML = "";
  for (let r=0;r<N;r++) for (let c=0;c<N;c++){
    const el = document.createElement("button");
    el.className = "cell"; el.type = "button"; el.setAttribute("role","gridcell");
    el.style.setProperty("--cc", `var(--c${P.grid[r][c]})`);
    el.dataset.r = r; el.dataset.c = c;
    el.innerHTML = XSVG + `<img src="${CAT}" alt="">`;
    el.addEventListener("click", () => tap(r,c));
    b.appendChild(el);
  }
  $("n").textContent = N;
  document.querySelectorAll("#picker button").forEach((x,i)=>x.setAttribute("aria-pressed", i===cur));
  render();
}

function render(){
  const P = PUZZLES[cur], N = P.n;
  const cats = [];
  for (let r=0;r<N;r++) for (let c=0;c<N;c++) if (marks[r][c]===2) cats.push([r,c]);
  const bad = new Set();
  for (const a of cats) for (const b of cats) if (a!==b && (attacks(a,b) || P.grid[a[0]][a[1]]===P.grid[b[0]][b[1]])) bad.add(a[0]+","+a[1]);
  document.querySelectorAll(".cell").forEach(el => {
    const r=+el.dataset.r, c=+el.dataset.c, m = marks[r][c];
    el.classList.toggle("x", m===1); el.classList.toggle("cat", m===2);
    el.classList.toggle("bad", bad.has(r+","+c));
    el.setAttribute("aria-label", `row ${r+1} column ${c+1}: ${m===2?"cat":m===1?"crossed":"empty"}`);
  });
  $("cats").textContent = cats.length;
  $("undo").disabled = undo.length===0;
  if (!done && cats.length===N && bad.size===0) win();
}

function push(){ undo.push(marks.map(row=>row.slice())); if (undo.length>200) undo.shift(); }
function tap(r,c){
  if (done) return;
  push();
  const P = PUZZLES[cur], N = P.n;
  marks[r][c] = (marks[r][c]+1)%3;
  if (marks[r][c]===2 && assist){
    for (let i=0;i<N;i++) for (let j=0;j<N;j++)
      if (marks[i][j]===0 && (attacks([r,c],[i,j]) || (P.grid[i][j]===P.grid[r][c] && (i!==r||j!==c)))) marks[i][j]=1;
  }
  clearHints(); render(); save(); startTimer();
}
function clearHints(){ document.querySelectorAll(".cell.hint").forEach(e=>e.classList.remove("hint")); }

function win(){
  done = true; stopTimer(); save();
  $("wontext").textContent = `${PUZZLES[cur].name} in ${fmt(seconds)}.`;
  $("won").classList.add("show");
}
function fmt(s){ return Math.floor(s/60)+":"+String(s%60).padStart(2,"0"); }
function startTimer(){ if (timer||done) return; timer = setInterval(()=>{seconds++; $("time").textContent=fmt(seconds); if(seconds%5===0) save();},1000); }
function stopTimer(){ clearInterval(timer); timer=null; }

$("undo").addEventListener("click", ()=>{ if(!undo.length||done) return; marks = undo.pop(); clearHints(); render(); save(); });
$("reset").addEventListener("click", ()=>{ if(!confirm("Clear this board?")) return; stopTimer(); const N=PUZZLES[cur].n; marks = Array.from({length:N},()=>Array(N).fill(0)); undo=[]; seconds=0; done=false; $("time").textContent="0:00"; clearHints(); render(); save(); });
$("check").addEventListener("click", ()=>{
  const P = PUZZLES[cur]; const sol = new Set(P.solution.map(s=>s.join(",")));
  let wrong = 0;
  document.querySelectorAll(".cell").forEach(el => {
    const r=+el.dataset.r, c=+el.dataset.c, m=marks[r][c];
    const isCat = sol.has(r+","+c);
    const mistake = (m===2 && !isCat) || (m===1 && isCat);
    el.classList.toggle("bad", mistake); if (mistake) wrong++;
  });
  if (!wrong) { $("wontext").textContent = "No mistakes so far."; }
  alert(wrong ? `${wrong} mistake${wrong>1?"s":""} marked in red.` : "No mistakes so far.");
});
$("hint").addEventListener("click", ()=>{
  if (done) return;
  const P = PUZZLES[cur];
  clearHints();
  // first: a wrongly placed cat
  for (let r=0;r<P.n;r++) for (let c=0;c<P.n;c++) if (marks[r][c]===2 && !P.solution.some(s=>s[0]===r&&s[1]===c)) {
    cellAt(r,c).classList.add("hint"); alert("The ringed cat is in the wrong place."); return; }
  // otherwise: reveal one missing cat
  const missing = P.solution.filter(s=>marks[s[0]][s[1]]!==2);
  if (!missing.length) return;
  const [r,c] = missing[Math.floor(Math.random()*missing.length)];
  push(); marks[r][c]=2;
  if (assist) for (let i=0;i<P.n;i++) for (let j=0;j<P.n;j++)
    if (marks[i][j]===0 && (attacks([r,c],[i,j]) || (P.grid[i][j]===P.grid[r][c] && (i!==r||j!==c)))) marks[i][j]=1;
  render(); cellAt(r,c).classList.add("hint"); save(); startTimer();
});
function cellAt(r,c){ return document.querySelector(`.cell[data-r="${r}"][data-c="${c}"]`); }
$("assist").addEventListener("click", ()=>{ assist=!assist; $("assist").setAttribute("aria-checked", assist); localStorage.setItem("meowdoku-assist", assist?"1":"0"); });
$("wonok").addEventListener("click", ()=>$("won").classList.remove("show"));

const picker = $("picker");
PUZZLES.forEach((p,i)=>{ const b=document.createElement("button"); b.type="button"; b.textContent=`${p.n}×${p.n}`; b.setAttribute("role","tab");
  b.addEventListener("click", ()=>{ stopTimer(); cur=i; load(); build(); $("time").textContent=fmt(seconds); localStorage.setItem("meowdoku-cur", i); }); picker.appendChild(b); });
assist = localStorage.getItem("meowdoku-assist") !== "0"; $("assist").setAttribute("aria-checked", assist);
cur = Math.min(PUZZLES.length-1, +(localStorage.getItem("meowdoku-cur")||0));
load(); build(); $("time").textContent = fmt(seconds);
</script>
</body>
</html>
"""

out = PAGE.replace("__PUZZLES__", json.dumps(PUZZLES)).replace("__CAT__", CAT)
with open(os.path.join(HERE, "play.html"), "w") as f:
    f.write(out)
print("wrote play.html", len(out), "bytes")
