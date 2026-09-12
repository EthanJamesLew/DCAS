#!/usr/bin/env python3
"""Narrated hand-solve of the hardest 10x10 board (or any board): WALKTHROUGH.md + walkthrough.html.

The solver applies the direct rules and logs every step.  When it stalls it
looks for the what-if with the *shortest* refutation, applies only that one
elimination (as a person would), and continues.
"""
import base64
import html
import json
import os
import sys

from gamegfx import IMG, board, figure
from make_rules import CSS
from rule_solver import Contradiction, Puzzle, State

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ["purple", "yellow", "pink", "brown", "orange", "green", "dark green", "blue", "rose", "gold"]
PAL = ["purple", "yellow", "pink", "brown", "orange", "green", "dgreen", "blue", "rose", "gold"]


def cell_name(c):
    return f"r{c[0] + 1}c{c[1] + 1}"


def cells_str(cells, limit=12):
    cells = sorted(cells)
    s = ", ".join(cell_name(c) for c in cells[:limit])
    if len(cells) > limit:
        s += f" and {len(cells) - limit} more"
    return s


def unit_name(kind, idx):
    if kind == "colour":
        return NAMES[idx]
    return f"{'row' if kind == 'row' else 'column'} {idx + 1}"


def reason_text(reason):
    import re
    m = re.match(r"(row|col|colour) (\d+) has no cell left", reason)
    if m:
        return f"{unit_name(m.group(1), int(m.group(2)))} has no cell left"
    return reason


def describe(entry):
    """Turn a solver log entry into a sentence a player would say."""
    rule, what, removed, placed = entry["rule"], entry["what"], entry["removed"], entry["placed"]
    if rule == "single":
        kind, idx = what.split()[0], int(what.split()[1])
        return (f"**{unit_name(kind, idx).capitalize()} has only one cell left**, so the cat goes on "
                f"{cell_name(placed)}. Cross out everything it attacks and the rest of its colour "
                f"({len(removed)} cell{'s' if len(removed) != 1 else ''}).")
    if rule == "common attack":
        kind, idx = what.split()[4], int(what.split()[5])
        return (f"**Common attack from {unit_name(kind, idx)}.** Every cell where its cat could still go "
                f"attacks {cells_str(removed)}, so cross those out.")
    if rule == "colours locked in lines":
        import re
        cols = [int(x) for x in re.findall(r"\d+", what.split("fit")[0])]
        lines = [int(x) + 1 for x in re.findall(r"\d+", what.split("inside")[1])]
        axis = "rows" if "rows" in what else "columns"
        one = len(lines) == 1
        return (f"**{' and '.join(NAMES[g] for g in cols).capitalize()} fit{'s' if len(cols) == 1 else ''} inside "
                f"{axis[:-1] if one else axis} {' and '.join(map(str, lines))}**, so "
                f"{'that ' + axis[:-1] + ' belongs' if one else 'those ' + axis + ' belong'} to "
                f"{'it' if len(cols) == 1 else 'them'}: cross out {cells_str(removed)}.")
    if rule == "lines made of few colours":
        import re
        axis = "rows" if what.startswith("rows") else "columns"
        lines = [int(x) + 1 for x in re.findall(r"\d+", what.split("contain")[0])]
        cols = [int(x) for x in re.findall(r"\d+", what.split("colours")[-1])]
        return (f"**{axis.capitalize()} {' and '.join(map(str, lines))} contain only "
                f"{' and '.join(NAMES[g] for g in cols)}**, so those colours' cats are there: cross out "
                f"their other cells {cells_str(removed)}.")
    if rule == "full rectangle":
        return f"**Full rectangle:** {what}. Cross out {cells_str(removed)}."
    return f"{rule}: {what}"


def human_solve(grid):
    p = Puzzle(grid)
    st = State(p, log=[])
    phases = []          # list of dicts: kind, text lines, snapshot
    whatifs = 0

    def snapshot(extra=None):
        N = p.N
        xs = [(r, c) for r in range(N) for c in range(N) if (r, c) not in st.cand and (r, c) not in st.cats]
        return {"cats": sorted(st.cats), "xs": xs, **(extra or {})}

    def flush_log(title):
        # split the log into chunks that each end with a cat placement
        chunk = []
        cats_so_far = 0
        for e in st.log:
            chunk.append(e)
            if e["placed"] is not None:
                cats_so_far = len([x for x in st.log[:st.log.index(e) + 1] if x["placed"] is not None])
        # rebuild properly with snapshots by replaying
        chunks, cur = [], []
        for e in st.log:
            cur.append(e)
            if e["placed"] is not None:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        replay = State(p)
        for c in placed_before:
            replay.place(c)
        for xcell in removed_before:
            replay.cand.discard(xcell)
        for i, ch in enumerate(chunks):
            for e in ch:
                for xcell in e["removed"]:
                    replay.cand.discard(tuple(xcell))
                if e["placed"] is not None:
                    replay.cats.add(tuple(e["placed"]))
                    replay.cand.discard(tuple(e["placed"]))
            N = p.N
            xs = [(r, c) for r in range(N) for c in range(N) if (r, c) not in replay.cand and (r, c) not in replay.cats]
            last = ch[-1]
            t = (f"Cat {len(replay.cats)}: {cell_name(last['placed'])}" if last["placed"] is not None
                 else title)
            phases.append({"kind": "direct", "title": t, "lines": [describe(e) for e in ch],
                           "snap": {"cats": sorted(replay.cats), "xs": xs}})
        placed_before[:] = sorted(st.cats)
        removed_before[:] = [c for c in xs_now()]
        st.log.clear()

    def xs_now():
        N = p.N
        return [(r, c) for r in range(N) for c in range(N) if (r, c) not in st.cand and (r, c) not in st.cats]

    placed_before, removed_before = [], []

    st.propagate()
    flush_log("Direct rules")
    while not st.solved():
        # find the what-if that unlocks the most (tie: shortest refutation)
        best = None
        for cell in sorted(st.cand):
            trial = st.copy()
            trial.log = []
            try:
                trial.place(cell)
                trial.propagate()
            except Contradiction as e:
                after = st.copy()
                after.log = None
                after.cand.discard(cell)
                try:
                    after.propagate()
                    progress = (len(after.cats) - len(st.cats), len(st.cand) - len(after.cand))
                except Contradiction:
                    progress = (0, 0)
                key = (tuple(-x for x in progress), len(trial.log), cell)
                if best is None or key < best[0]:
                    N = p.N
                    xs = [(r, c) for r in range(N) for c in range(N) if (r, c) not in trial.cand and (r, c) not in trial.cats]
                    best = (key, cell, list(trial.log), str(e), {"cats": sorted(trial.cats), "xs": xs})
        if best is None:
            phases.append({"kind": "stuck", "title": "No single what-if resolves this", "lines": [], "snap": snapshot()})
            break
        whatifs += 1
        _, cell, trace, reason, tsnap = best
        lines = [f"Suppose a cat sits on **{cell_name(cell)}**. It crosses out its row, column, colour and neighbours."]
        lines += [describe(e) for e in trace]
        lines.append(f"**Contradiction: {reason_text(reason)}.** So {cell_name(cell)} cannot hold a cat: cross it out.")
        phases.append({"kind": "whatif", "title": f"Stuck: try {cell_name(cell)}", "lines": lines,
                       "snap": {**tsnap, "trial": cell}})
        st.cand.discard(cell)
        removed_before.append(cell)
        st.propagate()
        flush_log("Direct rules again")
    return p, phases, whatifs


