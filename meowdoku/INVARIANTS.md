# Meowdoku invariants, found and proven with Z3

Meowdoku is the "Queens" / Star-Battle puzzle with cats: an N x N grid is
partitioned into N coloured regions and you must place N cats so that

1. every row has exactly one cat,
2. every column has exactly one cat,
3. every colour has exactly one cat,
4. no two cats touch, not even diagonally.

This document lists rules that hold on **every** board.  Two kinds of proof
were used (`meowdoku_z3.py`, results in `results.json`, full pictures in
`CATALOGUE.md`):

* **Region-free proofs.**  Only rows, columns and touching are modelled.  Any
  cell that Z3 proves empty here is empty on every board, because the colour
  constraint can only remove solutions.  Box rules were additionally proven on
  an *at-most-one* model, which makes them independent of board size and of
  where the box sits.
* **Symbolic-region proofs.**  Every cell's colour is a free Z3 integer, so a
  proof covers all region layouts of that size (done for N = 5 and 6; the
  underlying counting arguments do not depend on N).

Coordinates are (row, column).  A region is *confined* to a set of cells if all
of its cells lie inside that set.  "Attack" means: same row, same column, or
touching.

---

## 1. The master rule: common attack

> If every remaining candidate cell of a unit (a colour, a row, or a column)
> attacks cell c, and c is not one of those candidates, then c is empty.

Everything in section 4 is an instance of this.  Z3 confirmed for all 21 free
polyominoes up to size 5 that a lone region eliminates *exactly* the cells
given by this rule and nothing more, so there is no hidden extra rule for a
single region.

Two consequences you use constantly:

* A region confined to one row (or column) empties the rest of that row
  (column).
* A region that is a 1x2 or 1x3 bar empties the cells directly above and below
  its centre (`x` = empty, `#` = region):

```
  . x x .        . . x . .
  x # # x        x # # # x
  . x x .        . . x . .
```

---

## 2. How many cats fit in a rectangle

`cap(a, b)` = the maximum number of cats in any a x b rectangle (region-free,
exact, universal):

| a \ b | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |
| 3 | 1 | 2 | 2 | 3 | 3 | 3 | 3 | 3 |
| 4 | 1 | 2 | 3 | 4 | 4 | 4 | 4 | 4 |
| 5 | 1 | 2 | 3 | 4 | 5 | 5 | 5 | 5 |

So `cap(a, b) = min(a, b)` **except** for the 2x2 (1 cat) and the 3x3
(2 cats).  Stated as playing rules:

* **Knight's-move rule.** Cats in consecutive rows are at least 2 columns
  apart (same for consecutive columns).  Proven for N = 10; it fails for rows
  two apart, as expected.
* **3x3 rule.** Any 3x3 block holds at most 2 cats.  Equivalently, the cats
  of three consecutive rows can never sit inside three consecutive columns.
