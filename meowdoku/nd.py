#!/usr/bin/env python3
"""Meowdoku in d dimensions: experiments behind REPORT_3D.md (writes variants_nd.json).

Two 3D-and-up variants:
  * slice variant: n cats in an n^d box, one per axis-slice, no two touching (Chebyshev distance 1)
  * line variant:  n^(d-1) cats, one per axis-parallel line, no two touching
    (equivalently a Latin (d-1)-cube whose king-adjacent entries differ by >= 2)

Usage: python3 nd.py <part> [...]   parts: counts caps boxrules shapes pairs random line all
"""
import itertools
import json
import os
import random
import sys
import time
from functools import lru_cache

from z3 import And, Bool, Not, Or, PbEq, PbGe, PbLe, Solver, sat, unsat

HERE = os.path.dirname(os.path.abspath(__file__))
OUTFILE = os.path.join(HERE, "variants_nd.json")
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def load():
    return json.load(open(OUTFILE)) if os.path.exists(OUTFILE) else {}


def save(key, value):
    data = load()
    data[key] = value
    json.dump(data, open(OUTFILE, "w"), indent=1)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------
def touch(a, b):
    return a != b and all(abs(x - y) <= 1 for x, y in zip(a, b))


def attack_slice(a, b):
    return a != b and (any(x == y for x, y in zip(a, b)) or touch(a, b))


def attack_line(a, b):
    d = len(a)
    return a != b and (sum(1 for x, y in zip(a, b) if x == y) == d - 1 or touch(a, b))


def box_cells(dims):
    return list(itertools.product(*(range(k) for k in dims)))


# ---------------------------------------------------------------------------
# Part 1: counts of region-free placements, slice variant
# cats (i, p_1(i), ..., p_{d-1}(i)); consecutive cats must differ by >= 2 in
# at least one transverse coordinate.
# ---------------------------------------------------------------------------
def slice_count(n, d):
    t = d - 1
    positions = list(itertools.product(range(n), repeat=t))

    @lru_cache(maxsize=None)
    def rec(i, used, last):
        # used: tuple of t bitmasks; last: tuple or None
        if i == n:
            return 1
        total = 0
        for pos in positions:
            if any(used[k] >> pos[k] & 1 for k in range(t)):
                continue
            if last is not None and all(abs(pos[k] - last[k]) <= 1 for k in range(t)):
                continue
            nu = tuple(used[k] | (1 << pos[k]) for k in range(t))
            total += rec(i + 1, nu, pos)
        return total

    return rec(0, tuple([0] * t), None)


def part_counts():
    out = {}
    for d, nmax in ((2, 8), (3, 7), (4, 5), (5, 4)):
        row = {}
        for n in range(1, nmax + 1):
            row[str(n)] = slice_count(n, d)
            log(f"  d={d} n={n}: {row[str(n)]}")
        out[str(d)] = row
    save("slice_counts", out)


# ---------------------------------------------------------------------------
# Part 2: box capacities
# ---------------------------------------------------------------------------
def capacity(dims, attack):
    cells = box_cells(dims)
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


def part_caps():
    out = {}
    for d, smax in ((3, 4), (4, 3), (5, 3)):
        row = {}
        for dims in itertools.combinations_with_replacement(range(1, smax + 1), d):
            if d == 5 and max(dims) == 3 and sum(1 for x in dims if x == 3) > 2:
                continue  # keep the 5D run small
            row["x".join(map(str, dims))] = capacity(dims, attack_slice)
        out[f"slice_d{d}"] = row
        log(f"  slice d={d}: {row}")
    row = {}
    for dims in itertools.combinations_with_replacement(range(1, 4), 3):
        row["x".join(map(str, dims))] = capacity(dims, attack_line)
    out["line_d3"] = row
    log(f"  line d=3: {row}")
    save("capacities", out)


# ---------------------------------------------------------------------------
# Part 3: box rules in 3D (region free): k = cap colours confined to a box
# ---------------------------------------------------------------------------
def board_solver(n, d, exact=True):
    cells = box_cells((n,) * d)
    s = Solver()
    X = {c: Bool(f"x{c}") for c in cells}
    Pb = PbEq if exact else PbLe
    for axis in range(d):
        for v in range(n):
            s.add(Pb([(X[c], 1) for c in cells if c[axis] == v], 1))
    for p, q in itertools.combinations(cells, 2):
        if touch(p, q):
            s.add(Not(And(X[p], X[q])))
    return s, X, cells


