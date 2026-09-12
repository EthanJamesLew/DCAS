#!/usr/bin/env python3
"""Search for the hardest Meowdoku boards under the rule-based difficulty meter.

For each size N: random unique-solution boards are sampled, then the best ones
are hill-climbed by moving boundary cells between colours.  Every board that
ties the maximum difficulty is kept (deduplicated under the 8 symmetries and
colour relabelling).  Output: hardest.json
"""
import json
import multiprocessing as mp
import os
import random
import sys
import time

from rule_solver import Puzzle, canon, difficulty, mutate, random_puzzle, to_strings

HERE = os.path.dirname(os.path.abspath(__file__))


def evaluate(col):
    p = Puzzle(col)
    sols = p.count_solutions(limit=2)
    if len(sols) != 1:
        return None, None
    return difficulty(p, max_depth=2), sols[0]


def search(N, budget_s, seed):
    rng = random.Random(seed)
    t0 = time.time()
    pool = {}          # canon -> (diff, col, sol)
    depth_hist = {}
    sampled = unique = 0
    # phase 1: random sampling (45% of budget)
    while time.time() - t0 < 0.45 * budget_s:
        col = random_puzzle(N, rng)
        sampled += 1
        d, sol = evaluate(col)
        if d is None:
            continue
        unique += 1
        depth_hist[d[0]] = depth_hist.get(d[0], 0) + 1
        pool[canon(col)] = (d, col, sol)
    ranked = sorted(pool.values(), key=lambda x: x[0], reverse=True)
    best = ranked[0][0] if ranked else None
    ties = {canon(x[1]): x for x in ranked if x[0] == best}
    # phase 2: hill climbing from the top boards
    frontier = [x for x in ranked[:20]]
    climbs = accepted = 0
    while time.time() - t0 < budget_s and frontier:
        cur = frontier[rng.randrange(len(frontier))]
        new = mutate(cur[1], rng)
        if new is None:
            continue
        climbs += 1
        d, sol = evaluate(new)
        if d is None:
            continue
        key = canon(new)
        if d[:2] >= cur[0][:2] and key not in pool:
            accepted += 1
            pool[key] = (d, new, sol)
            frontier.append((d, new, sol))
            frontier.sort(key=lambda x: x[0], reverse=True)
            frontier = frontier[:30]
            if best is None or d > best:
                best = d
                ties = {key: (d, new, sol)}
            elif d == best:
                ties[key] = (d, new, sol)
    return {
        "N": N, "seed": seed, "budget_s": budget_s,
        "sampled": sampled, "unique": unique,
        "depth_histogram_random_unique": {str(k): v for k, v in sorted(depth_hist.items())},
        "climb_steps": climbs, "climb_accepted": accepted,
        "max_difficulty": list(best) if best else None,
        "hardest": [{"difficulty": list(v[0]), "grid": to_strings(v[1]), "solution": v[2]}
                    for v in ties.values()],
    }


def worker(args):
    N, budget, seed = args
    res = search(N, budget, seed)
    print(f"N={N}: sampled {res['sampled']}, unique {res['unique']}, max {res['max_difficulty']}, "
          f"ties {len(res['hardest'])}, hist {res['depth_histogram_random_unique']}", flush=True)
    return res


if __name__ == "__main__":
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 300
    sizes = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [5, 6, 7, 8, 9, 10]
    with mp.Pool(min(4, len(sizes))) as pool:
        results = pool.map(worker, [(N, budget, 12345 + N) for N in sizes])
    out = {str(r["N"]): r for r in results}
    with open(os.path.join(HERE, "hardest.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote hardest.json")
