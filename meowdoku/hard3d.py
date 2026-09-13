#!/usr/bin/env python3
"""Hill-climb for d-dimensional boards that need a what-if (variants_nd_hard.json)."""
import json, os, random, sys, time
import nd

def mutate(colour, n, d, rng):
    cells = list(colour)
    for _ in range(60):
        c = rng.choice(cells)
        g = colour[c]
        nb = []
        for axis in range(d):
            for dl in (1, -1):
                q = list(c); q[axis] += dl; q = tuple(q)
                if 0 <= q[axis] < n and colour[q] != g:
                    nb.append(colour[q])
        if not nb:
            continue
        own = [x for x in cells if colour[x] == g]
        if len(own) == 1:
            continue
        new = dict(colour); new[c] = rng.choice(nb)
        rest = [x for x in own if x != c]
        # connectivity of the shrunk region
        seen = {rest[0]}; stack = [rest[0]]; restset = set(rest)
        while stack:
            x = stack.pop()
            for axis in range(d):
                for dl in (1, -1):
                    q = list(x); q[axis] += dl; q = tuple(q)
                    if q in restset and q not in seen:
                        seen.add(q); stack.append(q)
        if len(seen) == len(rest):
            return new
    return None

def search(n, d, budget, seed):
    rng = random.Random(seed)
    t0 = time.time()
    pool = []
    while time.time() - t0 < 0.3 * budget:
        seeds = nd.random_placement_nd(n, d, rng)
        colour = nd.grow_regions_nd(n, d, seeds, rng)
        p = nd.PuzzleND(n, d, colour)
        sols = p.count_solutions(limit=2)
        if len(sols) != 1:
            continue
        pool.append((nd.difficulty_nd(p), colour, sols[0]))
    pool.sort(key=lambda x: x[0], reverse=True)
    best = pool[0]
    frontier = pool[:15]
    steps = 0
    while time.time() - t0 < budget:
        cur = frontier[rng.randrange(len(frontier))]
        new = mutate(cur[1], n, d, rng)
        if new is None:
            continue
        steps += 1
        p = nd.PuzzleND(n, d, new)
        sols = p.count_solutions(limit=2)
        if len(sols) != 1:
            continue
        diff = nd.difficulty_nd(p)
        if diff[:2] >= cur[0][:2]:
            frontier.append((diff, new, sols[0])); frontier.sort(key=lambda x: x[0], reverse=True); frontier = frontier[:20]
            if diff > best[0]:
                best = (diff, new, sols[0])
    return {"n": n, "d": d, "sampled_unique": len(pool), "climb_steps": steps, "best_difficulty": list(best[0]),
            "colour": {",".join(map(str, c)): g for c, g in best[1].items()}, "solution": [list(c) for c in best[2]]}

if __name__ == "__main__":
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = {}
    for d, n in ((3, 4), (3, 5), (4, 3)):
        r = search(n, d, budget, 11)
        print(f"d={d} n={n}: best {r['best_difficulty']} after {r['climb_steps']} steps ({r['sampled_unique']} sampled)", flush=True)
        out[f"d{d}_n{n}"] = r
    json.dump(out, open(os.path.join(nd.HERE, "variants_nd_hard.json"), "w"), indent=1)