def forced_empty(s, X, cells, extra):
    s.push()
    for e in extra:
        s.add(e)
    if s.check() == unsat:
        s.pop()
        return None
    out = []
    for c in cells:
        s.push()
        s.add(X[c])
        if s.check() == unsat:
            out.append(c)
        s.pop()
    s.pop()
    return out


def part_boxrules():
    n, d = 6, 3
    s, X, cells = board_solver(n, d, exact=False)
    caps = load().get("capacities", {}).get("slice_d3", {})
    out = {}
    for dims in itertools.combinations_with_replacement(range(1, 4), 3):
        key = "x".join(map(str, dims))
        k = caps.get(key) or capacity(dims, attack_slice)
        off = (1, 1, 1)
        box = [tuple(o + x for o, x in zip(off, c)) for c in box_cells(dims)]
        fe = forced_empty(s, X, cells, [PbGe([(X[c], 1) for c in box], k)])
        rel = [tuple(c[i] - off[i] for i in range(3)) for c in fe]
        inside = [c for c in rel if all(0 <= c[i] < dims[i] for i in range(3))]
        near = [c for c in rel if all(-1 <= c[i] <= dims[i] for i in range(3)) and c not in inside]
        # which slices of the box are fully used (their cats are inside the box)
        used = {}
        for axis in range(3):
            used[axis] = [v for v in range(dims[axis])
                          if all(c in fe for c in cells if c[axis] == off[axis] + v and c not in box)]
        out[key] = {"k": k, "forced_inside": inside, "forced_adjacent": near,
                    "slices_used": {str(a): v for a, v in used.items()}}
        log(f"  box {key} k={k}: inside={inside} adjacent={len(near)} slices_used={used}")
    save("box_rules_3d", out)


# ---------------------------------------------------------------------------
# Part 4: single-colour polycube shapes (6-connected), size <= 4
# ---------------------------------------------------------------------------
def polycubes(max_size):
    def normalize(cells):
        m = [min(c[i] for c in cells) for i in range(3)]
        return tuple(sorted(tuple(c[i] - m[i] for i in range(3)) for c in cells))

    def transforms(cells):
        out = []
        for perm in itertools.permutations(range(3)):
            for signs in itertools.product((1, -1), repeat=3):
                out.append(normalize([tuple(signs[i] * c[perm[i]] for i in range(3)) for c in cells]))
        return out

    def canon(cells):
        return min(transforms(cells))

    levels = {1: {((0, 0, 0),)}}
    for k in range(2, max_size + 1):
        nxt = set()
        for p in levels[k - 1]:
            for c in p:
                for axis in range(3):
                    for dlt in (1, -1):
                        q = list(c)
                        q[axis] += dlt
                        q = tuple(q)
                        if q not in p:
                            nxt.add(canon(list(p) + [q]))
        levels[k] = nxt
    return levels


def intersection_rule(shape):
    cells = list(shape)
    lo = [min(c[i] for c in cells) - 2 for i in range(3)]
    hi = [max(c[i] for c in cells) + 2 for i in range(3)]
    out = []
    for c in itertools.product(*(range(lo[i], hi[i] + 1) for i in range(3))):
        if c not in cells and all(attack_slice(x, c) for x in cells):
            out.append(c)
    return sorted(out)


def part_shapes():
    n = 7
    s, X, cells = board_solver(n, 3, exact=False)
    levels = polycubes(4)
    out = []
    all_equal = True
    for k in sorted(levels):
        for shape in sorted(levels[k]):
            off = (2, 2, 2)
            sc = [tuple(o + x for o, x in zip(off, c)) for c in shape]
            fe = forced_empty(s, X, cells, [PbEq([(X[c], 1) for c in sc], 1)])
            rel = sorted(tuple(c[i] - off[i] for i in range(3)) for c in fe if c not in sc)
            inter = intersection_rule(shape)
            win = [c for c in rel if all(min(x[i] for x in shape) - 2 <= c[i] <= max(x[i] for x in shape) + 2 for i in range(3))]
            eq = (win == inter)
            all_equal &= eq
            # cells forced that are NOT on a shared slice with all shape cells (the "new" 3D ones)
            out.append({"size": k, "cells": [list(c) for c in shape], "forced": [list(c) for c in win],
                        "equals_intersection_rule": eq})
    log(f"  {len(out)} polycubes up to size 4; all equal to intersection rule: {all_equal}")
    save("shapes_3d", {"count": len(out), "all_equal_intersection_rule": all_equal, "shapes": out})


