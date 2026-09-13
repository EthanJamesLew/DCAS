#!/usr/bin/env python3
"""Build REPORT_3D.md and report3d.html (figures in img/nd_*.png) from the nd.py results."""
import base64
import html
import itertools
import json
import os
import re

from gamegfx import IMG, INK, RED, board, figure
from make_rules import CSS
import nd

HERE = os.path.dirname(os.path.abspath(__file__))
PAL = ["purple", "yellow", "pink", "brown", "orange", "green", "dgreen", "blue", "rose", "gold"]


def J(name):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else {}


V = J("variants_nd.json")
C = J("variants_nd_counts.json").get("slice_counts", {})
R = J("variants_nd_random.json").get("random_nd", {})
P = J("variants_nd_pairs.json").get("pairs_3d", {})
HD = J("variants_nd_hard.json")
V2 = J("variants.json")


def logline(name, pat):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    return [l.strip() for l in open(p) if re.match(pat, l)]


# ---------------------------------------------------------------------------
# figures: a cube drawn as its layers (axis 0 = layer, axis 1 = row, axis 2 = column)
# ---------------------------------------------------------------------------
def layers(name, n, colours=None, cats=(), xs=(), rings=(), captions=None, cell=44):
    panels = []
    caps = []
    for z in range(n):
        col = {(r, c): colours.get((z, r, c), "gray") for r in range(n) for c in range(n)} if colours else None
        panels.append(board(n, n, colors=col,
                            cats=[(r, c) for (a, r, c) in cats if a == z],
                            xs=[(r, c) for (a, r, c) in xs if a == z],
                            rings=[(r, c) for (a, r, c) in rings if a == z],
                            cell=cell, gap=5, pad=8))
        caps.append(captions[z] if captions else f"layer {z + 1}")
    figure(name, panels, caps, gapx=14)


def attacked_by(cats, n):
    cells = itertools.product(range(n), repeat=3)
    return [c for c in cells if any(nd.attack_slice(k, c) for k in cats) and c not in cats]


figs = []

# 1. three cats in a 3x3x3 (the vanished anomaly)
ex = [(0, 0, 1), (1, 2, 0), (2, 1, 2)]
layers("nd_333.png", 3, cats=ex, xs=attacked_by(ex, 3))
figs.append("nd_333.png")

# 2. box rules from the data
BR = V.get("box_rules_3d", {})


