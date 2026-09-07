#!/usr/bin/env python3
"""Single source of truth for the illustrated rules.

Emits RULES.md (for the repo, images by path) and rules.html (self-contained,
images embedded) from the same content.
"""
import base64
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")

NOTATION = """
The board is N x N; cell (r, c) is row r, column c, counted from 0 at the top left.
x[r,c] = 1 if a cat sits on (r, c), else 0.  The colours G_1 ... G_N partition the cells.
A *unit* is a row, a column, or a colour.  The four game rules are

    (R)  for every row r:        sum over c of x[r,c] = 1
    (C)  for every column c:     sum over r of x[r,c] = 1
    (G)  for every colour G_i:   sum over (r,c) in G_i of x[r,c] = 1
    (T)  x[a] + x[b] <= 1 whenever cells a and b touch (max(|dr|, |dc|) = 1)

Cell a *attacks* cell b (written a -> b) if a and b share a row, share a column, or touch.
(R), (C) and (T) together say: x[a] = 1 implies x[b] = 0 for every b attacked by a.
A colour is *confined* to a set of cells S if all of its cells lie inside S.
cap(a, b) is the largest number of cats that can sit inside an a x b rectangle
under (R), (C), (T) alone (one per row, one per column, no touching).

Every rule below is proven twice: once by hand, once by Z3 (`meowdoku_z3.py`,
the key named in each proof is in `results.json`).  Rules whose proof never
mentions colours hold on every board of every size, because adding (G) can only
remove solutions.  Rules that mention colours were checked with the colour map
left fully symbolic on 5 x 5 and 6 x 6 boards, and the counting proofs given do
not depend on N.
"""