# ---------------------------------------------------------------------------
# Part 5: two colours in a 3x3x3 window, shapes of size <= 2: is one what-if complete?
# ---------------------------------------------------------------------------
def part_pairs():
    n = 5
    s, X, cells = board_solver(n, 3, exact=True)
    window = box_cells((3, 3, 3))
    shapes = [(c,) for c in window]
    for c in window:
        for axis in range(3):
            q = list(c); q[axis] += 1; q = tuple(q)
            if q in window:
                shapes.append((c, q))
    off = (1, 1, 1)

    def sym(pts):
        out = []
        for perm in itertools.permutations(range(3)):
            for signs in itertools.product((1, -1), repeat=3):
                out.append(tuple(sorted(tuple((2 if signs[i] < 0 else 0) + signs[i] * p[perm[i]] for i in range(3)) for p in pts)))
        return out

    seen = set()
    stats = {"pairs": 0, "impossible": 0, "novel": 0, "beyond_one_whatif": 0, "examples": []}
    for S1 in shapes:
        for S2 in shapes:
            if set(S1) & set(S2) or S1 > S2:
                continue
            key = min(zip(sym(S1), sym(S2)))
            key = tuple(sorted(key))
            if key in seen:
                continue
            seen.add(key)
            stats["pairs"] += 1
            A = [tuple(o + x for o, x in zip(off, c)) for c in S1]
            B = [tuple(o + x for o, x in zip(off, c)) for c in S2]
            extra = [PbEq([(X[c], 1) for c in A], 1), PbEq([(X[c], 1) for c in B], 1)]
            fe = forced_empty(s, X, cells, extra)
            if fe is None:
                stats["impossible"] += 1
                continue
            forced = {c for c in fe} - set(A) - set(B)
            base = {c for c in cells if c not in A and c not in B and
                    (all(attack_slice(a, c) for a in A) or all(attack_slice(b, c) for b in B))}
            novel = forced - base
            if novel:
                stats["novel"] += 1
                # one what-if with the direct rules (common attack for A, B and the slices)
                ok = True
                for c in novel:
                    if not whatif_refutes(n, A, B, c):
                        ok = False
                if not ok:
                    stats["beyond_one_whatif"] += 1
                    if len(stats["examples"]) < 5:
                        stats["examples"].append({"A": [list(c) for c in S1], "B": [list(c) for c in S2],
                                                  "novel": [list(tuple(x - o for x, o in zip(c, off))) for c in novel]})
    log(f"  3D pairs: {stats}")
    save("pairs_3d", stats)


def whatif_refutes(n, A, B, c):
    """Assume a cat on c; propagate common attack for the two colours and all slices; contradiction?"""
    cells = box_cells((n, n, n))
    cand = set(cells)
    cats = {c}
    for q in cells:
        if attack_slice(c, q):
            cand.discard(q)
    cand.discard(c)
    CA, CB = set(A) & cand, set(B) & cand
    if c in A:
        CA = {c}
    if c in B:
        CB = {c}
    units = [CA, CB] + [{q for q in cells if q[axis] == v} for axis in range(3) for v in range(n)]
    changed = True
    while changed:
        changed = False
        for U in units:
            K = [q for q in U if q in cand or q in cats]
            if not K:
                return True
            common = None
            for k in K:
                att = {q for q in cand if attack_slice(k, q)}
                common = att if common is None else common & att
            if common:
                cand -= common
                changed = True
    return False


# ---------------------------------------------------------------------------
# Part 6: random unique boards in d dimensions and a rule-based difficulty meter
# ---------------------------------------------------------------------------
class Contradiction(Exception):
    pass


