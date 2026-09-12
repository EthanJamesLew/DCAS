#!/usr/bin/env python3
"""A Meowdoku solver that only uses the rules of RULES.md, plus a difficulty meter.

Depth 0: the direct rules to a fixed point
    - a unit (row / column / colour) with one candidate gets its cat
    - common attack (Rule 1) for every unit
    - colours locked in k rows/columns and rows/columns made of k colours (Rules 8, 9), k <= 3
    - full rectangles (Rules 3-7, 10): k = cap colours confined to a box up to 4x4
Depth d: assume a cat on a candidate cell, run depth d-1; a contradiction empties the cell.

difficulty(puzzle) = (depth needed, number of what-if rounds, number of what-if eliminations,
                      number of direct-rule steps) -- compared lexicographically.
"""
import itertools
import random
import sys

# ---------------------------------------------------------------------------
# box rule table (region free), computed by brute force once
# ---------------------------------------------------------------------------
def _attacks(a, b):
    return a != b and (a[0] == b[0] or a[1] == b[1] or (abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1))


def _patterns(a, b, k):
    cells = [(i, j) for i in range(a) for j in range(b)]
    out = []
    for combo in itertools.combinations(cells, k):
        if all(not _attacks(p, q) for p, q in itertools.combinations(combo, 2)):
            out.append(combo)
    return out


CAP = {}
BOX_RULE = {}   # (a, b) -> (k=cap, forced relative cells within a margin window)
for a in range(1, 5):
    for b in range(1, 5):
        k = 0
        while _patterns(a, b, k + 1):
            k += 1
        CAP[(a, b)] = k
        pats = _patterns(a, b, k)
        window = [(i, j) for i in range(-1, a + 1) for j in range(-1, b + 1)]
        forced = []
        for c in window:
            inside = 0 <= c[0] < a and 0 <= c[1] < b
            if all((inside and c not in P) or any(_attacks(p, c) for p in P) for P in pats):
                forced.append(c)
        BOX_RULE[(a, b)] = (k, forced, pats)


# ---------------------------------------------------------------------------
class Contradiction(Exception):
    pass


class Puzzle:
    def __init__(self, grid):
        """grid: list of strings/lists of colour ids (0..N-1)."""
        self.N = N = len(grid)
        self.col = [[int(grid[r][c]) for c in range(N)] for r in range(N)]
        self.cells_of = {}
        for r in range(N):
            for c in range(N):
                self.cells_of.setdefault(self.col[r][c], []).append((r, c))
        self.units = []
        for r in range(N):
            self.units.append(("row", r, [(r, c) for c in range(N)]))
        for c in range(N):
            self.units.append(("col", c, [(r, c) for r in range(N)]))
        for g in range(N):
            self.units.append(("colour", g, self.cells_of[g]))
        self.att = {}
        for r in range(N):
            for c in range(N):
                self.att[(r, c)] = [q for q in ((i, j) for i in range(N) for j in range(N)) if _attacks((r, c), q)]

    # ---- brute-force solution count (for uniqueness) -----------------------
    def count_solutions(self, limit=2):
        N = self.N
        sols = []
        used_c = [False] * N
        used_g = [False] * N
        place = []

        def rec(r):
            if len(sols) >= limit:
                return
            if r == N:
                sols.append(list(place))
                return
            for c in range(N):
                if used_c[c] or used_g[self.col[r][c]]:
                    continue
                if r > 0 and abs(place[-1][1] - c) <= 1:
                    continue
                used_c[c] = used_g[self.col[r][c]] = True
                place.append((r, c))
                rec(r + 1)
                place.pop()
                used_c[c] = used_g[self.col[r][c]] = False
        rec(0)
        return sols


