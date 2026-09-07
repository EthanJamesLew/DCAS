#!/usr/bin/env python3
"""
Meowdoku invariant search with Z3.

Meowdoku (the cat game in the screenshot) is the "Queens" / Star-Battle-1 puzzle:
an N x N grid partitioned into N coloured regions, place N cats such that

  * exactly one cat per row,
  * exactly one cat per column,
  * exactly one cat per region (colour),
  * no two cats touch (not even diagonally).

Everything below that is proven WITHOUT reference to the regions (only rows,
columns and touching) holds on *every* board, because the region constraint
only removes solutions.  Rules that mention regions are proven with the region
map left completely symbolic (every cell's colour is a free Z3 variable), so
they also hold for every board of that size.

Run:   python3 meowdoku_z3.py            (writes results.json next to this file)
"""
import itertools
import json
import os
import sys
import time

from z3 import (And, Bool, If, Int, Not, Or, PbEq, PbGe, PbLe, Solver, Sum,
                sat, unsat)

HERE = os.path.dirname(os.path.abspath(__file__))
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Core model
# --------------------------------------------------------------------------
def touching(a, b):
    return a != b and abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1


def attacks(a, b):
    """True if a cat at a forbids a cat at b (same row/col or touching)."""
    return a != b and (a[0] == b[0] or a[1] == b[1] or touching(a, b))


def make_board(N, exact=True):
    """Region-free model: one cat per row/col (exactly, or at most), no touching."""
    X = [[Bool(f"x_{r}_{c}") for c in range(N)] for r in range(N)]
    s = Solver()
    Pb = PbEq if exact else PbLe
    for r in range(N):
        s.add(Pb([(X[r][c], 1) for c in range(N)], 1))
    for c in range(N):
        s.add(Pb([(X[r][c], 1) for r in range(N)], 1))
    for r in range(N - 1):
        for c in range(N):
            for dc in (-1, 1):
                if 0 <= c + dc < N:
                    s.add(Not(And(X[r][c], X[r + 1][c + dc])))
    return s, X


def cells_in_box(r0, c0, a, b):
    return [(r0 + i, c0 + j) for i in range(a) for j in range(b)]


def forced_empty(s, X, N, extra, cells=None):
    """Cells that cannot hold a cat once `extra` constraints are assumed."""
    cells = cells if cells is not None else [(r, c) for r in range(N) for c in range(N)]
    out = []
    s.push()
    for e in extra:
        s.add(e)
    if s.check() == unsat:
        s.pop()
        return None  # hypothesis itself is contradictory
    for (r, c) in cells:
        s.push()
        s.add(X[r][c])
        if s.check() == unsat:
            out.append((r, c))
        s.pop()
    s.pop()
    return out


# --------------------------------------------------------------------------
# Experiment 1: how many cats fit in an a x b box?  (rows/cols distinct, no touch)
# --------------------------------------------------------------------------
def box_capacity(a, b):
    s, X = make_board(max(a, b), exact=False)  # a square super-board, at-most-one
    cells = cells_in_box(0, 0, a, b)
    # cats only inside the box
    for r in range(max(a, b)):
        for c in range(max(a, b)):
            if (r, c) not in cells:
                s.add(Not(X[r][c]))
    k = 0
    while True:
        s.push()
        s.add(PbGe([(X[r][c], 1) for (r, c) in cells], k + 1))
        res = s.check()
        s.pop()
        if res == unsat:
            return k
        k += 1


def full_patterns(a, b, k):
    """Enumerate all placements of k cats inside an a x b box (no other cats)."""
    s, X = make_board(max(a, b), exact=False)
    cells = cells_in_box(0, 0, a, b)
    for r in range(max(a, b)):
        for c in range(max(a, b)):
            if (r, c) not in cells:
                s.add(Not(X[r][c]))
    s.add(PbEq([(X[r][c], 1) for (r, c) in cells], k))
    pats = []
    while s.check() == sat and len(pats) < 5000:
        m = s.model()
        p = tuple(sorted((r, c) for (r, c) in cells if m.eval(X[r][c], True)))
        pats.append(p)
        s.add(Or([Not(X[r][c]) for (r, c) in p]))
    return pats


