#!/usr/bin/env python3
"""Render game-style figures for RULES.md into img/.

Colours are sampled from the level-155 screenshot; the cat sprite is cut out of
it (cat.png).  Cells are drawn 3x oversampled and downscaled for smooth edges.
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

PAL = {
    "purple": (137, 121, 218), "yellow": (251, 217, 131), "pink": (248, 155, 229),
    "brown": (168, 109, 74), "orange": (250, 157, 92), "green": (139, 213, 125),
    "dgreen": (42, 140, 83), "blue": (56, 169, 192), "rose": (211, 111, 143),
    "gold": (205, 164, 0), "gray": (226, 219, 214),
}
PAGE = (247, 242, 239)
INK = (140, 92, 92)        # the game's mauve text colour
RED = (225, 70, 70)
S = 3                      # oversampling
CAT = Image.open(os.path.join(HERE, "cat.png")).convert("RGBA")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15 * S)
FONT_B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15 * S)


def board(rows, cols, colors=None, xs=(), cats=(), rings=(), outlines=(), dots=(),
          cell=64, gap=7, pad=12):
    """Draw one board panel (white rounded card) at oversampled scale."""
    colors = colors or {}
    cs, gs, ps = cell * S, gap * S, pad * S
    W = ps * 2 + cols * cs + (cols - 1) * gs
    H = ps * 2 + rows * cs + (rows - 1) * gs
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)

    def xy(r, c):
        return ps + c * (cs + gs), ps + r * (cs + gs)

    for r in range(rows):
        for c in range(cols):
            x, y = xy(r, c)
            col = colors.get((r, c), "gray")
            col = PAL[col] if isinstance(col, str) else col
            d.rounded_rectangle([x, y, x + cs, y + cs], radius=10 * S, fill=col)
    for (r, c) in xs:
        x, y = xy(r, c)
        cx, cy = x + cs / 2, y + cs / 2
        a = cs * 0.30
        w = int(cs * 0.115)
        for (dx1, dy1, dx2, dy2) in ((-a, -a, a, a), (-a, a, a, -a)):
            d.line([cx + dx1, cy + dy1, cx + dx2, cy + dy2], fill="white", width=w)
            for (dx, dy) in ((dx1, dy1), (dx2, dy2)):
                d.ellipse([cx + dx - w / 2, cy + dy - w / 2, cx + dx + w / 2, cy + dy + w / 2], fill="white")
    for (r, c) in dots:
        x, y = xy(r, c)
        cx, cy = x + cs / 2, y + cs / 2
        d.ellipse([cx - cs * 0.11, cy - cs * 0.11, cx + cs * 0.11, cy + cs * 0.11],
                  fill=(255, 255, 255, 230))
    for (r, c) in rings:
        x, y = xy(r, c)
        d.rounded_rectangle([x - 2 * S, y - 2 * S, x + cs + 2 * S, y + cs + 2 * S],
                            radius=12 * S, outline=(255, 205, 60), width=4 * S)
    for (r, c) in cats:
        x, y = xy(r, c)
        sz = int(cs * 0.80)
        cat = CAT.resize((sz, int(sz * CAT.height / CAT.width)), Image.LANCZOS)
        im.alpha_composite(cat, (int(x + (cs - cat.width) / 2), int(y + (cs - cat.height) / 2)))
    for (r0, c0, r1, c1, colour) in outlines:
        x0, y0 = xy(r0, c0)
        x1, y1 = xy(r1, c1)
        d.rounded_rectangle([x0 - gs * 0.5, y0 - gs * 0.5, x1 + cs + gs * 0.5, y1 + cs + gs * 0.5],
                            radius=13 * S, outline=colour, width=3 * S)
    return im


def figure(name, panels, captions=None, arrows=False, gapx=26):
    """Lay panels out side by side on the page background with captions."""
    captions = captions or [""] * len(panels)
    gx = gapx * S
    arrow_w = 40 * S if arrows else 0
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

    def wrap(text, width):
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if dummy.textlength(trial, font=FONT) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines
    wrapped = [wrap(c, p.width + gx * 0.8) if c else [] for c, p in zip(captions, panels)]
    nlines = max((len(w) for w in wrapped), default=0)
    text_h = (10 + 20 * nlines) * S if nlines else 0
    W = gx * 2 + sum(p.width for p in panels) + (len(panels) - 1) * (gx + arrow_w)
    H = gx * 2 + max(p.height for p in panels) + text_h
    im = Image.new("RGBA", (W, H), PAGE + (255,))
    d = ImageDraw.Draw(im)
    x = gx
    for i, p in enumerate(panels):
        y = gx
        # soft shadow + rounded card
        card = Image.new("RGBA", p.size, (0, 0, 0, 0))
        mask = Image.new("L", p.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, p.width - 1, p.height - 1], radius=16 * S, fill=255)
        card.paste(p, (0, 0), mask)
        im.alpha_composite(card, (x, y))
        for k, line in enumerate(wrapped[i]):
            tw = d.textlength(line, font=FONT)
            d.text((x + (p.width - tw) / 2, y + p.height + (8 + 20 * k) * S), line, fill=INK, font=FONT)
        x += p.width
        if arrows and i < len(panels) - 1:
            cy = y + p.height / 2
            ax0, ax1 = x + gx * 0.4, x + gx + arrow_w - gx * 0.4
            d.line([ax0, cy, ax1, cy], fill=INK, width=4 * S)
            d.polygon([(ax1, cy), (ax1 - 12 * S, cy - 9 * S), (ax1 - 12 * S, cy + 9 * S)], fill=INK)
            x += arrow_w
        x += gx
    out = im.resize((W // S, H // S), Image.LANCZOS).convert("RGB")
    out.save(os.path.join(IMG, name))
    print("wrote", name)


def rect(r0, c0, r1, c1):
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def row_cells(r, cols, exclude=()):
    return [(r, c) for c in range(cols) if (r, c) not in exclude]


def col_cells(c, rows, exclude=()):
    return [(r, c) for r in range(rows) if (r, c) not in exclude]


def attacked(cell, rows, cols):
    r, c = cell
    return [(i, j) for i in range(rows) for j in range(cols)
            if (i, j) != cell and (i == r or j == c or (abs(i - r) <= 1 and abs(j - c) <= 1))]


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