class State:
    __slots__ = ("p", "cand", "cats", "steps", "log")

    def __init__(self, p, cand=None, cats=None, log=None):
        self.p = p
        N = p.N
        self.cand = cand if cand is not None else {(r, c) for r in range(N) for c in range(N)}
        self.cats = cats if cats is not None else set()
        self.steps = 0
        self.log = log

    def copy(self):
        s = State(self.p, set(self.cand), set(self.cats), None if self.log is None else [])
        return s

    def note(self, rule, what, removed=(), placed=None):
        if self.log is not None:
            self.log.append({"rule": rule, "what": what, "removed": sorted(removed),
                             "placed": placed})

    def solved(self):
        return len(self.cats) == self.p.N

    # ---- elementary operations --------------------------------------------
    def place(self, cell):
        if cell not in self.cand:
            raise Contradiction
        self.cats.add(cell)
        self.cand.discard(cell)
        for q in self.p.att[cell]:
            self.cand.discard(q)
        g = self.p.col[cell[0]][cell[1]]
        for q in self.p.cells_of[g]:
            self.cand.discard(q)

    def unit_cands(self, cells):
        return [c for c in cells if c in self.cand]

    def unit_done(self, cells):
        return any(c in self.cats for c in cells)

    # ---- depth-0 propagation -----------------------------------------------
    def propagate(self):
        p = self.p
        N = p.N
        changed = True
        while changed:
            changed = False
            # singles + common attack
            for kind, idx, cells in p.units:
                if self.unit_done(cells):
                    continue
                K = self.unit_cands(cells)
                if not K:
                    raise Contradiction(f"{kind} {idx} has no cell left")
                if len(K) == 1:
                    before = set(self.cand)
                    self.place(K[0])
                    self.note("single", f"{kind} {idx} has one cell left", before - self.cand, K[0])
                    self.steps += 1
                    changed = True
                    continue
                common = set(p.att[K[0]])
                for k in K[1:]:
                    common &= set(p.att[k])
                    if not common:
                        break
                common &= self.cand
                common -= set(K)
                if common:
                    self.cand -= common
                    self.note("common attack", f"every remaining cell of {kind} {idx} attacks these", common)
                    self.steps += 1
                    changed = True
            if changed:
                continue
            # Rules 8/9: colours in k lines, lines made of k colours (k <= 3)
            open_colours = [g for g in range(N) if not any(c in self.cats for c in p.cells_of[g])]
            for axis in (0, 1):
                span = {g: {c[axis] for c in self.unit_cands(p.cells_of[g])} for g in open_colours}
                for k in (1, 2, 3):
                    for combo in itertools.combinations(open_colours, k):
                        lines = set().union(*(span[g] for g in combo))
                        if len(lines) < k:
                            raise Contradiction(f"colours {combo} are squeezed into fewer than {k} lines")
                        if len(lines) == k:
                            rm = {c for c in self.cand if c[axis] in lines and p.col[c[0]][c[1]] not in combo}
                            if rm:
                                self.cand -= rm
                                self.note("colours locked in lines", f"colours {combo} fit inside {'rows' if axis == 0 else 'columns'} {sorted(lines)}", rm)
                                self.steps += 1
                                changed = True
                open_lines = [i for i in range(N) if not any(c[axis] == i for c in self.cats)]
                for k in (1, 2, 3):
                    for combo in itertools.combinations(open_lines, k):
                        cols_present = {p.col[c[0]][c[1]] for c in self.cand if c[axis] in combo}
                        if len(cols_present) < k:
                            raise Contradiction(f"lines {combo} contain fewer than {k} colours")
                        if len(cols_present) == k:
                            rm = {c for c in self.cand if c[axis] not in combo and p.col[c[0]][c[1]] in cols_present}
                            if rm:
                                self.cand -= rm
                                self.note("lines made of few colours", f"{'rows' if axis == 0 else 'columns'} {list(combo)} contain only colours {sorted(cols_present)}", rm)
                                self.steps += 1
                                changed = True
            if changed:
                continue
            # box rules
            bbox = {}
            for g in open_colours:
                K = self.unit_cands(p.cells_of[g])
                rs = [c[0] for c in K]
                cs = [c[1] for c in K]
                bbox[g] = (min(rs), min(cs), max(rs), max(cs))
            for a in range(1, 5):
                for b in range(1, 5):
                    cap, forced, _ = BOX_RULE[(a, b)]
                    for r0 in range(N - a + 1):
                        for c0 in range(N - b + 1):
                            confined = [g for g, (r1, c1, r2, c2) in bbox.items()
                                        if r1 >= r0 and c1 >= c0 and r2 < r0 + a and c2 < c0 + b]
                            if len(confined) > cap:
                                raise Contradiction(f"{len(confined)} colours inside a {a}x{b} box that holds {cap}")
                            if len(confined) == cap and cap >= 1:
                                rm = set()
                                for c in self.cand:
                                    if r0 <= c[0] < r0 + a and c0 <= c[1] < c0 + b and p.col[c[0]][c[1]] not in confined:
                                        rm.add(c)
                                for (i, j) in forced:
                                    q = (r0 + i, c0 + j)
                                    if q in self.cand:
                                        rm.add(q)
                                # rows / columns fully used by the box
                                pats = BOX_RULE[(a, b)][2]
                                rows_used = set.intersection(*({p_[0] for p_ in P} for P in pats))
                                cols_used = set.intersection(*({p_[1] for p_ in P} for P in pats))
                                for c in self.cand:
                                    if (c[0] - r0) in rows_used and not (c0 <= c[1] < c0 + b):
                                        rm.add(c)
                                    if (c[1] - c0) in cols_used and not (r0 <= c[0] < r0 + a):
                                        rm.add(c)
                                if rm:
                                    self.cand -= rm
                                    self.note("full rectangle", f"colours {confined} fill the {a}x{b} box at rows {r0}-{r0 + a - 1}, columns {c0}-{c0 + b - 1}", rm)
                                    self.steps += 1
                                    changed = True
        return self