# --------------------------------------------------------------------------
# Experiment 2: lower bound on cats in a box in the corner of an N x N board.
# Plain counting gives  cats(R x C) >= |R| + |C| - N.  Touching sharpens it:
# the cats of the a rows that are NOT in the box must fit in the a x (N-b)
# complementary band, so  cats >= a - cap(a, N-b)  (and symmetrically).
# --------------------------------------------------------------------------
def min_cats_in_box(N, a, b):
    s, X = make_board(N)
    cells = cells_in_box(0, 0, a, b)
    k = 0
    while True:
        s.push()
        s.add(PbLe([(X[r][c], 1) for (r, c) in cells], k))
        res = s.check()
        s.pop()
        if res == sat:
            return k
        k += 1


def lower_bound_formula(N, a, b, cap):
    def C(x, y):
        return 0 if x == 0 or y == 0 else cap[(min(x, y), max(x, y))]
    return max(0, a + b - N, a - C(a, N - b), b - C(N - a, b))


# --------------------------------------------------------------------------
# Experiment 3: k regions confined to an a x b box  =>  forced-empty cells
# (region-free: "at least k cats in the box" is implied by the confinement)
# --------------------------------------------------------------------------
def box_rule(N, r0, c0, a, b, k, s=None, X=None):
    if s is None:
        s, X = make_board(N)
    cells = cells_in_box(r0, c0, a, b)
    fe = forced_empty(s, X, N, [PbGe([(X[r][c], 1) for (r, c) in cells], k)])
    if fe is None:
        return None
    return sorted((r - r0, c - c0) for (r, c) in fe)


def render_box_rule(a, b, k, rel, N, r0, c0):
    """ASCII picture of the box with a 1-cell margin; row/col-wide effects as text."""
    fe = set(rel)
    lines = []
    for i in range(-1, a + 1):
        row = []
        for j in range(-1, b + 1):
            inside = 0 <= i < a and 0 <= j < b
            if (i, j) in fe:
                row.append("x")
            elif inside:
                row.append("#")
            else:
                row.append(".")
        lines.append(" ".join(row))
    notes = []
    # rows of the box that are entirely empty outside the box
    for i in range(a):
        outside = [(i, j) for j in range(-c0, N - c0) if not 0 <= j < b]
        if outside and all(x in fe for x in outside):
            notes.append(f"whole row {i} of the box is empty outside the box")
    for j in range(b):
        outside = [(i, j) for i in range(-r0, N - r0) if not 0 <= i < a]
        if outside and all(x in fe for x in outside):
            notes.append(f"whole column {j} of the box is empty outside the box")
    far = [x for x in fe if not (-1 <= x[0] <= a and -1 <= x[1] <= b)]
    far_unexplained = [x for x in far
                       if not any(n.startswith(f"whole row {x[0]}") for n in notes)
                       and not any(n.startswith(f"whole column {x[1]}") for n in notes)]
    return "\n".join(lines), notes, far_unexplained


# --------------------------------------------------------------------------
# Experiment 4: single region of a given shape  =>  forced-empty cells
# --------------------------------------------------------------------------
def polyominoes(max_size):
    """Free polyominoes up to max_size, as canonical frozensets of (r,c)."""
    def normalize(cells):
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        return tuple(sorted((r - mr, c - mc) for r, c in cells))

    def transforms(cells):
        out = []
        for t in range(8):
            pts = []
            for r, c in cells:
                if t & 1:
                    r, c = c, r
                if t & 2:
                    r = -r
                if t & 4:
                    c = -c
                pts.append((r, c))
            out.append(normalize(pts))
        return out

    def canon(cells):
        return min(transforms(cells))

    levels = {1: {((0, 0),)}}
    for n in range(2, max_size + 1):
        nxt = set()
        for p in levels[n - 1]:
            for (r, c) in p:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (r + dr, c + dc)
                    if q not in p:
                        nxt.add(canon(list(p) + [q]))
        levels[n] = nxt
    return levels


def shape_rule(N, r0, c0, shape, s=None, X=None):
    if s is None:
        s, X = make_board(N)
    cells = [(r0 + r, c0 + c) for (r, c) in shape]
    fe = forced_empty(s, X, N, [PbEq([(X[r][c], 1) for (r, c) in cells], 1)])
    return sorted((r - r0, c - c0) for (r, c) in fe if (r, c) not in cells)


