# Meowdoku invariants (Z3)

Unrelated to the rest of this repo: a Z3-based search for rules that hold on
every Meowdoku ("Queens" / Star-Battle with cats) board.

* `INVARIANTS.md`: the rules, with proofs status and a worked example.
* `CATALOGUE.md`: every box rule, polyomino and two-region pattern, drawn.
* `meowdoku_z3.py`: the experiments (`pip install z3-solver`, ~20 s).
* `make_catalogue.py`: renders `results.json` into `CATALOGUE.md`.
