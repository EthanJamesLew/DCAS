#!/usr/bin/env python3
"""Render hardest.json into img/hardest_*.png, HARDEST.md and hardest.html."""
import base64
import html
import json
import os

from gamegfx import IMG, board, figure
from make_rules import CSS
from rule_solver import Contradiction, Puzzle, State, solve_depth

HERE = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(HERE, "hardest.json")))
PALETTE = ["purple", "yellow", "pink", "brown", "orange", "green", "dgreen", "blue", "rose", "gold",
           "purple", "yellow", "pink"]


def colours_of(grid):
    N = len(grid)
    return {(r, c): PALETTE[int(grid[r][c])] for r in range(N) for c in range(N)}


def stall_state(grid):
    """Run the direct rules to a fixed point; return (cats, eliminated, refutable cells)."""
    p = Puzzle(grid)
    st = State(p)
    st.propagate()
    N = p.N
    elim = [(r, c) for r in range(N) for c in range(N) if (r, c) not in st.cand and (r, c) not in st.cats]
    refuted = []
    if not st.solved():
        for cell in sorted(st.cand):
            trial = st.copy()
            try:
                trial.place(cell)
                solve_depth(trial, 0, {"rounds": {}, "elims": {}})
            except Contradiction:
                refuted.append(cell)
    return sorted(st.cats), elim, refuted, st.solved()


def render(N, idx, entry):
    grid = entry["grid"]
    cols = colours_of(grid)
    sol = [tuple(x) for x in entry["solution"]]
    cats, elim, refuted, solved = stall_state(grid)
    cell = 60 if N <= 6 else (50 if N <= 8 else 42)
    panels = [board(N, N, colors=cols, cell=cell, gap=6),
              board(N, N, colors=cols, cats=cats, xs=elim, rings=refuted, cell=cell, gap=6),
              board(N, N, colors=cols, cats=sol, xs=[c for c in cols if c not in sol], cell=cell, gap=6)]
    caps = ["the board",
            "where the direct rules stall (rings: cells only a what-if refutes)",
            "the unique solution"]
    name = f"hardest_{N}_{idx}.png"
    figure(name, panels, caps, arrows=True, gapx=20)
    return name


