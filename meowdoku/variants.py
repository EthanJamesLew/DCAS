#!/usr/bin/env python3
"""Numbers behind the open questions on rectangular and 3D Meowdoku (variants.json)."""
import itertools
import json
import os
import time

from z3 import And, Bool, Not, Or, PbEq, PbGe, PbLe, Solver, sat, unsat

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = {}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# ---------------------------------------------------------------------------
# 1. Rectangular boards: m rows, n columns, m cats (one per row, at most one per
#    column, no touching).  Region-free count = "knight injections".
# ---------------------------------------------------------------------------
def rect_count(m, n):
    cnt = 0

    def rec(i, used, prev):
        nonlocal cnt
        if i == m:
            cnt += 1
            return
        for c in range(n):
            if c in used or (prev is not None and abs(c - prev) <= 1):
                continue
            used.add(c)
            rec(i + 1, used, c)
            used.discard(c)
    rec(0, set(), None)
    return cnt


log("rectangular counts")
OUT["rect_counts"] = {f"{m}x{n}": rect_count(m, n) for m in range(1, 8) for n in range(m, 9)}


# ---------------------------------------------------------------------------
# 2. 3D, "one per slice" variant: n cats in an n^3 cube, one per x-slice,
#    y-slice and z-slice, no two cats touching (26-neighbourhood).
#    Cats are (i, s(i), t(i)) with s, t permutations; consecutive i must not be
#    within 1 in both s and t.
# ---------------------------------------------------------------------------
def cube_slice_count(n):
    cnt = 0
    for s in itertools.permutations(range(n)):
        for t in itertools.permutations(range(n)):
            if all(abs(s[i] - s[i + 1]) >= 2 or abs(t[i] - t[i + 1]) >= 2 for i in range(n - 1)):
                cnt += 1
    return cnt


log("cube slice-variant counts")
OUT["cube_slice_counts"] = {str(n): cube_slice_count(n) for n in range(1, 7)}


def cube_touch(a, b):
    return a != b and all(abs(a[i] - b[i]) <= 1 for i in range(3))


def cube_attack_slice(a, b):
    """slice variant: cats attack if they share any coordinate or touch."""
    return a != b and (a[0] == b[0] or a[1] == b[1] or a[2] == b[2] or cube_touch(a, b))


def box_capacity_3d(dims, attack):
    cells = list(itertools.product(*(range(d) for d in dims)))
    s = Solver()
    X = {c: Bool(f"x{c}") for c in cells}
    for p, q in itertools.combinations(cells, 2):
        if attack(p, q):
            s.add(Not(And(X[p], X[q])))
    k = 0
    while True:
        s.push()
        s.add(PbGe([(X[c], 1) for c in cells], k + 1))
        r = s.check()
        s.pop()
        if r == unsat:
            return k
        k += 1


log("3D box capacities (slice variant)")
OUT["cube_slice_box_capacity"] = {}
for a in range(1, 5):
    for b in range(a, 5):
        for c in range(b, 5):
            OUT["cube_slice_box_capacity"][f"{a}x{b}x{c}"] = box_capacity_3d((a, b, c), cube_attack_slice)
log("  ", OUT["cube_slice_box_capacity"])


# ---------------------------------------------------------------------------
# 3. 3D, "one per line" variant: n^2 cats in an n^3 cube, one per axis-parallel
#    line (a 3D permutation / Latin square), no two cats touching.
# ---------------------------------------------------------------------------
def cube_attack_line(a, b):
    same = sum(1 for i in range(3) if a[i] == b[i])
    return a != b and (same == 2 or cube_touch(a, b))


def cube_line_count(n, limit=100000):
    cells = list(itertools.product(range(n), repeat=3))
    s = Solver()
    X = {c: Bool(f"x{c}") for c in cells}
    for i in range(n):
        for j in range(n):
            s.add(PbEq([(X[(i, j, k)], 1) for k in range(n)], 1))
            s.add(PbEq([(X[(i, k, j)], 1) for k in range(n)], 1))
            s.add(PbEq([(X[(k, i, j)], 1) for k in range(n)], 1))
    for p, q in itertools.combinations(cells, 2):
        if cube_touch(p, q):
            s.add(Not(And(X[p], X[q])))
    cnt = 0
    while s.check() == sat and cnt < limit:
        m = s.model()
        sol = [c for c in cells if m.eval(X[c], True)]
        cnt += 1
        s.add(Or([Not(X[c]) for c in sol]))
    return cnt


log("cube line-variant counts")
OUT["cube_line_counts"] = {str(n): cube_line_count(n) for n in range(1, 5)}
log("  ", OUT["cube_line_counts"])

OUT["cube_line_box_capacity"] = {}
for a in range(1, 4):
    for b in range(a, 4):
        for c in range(b, 4):
            OUT["cube_line_box_capacity"][f"{a}x{b}x{c}"] = box_capacity_3d((a, b, c), cube_attack_line)
log("  line-variant box capacities", OUT["cube_line_box_capacity"])

# ---------------------------------------------------------------------------
# 4. Hexagonal / king-graph aside: on a rectangle m x n with m rows and m cats,
#    the minimum width n that admits a placement at all (knight injections).
# ---------------------------------------------------------------------------
OUT["rect_min_width"] = {}
for m in range(1, 9):
    n = m
    while rect_count(m, n) == 0:
        n += 1
    OUT["rect_min_width"][str(m)] = n

with open(os.path.join(HERE, "variants.json"), "w") as f:
    json.dump(OUT, f, indent=1)
log("wrote variants.json")
