#!/usr/bin/env python3
"""Generate pack3d.json: unique-solution 3D Meowdoku cubes for the playable page (incremental)."""
import json, random, sys, time
import nd

plan = [(3, 4), (4, 10), (5, 8), (6, 5)]
rng = random.Random(2026)
pack = []
t0 = time.time()
for n, want in plan:
    got = tries = 0
    while got < want:
        tries += 1
        seeds = nd.random_placement_nd(n, 3, rng)
        colour = nd.grow_regions_nd(n, 3, seeds, rng)
        sizes = [sum(1 for c in colour if colour[c] == g) for g in range(n)]
        if max(sizes) > n * n * n * 0.6:
            continue
        p = nd.PuzzleND(n, 3, colour)
        sols = p.count_solutions(limit=2)
        if len(sols) != 1:
            continue
        flat = [colour[(x, y, z)] for x in range(n) for y in range(n) for z in range(n)]
        got += 1
        pack.append({"id": f"{n}-{got}", "n": n, "colour": flat, "solution": [list(c) for c in sols[0]],
                     "singletons": sum(1 for s in sizes if s == 1)})
        json.dump(pack, open("pack3d.json", "w"))
        print(f"n={n} level {got}/{want} after {tries} tries, {time.time() - t0:.0f}s", flush=True)
print("done", len(pack))
