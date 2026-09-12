#!/usr/bin/env python3
"""Render game-style figures for RULES.md into img/ (drawing code lives in gamegfx.py)."""
import json
import os

from gamegfx import (HERE, IMG, INK, RED, attacked, board, col_cells, figure, rect, row_cells)

# ---------------------------------------------------------------------------
# Figure 0: the four rules
# ---------------------------------------------------------------------------
figure("fig00_rules.png", [
    board(4, 4, cats=[(1, 1)], xs=row_cells(1, 4, [(1, 1)]) + col_cells(1, 4, [(1, 1)])),
    board(4, 4, colors={c: "orange" for c in [(0, 0), (1, 0), (1, 1), (2, 1)]},
          cats=[(1, 1)], xs=[(0, 0), (1, 0), (2, 1)]),
    board(4, 4, cats=[(1, 1)], xs=[(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]),
    board(4, 4, cats=[(1, 1)], xs=attacked((1, 1), 4, 4)),
], ["one per row and column", "one per colour", "cats cannot touch", "all together: what a cat attacks"])

# ---------------------------------------------------------------------------
# Figure 1: common attack (master rule)
# ---------------------------------------------------------------------------
L = [(1, 1), (1, 2), (2, 1)]
bar = [(2, 1), (2, 2), (2, 3)]
dom = [(2, 2), (2, 3)]
figure("fig01_common_attack.png", [
    board(5, 5, colors={c: "orange" for c in L}, xs=[(2, 2)]),
    board(5, 5, colors={c: "yellow" for c in bar}, xs=[(1, 2), (3, 2), (2, 0), (2, 4)]),
    board(5, 5, colors={c: "green" for c in dom}, xs=[(1, 2), (1, 3), (3, 2), (3, 3), (2, 0), (2, 1), (2, 4)]),
], ["L: the inner corner is attacked by all three", "bar of 3: above and below the middle", "bar of 2: the 2x4 around it"])

# ---------------------------------------------------------------------------
# Figure 2: knight's move
# ---------------------------------------------------------------------------
figure("fig02_knight.png", [
    board(3, 6, cats=[(0, 2)], xs=attacked((0, 2), 3, 6), dots=[(1, 0), (1, 4), (1, 5)]),
    board(3, 6, cats=[(0, 2), (1, 4)], xs=attacked((0, 2), 3, 6) + attacked((1, 4), 3, 6)),
], ["row below: only cells 2+ columns away remain", "consecutive rows sit a knight's move apart"])

# ---------------------------------------------------------------------------
# Figure 3: 2x2 and impossible layouts
# ---------------------------------------------------------------------------
figure("fig03_capacity_small.png", [
    board(4, 4, outlines=[(1, 1, 2, 2, INK)], cats=[(1, 1)], xs=[(1, 2), (2, 1), (2, 2)]),
    board(4, 4, colors={(1, 1): "purple", (2, 1): "purple", (1, 2): "pink", (2, 2): "pink"},
          outlines=[(1, 1, 2, 2, RED)]),
    board(5, 5, colors={**{c: "purple" for c in [(1, 1), (1, 2), (2, 1)]},
                        **{c: "pink" for c in [(1, 3), (2, 2), (2, 3)]},
                        **{c: "blue" for c in [(3, 1), (3, 2), (3, 3)]}},
          outlines=[(1, 1, 3, 3, RED)]),
], ["a 2x2 holds at most one cat", "IMPOSSIBLE: two colours inside a 2x2", "IMPOSSIBLE: three colours inside a 3x3"])

# ---------------------------------------------------------------------------
# Figure 4: 3x3 rule
# ---------------------------------------------------------------------------
figure("fig04_3x3.png", [
    board(5, 5, outlines=[(1, 1, 3, 3, INK)], cats=[(1, 1), (2, 3)],
          xs=[c for c in set(attacked((1, 1), 5, 5) + attacked((2, 3), 5, 5))]),
    board(5, 5, colors={**{c: "purple" for c in [(1, 1), (1, 2), (1, 3), (2, 1)]},
                        **{c: "pink" for c in [(2, 2), (2, 3), (3, 1), (3, 2), (3, 3)]}},
          outlines=[(1, 1, 3, 3, INK)], xs=[(2, 2)]),
], ["two cats in a 3x3 kill its third row", "two colours in a 3x3: the centre is empty"])

# ---------------------------------------------------------------------------
# Figure 5: two colours in a 2x3
# ---------------------------------------------------------------------------
A = [(2, 1), (2, 2), (3, 1)]
B = [(2, 3), (3, 2), (3, 3)]
xs = set(row_cells(2, 6) + row_cells(3, 6) + col_cells(1, 6) + col_cells(3, 6) +
         [(1, 1), (1, 2), (1, 3), (4, 1), (4, 2), (4, 3), (2, 2), (3, 2)]) - {(2, 1), (3, 1), (2, 3), (3, 3)}
figure("fig05_2x3.png", [
    board(6, 6, colors={**{c: "purple" for c in A}, **{c: "pink" for c in B}},
          outlines=[(2, 1, 3, 3, INK)]),
    board(6, 6, colors={**{c: "purple" for c in A}, **{c: "pink" for c in B}},
          outlines=[(2, 1, 3, 3, INK)], xs=sorted(xs)),
], ["two colours confined to a 2x3", "middle column, the cells above/below it, and both rows and end columns"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 6: three colours in a 3x4
# ---------------------------------------------------------------------------
A = [(1, 1), (1, 2), (1, 3), (1, 4)]
B = [(2, 1), (2, 2), (3, 1), (3, 2)]
C = [(2, 3), (2, 4), (3, 3), (3, 4)]
box = set(rect(1, 1, 3, 4))
xs = set(row_cells(1, 6) + row_cells(2, 6) + row_cells(3, 6) + col_cells(1, 6) + col_cells(4, 6)) - box
xs |= {(2, 2), (2, 3), (0, 1), (0, 4), (4, 1), (4, 4)}
cols6 = {**{c: "yellow" for c in A}, **{c: "purple" for c in B}, **{c: "pink" for c in C}}
figure("fig06_3x4.png", [
    board(6, 6, colors=cols6, outlines=[(1, 1, 3, 4, INK)]),
    board(6, 6, colors=cols6, outlines=[(1, 1, 3, 4, INK)], xs=sorted(xs)),
], ["three colours confined to a 3x4", "middle row's cat is at an end; rows and end columns fill"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 7: four colours in a 4x4 (knight ring)
# ---------------------------------------------------------------------------
quad = {**{c: "purple" for c in rect(1, 1, 2, 2)}, **{c: "pink" for c in rect(1, 3, 2, 4)},
        **{c: "green" for c in rect(3, 1, 4, 2)}, **{c: "blue" for c in rect(3, 3, 4, 4)}}
box = set(rect(1, 1, 4, 4))
xs = set((r, c) for r in range(6) for c in range(6)) - box - {(0, 0), (0, 5), (5, 0), (5, 5)}
xs |= {(1, 1), (1, 4), (4, 1), (4, 4), (2, 2), (2, 3), (3, 2), (3, 3)}
p1 = [(1, 2), (2, 4), (3, 1), (4, 3)]
p2 = [(1, 3), (2, 1), (3, 4), (4, 2)]
figure("fig07_4x4.png", [
    board(6, 6, colors=quad, outlines=[(1, 1, 4, 4, INK)], xs=sorted(xs)),
    board(6, 6, colors=quad, outlines=[(1, 1, 4, 4, INK)], cats=p1, xs=sorted(xs)),
    board(6, 6, colors=quad, outlines=[(1, 1, 4, 4, INK)], cats=p2, xs=sorted(xs)),
], ["four colours in a 4x4: corners and centre empty", "knight ring 1", "knight ring 2 (the only other option)"])

# ---------------------------------------------------------------------------
# Figure 8: k colours inside k rows
# ---------------------------------------------------------------------------
A = [(1, 0), (1, 1), (2, 0)]
B = [(1, 3), (2, 3), (2, 4)]
cols8 = {**{c: "purple" for c in A}, **{c: "pink" for c in B}}
xs = set(row_cells(1, 6) + row_cells(2, 6)) - set(A) - set(B)
figure("fig08_hall_rows.png", [
    board(6, 6, colors=cols8),
    board(6, 6, colors=cols8, xs=sorted(xs)),
], ["two colours live entirely inside rows 2 and 3", "those rows belong to them: everything else there is empty"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 9: k rows covered by k colours
# ---------------------------------------------------------------------------
A = [(0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]
B = [(1, 3), (1, 4), (1, 5), (2, 2), (2, 3), (2, 4), (2, 5), (3, 4), (3, 5)]
cols9 = {**{c: "purple" for c in A}, **{c: "pink" for c in B}}
figure("fig09_hall_regions.png", [
    board(6, 6, colors=cols9),
    board(6, 6, colors=cols9, xs=[(0, 0), (3, 4), (3, 5)]),
], ["rows 2 and 3 contain only two colours", "those colours' cats are in rows 2-3: their other cells are empty"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 10: box + colour
# ---------------------------------------------------------------------------
A = [(1, 1), (1, 2), (2, 1)]
B = [(2, 3), (3, 2), (3, 3)]
C = [(1, 3), (2, 2), (3, 1), (0, 3), (0, 4), (4, 1), (4, 0)]
cols10 = {**{c: "purple" for c in A}, **{c: "pink" for c in B}, **{c: "green" for c in C}}
figure("fig10_box_colour.png", [
    board(6, 6, colors=cols10, outlines=[(1, 1, 3, 3, INK)]),
    board(6, 6, colors=cols10, outlines=[(1, 1, 3, 3, INK)], xs=[(1, 3), (2, 2), (3, 1)]),
], ["a 3x3 holds 2 cats; purple and pink are confined to it", "green cannot also have a cat inside: its cells there are empty"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 11: lower bound with touching
# ---------------------------------------------------------------------------
figure("fig11_lower_bound.png", [
    board(8, 8, outlines=[(0, 0, 1, 5, INK), (0, 6, 1, 7, RED)], dots=rect(0, 6, 1, 7)),
    board(8, 8, outlines=[(0, 0, 1, 5, INK), (0, 6, 1, 7, RED)], cats=[(0, 6), (1, 7)],
          xs=sorted(set(attacked((0, 6), 8, 8)) | set(attacked((1, 7), 8, 8)))),
], ["rows 1-2 need two cats; the red 2x2 can hold only one", "so the 2x6 box must contain a cat (plain counting says 0)"])

# ---------------------------------------------------------------------------
# Figure 12: one what-if
# ---------------------------------------------------------------------------
A = [(1, 1), (2, 1)]
B = [(3, 2), (3, 3)]
cols12 = {**{c: "purple" for c in A}, **{c: "green" for c in B}}
t = (1, 3)
figure("fig12_whatif.png", [
    board(5, 5, colors=cols12, cats=[t], rings=[t], xs=attacked(t, 5, 5)),
    board(5, 5, colors=cols12, cats=[t, (2, 1)], rings=[t],
          xs=sorted(set(attacked(t, 5, 5)) | set(attacked((2, 1), 5, 5))), outlines=[(3, 2, 3, 3, RED)]),
    board(5, 5, colors=cols12, xs=[t]),
], ["try a cat here: it takes row 2, so purple must be (3,2)", "that cat touches (4,3); green's last cell (4,4) shares the trial column", "contradiction: the trial cell is empty"], arrows=True)

# ---------------------------------------------------------------------------
# Figure 13: shape gallery
# ---------------------------------------------------------------------------
R = json.load(open(os.path.join(HERE, "results.json")))
names = {
    ((0, 0), (0, 1), (1, 0)): "L-tromino",
    ((0, 0), (0, 1), (0, 2), (1, 0)): "L-tetromino",
    ((0, 0), (0, 1), (0, 2), (1, 1)): "T-tetromino",
    ((0, 0), (0, 1), (1, 1), (1, 2)): "S-tetromino",
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)): "U-pentomino",
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)): "V-pentomino",
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)): "T-pentomino",
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3)): "N-pentomino",
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)): "F-pentomino",
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)): "W-pentomino",
}
panels, caps = [], []
palette_cycle = ["orange", "yellow", "green", "blue", "rose", "purple", "pink", "gold", "dgreen", "brown"]
for i, (shape, nm) in enumerate(names.items()):
    entry = next(s for s in R["shape_rules"] if tuple(map(tuple, s["cells"])) == shape)
    rs = [r for r, _ in shape]
    cs_ = [c for _, c in shape]
    rows = max(rs) - min(rs) + 3
    cols = max(cs_) - min(cs_) + 3
    colors = {(r + 1, c + 1): palette_cycle[i] for (r, c) in shape}
    fe = [(r + 1, c + 1) for (r, c) in entry["forced_empty"]
          if -1 <= r <= max(rs) + 1 and -1 <= c <= max(cs_) + 1]
    panels.append(board(rows, cols, colors=colors, xs=fe, cell=44, gap=5, pad=8))
    caps.append(nm)