def intersection_rule(shape):
    """Cells attacked by every cell of the shape (the 'obvious' rule)."""
    cells = list(shape)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    out = set()
    for r in range(min(rs) - 2, max(rs) + 3):
        for c in range(min(cs) - 2, max(cs) + 3):
            if (r, c) not in cells and all(attacks(x, (r, c)) for x in cells):
                out.add((r, c))
    return out


def render_shape(shape, forced, margin=1):
    cells = set(shape)
    fe = set(forced)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    lines = []
    for r in range(min(rs) - margin, max(rs) + margin + 1):
        row = []
        for c in range(min(cs) - margin, max(cs) + margin + 1):
            if (r, c) in cells:
                row.append("#")
            elif (r, c) in fe:
                row.append("x")
            else:
                row.append(".")
        lines.append(" ".join(row))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Experiment 5: rules that mention regions, with the region map fully symbolic
# --------------------------------------------------------------------------
def make_symbolic_board(N):
    s, X = make_board(N)
    R = [[Int(f"reg_{r}_{c}") for c in range(N)] for r in range(N)]
    for r in range(N):
        for c in range(N):
            s.add(R[r][c] >= 0, R[r][c] < N)
    for g in range(N):
        s.add(Sum([If(And(X[r][c], R[r][c] == g), 1, 0)
                   for r in range(N) for c in range(N)]) == 1)
    return s, X, R


def prove(s, negated_claim):
    """Return True if claim holds (its negation is unsat)."""
    s.push()
    for e in negated_claim:
        s.add(e)
    res = s.check()
    s.pop()
    return res == unsat


def symbolic_proofs(N):
    s, X, R = make_symbolic_board(N)
    results = {}

    # A. Hall (rows->regions): regions 0..k-1 live entirely inside rows 0..k-1
    #    => every cell of rows 0..k-1 that belongs to another region is empty.
    for k in range(1, N - 1):
        hyp = [Not(Or([R[r][c] == g for g in range(k)]))
               for r in range(k, N) for c in range(N)]
        bad = Or([And(X[r][c], R[r][c] >= k) for r in range(k) for c in range(N)])
        results[f"hall_rows_confine_k{k}"] = prove(s, hyp + [bad])

    # B. Hall (regions->rows): rows 0..k-1 contain cells of only k regions (0..k-1)
    #    => those regions have no cat outside rows 0..k-1.
    for k in range(1, N - 1):
        hyp = [R[r][c] < k for r in range(k) for c in range(N)]
        bad = Or([And(X[r][c], R[r][c] < k) for r in range(k, N) for c in range(N)])
        results[f"hall_regions_cover_rows_k{k}"] = prove(s, hyp + [bad])

    # C. Intersection rule instance: region 0 is exactly the L-tromino
    #    {(1,1),(1,2),(2,1)}  =>  (2,2) is empty (it touches all three).
    L = [(1, 1), (1, 2), (2, 1)]
    hyp = [R[r][c] == 0 if (r, c) in L else R[r][c] != 0 for r in range(N) for c in range(N)]
    results["intersection_rule_L_tromino"] = prove(s, hyp + [X[2][2]])

    # D. Box + region counting: if k = capacity(box) regions are confined to a box,
    #    every cell of the box belonging to any other region is empty.
    for (a, b, k) in [(2, 2, 1), (2, 3, 2), (3, 3, 2), (3, 4, 3), (4, 4, 4)]:
        if a > N or b > N:
            continue
        box = set(cells_in_box(0, 0, a, b))
        hyp = [Not(Or([R[r][c] == g for g in range(k)]))
               for r in range(N) for c in range(N) if (r, c) not in box]
        bad = Or([And(X[r][c], R[r][c] >= k) for (r, c) in box])
        results[f"box_{a}x{b}_k{k}_other_regions_empty"] = prove(s, hyp + [bad])

    # E. Over-capacity confinement is impossible (a valid puzzle never has it).
    for (a, b, k) in [(2, 2, 2), (2, 3, 3), (3, 3, 3)]:
        box = set(cells_in_box(0, 0, a, b))
        hyp = [Not(Or([R[r][c] == g for g in range(k)]))
               for r in range(N) for c in range(N) if (r, c) not in box]
        results[f"box_{a}x{b}_k{k}_impossible"] = prove(s, hyp)

    # F. Single-cell region => cat there (sanity).
    hyp = [R[r][c] == 0 if (r, c) == (0, 0) else R[r][c] != 0 for r in range(N) for c in range(N)]
    results["singleton_region_forces_cat"] = prove(s, hyp + [Not(X[0][0])])

    # G. Region that is exactly one full row => nothing new (control: should be
    #    unprovable that a specific cell is empty).  Included to show the method
    #    distinguishes true from false claims.
    hyp = [R[r][c] == 0 if r == 0 else R[r][c] != 0 for r in range(N) for c in range(N)]
    results["control_full_row_region_forces_(0,0)_empty_[expected False]"] = prove(s, hyp + [X[0][0]])
    return results