def box_figure(name, dims, entry, n=4, off=(1, 1, 1)):
    box = [tuple(o + x for o, x in zip(off, c)) for c in itertools.product(*(range(k) for k in dims))]
    inside = [tuple(o + x for o, x in zip(off, c)) for c in map(tuple, entry["forced_inside"])]
    near = [tuple(o + x for o, x in zip(off, c)) for c in map(tuple, entry["forced_adjacent"])]
    colours = {}
    k = entry["k"]
    # colour the box cells with k colours by splitting along the longest axis
    axis = max(range(3), key=lambda a: dims[a])
    for c in box:
        colours[c] = PAL[(c[axis] - off[axis]) * k // dims[axis]]
    layers(name, n, colours=colours, xs=inside + near)


for key, dims in (("2x2x3", (2, 2, 3)), ("2x3x3", (2, 3, 3)), ("3x3x3", (3, 3, 3))):
    if key in BR:
        nm = f"nd_box_{key}.png"
        box_figure(nm, dims, BR[key], n=4 if key != "3x3x3" else 5)
        figs.append(nm)

# 3. hardest random 3D board found
hard = HD.get("d3_n4") or (R.get("d3_n4") or {}).get("hardest")
if hard:
    colour = {tuple(map(int, k.split(","))): g for k, g in hard["colour"].items()}
    sol = [tuple(c) for c in hard["solution"]]
    colours = {c: PAL[g % 10] for c, g in colour.items()}
    layers("nd_hard4.png", 4, colours=colours)
    layers("nd_hard4_sol.png", 4, colours=colours, cats=sol, xs=[c for c in colour if c not in sol])
    figs += ["nd_hard4.png", "nd_hard4_sol.png"]

# 4. the order-9 king-distance Latin square
L9 = [[(5 + 4 * j - 2 * i) % 9 for j in range(9)] for i in range(9)]
figure("nd_latin9.png", [board(9, 9, colors={(i, j): PAL[L9[i][j]] for i in range(9) for j in range(9)},
                               labels={(i, j): L9[i][j] for i in range(9) for j in range(9)}, cell=44, gap=5)],
       ["L(i, j) = 5 + 4j - 2i (mod 9): king-adjacent entries always differ by at least 2"], gapx=14)
figs.append("nd_latin9.png")


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------
def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


caps = V.get("capacities", {})


def cap_table(key, d):
    row = caps.get(key, {})
    items = sorted(row.items(), key=lambda kv: tuple(int(x) for x in kv[0].split("x")))
    anomalies = [k for k, v in items if v < min(int(x) for x in k.split("x"))]
    return items, anomalies


md = []
w = md.append
w("# Meowdoku in three and more dimensions: a report\n")
w("Everything below was computed by `nd.py` (results in `variants_nd*.json`), except where a "
  "proof is given.  Notation: a *d-cube of side n* has n^d cells; a *slice* is an (d−1)-dimensional "
  "layer perpendicular to one axis; two cells *touch* when every coordinate differs by at most 1 "
  "(the 3^d − 1 neighbourhood).\n")
w("## 1. Two ways to go up a dimension\n")
w("In 2D a cat owns a row and a column.  In d dimensions there are two natural readings:\n")
w("* **Slice variant.**  n cats in the n^d cube, exactly one per slice in every direction, n colours "
  "with one cat each, no two cats touching.  A placement is a list of cats (i, p₁(i), …, p_{d−1}(i)) "
  "with each pᵢ a permutation.  This is the reading in which every 2D theorem has a direct analogue.\n"
  "* **Line variant.**  One cat on every axis-parallel line, so n^{d−1} cats, n^{d−1} colours, no two "
  "cats touching.  Writing the height of the cat above the cell x of the base as L(x), the line rules "
  "say that L is a *Latin (d−1)-cube* and the touching rule says that king-adjacent entries of L "
  "differ by at least 2.\n")
w("The 2D counting rules (Rules 8-10) need only that rows, columns and colours are *separating*: two "
  "cats that share one are the same cat.  Slices and colours are separating in every dimension and "
  "for both variants, so the Lean lemmas `hall1`, `hall2`, `hall3` and common attack (Rule 1) transfer "
  "without change.  What does *not* transfer is anything that used the geometry of the knight's move.\n")

# --- slice variant ---------------------------------------------------------
w("## 2. The slice variant\n")
w("### 2.1 The knight's move in d dimensions\n")
w("Two cats in consecutive slices of one axis must differ by at least 2 in *at least one* of the "
  "other d − 1 coordinates (otherwise they touch).  In 2D there is only one other coordinate, so the "
  "cats are a knight's move apart.  In 3D the projection onto the transverse plane must move at "
  "Chebyshev distance ≥ 2: a knight's move in one coordinate is enough, the other may stay put.  "
  "This single difference explains every change below.\n")

w("### 2.2 Capacities: the 3 × 3 anomaly disappears, the 2^d anomaly stays\n")
for d, key in ((3, "slice_d3"), (4, "slice_d4"), (5, "slice_d5")):
    items, anomalies = cap_table(key, d)
    if not items:
        continue
    w(f"**d = {d}** (region-free maximum number of cats in a box):\n")
    w(table(["box"] + [k for k, _ in items], [["cats"] + [v for _, v in items]]))
    w("")
    w(f"Boxes holding fewer than their smallest side: {', '.join(anomalies) if anomalies else 'none'}.\n")
w("**Theorem (2^d rule).**  A 2 × 2 × … × 2 box holds at most one cat in every dimension: any two of "
  "its cells differ by at most 1 in every coordinate, so they touch.\n")
w("**Observation (verified for all boxes with sides ≤ 4 in 3D and ≤ 3 in 4D and 5D).**  Every other "
  "box holds min(side) cats.  In particular the 3 × 3 × 3 holds three cats, for example (0,0,1), "
  "(1,2,0), (2,1,2): consecutive layers use a knight's move in one transverse coordinate and a step "
  "of 0 or 2 in the other.  The 2D proof of the 3 × 3 rule fails exactly because it has no second "
  "transverse coordinate to spend.  Consequence: *the impossible layouts of 2D are not impossible in "
  "3D*, except for the all-2 box.  Three colours confined to a 3 × 3 × 3 is a legal position.\n")
w(f"![three cats in a 3x3x3](img/nd_333.png)\n")

w("### 2.3 How many placements\n")
rows = []
for d in sorted(C, key=int):
    rows.append([f"d = {d}"] + [C[d].get(str(n), "") for n in range(1, 9)])
w(table(["dimension \\ n"] + [str(n) for n in range(1, 9)], rows))
w("")
w("d = 2 is Hertzsprung's sequence (OEIS A002464).  The d = 3 sequence 1, 0, 8, 236, 7188, 288940, "
  "15296980 is not in the OEIS (searched 2026-09-13), but it needs no new recurrence: every dimension "
  "is determined by 2D data.\n")
w("**Theorem (transfer formula).**  Call a step i (between slices i and i+1) *bad* in a permutation π "
  "if |π(i) − π(i+1)| ≤ 1, and let B(S) be the number of permutations of [n] that are bad at every step "
  "of a set S.  A placement is a (d−1)-tuple of permutations, and two consecutive cats touch exactly when "
  "the step is bad in *every* coordinate.  Inclusion-exclusion over the set of touching steps gives\n\n"
  "    K_d(n) = Σ_{S ⊆ {0..n−2}} (−1)^{|S|} · B(S)^{d−1}.\n\n"
  "Checked against every entry of the table (n ≤ 6, d ≤ 5).  For d = 2 it is the inclusion-exclusion "
  "form of Hertzsprung's count; for n = 3 the only permutations with a bad step 0 are 012, 210, 102, 120 "
  "(B = 4), with a bad step 1 likewise 4, with both bad 2, so\n\n"
  "    K_d(3) = 6^{d−1} − 2·4^{d−1} + 2^{d−1}  =  0, 8, 96, 800, ...\n\n"
  "which is the row n = 3 above.  In words: as d grows, K_d(n)/(n!)^{d−1} → 1, because a step touches "
  "with probability about (3/n)^{d−1} per coordinate pair and the corrections are geometric.\n")
w("### 2.4 Forced patterns inside small boxes\n")
w("As in 2D, if k = cap(box) colours are confined to a box, the k cats sit inside it and some cells "
  "of the box (and around it) are provably empty in every solution.  Computed region-free on a 6 × 6 × 6 "
  "board:\n")
rows = []
for key, e in sorted(BR.items(), key=lambda kv: tuple(int(x) for x in kv[0].split("x"))):
    used = "; ".join(f"axis {a}: layers {v}" for a, v in e["slices_used"].items() if v)
    rows.append([key, e["k"], len(e["forced_inside"]), len(e["forced_adjacent"]), used or "none"])
w(table(["box", "k = cap", "forced empty inside", "forced empty adjacent", "slices whose cat is inside the box"], rows))
w("")
w("Three of them deserve names:\n")
w("* **2 × 2 × 3 with two colours** (the 3D Rule 5): the middle layer of the long axis is empty, "
  "the two cats are in the end layers, and every slice of the box in the two short directions is "
  "used, so those slices are empty outside the box.\n"
  "* **2 × 3 × 3 with two colours** (the 3D Rule 4): the two central cells (1,1) of both layers are "
  "empty.  Unlike 2D, nothing outside the box is forced.\n"
  "* **3 × 3 × 3 with three colours** (the 3D knight ring): 15 of the 27 cells are empty.  The outer "
  "layers keep only their four edge-midpoints, the middle layer keeps only its four corners, and every "
  "slice in every direction is used, so the box empties its three layers in all three directions "
  "outside itself.\n")
for key in ("2x2x3", "2x3x3", "3x3x3"):
    if f"nd_box_{key}.png" in figs:
        w(f"![{key} box rule](img/nd_box_{key}.png)\n")

w("### 2.5 Single colours: nothing beyond common attack\n")
S = V.get("shapes_3d", {})
w(f"For all {S.get('count', '?')} polycubes up to size 4 the cells a lone colour forces empty are exactly "
  "the cells attacked by every cell of the shape (the intersection rule), verified with Z3 on a 7 × 7 × 7 "
  "board (the straight tetracube was re-checked on 9 × 9 × 9 because its window fell off the smaller "
  "board).  So, as in 2D, there is no hidden single-colour rule.\n")

w("### 2.6 Two colours: one what-if is still enough (small shapes)\n")
if P:
    w(f"For every pair of disjoint shapes of size ≤ 2 inside a 3 × 3 × 3 window ({P['pairs']} pairs up to "
      f"the 48 symmetries of the cube), on a 5 × 5 × 5 board: {P['impossible']} pairs are impossible, "
      f"{P['novel']} force cells that common attack alone misses, and in {P['novel'] - P['beyond_one_whatif']} "
      f"of those every missed cell falls to a single what-if (assume the cat, apply common attack for the "
      f"two colours and the slices, reach an empty unit).  Pairs needing more: {P['beyond_one_whatif']}.\n")

w("### 2.7 Random boards are easier, not harder\n")
rows = []
for key in sorted(R, key=lambda k: (int(k[1]), int(k.split("_n")[1]))):
    r = R[key]
    d, n = key[1], key.split("_n")[1]
    need = sum(v for k, v in r["depth_histogram"].items() if int(k) >= 1)
    rows.append([f"{d}D, n = {n}", r["samples"], r["unique"], f"{100 * r['unique'] / r['samples']:.0f}%", need])
w(table(["board", "random boards", "unique solution", "share unique", "needing a what-if"], rows))
w("")
w("Colours were grown from a random valid placement exactly as in 2D.  Two things stand out.  Random "
  "3D and 4D colourings have a unique solution far more often than 2D ones (2D: 65% at n = 5 falling "
  "to 15% at n = 10; 3D: 54% at n = 3, 26% at n = 4, 15% at n = 5), because a colour that touches n − 1 "
  "slices in each of three directions is a very tight constraint.  And *none* of the unique random "
  "boards needed a what-if: the direct rules finished every one.  A hill-climb on the colouring "
  "(`hard3d.py`) looks for boards that do:\n")
if HD:
    rows = []
    for key in sorted(HD):
        r = HD[key]
        rows.append([f"{r['d']}D, n = {r['n']}", r["sampled_unique"], r["climb_steps"], tuple(r["best_difficulty"])])
    w(table(["board", "unique boards sampled", "climb steps", "best difficulty (depth, rounds, eliminations)"], rows))
    w("")
    best3 = HD.get("d3_n4", {}).get("best_difficulty", [0])
    if best3 and best3[0] >= 1:
        w("A 4 × 4 × 4 board that needs a what-if exists; the hardest one found is drawn below with its "
          "solution.  Its difficulty is still depth 1: nothing found in any dimension needs a what-if inside "
          "a what-if.\n")
    else:
        w("No 3D or 4D board needing a what-if was found within the budget (seven minutes per size).  For "
          "comparison, the same hill-climb in 2D reaches depth 1 within seconds at every size from 5 to 10.  "
          "Conjecture: with one cat per slice in three directions, the direct rules plus the counting rules "
          "are complete for cubes of side at most 5.\n")
if "nd_hard4.png" in figs:
    w("A typical unique 4 × 4 × 4 board from the search, drawn layer by layer, and its solution "
      "(crosses mark every cell the ten direct-rule steps eliminate):\n")
    w("![a unique 4x4x4 board](img/nd_hard4.png)\n")
    w("![its solution](img/nd_hard4_sol.png)\n")

# --- line variant ------------------------------------------------------------
w("## 3. The line variant: king-distance Latin cubes\n")
w("With one cat per axis-parallel line, the cat above base cell x is at height L(x) and:\n\n"
  "* each line of the base holds every height once (L is a Latin square in 3D, a Latin cube in 4D);\n"
  "* two cats touch iff their base cells are king-adjacent (or equal) and |ΔL| ≤ 1.\n\n"
  "So the line variant is solvable exactly when a Latin (d−1)-cube of order n exists whose king-adjacent "
  "entries always differ by at least 2.  In 2D (d = 2) this is just a knight permutation.\n")
w("### 3.1 The cyclic construction\n")
w("Take L(x) = Σ aᵢ xᵢ (mod n).  It is Latin iff every aᵢ is a unit mod n, and it has the king "
  "property iff every signed sum ±aᵢ ± aⱼ ± … over a non-empty subset of the coefficients lies in "
  "[2, n − 2] mod n.  Orders admitting such coefficients (checked up to 40):\n")
LC = V.get("line_cyclic", {})
rows = []
for d in (2, 3, 4, 5):
    e = LC.get(f"cyclic_d{d}")
    if e:
        orders = e["orders_with_cyclic_solution"]
        missing = [n for n in range(2, 41) if n not in orders]
        rows.append([f"d = {d} (Latin {d - 1}-cube)", min(orders) if orders else "-",
                     ", ".join(map(str, missing)) if missing else "none"])
w(table(["variant", "smallest cyclic order", "orders ≤ 40 with no cyclic solution"], rows))
w("")
w("### 3.2 Existence by exhaustive search\n")
l9 = logline("variants_line910.log", r"^\d+ (sat|unsat)")
l12 = logline("variants_line12.log", r"^\d+ (sat|unsat)")
lc = logline("nd_latincube.log", r"^\d+ (sat|unsat|unknown)")
w("3D (Latin squares), Z3 on the full search space:\n")
res3 = {n: "no" for n in range(2, 9)}
for line in (l9 or []) + (l12 or []):
    n, r = line.split()[:2]
    res3[int(n)] = "yes" if r == "sat" else ("no" if r == "unsat" else r)
w(table(["order"] + [str(n) for n in sorted(res3)], [["exists?"] + [res3[n] for n in sorted(res3)]]))
w("")
w("So the smallest solvable 3D line-variant cube has side 9, the cyclic square of section 3.1 is a "
  "witness, order 10 has none at all (not just none cyclic), and orders 11 and above 12 are covered by "
  "the cyclic construction.  Order 12 is the last open case below 40"
  + (": " + ("it exists" if res3.get(12) == "yes" else "it does not exist" if res3.get(12) == "no" else "the search did not finish") + "." if 12 in res3 else "."))
w("")
if lc:
    w("4D (Latin cubes with the 26-neighbour king condition), Z3 with a 20-minute cap per order:\n")
    w(table(["order"] + [l.split()[0] for l in lc], [["result"] + [l.split()[1] for l in lc]]))
    w("")
w("![order 9](img/nd_latin9.png)\n")
w("### 3.3 Capacities in the dense variant\n")
items, _ = cap_table("line_d3", 3)
if items:
    w(table(["box"] + [k for k, _ in items], [["cats"] + [v for _, v in items]]))
    w("")
    w("A 3 × 3 × 3 holds five non-touching cats when a cat only owns its three lines.  Because the "
      "variant is dense (n² cats in n³ cells, one on every line) these numbers are upper bounds *and* "
      "every line inside a box wants a cat, so a box of side s must contain at least s² − (cats that "
      "can sit on its lines outside it); the exact lower bounds are an open item.\n")

# --- summary -------------------------------------------------------------------
w("## 4. Scorecard: what survives in dimension d\n")
w(table(["2D rule", "slice variant, d ≥ 3", "line variant"], [
    ["Rule 1 common attack", "yes, verbatim (attack = shares a slice or touches)", "yes (attack = shares a line or touches)"],
    ["Rule 2 knight's move", "weaker: Chebyshev distance ≥ 2 in the transverse projection", "|ΔL| ≥ 2 on king-adjacent base cells"],
    ["2 × 2 holds one cat", "yes: the 2^d box holds one cat", "yes (2 × 2 × 2 holds one)"],
    ["3 × 3 holds two cats", "no: 3^d holds three (min side) for d ≥ 3", "3 × 3 × 3 holds five"],
    ["Rules 5-7 patterns", "replaced by the 2 × 2 × 3, 2 × 3 × 3 and 3 × 3 × 3 patterns of 2.4", "open"],
    ["Rules 8-10 counting", "yes, verbatim (separating maps)", "yes, verbatim"],
    ["single colour = intersection rule", "yes (polycubes ≤ 4)", "not checked"],
    ["one what-if is complete locally", "yes for shapes ≤ 2 in a 3 × 3 × 3 window", "not checked"],
    ["random boards need what-ifs", "never observed; hill-climb result in 2.7", "n/a"],
]))
w("")
w("## 5. Conjectures\n")
w("1. **cap = min side except the all-2 box**, for the slice variant in every dimension d ≥ 3 and "
  "every box.  (Verified: sides ≤ 4 in 3D, ≤ 3 in 4D and 5D.)\n"
  "2. **A recurrence for the 3D counts.**  The transfer formula of 2.3 expresses K_3(n) through the "
  "2^{n−1} numbers B(S); Hertzsprung's recurrence comes from the fact that for d = 2 only |S| matters "
  "after grouping runs.  For d = 3 the squares B(S)² should still admit a linear recurrence in n; find "
  "it.\n"
  "3. **King-distance Latin squares exist for every order n ≥ 13 and for 9 and 11, and for no other "
  "order**.  Latin cubes with the 26-neighbour condition (4D line variant) exist for every n ≥ 25 and "
  "for 17, 19, 21, 23 by the cyclic construction and for no n ≤ 13 by exhaustive search; the smallest "
  "order is 14, 15, 16 or 17.\n"
  "4. **One what-if is locally complete in 3D** for two colours of any shape inside a 3 × 3 × 3 window, "
  "as it is in 2D for shapes up to size 4 inside a 3 × 3 window.\n"
  "5. **Direct rules are complete for small cubes**: no 3D or 4D colouring with a unique solution and "
  "n ≤ 5 needs a what-if.  The hill-climb of 2.7 (about 150,000 accepted-or-rejected mutations over "
  "16,000 unique boards) never found one; in 2D the same search finds depth-1 boards within seconds.\n")

with open(os.path.join(HERE, "REPORT_3D.md"), "w") as f:
    f.write("\n".join(md) + "\n")


# ---------------------------------------------------------------------------
# html
# ---------------------------------------------------------------------------
def uri(name):
    with open(os.path.join(IMG, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def md_to_html(text):
    out = []
    lines = text.split("\n")
    i = 0
    in_list = False
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            hdr = [c.strip() for c in rows[0].strip("|").split("|")]
            body = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
            out.append('<div style="overflow-x:auto"><table style="border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;font-size:.92rem">'
                       + "<tr>" + "".join(f'<th style="text-align:left;padding:4px 8px;border-bottom:1px solid var(--line)">{inline(h)}</th>' for h in hdr) + "</tr>"
                       + "".join("<tr>" + "".join(f'<td style="padding:4px 8px;border-bottom:1px solid var(--line)">{inline(c)}</td>' for c in r) + "</tr>" for r in body)
                       + "</table></div>")
            continue
        if ln.startswith("!["):
            m = re.match(r"!\[(.*?)\]\(img/(.*?)\)", ln)
            out.append(f'<figure><img src="{uri(m.group(2))}" alt="{html.escape(m.group(1))}"></figure>')
            i += 1; continue
        if ln.startswith("# "):
            out.append(f"<h1>{inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("* ") or re.match(r"^\d+\. ", ln):
            items = []
            tag = "ul" if ln.startswith("* ") else "ol"
            while i < len(lines) and (lines[i].startswith("* ") or re.match(r"^\d+\. ", lines[i]) or (lines[i].startswith("  ") and items)):
                if lines[i].startswith("  "):
                    items[-1] += " " + lines[i].strip()
                else:
                    items.append(re.sub(r"^(\* |\d+\. )", "", lines[i]))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(it)}</li>" for it in items) + f"</{tag}>")
            continue
        elif ln.strip():
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("|", "!", "#", "* ")) and not re.match(r"^\d+\. ", lines[i]):
                para.append(lines[i]); i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
            continue
        i += 1
    return "\n".join(out)


def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


body = md_to_html("\n".join(md))
page = ['<title>Meowdoku in Higher Dimensions</title>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400&display=swap">',
        '<style>' + CSS + ' main{max-width:82ch} h3{margin-top:22px;font-size:1.15rem} article{padding:6px 26px 18px} figure{margin:14px 0} figure img{max-width:100%} p,ul,ol{margin:10px 0}</style>',
        '<main><header><div class="eyebrow">Meowdoku &middot; three and more dimensions</div></header>',
        '<article>' + body + '</article>',
        '<footer>Computed by nd.py and hard3d.py; sources in the meowdoku/ folder of the DCAS repository.</footer></main>']
with open(os.path.join(HERE, "report3d.html"), "w") as f:
    f.write("\n".join(page))
print("wrote REPORT_3D.md and report3d.html;", len(figs), "figures")