* **Four in a row.** If four consecutive rows have their cats inside four
  consecutive columns there are only 2 patterns, both "knight rings":
  the four corners and the central 2x2 of that 4x4 block are empty.
  (Counts of full patterns for n x n: 1, 4, 10, 2, 14, 90 for n = 1..6; from
  n = 4 on these are Hertzsprung's numbers, OEIS A002464.)

**Impossible configurations** (a valid puzzle never contains them; proven with
symbolic regions): two regions confined to one 2x2, three regions confined to
one 3x3, three regions confined to two rows or to a 2x3.  If you think you see
one, you have misread a colour.

---

## 3. Counting rules that involve colours (Hall-type)

All proven for every region layout with N = 5 and N = 6, k = 1 .. N-2.

* **Regions inside rows.** If k regions are confined to k rows, then every
  other cell of those rows is empty.  (Same for columns.)
* **Rows inside regions.** If k rows contain cells of only k regions, then
  those regions have no cat outside those rows: their cells elsewhere are
  empty.  (Same for columns.)
* **Box version.** If `cap(a, b)` regions are confined to an a x b box, then
  every cell of the box that belongs to any other colour is empty.  Proven
  for 2x2 (1 region), 2x3 (2), 3x3 (2), 3x4 (3), 4x4 (4).
* **Lower bound.** In an N x N board, the number of cats in a set of rows R
  crossed with a set of columns C is at least
  `max(|R| + |C| - N,  |R| - cap(|R|, N - |C|),  |C| - cap(N - |R|, |C|), 0)`.
  Plain counting gives only the first term; the other two come from touching
  and are sometimes strictly better (a 2x6 corner box of an 8x8 board must
  contain a cat because the two cats of its rows cannot both fit in the two
  remaining columns).  The formula is exact for every corner box at N = 8.

---

## 4. Regions confined to a box: what is forced

Region-free and universal (checked identical on at-most-one N = 12, exact
N = 10 interior, exact N = 10 corner, exact N = 12).  `#` box cell, `x` forced
empty, `.` unknown; a 1-cell margin is shown.

**2 regions in a 2x3** (rows and columns 1, 3 of the box fill up):

```
. x x x .
x # x # x
x # x # x
. x x x .
```
The middle column of the box is empty, and so are the cells above and below it.

**2 regions in a 3x3** (the only one that leaves the surroundings alone):

```
. . . . .
. # # # .
. # x # .
. # # # .
. . . . .
```
The centre is empty.

**3 regions in a 3x4** (the three rows and the two end columns fill up):

```
. x . . x .
x # # # # x
x # x x # x
x # # # # x
. x . . x .
```
The middle row's cat is at one of the two ends.

**4 regions in a 4x4** (the knight ring):

```
. x x x x .
x x # # x x
x # x x # x
x # x x # x
x x # # x x
. x x x x .
```
Corners and centre 2x2 empty; the cat pattern is one of two knight rings.

Nothing *inside* the box is forced for 2x4, 2x5, 3x5, 4x5 or 5x5 at capacity:
those only fill their rows (and columns, when square).  Confining fewer
regions than the capacity forces nothing at all.

---

## 5. Single-region shape catalogue (highlights)

All 21 free polyominoes up to size 5 are in `CATALOGUE.md`.  The ones with an
elimination that is easy to miss:

```
L-tromino      L-tetromino      T-tetromino    S-tetromino
. x . .        . . . . .        . . x . .      . . . . .
x # # .        x # # # .        . # # # .      . # # x .
. # x .        . # x . .        . . # . .      . x # # .
. . . .        . . . . .        . . . . .      . . . . .

U-pentomino    V-pentomino    T-pentomino    N-pentomino
. . . . .      . . . . .      . . x . .      . . . . . .
. # # # .      . # # # .      . # # # .      . # # # x .
. # x # .      . # x . .      . . # . .      . . x # # .
. . . . .      . # . . .      . . # . .      . . . . . .
               . . . . .      . . . . .

F-pentomino    W-pentomino
. . . . .      . . . . .
. # # . .      . # # x .
. x # # .      . . # # .
. . # . .      . . . # .
. . . . .      . . . . .
```

The 2x2 square, the P-, L-, Y-, Z- and X-pentominoes and the straight bars of
length 4 and 5 eliminate nothing beyond their own row or column.

---

## 6. Two-region patterns and the "one what-if" theorem

For every pair of disjoint connected shapes of size <= 4 inside a 3x3 window
(237 pairs up to symmetry), Z3 computed the exact set of forced-empty cells
when one region is confined to each shape, and compared it with what the
direct rules above give.

* 38 pairs are impossible (all caught by the direct rules).
* 69 pairs have eliminations the direct rules miss.
* **In all 69, the missing cells follow from one what-if step**: assume a cat
  at c, apply the direct rules once, get a contradiction.  No pair needed
  two nested assumptions, and the one-step what-if never over-eliminated.

Typical example (A = vertical domino, B = horizontal domino):

```
. x . . .
x A x x .
x A x x .
x x B B x
. x x x .
```
The top-right `x` at (0,2) needs the what-if: a cat there takes row 0, so
A's cat is (1,0); that touches (2,1), so B's cat is (2,2), which is in the
same column as (0,2).  The same mechanism (the trial cat squeezes A to one
cell, which squeezes B into the trial cell's row or column, or into a
touching cell) explains all 69 patterns, which are drawn in `CATALOGUE.md`.

---

## 7. Worked example: level 155 from the screenshot

Region map recovered from the pixels (digits = colours, `*` = placed cat):

```
0* 1  1  1  1  1  1  1  1  1
0  1  1  1  1  1  1  1  1  2*
3  3  3  3  3  3  1* 1  1  2
3  3  4  3  4  5  5  1  6* 6
3  3  4  4* 4  4  5  1  5  5
3  3  4  3  4  5  5  5  5  5
3  3  4  3  4  7  7  5  8  8
3  3  3  3  7  7  8  5  8  8
3  3  9  9  7  8  8  8  8  8
3  3  9* 7  7  7  7  7  8  8
```
(0 purple, 1 yellow, 2 pink, 3 brown, 4 orange, 5 green, 6 dark green,
7 blue, 8 rose, 9 gold.)

Z3 confirms the puzzle has a unique solution and that from the screenshot's
position the remaining four cats are forced:

1. Column 4 has a single un-crossed cell, (7,4), so blue's cat is there.
2. (8,5) touches (7,4), so rose (only (8,5) and (8,7) left) goes to (8,7).
3. Row 7 and column 7 are now taken, so green (cells (5,5), (5,7), (6,7), (7,7))
   goes to (5,5).
4. Brown's last candidates are (5,1), (6,1), (7,1); rows 5 and 7 are taken,
   so brown goes to (6,1).

Solution: (0,0) (1,9) (2,6) (3,8) (4,3) (5,5) (6,1) (7,4) (8,7) (9,2).

---

## Files

* `meowdoku_z3.py`: all experiments (about 20 s with `z3-solver`).
* `results.json`: raw output.
* `make_catalogue.py` -> `CATALOGUE.md`: every box rule, every polyomino, every
  two-region pattern, with pictures.