# --------------------------------------------------------------------------
# Experiment 6: search for two-region rules inside a 3x3 window that are NOT
# explained by the single-region intersection rule or by row/column counting.
# --------------------------------------------------------------------------
def connected_subsets(cells, max_size):
    cells = list(cells)
    out = set()
    cellset = set(cells)

    def grow(cur):
        if len(cur) > max_size:
            return
        key = frozenset(cur)
        if key in out:
            return
        out.add(key)
        for (r, c) in cur:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in cellset and q not in cur:
                    grow(cur | {q})

    for x in cells:
        grow(frozenset([x]))
    return [s for s in out if len(s) <= max_size]


def sym_transforms(pts, size=3):
    out = []
    for t in range(8):
        new = []
        for r, c in pts:
            if t & 1:
                r, c = c, r
            if t & 2:
                r = size - 1 - r
            if t & 4:
                c = size - 1 - c
            new.append((r, c))
        out.append(tuple(sorted(new)))
    return out


def baseline_propagate(S1, S2, box_table, E=None, lo=-3, hi=6):
    """Fixpoint of the 'obvious' rules on two regions confined to S1, S2:
       - intersection rule (cells attacked by every remaining candidate of a region),
       - two regions inside two rows / two columns fill those rows / columns,
       - the box rule table (>=2 cats in the bounding box of the candidates).
       Returns (eliminated cells, contradiction?, candidates A, candidates B)."""
    E = set(E or ())
    CA, CB = set(S1) - E, set(S2) - E
    board = [(r, c) for r in range(lo, hi) for c in range(lo, hi)]
    while True:
        before = len(E)
        for C in (CA, CB):
            if not C:
                return E, True, CA, CB
            for cell in board:
                if cell not in C and all(attacks(x, cell) for x in C):
                    E.add(cell)
        U = CA | CB
        rows = {r for r, _ in U}
        cols = {c for _, c in U}
        if len(rows) <= 2:
            E |= {(r, c) for (r, c) in board if r in rows and (r, c) not in U}
        if len(cols) <= 2:
            E |= {(r, c) for (r, c) in board if c in cols and (r, c) not in U}
        r_lo, r_hi = min(rows), max(rows)
        c_lo, c_hi = min(cols), max(cols)
        a, b = r_hi - r_lo + 1, c_hi - c_lo + 1
        key = (min(a, b), max(a, b), 2)
        if key in box_table:
            for (i, j) in box_table[key]:
                if a > b:
                    i, j = j, i
                cell = (r_lo + i, c_lo + j)
                if cell not in U:
                    E.add(cell)
        CA -= E
        CB -= E
        if len(E) == before:
            return E, False, CA, CB


def lookahead(S1, S2, box_table, cap, lo=-3, hi=6):
    """Cells x such that 'cat at x' + the obvious rules gives a contradiction."""
    E, contra, CA, CB = baseline_propagate(S1, S2, box_table, lo=lo, hi=hi)
    out = set()
    board = [(r, c) for r in range(lo, hi) for c in range(lo, hi)]
    for x in board:
        if x in E:
            continue
        E2 = E | {y for y in board if attacks(x, y)}
        A2 = {x} if x in CA else CA - E2
        B2 = {x} if x in CB else CB - E2
        if x in CA:
            E2 |= CA - {x}
        if x in CB:
            E2 |= CB - {x}
        E3, contra, A3, B3 = baseline_propagate(A2, B2, box_table, E=E2, lo=lo, hi=hi)
        if not contra and x not in CA and x not in CB:
            # three cats (x, A, B) inside a box whose capacity is < 3
            U = A3 | B3 | {x}
            rows = {r for r, _ in U}
            cols = {c for _, c in U}
            a, b = max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
            if cap.get((min(a, b), max(a, b)), 99) < 3:
                contra = True
        if contra:
            out.add(x)
    return E, out