def main():
    md = ["# The hardest Meowdoku boards, by the rulebook\n",
          "Difficulty here means *how much the rules of `RULES.md` have to guess*.  A rule-only "
          "solver (`rule_solver.py`) runs the direct rules (single candidates, common attack, "
          "colours locked in lines, lines made of few colours, full rectangles) to a fixed point.  "
          "If that does not finish the board, it tries a what-if on every open cell: place a cat "
          "there and run the direct rules; a contradiction crosses the cell out.  A board that "
          "needs a what-if has depth 1; one that needs a what-if *inside* a what-if has depth 2.  "
          "The meter is the tuple (depth, what-if rounds at that depth, cells crossed out by "
          "what-ifs, direct-rule steps), compared left to right.\n",
          "For each size, `hardest.py` samples random boards with a unique solution and then "
          "hill-climbs the best ones by moving boundary cells between colours.  Every board that "
          "ties the maximum is listed, after removing the 8 symmetries and colour renamings.  "
          "The search is heuristic: these are the hardest boards *found*, not a proof that "
          "nothing harder exists.\n",
          "## Summary\n",
          "| size | random boards sampled | with a unique solution | of those, needing a what-if | "
          "climb steps | max difficulty | boards tying the max |",
          "|---|---|---|---|---|---|---|"]
    sections = []
    for N in sorted(H, key=int):
        r = H[N]
        hist = r["depth_histogram_random_unique"]
        need = sum(v for k, v in hist.items() if int(k) >= 1)
        md.append(f"| {N} x {N} | {r['sampled']} | {r['unique']} | {need} | {r['climb_steps']} | "
                  f"{tuple(r['max_difficulty'])} | {len(r['hardest'])} |")
        figs = []
        for i, e in enumerate(r["hardest"][:6]):
            figs.append((render(int(N), i, e), e))
        sections.append((N, r, figs))
    md.append("")
    md.append("Level 155 from the screenshot scores (0, 0, 0, 16): the direct rules alone solve it.\n")
    for N, r, figs in sections:
        md.append(f"## {N} x {N}: difficulty {tuple(r['max_difficulty'])}, {len(r['hardest'])} board(s)\n")
        for name, e in figs:
            md.append(f"![{N}x{N} hardest]({'img/' + name})\n")
            md.append("```\n" + "\n".join(e["grid"]) + "\n```\n")
        if len(r["hardest"]) > 6:
            md.append(f"{len(r['hardest']) - 6} more tying boards are in `hardest.json`.\n")
    with open(os.path.join(HERE, "HARDEST.md"), "w") as f:
        f.write("\n".join(md) + "\n")

    # ---- html --------------------------------------------------------------
    def uri(name):
        with open(os.path.join(IMG, name), "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    parts = ['<title>Hardest Meowdoku Boards</title>',
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400&display=swap">',
             '<style>' + CSS + '</style>',
             '<main><header><div class="eyebrow">Meowdoku &middot; searched with the rulebook</div>',
             '<h1>The boards that make the rules guess</h1>',
             '<p>A solver that knows only the rules of the rulebook runs them to a fixed point. '
             'If the board is not finished, it must try a cell: put a cat there, run the rules, and '
             'cross the cell out on a contradiction. Depth 1 means one such what-if is needed; '
             'depth 2 means a what-if inside a what-if. For each size, random boards with a unique '
             'solution were sampled and the best were hill-climbed by moving boundary cells between '
             'colours. Every board that ties the maximum is shown, up to symmetry and colour renaming. '
             'These are the hardest boards found by the search, not a proof that none harder exist.</p>',
             '<nav class="pills">']
    for N, r, figs in sections:
        parts.append(f'<a href="#n{N}">{N} &times; {N}</a>')
    parts.append('</nav></header>')
    parts.append('<section class="notation"><h2>Summary</h2><div style="overflow-x:auto"><table style="border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%">')
    parts.append('<tr><th style="text-align:left">size</th><th>sampled</th><th>unique</th><th>needing a what-if</th><th>climb steps</th><th>max difficulty</th><th>ties</th></tr>')
    for N, r, figs in sections:
        hist = r["depth_histogram_random_unique"]
        need = sum(v for k, v in hist.items() if int(k) >= 1)
        parts.append(f'<tr><td>{N} &times; {N}</td><td style="text-align:right">{r["sampled"]}</td>'
                     f'<td style="text-align:right">{r["unique"]}</td><td style="text-align:right">{need}</td>'
                     f'<td style="text-align:right">{r["climb_steps"]}</td><td style="text-align:center"><code>{tuple(r["max_difficulty"])}</code></td>'
                     f'<td style="text-align:right">{len(r["hardest"])}</td></tr>')
    parts.append('</table></div><p style="margin-top:12px">Difficulty is (depth, what-if rounds, cells crossed out by what-ifs, direct-rule steps). '
                 'Level 155 from the screenshot scores (0, 0, 0, 16): the direct rules finish it alone.</p></section>')
    for N, r, figs in sections:
        parts.append(f'<article id="n{N}">')
        for k, (name, e) in enumerate(figs):
            parts.append(f'<figure><img src="{uri(name)}" alt="{N} by {N} hardest board {k + 1}"></figure>')
            parts.append('<div class="body">')
            if k == 0:
                parts.append(f'<h2>{N} &times; {N}: difficulty {html.escape(str(tuple(r["max_difficulty"])))}, {len(r["hardest"])} board{"s" if len(r["hardest"]) != 1 else ""} tie</h2>')
            parts.append(f'<div class="label">Board {k + 1}</div><div class="formalbox"><pre>' + html.escape("\n".join(e["grid"])) + '</pre></div>')
            parts.append('</div>')
        if len(r["hardest"]) > 6:
            parts.append(f'<div class="body"><p>{len(r["hardest"]) - 6} more tying boards are listed in hardest.json.</p></div>')
        parts.append('</article>')
    parts.append('<footer>Search script, solver and raw results: the <code>meowdoku/</code> folder of the DCAS repository.</footer></main>')
    with open(os.path.join(HERE, "hardest.html"), "w") as f:
        f.write("\n".join(parts))
    print("wrote HARDEST.md and hardest.html")


if __name__ == "__main__":
    main()