def main(N="10", idx=0):
    H = json.load(open(os.path.join(HERE, "hardest.json")))
    entry = H[N]["hardest"][idx]
    grid = entry["grid"]
    p, phases, whatifs = human_solve(grid)
    n = p.N
    colours = {(r, c): PAL[int(grid[r][c])] for r in range(n) for c in range(n)}
    cellpx = 40
    # figures
    figs = []
    figure("walk_00.png", [board(n, n, colors=colours, cell=cellpx, gap=5)], ["the board"], gapx=16)
    figs.append("walk_00.png")
    for i, ph in enumerate(phases, 1):
        s = ph["snap"]
        rings = [s["trial"]] if "trial" in s else []
        name = f"walk_{i:02d}.png"
        cap = ph["title"]
        figure(name, [board(n, n, colors=colours, cats=s["cats"], xs=s["xs"], rings=rings, cell=cellpx, gap=5)], [cap], gapx=16)
        figs.append(name)

    # markdown
    md = [f"# Solving the hardest {n} x {n} board by hand\n",
          "Cells are written r<row>c<column>, counted from 1 at the top left.  Colours are named as in "
          "the playable page.  Every step is one rule from RULES.md; the solver logged them in the order "
          "a careful player would find them.\n",
          f"![board](img/{figs[0]})\n"]
    for i, ph in enumerate(phases, 1):
        md.append(f"## {i}. {ph['title']}\n")
        for line in ph["lines"]:
            md.append(f"* {line}")
        md.append("")
        md.append(f"![after step {i}](img/{figs[i]})\n")
    md.append(f"Total: {whatifs} what-if{'s' if whatifs != 1 else ''}; everything else is direct rules.\n")
    with open(os.path.join(HERE, "WALKTHROUGH.md"), "w") as f:
        f.write("\n".join(md) + "\n")

    # html
    def uri(name):
        with open(os.path.join(IMG, name), "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()

    def md_inline(s):
        import re
        s = html.escape(s)
        return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    parts = [f'<title>Hand-Solving the {n}x{n}</title>',
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400&display=swap">',
             '<style>' + CSS + ' article figure img{max-width:420px;margin:0 auto} .steps{margin:0;padding-left:1.2em} .steps li{margin:6px 0}</style>',
             '<main><header><div class="eyebrow">Meowdoku &middot; hard mode &middot; walkthrough</div>',
             f'<h1>How to solve the {n} &times; {n} by hand</h1>',
             '<p>Cells are written r&lt;row&gt;c&lt;column&gt;, counted from 1 at the top left. Every step is '
             'one rule from the rulebook, in the order a careful player finds them. The board stalls once; '
             'the what-if chosen is the one with the shortest chain to a contradiction.</p></header>',
             f'<article><figure><img src="{uri(figs[0])}" alt="the board"></figure></article>']
    for i, ph in enumerate(phases, 1):
        parts.append('<article>')
        parts.append(f'<div class="body"><h2>{i}. {html.escape(ph["title"])}</h2>')
        parts.append(f'<div class="label{" proof" if ph["kind"] == "whatif" else ""}">{"What-if" if ph["kind"] == "whatif" else "Direct rules"}</div>')
        parts.append('<ol class="steps">' + "".join(f"<li>{md_inline(l)}</li>" for l in ph["lines"]) + '</ol></div>')
        parts.append(f'<figure><img src="{uri(figs[i])}" alt="board after step {i}"></figure></article>')
    parts.append(f'<footer>{whatifs} what-if{"s" if whatifs != 1 else ""}; everything else is direct rules. Generated by walkthrough.py.</footer></main>')
    with open(os.path.join(HERE, "walkthrough.html"), "w") as f:
        f.write("\n".join(parts))
    print(f"{len(phases)} phases, {whatifs} what-ifs; wrote WALKTHROUGH.md and walkthrough.html")
    return phases


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["10"]))