def solve_depth(state, depth, stats):
    """Propagate with what-if up to `depth`. Returns True if solved."""
    state.propagate()
    while not state.solved():
        if depth == 0:
            return False
        # one what-if round: test every candidate at depth-1
        refuted = []
        for cell in sorted(state.cand):
            trial = state.copy()
            try:
                trial.place(cell)
                solve_depth(trial, depth - 1, stats)
            except Contradiction:
                refuted.append(cell)
        if not refuted:
            return False
        stats["rounds"][depth] = stats["rounds"].get(depth, 0) + 1
        stats["elims"][depth] = stats["elims"].get(depth, 0) + len(refuted)
        state.cand -= set(refuted)
        state.propagate()
    return True


def difficulty(puzzle, max_depth=3):
    """(depth needed, what-if rounds at that depth, what-if eliminations, direct steps)."""
    for d in range(max_depth + 1):
        stats = {"rounds": {}, "elims": {}}
        st = State(puzzle)
        try:
            ok = solve_depth(st, d, stats)
        except Contradiction:
            return None
        if ok:
            return (d, stats["rounds"].get(d, 0), sum(stats["elims"].values()), st.steps)
    return (max_depth + 1, 0, 0, 0)


# ---------------------------------------------------------------------------
# random puzzle generation
# ---------------------------------------------------------------------------
def random_placement(N, rng):
    """A random non-touching permutation (one cat per row/column)."""
    while True:
        cols = list(range(N))
        rng.shuffle(cols)
        if all(abs(cols[i] - cols[i + 1]) >= 2 for i in range(N - 1)):
            return [(r, cols[r]) for r in range(N)]


def grow_regions(N, seeds, rng, bias=0.5):
    """Grow N connected regions from the seed cells until the board is covered."""
    col = [[-1] * N for _ in range(N)]
    frontier = []
    for g, (r, c) in enumerate(seeds):
        col[r][c] = g
        frontier.append((r, c))
    while frontier:
        i = rng.randrange(len(frontier)) if rng.random() < bias else len(frontier) - 1
        r, c = frontier[i]
        nbrs = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < N and 0 <= c + dc < N and col[r + dr][c + dc] == -1]
        if not nbrs:
            frontier.pop(i)
            continue
        nr, nc = rng.choice(nbrs)
        col[nr][nc] = col[r][c]
        frontier.append((nr, nc))
    return col


def random_puzzle(N, rng):
    seeds = random_placement(N, rng)
    return grow_regions(N, seeds, rng, bias=rng.random())


def connected(cells):
    cells = set(cells)
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for q in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if q in cells and q not in seen:
                seen.add(q)
                stack.append(q)
    return len(seen) == len(cells)


def mutate(col, rng):
    """Move one boundary cell to a neighbouring colour, keeping both connected."""
    N = len(col)
    for _ in range(50):
        r, c = rng.randrange(N), rng.randrange(N)
        g = col[r][c]
        nbr_cols = {col[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= r + dr < N and 0 <= c + dc < N} - {g}
        if not nbr_cols:
            continue
        h = rng.choice(sorted(nbr_cols))
        own = [(i, j) for i in range(N) for j in range(N) if col[i][j] == g]
        if len(own) == 1:
            continue
        new = [row[:] for row in col]
        new[r][c] = h
        rest = [x for x in own if x != (r, c)]
        if connected(rest):
            return new
    return None


def canon(col):
    """Canonical form under the 8 symmetries and colour relabelling."""
    N = len(col)
    best = None
    for t in range(8):
        grid = [[None] * N for _ in range(N)]
        for r in range(N):
            for c in range(N):
                i, j = r, c
                if t & 1:
                    i, j = j, i
                if t & 2:
                    i = N - 1 - i
                if t & 4:
                    j = N - 1 - j
                grid[i][j] = col[r][c]
        relabel = {}
        s = []
        for r in range(N):
            for c in range(N):
                g = grid[r][c]
                if g not in relabel:
                    relabel[g] = len(relabel)
                s.append(relabel[g])
        key = tuple(s)
        if best is None or key < best:
            best = key
    return best


def to_strings(col):
    return ["".join(str(x) for x in row) for row in col]


if __name__ == "__main__":
    import json, os, time
    here = os.path.dirname(os.path.abspath(__file__))
    R = json.load(open(os.path.join(here, "results.json")))
    p = Puzzle(R["level155"]["grid"])
    t = time.time()
    print("level 155 solutions:", len(p.count_solutions()), "difficulty:", difficulty(p), f"{time.time()-t:.2f}s")
    rng = random.Random(1)
    for N in (5, 6, 7, 8, 9, 10):
        t = time.time()
        n_unique = 0
        for _ in range(50):
            col = random_puzzle(N, rng)
            pz = Puzzle(col)
            if len(pz.count_solutions()) == 1:
                n_unique += 1
                d = difficulty(pz)
        print(f"N={N}: {n_unique}/50 unique, {time.time()-t:.1f}s")