figure("fig13_shapes.png", panels[:5], caps[:5], gapx=16)
figure("fig13_shapes_b.png", panels[5:], caps[5:], gapx=16)

# ---------------------------------------------------------------------------
# Figure 14: level 155
# ---------------------------------------------------------------------------
grid = R["level155"]["grid"]
name_of = {0: "purple", 1: "yellow", 2: "pink", 3: "brown", 4: "orange", 5: "green",
           6: "dgreen", 7: "blue", 8: "rose", 9: "gold"}
colors = {(r, c): name_of[int(grid[r][c])] for r in range(10) for c in range(10)}
given = [tuple(x) for x in R["level155"]["cats_placed"]]
forced = [tuple(x) for x in R["level155"]["forced_from_screenshot"]]
allcats = set(given) | set(forced)
xs = [(r, c) for r in range(10) for c in range(10) if (r, c) not in allcats]
# cells the player had not yet crossed out in the screenshot
open_cells = {(5, 1), (5, 5), (5, 7), (6, 1), (6, 5), (6, 7), (7, 1), (7, 4), (7, 5), (7, 7), (8, 5), (8, 7)}
figure("fig14_level155.png", [
    board(10, 10, colors=colors, cats=given, xs=[(r, c) for (r, c) in xs if (r, c) not in open_cells],
          rings=forced, cell=48, gap=5),
    board(10, 10, colors=colors, cats=sorted(allcats), xs=xs, rings=forced, cell=48, gap=5),
], ["level 155 as in the screenshot (rings: cells forced next)", "the unique solution"], arrows=True)