def pair_search(N, r0, c0, box_table, cap, max_size=4):
    s, X = make_board(N)
    win = cells_in_box(0, 0, 3, 3)
    subsets = connected_subsets(win, max_size)
    seen = set()
    found = []
    pairs = 0
    for S1 in subsets:
        for S2 in subsets:
            if S1 & S2 or sorted(S1) > sorted(S2):
                continue
            key = min(zip(sym_transforms(S1), sym_transforms(S2)))
            key = tuple(sorted(key))
            if key in seen:
                continue
            seen.add(key)
            pairs += 1
            A = [(r0 + r, c0 + c) for (r, c) in S1]
            B = [(r0 + r, c0 + c) for (r, c) in S2]
            extra = [PbEq([(X[r][c], 1) for (r, c) in A], 1),
                     PbEq([(X[r][c], 1) for (r, c) in B], 1)]
            fe = forced_empty(s, X, N, extra)
            base, contradiction, _, _ = baseline_propagate(S1, S2, box_table)
            if fe is None:
                found.append({"S1": sorted(S1), "S2": sorted(S2), "impossible": True,
                              "baseline_finds_contradiction": contradiction})
                continue
            rel_full = {(r - r0, c - c0) for (r, c) in fe}
            rel = rel_full - set(S1) - set(S2)
            novel = sorted(rel - base)
            if novel:
                _, la = lookahead(S1, S2, box_table, cap)
                found.append({"S1": sorted(S1), "S2": sorted(S2), "novel": novel,
                              "all_forced": sorted(rel),
                              "beyond_one_step_lookahead": sorted(rel - base - la),
                              "lookahead_unsound_cells": sorted(la - rel_full)})
    return pairs, found


def render_pair(S1, S2, forced):
    fe = set(forced)
    lines = []
    for r in range(-1, 4):
        row = []
        for c in range(-1, 4):
            if (r, c) in S1:
                row.append("A")
            elif (r, c) in S2:
                row.append("B")
            elif (r, c) in fe:
                row.append("x")
            else:
                row.append(".")
        lines.append(" ".join(row))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Experiment 7: consecutive-row column gaps and Hertzsprung counts (sanity)
# --------------------------------------------------------------------------
def consecutive_row_gap(N):
    """Prove |col(row i) - col(row i+1)| >= 2 and find whether gap 1 across 2 rows is possible."""
    s, X = make_board(N)
    # negation: some i with cats at (i,c),(i+1,c') and |c-c'|<=1
    bad = Or([And(X[i][c], X[i + 1][c2]) for i in range(N - 1)
              for c in range(N) for c2 in range(N) if abs(c - c2) <= 1])
    ok1 = prove(s, [bad])
    # rows i and i+2: gap 1 IS possible (control)
    bad2 = Or([And(X[i][c], X[i + 2][c + 1]) for i in range(N - 2) for c in range(N - 1)])
    ok2 = prove(s, [bad2])
    return ok1, ok2


# --------------------------------------------------------------------------
# Worked example: the screenshot (level 155)
# --------------------------------------------------------------------------
LEVEL_155 = [
    "0111111111",
    "0111111112",
    "3333331112",
    "3343455166",
    "3344445155",
    "3343455555",
    "3343477588",
    "3333778588",
    "3399788888",
    "3397777788",
]
LEVEL_155_CATS = [(0, 0), (1, 9), (2, 6), (3, 8), (4, 3), (9, 2)]
LEVEL_155_NAMES = {0: "purple", 1: "yellow", 2: "pink", 3: "brown", 4: "orange",
                   5: "green", 6: "dark green", 7: "blue", 8: "rose", 9: "gold"}


def solve_level(grid, placed=()):
    N = len(grid)
    s, X = make_board(N)
    regions = {}
    for r in range(N):
        for c in range(N):
            regions.setdefault(int(grid[r][c]), []).append((r, c))
    for g, cells in regions.items():
        s.add(PbEq([(X[r][c], 1) for (r, c) in cells], 1))
    for (r, c) in placed:
        s.add(X[r][c])
    sols = []
    while s.check() == sat and len(sols) < 10:
        m = s.model()
        sol = sorted((r, c) for r in range(N) for c in range(N) if m.eval(X[r][c], True))
        sols.append(sol)
        s.add(Or([Not(X[r][c]) for (r, c) in sol]))
    return regions, sols


