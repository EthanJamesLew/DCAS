# Open questions: Meowdoku on rectangles and in three dimensions

The numbers below come from `variants.py` (`variants.json`) and a few one-off
Z3 runs (`variants_line*.log`).  "Region-free" means only the line and
touching rules are used, no colours.  Everything marked *computed* was
checked by machine; everything marked *question* is open as far as this
search goes.

## 0. What generalises and what does not

Meowdoku's 2D rules are: one cat per row, per column, per colour; no two cats
touch.  The Lean proofs in `lean/` use three ingredients, and each one has a
choice to make in a new geometry:

1. **A family of lines, each holding exactly one cat** (rows, columns).  In
   3D a "line" can mean a slice (n cats in the cube) or an axis-parallel
   line (n² cats).  On an m × n rectangle with m < n the columns cannot all
   hold a cat, and the natural rule is *at most one* per column.
2. **A touching relation.**  In 3D the 26-neighbourhood (the 3 × 3 × 3
   block around a cat) is the analogue of the 8-neighbourhood.
3. **A partition into colours, one cat each.**  The number of colours must
   equal the number of cats.

The abstract counting lemma (`Solution.hall1/2/3` in `Rules.lean`) only needs
"separating maps": two cats with the same row, column or colour are the same
cat.  Any geometry whose lines and colours are separating inherits every
counting rule for free.

## 1. Rectangles: m rows, n columns, m cats (m ≤ n)

Rules: one cat per row, at most one per column, one per colour (m colours),
no touching.  A region-free placement is an injection σ : [m] → [n] with
|σ(i) − σ(i+1)| ≥ 2 ("knight injections", K(m, n)).

*Computed.*

| m \ n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| 2 | | 0 | 2 | 6 | 12 | 20 | 30 | 42 |
| 3 | | | 0 | 4 | 18 | 48 | 100 | 180 |
| 4 | | | | 2 | 20 | 90 | 272 | 650 |
| 5 | | | | | 14 | 124 | 582 | 1928 |
| 6 | | | | | | 90 | 860 | 4386 |
| 7 | | | | | | | 646 | 6748 |

The diagonal is Hertzsprung's sequence (OEIS A002464).  The row m = 2 is
(n − 1)(n − 2) exactly (checked for n ≤ 8: the two cats avoid each other's
column and the two neighbouring columns).  The narrowest board with any
placement has width m, except width 3 for m = 2 and width 4 for m = 3: the
2 × 2 and 3 × 3 capacity anomalies, and nothing else.

**Questions.**

* **Q1.1 (a formula).**  Find a recurrence or closed form for K(m, n).  The
  row m = 2 is quadratic and m = 3 (0, 4, 18, 48, 100, 180) looks like a
  cubic in n; is K(m, ·) always a polynomial of degree m for n ≥ m + 1, and
  what is its leading behaviour?  Hertzsprung's recurrence for K(n, n) is
  the m = n slice.
* **Q1.2 (rectangular capacity).**  On rectangles, is cap(a, b) = min(a, b)
  except for the 2 × 2 and 3 × 3 still the whole story, and can any colour
  layout force a stronger local rule?  On square boards every single-colour
  rule turned out to be the common-attack rule; the proof does not use the
  board being square, so the conjecture is *no*.
* **Q1.3 (the free columns).**  On an m × n board, n − m columns hold no
  cat.  Rule 9 (lines made of few colours) dualises: a set of k columns whose
  remaining cells belong to fewer than k colours contains an empty column.
  Is there a *complete* set of column-emptiness rules, the way one what-if
  was complete for two colours in a 3 × 3 window?
* **Q1.4 (hardest rectangles).**  Under the rule-based difficulty meter, are
  wide boards harder (more what-ifs) or easier (more room)?  The generator
  in `hardest.py` needs only the "at most one per column" change.

## 2. Cubes, "one cat per slice" (n cats in n × n × n)

Rules: one cat per x-slice, per y-slice, per z-slice; one per colour (n
colours); no two cats in touching cells (26-neighbourhood).  A placement is
a pair of permutations (σ, τ) with cats (i, σ(i), τ(i)); consecutive cats must
not be within 1 in *both* σ and τ.

*Computed.*  Number of region-free placements: 1, 0, 8, 236, 7188, 288940
for n = 1..6.  Box capacities cap(a, b, c) for a ≤ b ≤ c ≤ 4:

| box | 1×1×1 | 2×2×2 | 2×2×3 | 2×3×3 | 3×3×3 | 3×3×4 | 3×4×4 | 4×4×4 |
|---|---|---|---|---|---|---|---|---|
| cats | 1 | 1 | 2 | 2 | **3** | 3 | 3 | 4 |

So cap(a, b, c) = min(a, b, c) except for the 2 × 2 × 2 (one cat).  **The
3 × 3 anomaly disappears in 3D**: (0,0,1), (1,2,0), (2,1,2) are three
pairwise non-touching cats in a 3 × 3 × 3 in distinct slices of every
direction.  A knight's move is needed in only one of the two transverse
coordinates, which is what the 2D proof of the 3 × 3 rule lacks.