class PuzzleND:
    def __init__(self, n, d, colour):
        self.n, self.d = n, d
        self.cells = box_cells((n,) * d)
        self.colour = colour  # dict cell -> colour id
        self.cells_of = {}
        for c in self.cells:
            self.cells_of.setdefault(colour[c], []).append(c)
        self.units = []
        for axis in range(d):
            for v in range(n):
                self.units.append((f"axis{axis}", v, [c for c in self.cells if c[axis] == v]))
        for g in range(n):
            self.units.append(("colour", g, self.cells_of.get(g, [])))
        self.att = {c: [q for q in self.cells if attack_slice(c, q)] for c in self.cells}

    def count_solutions(self, limit=2):
        n, d = self.n, self.d
        sols = []
        used = [set() for _ in range(d)]
        used_g = set()
        place = []

        def rec(i):
            if len(sols) >= limit:
                return
            if i == n:
                sols.append(list(place))
                return
            for pos in itertools.product(range(n), repeat=d - 1):
                c = (i,) + pos
                if any(pos[k] in used[k + 1] for k in range(d - 1)) or self.colour[c] in used_g:
                    continue
                if place and touch(place[-1], c):
                    continue
                for k in range(d - 1):
                    used[k + 1].add(pos[k])
                used_g.add(self.colour[c])
                place.append(c)
                rec(i + 1)
                place.pop()
                used_g.discard(self.colour[c])
                for k in range(d - 1):
                    used[k + 1].discard(pos[k])
        rec(0)
        return sols


class StateND:
    def __init__(self, p, cand=None, cats=None):
        self.p = p
        self.cand = set(p.cells) if cand is None else cand
        self.cats = set() if cats is None else cats

    def copy(self):
        return StateND(self.p, set(self.cand), set(self.cats))

    def solved(self):
        return len(self.cats) == self.p.n

    def place(self, c):
        if c not in self.cand:
            raise Contradiction
        self.cats.add(c)
        self.cand.discard(c)
        for q in self.p.att[c]:
            self.cand.discard(q)
        for q in self.p.cells_of[self.p.colour[c]]:
            self.cand.discard(q)

    def propagate(self):
        p = self.p
        changed = True
        while changed:
            changed = False
            for kind, idx, cells in p.units:
                if any(c in self.cats for c in cells):
                    continue
                K = [c for c in cells if c in self.cand]
                if not K:
                    raise Contradiction
                if len(K) == 1:
                    self.place(K[0]); changed = True; continue
                common = set(p.att[K[0]])
                for k in K[1:]:
                    common &= set(p.att[k])
                    if not common:
                        break
                common &= self.cand
                common -= set(K)
                if common:
                    self.cand -= common; changed = True
            if changed:
                continue
            open_colours = [g for g in range(p.n) if not any(c in self.cats for c in p.cells_of.get(g, []))]
            for axis in range(p.d):
                span = {g: {c[axis] for c in p.cells_of.get(g, []) if c in self.cand} for g in open_colours}
                for k in (1, 2, 3):
                    for combo in itertools.combinations(open_colours, k):
                        lines = set().union(*(span[g] for g in combo))
                        if len(lines) < k:
                            raise Contradiction
                        if len(lines) == k:
                            rm = {c for c in self.cand if c[axis] in lines and p.colour[c] not in combo}
                            if rm:
                                self.cand -= rm; changed = True
                open_lines = [v for v in range(p.n) if not any(c[axis] == v for c in self.cats)]
                for k in (1, 2, 3):
                    for combo in itertools.combinations(open_lines, k):
                        present = {p.colour[c] for c in self.cand if c[axis] in combo}
                        if len(present) < k:
                            raise Contradiction
                        if len(present) == k:
                            rm = {c for c in self.cand if c[axis] not in combo and p.colour[c] in present}
                            if rm:
                                self.cand -= rm; changed = True
        return self


def solve_depth_nd(state, depth, stats):
    state.propagate()
    while not state.solved():
        if depth == 0:
            return False
        refuted = []
        for cell in sorted(state.cand):
            trial = state.copy()
            try:
                trial.place(cell)
                solve_depth_nd(trial, depth - 1, stats)
            except Contradiction:
                refuted.append(cell)
        if not refuted:
            return False
        stats["rounds"][depth] = stats["rounds"].get(depth, 0) + 1
        stats["elims"][depth] = stats["elims"].get(depth, 0) + len(refuted)
        state.cand -= set(refuted)
        state.propagate()
    return True