def deduce_level(grid, placed):
    """Cells provably empty / forced from the current position, region-aware."""
    N = len(grid)
    s, X = make_board(N)
    regions = {}
    for r in range(N):
        for c in range(N):
            regions.setdefault(int(grid[r][c]), []).append((r, c))
    for g, cells in regions.items():
        s.add(PbEq([(X[r][c], 1) for (r, c) in cells], 1))
    for (r, c) in placed:
        s.add(X[r][c])
    empties, forced = [], []
    for r in range(N):
        for c in range(N):
            if (r, c) in placed:
                continue
            s.push(); s.add(X[r][c]); e = s.check() == unsat; s.pop()
            s.push(); s.add(Not(X[r][c])); f = s.check() == unsat; s.pop()
            if e:
                empties.append((r, c))
            if f:
                forced.append((r, c))
    return empties, forced


# --------------------------------------------------------------------------
def main():
    results = {}

    # ---- E1: capacities ------------------------------------------------
    log("E1 box capacities")
    cap = {}
    for a in range(1, 9):
        for b in range(a, 9):
            cap[(a, b)] = box_capacity(a, b)
    results["box_capacity"] = {f"{a}x{b}": v for (a, b), v in cap.items()}
    log("  ", results["box_capacity"])

    # full-pattern counts for square boxes (Hertzsprung's problem)
    results["full_patterns_square"] = {}
    for n in range(1, 7):
        k = cap[(n, n)]
        pats = full_patterns(n, n, k)
        results["full_patterns_square"][f"{n}x{n}"] = {"cats": k, "count": len(pats)}
    log("  full patterns:", results["full_patterns_square"])

    # ---- E2: lower bounds -----------------------------------------------
    log("E2 lower bounds on cats in a box (N=8)")
    N = 8
    lb_ok = True
    lb = {}
    for a in range(1, N + 1):
        for b in range(a, N + 1):
            m = min_cats_in_box(N, a, b)
            lb[f"{a}x{b}"] = m
            if m != lower_bound_formula(N, a, b, cap):
                lb_ok = False
                log(f"   MISMATCH {a}x{b}: z3 {m} formula {lower_bound_formula(N, a, b, cap)}")
    results["min_cats_in_box_N8"] = lb
    results["min_cats_formula_holds"] = lb_ok
    log("   refined lower-bound formula exact:", lb_ok)

    # ---- E3: box confinement rules -------------------------------------
    # Universal version: at-most-one per row/col + no touching (no board-size
    # effects), box placed in the interior of a 12x12 grid.  Cross-checked
    # against the exact-one model at N=10 (interior and corner) and N=12.
    log("E3 box confinement rules")
    sU, XU = make_board(12, exact=False)
    s10, X10 = make_board(10)
    s12, X12 = make_board(12)
    box_rules = []
    box_table = {}
    for a in range(1, 6):
        for b in range(a, 6):
            for k in range(1, cap[(a, b)] + 1):
                rel = box_rule(12, 3, 3, a, b, k, sU, XU)          # universal
                box_table[(a, b, k)] = rel
                local = [x for x in rel if -1 <= x[0] <= a and -1 <= x[1] <= b]

                def local_of(lst):
                    return None if lst is None else [x for x in lst if -1 <= x[0] <= a and -1 <= x[1] <= b]
                e10 = box_rule(10, 2, 2, a, b, k, s10, X10)
                e12 = box_rule(12, 3, 3, a, b, k, s12, X12)
                e10c = box_rule(10, 0, 0, a, b, k, s10, X10)
                # visible window shared by interior(2,2) and corner placements at N=10
                vis = lambda lst: {x for x in lst if 0 <= x[0] <= 7 and 0 <= x[1] <= 7}
                pic, notes, far = render_box_rule(a, b, k, rel, 12, 3, 3)
                entry = {"box": f"{a}x{b}", "k": k, "capacity": cap[(a, b)],
                         "forced_empty_local": local, "notes": notes, "picture": pic,
                         "exact_N10_interior_same_local": local_of(e10) == local,
                         "exact_N12_interior_same_local": local_of(e12) == local,
                         "exact_N10_corner_same_as_interior": vis(e10) == vis(e10c),
                         "extra_forced_exact_N10_interior_local":
                             sorted(set(local_of(e10)) - set(local)),
                         "far_unexplained": far}
                box_rules.append(entry)
                if local or notes:
                    log(f"   {a}x{b} k={k}: local forced={local} notes={notes} "
                        f"exact10={entry['exact_N10_interior_same_local']} "
                        f"exact12={entry['exact_N12_interior_same_local']} "
                        f"corner={entry['exact_N10_corner_same_as_interior']}")
    results["box_rules"] = box_rules

    # ---- E4: single-region shapes ---------------------------------------
    log("E4 single-region shape catalogue")
    N = 10
    levels = polyominoes(5)
    shapes = []
    all_match = True
    for n in sorted(levels):
        for shape in sorted(levels[n]):
            fe = shape_rule(N, 3, 3, shape, s10, X10)
            inter = sorted(intersection_rule(shape))
            rs = [r for r, _ in shape]; cs = [c for _, c in shape]
            win = {x for x in fe if min(rs) - 2 <= x[0] <= max(rs) + 2 and min(cs) - 2 <= x[1] <= max(cs) + 2}
            match = (win == set(inter))
            all_match &= match
            shapes.append({"size": n, "cells": list(shape), "forced_empty": fe,
                           "equals_intersection_rule": match,
                           "picture": render_shape(shape, fe)})
    results["shape_rules"] = shapes
    results["shape_rules_all_equal_intersection_rule"] = all_match
    log(f"   {len(shapes)} free polyominoes; all equal to intersection rule: {all_match}")

    # ---- E5: symbolic-region proofs ------------------------------------
    for N_sym in (5, 6):
        log(f"E5 symbolic-region proofs, N={N_sym}")
        pr = symbolic_proofs(N_sym)
        results[f"symbolic_proofs_N{N_sym}"] = pr
        for k, v in pr.items():
            log(f"   {k}: {v}")

    # ---- E6: two-region rule search -------------------------------------
    log("E6 two-region search in a 3x3 window (N=9)")
    pairs, found = pair_search(9, 3, 3, box_table, cap, max_size=4)
    for f in found:
        if "novel" in f:
            f["picture"] = render_pair(set(map(tuple, f["S1"])), set(map(tuple, f["S2"])),
                                       set(map(tuple, f["all_forced"])))
    results["pair_search"] = {"pairs_examined_up_to_symmetry": pairs,
                              "impossible": [f for f in found if f.get("impossible")],
                              "novel": [f for f in found if "novel" in f]}
    nov = results['pair_search']['novel']
    beyond = [f for f in nov if f["beyond_one_step_lookahead"]]
    unsound = [f for f in nov if f["lookahead_unsound_cells"]]
    results["pair_search"]["pairs_beyond_one_step_lookahead"] = len(beyond)
    results["pair_search"]["lookahead_unsound_pairs"] = len(unsound)
    log(f"   {pairs} pairs; impossible={len(results['pair_search']['impossible'])}, "
        f"novel={len(nov)}, beyond one-step lookahead={len(beyond)}, lookahead unsound={len(unsound)}")

    # ---- E7: consecutive rows -------------------------------------------
    log("E7 consecutive-row gap")
    ok1, ok2 = consecutive_row_gap(10)
    results["consecutive_rows_gap_ge_2"] = ok1
    results["rows_two_apart_gap_ge_2_[expected False]"] = ok2
    log("   adjacent rows gap>=2:", ok1, "| rows i,i+2 gap>=2 (should be False):", ok2)

    # ---- Worked example --------------------------------------------------
    log("Worked example: level 155")
    regions, sols = solve_level(LEVEL_155)
    results["level155"] = {"grid": LEVEL_155, "cats_placed": LEVEL_155_CATS,
                           "solutions": sols, "unique": len(sols) == 1}
    empties, forced = deduce_level(LEVEL_155, LEVEL_155_CATS)
    results["level155"]["forced_from_screenshot"] = forced
    results["level155"]["empty_from_screenshot"] = empties
    log("   solutions:", sols)
    log("   forced from screenshot state:", forced)

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=1, default=list)
    log("done")


if __name__ == "__main__":
    main()