**Questions.**

* **Q2.1 (which rules survive).**  Common attack, the 2 × 2 × 2 rule and the
  counting rules survive verbatim (they only use separating maps and
  touching).  The 3 × 3 rule, the 2 × 3 and 3 × 4 patterns and the 4 × 4
  knight ring do not.  What are the forced patterns in a 2 × 2 × 3 with two
  cats, and in a 2 × 3 × 3?  (Conjecture: two cats in a 2 × 2 × 3 sit in the
  two end layers of the long axis, mirroring Rule 5.)
* **Q2.2 (counting).**  1, 0, 8, 236, 7188, 288940 is not in the OEIS at the
  time of writing.  A pair of consecutive cats is bad only when it is bad in
  both projections, so an inclusion-exclusion over "bad" adjacent pairs of
  the two permutations should give a formula in terms of the 2D statistics
  (number of permutations with a prescribed set of adjacent-difference-1
  positions).  Find it.
* **Q2.3 (one what-if).**  Is the two-colour completeness theorem (every
  deduction in a 3 × 3 window needs at most one what-if) still true in a
  3 × 3 × 3 window?  The search in `meowdoku_z3.py` transfers directly.
* **Q2.4 (uniqueness and difficulty).**  With n cats in n³ cells the boards
  are sparse.  Do unique-solution colourings exist for every n ≥ 3 (n = 2 has
  no placement at all), and does the share of random unique boards that need
  a what-if rise or fall with the dimension?

## 3. Cubes, "one cat per line" (n² cats in n × n × n)

Rules: exactly one cat on every axis-parallel line (n² lines in each of the
three directions); no two cats touching.  Writing L(i, j) for the height of
the cat above cell (i, j), the line rules say exactly that **L is a Latin
square**, and the touching rule says that **king-adjacent entries of L
differ by at least 2** (orthogonal and diagonal neighbours alike).

*Computed.*

* No such Latin square exists for n = 2, 3, 4, 5, 6, 7, 8 (Z3, each in
  under a second).  For n ≤ 4 the reason is visible: each row must be a
  knight permutation and there are only 0, 0, 2 of those.
* For n = 9 one exists, and it is cyclic: L(i, j) = 5 + 4j − 2i (mod 9).
* The cyclic construction L(i, j) = a·j + b·i (mod n) works exactly when a
  and b are units mod n and each of a, b, a + b, a − b lies in
  [2, n − 2] mod n.  That happens for n = 9, 11 and every n ≥ 13 (checked to
  40), and fails for n = 2..8, 10 and 12.
* Whether n = 10 and n = 12 admit a *non*-cyclic square is not settled by
  the runs so far.

**Questions.**

* **Q3.1 (the gap).**  Do king-distance-2 Latin squares of order 10 and 12
  exist?  These are the only orders below 40 that the cyclic construction
  misses (their units mod n are too few to keep a, b, a + b and a − b all
  away from 0 and ±1).  Either a structural obstruction for these two orders
  or a sporadic, non-cyclic square would settle the existence question for
  every n.
* **Q3.2 (minimal order).**  Prove without a computer that no order n ≤ 8
  works.  The n ≤ 4 argument is by counting knight permutations; for
  5 ≤ n ≤ 8 a cleaner obstruction is wanted.  Note that the 2D knight
  permutations of order 5 number 14, so rows are not the bottleneck; the
  diagonal condition is.
* **Q3.3 (rules for the line variant).**  Region-free box capacities are
  1, 1, 2, 4, 5 for 1×1×1, 2×2×2, 2×2×3, 2×3×3, 3×3×3.  A 3 × 3 × 3 holds
  five cats although it contains nine lines per direction that each want a
  cat: the line variant is dense, so capacities are *lower* bounds on what a
  region must contain as well as upper bounds.  Formulate the analogue of
  Rule 11 (a rectangle that cannot be empty) for this variant.
* **Q3.4 (relaxed touching).**  If only orthogonal touching is forbidden
  (6-neighbourhood in the cube), the condition becomes |ΔL| ≥ 2 across
  orthogonal neighbours only; the cyclic construction then needs just a and
  b in [2, n − 2].  Which small orders become solvable, and is n = 5 the
  smallest?

## 4. Both at once: rectangles in 3D

* **Q4.1.**  An a × b × c box with a ≤ b ≤ c and a cats (one per a-slice, at
  most one per b- and c-slice): is the region-free count determined by the
  2D knight-injection numbers K(a, b), K(a, c) together with the finer
  statistics of Q2.2?
* **Q4.2.**  Is there a geometry (a torus, a hexagonal grid, a cube) in which
  the capacity anomalies vanish entirely, so that cap = min of the
  dimensions for every box?  The cube removes the 3 × 3 anomaly but keeps
  the 2 × 2 × 2 one; on a torus the knight's move wraps and the 2 × 2
  anomaly should survive.