def difficulty_nd(p, max_depth=2):
    for dpt in range(max_depth + 1):
        stats = {"rounds": {}, "elims": {}}
        st = StateND(p)
        try:
            ok = solve_depth_nd(st, dpt, stats)
        except Contradiction:
            return None
        if ok:
            return (dpt, stats["rounds"].get(dpt, 0), sum(stats["elims"].values()))
    return (max_depth + 1, 0, 0)


def random_placement_nd(n, d, rng):
    while True:
        perms = [list(range(n)) for _ in range(d - 1)]
        for pm in perms:
            rng.shuffle(pm)
        cats = [(i,) + tuple(pm[i] for pm in perms) for i in range(n)]
        if all(not touch(cats[i], cats[i + 1]) for i in range(n - 1)):
            return cats


def grow_regions_nd(n, d, seeds, rng):
    colour = {}
    frontier = []
    for g, c in enumerate(seeds):
        colour[c] = g
        frontier.append(c)
    bias = rng.random()
    while frontier:
        i = rng.randrange(len(frontier)) if rng.random() < bias else len(frontier) - 1
        c = frontier[i]
        nbrs = []
        for axis in range(d):
            for dlt in (1, -1):
                q = list(c); q[axis] += dlt; q = tuple(q)
                if 0 <= q[axis] < n and q not in colour:
                    nbrs.append(q)
        if not nbrs:
            frontier.pop(i)
            continue
        q = rng.choice(nbrs)
        colour[q] = colour[c]
        frontier.append(q)
    return colour


def part_random():
    out = {}
    rng = random.Random(7)
    for d, n, samples in ((3, 3, 3000), (3, 4, 2000), (3, 5, 300), (4, 3, 2000), (4, 4, 150)):
        t = time.time()
        unique = 0
        hist = {}
        hardest = None
        for _ in range(samples):
            seeds = random_placement_nd(n, d, rng)
            colour = grow_regions_nd(n, d, seeds, rng)
            p = PuzzleND(n, d, colour)
            sols = p.count_solutions(limit=2)
            if len(sols) != 1:
                continue
            unique += 1
            diff = difficulty_nd(p, max_depth=2)
            hist[diff[0]] = hist.get(diff[0], 0) + 1
            if hardest is None or diff > hardest[0]:
                hardest = (diff, colour, sols[0])
        out[f"d{d}_n{n}"] = {"samples": samples, "unique": unique,
                             "depth_histogram": {str(k): v for k, v in sorted(hist.items())},
                             "hardest": None if hardest is None else {
                                 "difficulty": list(hardest[0]),
                                 "colour": {",".join(map(str, c)): g for c, g in hardest[1].items()},
                                 "solution": [list(c) for c in hardest[2]]},
                             "seconds": round(time.time() - t, 1)}
        log(f"  d={d} n={n}: unique {unique}/{samples}, depths {hist}, {time.time() - t:.0f}s")
    save("random_nd", out)


# ---------------------------------------------------------------------------
# Part 7: line variant = king-distance Latin (d-1)-cubes; cyclic constructions
# ---------------------------------------------------------------------------
def cyclic_ok(n, coeffs):
    from math import gcd
    if any(gcd(a, n) != 1 for a in coeffs):
        return False
    for signs in itertools.product((-1, 0, 1), repeat=len(coeffs)):
        if all(s == 0 for s in signs):
            continue
        dlt = sum(s * a for s, a in zip(signs, coeffs)) % n
        if not (2 <= dlt <= n - 2):
            return False
    return True


def part_line():
    out = {}
    for d in (2, 3, 4, 5):
        k = d - 1
        first = {}
        for n in range(2, 41):
            found = next((cs for cs in itertools.product(range(1, n), repeat=k) if cyclic_ok(n, cs)), None)
            if found:
                first[str(n)] = list(found)
        out[f"cyclic_d{d}"] = {"orders_with_cyclic_solution": sorted(int(x) for x in first),
                               "example_coefficients": first}
        log(f"  line variant d={d} (Latin {k}-cube): cyclic solutions for n = {sorted(int(x) for x in first)}")
    save("line_cyclic", out)


PARTS = {"counts": part_counts, "caps": part_caps, "boxrules": part_boxrules, "shapes": part_shapes,
         "pairs": part_pairs, "random": part_random, "line": part_line}

if __name__ == "__main__":
    for arg in sys.argv[1:] or ["all"]:
        if arg == "all":
            for f in PARTS.values():
                f()
        else:
            PARTS[arg]()
    log("done")