RULES = [
    dict(
        id="rules", title="What one cat rules out", img="fig00_rules.png",
        english="""Placing a cat crosses out its whole row, its whole column, the rest of its
colour, and the eight cells around it.  Everything else in this document is a way
of crossing out cells *before* you know where the cat is.""",
        formal="""x[a] = 1  implies  x[b] = 0  for every b with a -> b,
and  x[b] = 0  for every b in the same colour as a.""",
        proof="""(R) and (C) forbid a second cat in the row or column, (G) in the colour,
and (T) on the eight neighbours.  This is the definition of the attack relation,
so there is nothing to check.""",
    ),
    dict(
        id="common", title="Rule 1: common attack", img="fig01_common_attack.png",
        english="""Look at where a colour's cat could still be.  If every one of those cells
would cross out some cell c, then c is crossed out now, without knowing which of
them is right.  The same works for the remaining cells of a row or a column.
Typical shapes: an L crosses out its inner corner, a bar of three crosses out the
cells above and below its middle, a bar of two crosses out the six cells above
and below it.""",
        formal="""Let U be a unit whose cat is known to lie in K (a set of cells), and let c be
a cell not in K.  If  k -> c  for every k in K, then  x[c] = 0.""",
        proof="""By (R), (C) or (G) the unit U has exactly one cat, at some k* in K.  Since
k* -> c, the cat at k* forces x[c] = 0.
Z3: `intersection_rule_L_tromino` (symbolic colours), and `shape_rules_all_equal_intersection_rule`
= true, which says more: for all 21 polyomino shapes up to size 5, a colour of that
shape crosses out *exactly* the cells this rule gives, nothing else.""",
    ),
    dict(
        id="knight", title="Rule 2: the knight's move", img="fig02_knight.png",
        english="""The cats of two neighbouring rows are always at least two columns apart,
like a knight's jump or wider.  So once a row's cat is pinned to a few columns,
the next row loses those columns *and* the columns right beside them.  Neighbouring
columns behave the same way.""",
        formal="""If x[r,c] = 1 and x[r+1,c'] = 1 then |c - c'| >= 2.  Equivalently, a 2 x 2 block
never holds two cats:  cap(2, 2) = 1.""",
        proof="""c = c' is forbidden by (C); |c - c'| = 1 makes the two cells touch diagonally,
forbidden by (T).  Rows two apart may share adjacent columns, so the rule is sharp.
Z3: `consecutive_rows_gap_ge_2` = true on 10 x 10; the control
`rows_two_apart_gap_ge_2` = false.""",
    ),
    dict(
        id="capacity", title="Rule 3: how many cats fit in a rectangle", img="fig03_capacity_small.png",
        english="""A rectangle a cells tall and b cells wide never holds more than min(a, b)
cats, and two sizes are worse than that: a 2 x 2 holds at most one cat, and a 3 x 3
holds at most two.  So if you ever see two colours entirely inside a 2 x 2, three
colours inside a 3 x 3, or three colours inside two rows, you have misread the
board: the puzzle would have no solution.""",
        formal="""cap(a, b) = min(a, b) for all a, b >= 1, except cap(2, 2) = 1 and cap(3, 3) = 2.
If k colours are confined to a rectangle B with cap(B) < k, the puzzle has no solution.""",
        proof="""Upper bound min(a, b): each cat needs its own row and column inside the rectangle.
2 x 2: all four cells touch each other, so (T) allows one cat.
3 x 3: suppose three cats.  They use all three rows.  Let the middle row's cat be in
column j.  The top and bottom cats must be in columns at distance >= 2 from j
(Rule 2), so j is 0 or 2 and both must be in the single column 2 - j, which
violates (C).  Hence at most two.
Achievability for the other sizes is by explicit patterns (Z3 enumerated them:
the number of ways to fill an n x n box to capacity is 1, 4, 10, 2, 14, 90 for
n = 1..6, Hertzsprung's numbers from n = 4 on).
Impossibility: by (G) each of the k confined colours has its cat inside B, giving
k > cap(B) cats there.
Z3: `box_capacity` table (exact search up to 8 x 8); `box_2x2_k2_impossible`,
`box_2x3_k3_impossible`, `box_3x3_k3_impossible` with symbolic colours.""",
    ),
    dict(
        id="three", title="Rule 4: the 3 x 3 block", img="fig04_3x3.png",
        english="""Two cats in a 3 x 3 block use up the block: the third row and column of
the block get their cats from outside.  And if two colours are confined to a 3 x 3,
its centre cell is empty, because a cat in the centre would leave no room for the
second one.""",
        formal="""If two colours are confined to a 3 x 3 block B with centre m, then x[m] = 0.
More generally, if at least two cats lie in B, then x[m] = 0.""",
        proof="""The centre attacks all eight other cells of B (they all touch it).  A cat at m
would therefore leave B with a single cat, contradicting the two cats guaranteed by
(G) for the two confined colours.
Z3: `box_rules` entry 3x3, k=2 (forced cell (1,1)), identical on the at-most-one
model, on 10 x 10 interior and corner, and on 12 x 12.""",
    ),
    dict(
        id="twobythree", title="Rule 5: two colours in a 2 x 3", img="fig05_2x3.png",
        english="""If two colours fit inside a 2 x 3 block, the cats are in the two end
columns of the block, one per row, so the middle column of the block is empty and
so are the cells directly above and below it.  Both rows and both end columns are
then spoken for: everything else in them is empty.""",
        formal="""Let B be a 2 x 3 block with rows r, r+1 and columns c, c+1, c+2, and let two
colours be confined to B.  Then x = 0 on (r,c+1), (r+1,c+1), (r-1,c+1), (r+2,c+1),
on every cell of rows r and r+1 outside B, and on every cell of columns c and c+2
outside B.""",
        proof="""By (G) two cats lie in B; by (R) they are in different rows; by Rule 2 their
columns differ by >= 2, which inside three columns forces columns c and c+2.  So the
middle column is empty, and both rows and both end columns already contain their cat,
which empties the rest of those rows and columns.  The cell (r-1, c+1) touches both
(r, c) and (r, c+2), one of which holds the row-r cat; likewise (r+2, c+1) for row r+1.
Z3: `box_rules` entry 2x3, k=2.""",
    ),
    dict(
        id="threebyfour", title="Rule 6: three colours in a 3 x 4", img="fig06_3x4.png",
        english="""Three colours inside a 3 x 4 block put the middle row's cat at one of
the two ends of the block, so the two inner cells of that row are empty.  Both end
columns of the block are used, and all three rows are used, so everything outside
the block in those rows and columns is empty too.""",
        formal="""Let B be a 3 x 4 block with rows r..r+2 and columns c..c+3, and three colours
confined to B.  Then x[r+1, c+1] = x[r+1, c+2] = 0, rows r..r+2 are empty outside B,
and columns c and c+3 are empty outside B.""",
        proof="""By (G) and (R) each of the three rows has its cat inside B.  Let the middle row's
cat be at column j.  Rows r and r+2 need distinct columns at distance >= 2 from j
(Rule 2).  If j is c+1 or c+2, only one column of B is that far away, so both rows
would need it: contradiction.  Hence j is c or c+3.  With j = c the other two rows
use columns from {c+2, c+3}, distinct, so column c+3 is used; symmetrically for
j = c+3.  So both end columns hold a cat, and all three rows do.
Z3: `box_rules` entry 3x4, k=3 (only patterns (0,3,1), (1,3,0), (2,0,3), (3,0,2)).""",
    ),
    dict(
        id="fourbyfour", title="Rule 7: four colours in a 4 x 4, the knight ring", img="fig07_4x4.png",
        english="""Four colours inside a 4 x 4 block leave exactly two ways to place the
cats, and both are the same ring of knight's moves.  The four corners of the block
and its central 2 x 2 are empty, and all four rows and columns of the block are used,
so nothing outside the block in those rows and columns can hold a cat.""",
        formal="""Let B be a 4 x 4 block with four colours confined to it.  Then the cats in B are
at relative positions {(0,1),(1,3),(2,0),(3,2)} or {(0,2),(1,0),(2,3),(3,1)}.  In
particular x = 0 on the corners and on the central 2 x 2 of B, and rows and columns
of B are empty outside B.""",
        proof="""The four cats occupy all rows and columns of B, so they form a permutation
p of {0,1,2,3} with |p(i) - p(i+1)| >= 2 (Rule 2).  If p(1) were 1, rows 0 and 2 would
both need column 3, the only column at distance >= 2; if p(1) were 2 they would both
need column 0.  So p(1) and likewise p(2) are in {0, 3}, hence rows 0 and 3 use
columns 1 and 2.  p(1) = 0 forces p(0) = 2, p(2) = 3, p(3) = 1; p(1) = 3 forces
p(0) = 1, p(2) = 0, p(3) = 2.  These are the two rings; neither uses a corner or a
central cell.
Z3: `full_patterns_square` 4x4 count = 2; `box_rules` entry 4x4, k=4.""",
    ),
    dict(
        id="hallrows", title="Rule 8: colours locked inside rows", img="fig08_hall_rows.png",
        english="""If some k colours live entirely inside the same k rows, those rows have
no cats to spare: every cell of those rows that belongs to another colour is empty.
The same holds with columns instead of rows, and with a rectangle instead of rows
(Rule 10).""",
        formal="""Let S be a set of k rows and let colours G_1..G_k be confined to the rows in S.
Then x[r,c] = 0 for every (r, c) with r in S and (r, c) not in G_1 ∪ ... ∪ G_k.""",
        proof="""By (G) each G_i has one cat, and it lies in the rows of S, giving k cats there.
By (R) the rows of S hold exactly k cats in total.  So no other colour has a cat in
those rows.
Z3: `hall_rows_confine_k1..k4` = true with symbolic colours on 6 x 6.""",
    ),
    dict(
        id="hallregions", title="Rule 9: rows made of few colours", img="fig09_hall_regions.png",
        english="""Turn Rule 8 around.  If k rows contain cells of only k colours, then those
k colours must place their cats inside those rows, so any cell of those colours
lying outside the rows is empty.  Again the same holds for columns.""",
        formal="""Let S be a set of k rows such that every cell in the rows of S belongs to one of
the colours G_1..G_k.  Then x[r,c] = 0 for every (r, c) in G_1 ∪ ... ∪ G_k with r not in S.""",
        proof="""By (R) the rows of S hold k cats; each belongs to one of G_1..G_k, and by (G)
no colour holds two, so each G_i has its single cat inside S.  Its cells outside S
are therefore empty.
Z3: `hall_regions_cover_rows_k1..k4` = true with symbolic colours on 6 x 6.""",
    ),
    dict(
        id="boxcolour", title="Rule 10: a full rectangle keeps other colours out", img="fig10_box_colour.png",
        english="""If as many colours as a rectangle can hold are confined to it, the
rectangle is full: any cell inside it that belongs to a different colour is empty.
The rectangle sizes that matter in practice are the 2 x 2 (one colour), the 2 x 3
and 3 x 3 (two colours), the 3 x 4 (three) and the 4 x 4 (four).""",
        formal="""Let B be an a x b rectangle and let cap(a, b) colours be confined to B.  Then
x[p] = 0 for every cell p of B that belongs to none of those colours.""",
        proof="""The confined colours put cap(a, b) cats in B by (G).  By the definition of cap,
B holds no more, so a cat of another colour inside B is impossible.
Z3: `box_2x2_k1_other_regions_empty`, `box_2x3_k2_...`, `box_3x3_k2_...`,
`box_3x4_k3_...`, `box_4x4_k4_...` = true with symbolic colours.""",
    ),
    dict(
        id="lower", title="Rule 11: a rectangle that cannot be empty", img="fig11_lower_bound.png",
        english="""Plain counting says a block of a rows and b columns must contain at least
a + b - N cats.  Touching makes this stronger: the cats of those a rows that are not
in the block have to fit in the leftover columns, which is itself a rectangle with a
capacity.  For example the two cats of rows 1-2 cannot both sit in two adjacent
leftover columns, so a 2 x (N-2) block at the edge always contains a cat.""",
        formal="""Let R be a set of rows and C a set of columns, with C' the remaining columns and
R' the remaining rows.  Then
    cats(R x C) >= max( |R| + |C| - N,  |R| - cap(R x C'),  |C| - cap(R' x C),  0 ),
where cap(R x C') is the capacity of the (possibly split) rectangle R x C'.  For a
corner block this is cap(|R|, N - |C|).""",
        proof="""The rows of R hold |R| cats (R).  Those not in R x C lie in R x C', which
holds at most cap(R x C') cats, so at least |R| - cap(R x C') lie in R x C.  The
column version is symmetric, and |R| + |C| - N is the special case that drops the
touching constraint (cap <= |C'| = N - |C|).
Z3: `min_cats_formula_holds` = true: the formula is exact for every corner block of
an 8 x 8 board; the 2 x 6 and 3 x 5 corner blocks need a cat although plain counting
allows none.""",
    ),
    dict(
        id="whatif", title="Rule 12: one what-if is enough (locally)", img="fig12_whatif.png",
        english="""Some cells can only be crossed out by trying them: put an imaginary cat
there, cross out what it attacks, and watch a nearby colour get squeezed to a single
cell that in turn takes the last cell of another colour.  Z3 checked every pair of
small colours inside a 3 x 3 window: whenever the direct rules miss something, a
single what-if with the direct rules finds it, and a single what-if is never wrong.""",
        formal="""Assume x[c] = 1, apply Rules 0-11 to a fixed point, and suppose some unit is
left with no candidate cell.  Then x[c] = 0.
Theorem (checked exhaustively): for every pair of disjoint connected shapes of size
<= 4 inside a 3 x 3 window (237 pairs up to symmetry), with one colour confined to
each shape, the set of cells forced empty equals the set found by the direct rules
plus one level of what-if.  69 of the 237 pairs need the what-if step; none needs two.""",
        proof="""Soundness: every rule only removes cells that hold no cat in any solution
consistent with the assumptions, so a solution with x[c] = 1 would satisfy every
derived fact, including the emptied unit, contradicting (R), (C) or (G).
The completeness claim is a finite computation: for each pair, Z3 computed the exact
forced set on a 9 x 9 board and the what-if propagator was compared against it.
Z3: `pair_search` with `pairs_beyond_one_step_lookahead` = 0 and
`lookahead_unsound_pairs` = 0.""",
    ),
    dict(
        id="shapes", title="Shape cheat sheet", img="fig13_shapes.png", img2="fig13_shapes_b.png",
        english="""The shapes whose crossed-out cells are easy to miss.  Every one is an
instance of Rule 1.  Straight bars of four or more, the 2 x 2 square, and the P, L,
Y, Z and X pentominoes cross out nothing beyond their own row or column.""",
        formal="""For a colour G of a given shape, the forced-empty set is
    { c not in G :  g -> c for every g in G }.""",
        proof="""Rule 1 with U = G and K = G.  Z3 confirmed equality (not just inclusion) for
all 21 free polyominoes up to size 5: `shape_rules_all_equal_intersection_rule`.""",
    ),
    dict(
        id="level", title="Worked example: level 155", img="fig14_level155.png",
        english="""The screenshot position.  Column 5 (counting from 1) has a single open
cell, so the blue cat goes there.  It touches the rose cell below-right, so rose goes
to its other cell.  That takes column 8, so green goes to its remaining cell in row 6,
and brown's column then has one free row left.""",
        formal="""With the six placed cats fixed, the four cells (5,5), (6,1), (7,4), (8,7)
have x = 1 in every solution, and the full puzzle has exactly one solution.""",
        proof="""Column 4 (0-indexed) has one un-crossed cell (7,4): Rule 1 on the column unit
with |K| = 1.  (8,5) touches (7,4), so the rose colour's candidates shrink to (8,7).
Column 7 is then taken, so green's candidates {(5,5), (5,7), (6,7), (7,7)} lose
column 7 and row 7, leaving (5,5).  Brown's candidates {(5,1), (6,1), (7,1)} lose
rows 5 and 7, leaving (6,1).
Z3: `level155.unique` = true; `level155.forced_from_screenshot` = those four cells.""",
    ),
]


# ---------------------------------------------------------------------------
def md():
    out = ["# Meowdoku: the rules, illustrated\n",
           "Each rule comes with a picture in the game's own style, a plain-English "
           "statement, a formal statement, and a proof.  The Z3 checks referenced are "
           "in `results.json` (produced by `meowdoku_z3.py`); pictures are produced by "
           "`make_images.py`; this file by `make_rules.py`.\n",
           "## Notation\n", "```" + NOTATION.replace("*", "").replace("`", "") + "```\n",
           "## Contents\n"]
    for r in RULES:
        out.append(f"* [{r['title']}](#{r['id']})")
    out.append("")
    for r in RULES:
        out.append(f'<a id="{r["id"]}"></a>\n## {r["title"]}\n')
        out.append(f"![{r['title']}](img/{r['img']})\n")
        if r.get("img2"):
            out.append(f"![{r['title']} (continued)](img/{r['img2']})\n")
        out.append("**In plain English.** " + " ".join(r["english"].split()) + "\n")
        out.append("**Formally.**\n\n```\n" + r["formal"].strip() + "\n```\n")
        out.append("**Proof.** " + r["proof"].strip().replace("\n", "\n") + "\n")
    return "\n".join(out) + "\n"


def data_uri(name):
    with open(os.path.join(IMG, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def para(text):
    """Plain text with `code` spans and *em* into HTML paragraphs."""
    import re
    t = html.escape(" ".join(text.split()))
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t


CSS = """
:root{
  --ground:#F7F2EF; --card:#FFFFFF; --ink:#4A3434; --mauve:#8C5C5C; --line:#E9DCD6;
  --code:#F3EAE6; --purple:#8979DA; --green:#8BD57D; --rose:#D36F8F; --yellow:#FBD983;
  --shadow:0 2px 10px rgba(120,80,80,.08);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#241D1F; --card:#312729; --ink:#F3E9E5; --mauve:#D9A9A9; --line:#4A3B3E;
    --code:#3C3033; --shadow:0 2px 12px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --ground:#241D1F; --card:#312729; --ink:#F3E9E5; --mauve:#D9A9A9; --line:#4A3B3E;
  --code:#3C3033; --shadow:0 2px 12px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"Nunito","Segoe UI",system-ui,sans-serif;font-size:17px;line-height:1.55}
main{max-width:76ch;margin:0 auto;padding:40px 20px 80px}
h1,h2,h3{font-family:"Fredoka","Nunito",system-ui,sans-serif;font-weight:600;
  text-wrap:balance;line-height:1.15;margin:0}
h1{font-size:2.6rem;letter-spacing:-.01em}
h2{font-size:1.55rem}
.eyebrow{font-family:"Fredoka",sans-serif;font-weight:500;text-transform:uppercase;
  letter-spacing:.12em;font-size:.78rem;color:var(--mauve)}
header{display:flex;flex-direction:column;gap:14px;margin-bottom:34px}
header p{margin:0;max-width:62ch}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 0}
.pills a{font-family:"Fredoka",sans-serif;font-weight:500;font-size:.85rem;text-decoration:none;
  color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:999px;
  padding:5px 12px;box-shadow:var(--shadow)}
.pills a:hover,.pills a:focus-visible{border-color:var(--purple);outline:none}
.notation{background:var(--card);border-radius:18px;box-shadow:var(--shadow);padding:22px 24px;margin:0 0 34px}
.notation h2{margin-bottom:10px}
pre,code{font-family:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.86em}
pre{white-space:pre-wrap;margin:0;line-height:1.5}
code{background:var(--code);border-radius:6px;padding:.05em .35em}
pre code{background:none;padding:0}
article{background:var(--card);border-radius:22px;box-shadow:var(--shadow);margin:0 0 30px;overflow:hidden}
article figure{margin:0;background:var(--ground);border-bottom:1px solid var(--line)}
article img{display:block;width:100%;height:auto}
.body{padding:22px 26px 26px;display:grid;grid-template-columns:8.5rem 1fr;column-gap:22px;row-gap:16px}
.body h2{grid-column:1/-1;margin-bottom:2px}
.label{font-family:"Fredoka",sans-serif;font-weight:500;font-size:.8rem;text-transform:uppercase;
  letter-spacing:.1em;color:var(--mauve);padding-top:.35em}
.label.formal{color:var(--purple)}
.label.proof{color:var(--rose)}
.body p{margin:0}
.formalbox{background:var(--code);border-radius:12px;padding:12px 14px;overflow-x:auto}
@media (max-width:640px){.body{grid-template-columns:1fr;row-gap:6px}.label{padding-top:8px}}
footer{color:var(--mauve);font-size:.9rem;margin-top:30px}
@media (prefers-reduced-motion:no-preference){.pills a{transition:border-color .15s}}
"""


def html_page():
    parts = ['<title>Meowdoku Rulebook</title>',
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Nunito:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400&display=swap">',
             '<style>' + CSS + '</style>', '<main>', '<header>',
             '<div class="eyebrow">Meowdoku &middot; proven with Z3</div>',
             '<h1>The rules behind the rules</h1>',
             '<p>Meowdoku asks for one cat per row, per column and per colour, with no two cats '
             'touching. These are the deductions that follow from that on <em>every</em> board, '
             'each with a picture, a plain-English version, a formal statement and a proof. '
             'Row and column numbers in the formal parts count from 0 at the top left.</p>',
             '<nav class="pills">']
    for r in RULES:
        t = r["title"]
        label = (t.split(":")[0].replace("Rule ", "") + " \u00b7 " + t.split(":", 1)[1].strip()) if ":" in t else t
        parts.append(f'<a href="#{r["id"]}">{html.escape(label)}</a>')
    parts.append('</nav></header>')
    import re
    note = html.escape(NOTATION.strip())
    note = re.sub(r"`([^`]+)`", r"<code>\1</code>", note)
    note = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", note)
    parts.append('<section class="notation"><h2>Notation</h2><pre>' + note + '</pre></section>')
    for r in RULES:
        parts.append(f'<article id="{r["id"]}"><figure><img src="{data_uri(r["img"])}" alt="{html.escape(r["title"])}">')
        if r.get("img2"):
            parts.append(f'<img src="{data_uri(r["img2"])}" alt="{html.escape(r["title"])} (continued)">')
        parts.append('</figure><div class="body">')
        parts.append(f'<h2>{html.escape(r["title"])}</h2>')
        parts.append(f'<div class="label">In plain English</div><p>{para(r["english"])}</p>')
        parts.append(f'<div class="label formal">Formally</div><div class="formalbox"><pre>{html.escape(r["formal"].strip())}</pre></div>')
        parts.append(f'<div class="label proof">Proof</div><p>{para(r["proof"])}</p>')
        parts.append('</div></article>')
    parts.append('<footer>Source, solver script and raw Z3 results: the <code>meowdoku/</code> folder of the DCAS repository.</footer>')
    parts.append('</main>')
    return "\n".join(parts)


if __name__ == "__main__":
    with open(os.path.join(HERE, "RULES.md"), "w") as f:
        f.write(md())
    with open(os.path.join(HERE, "rules.html"), "w") as f:
        f.write(html_page())
    print("wrote RULES.md and rules.html")
