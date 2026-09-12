# Meowdoku invariants (Z3)

Unrelated to the rest of this repo: a Z3-based search for rules that hold on
every Meowdoku ("Queens" / Star-Battle with cats) board.

* `RULES.md`: every rule with a game-style picture (`img/`), plain English, formal statement and proof.
* `INVARIANTS.md`: the compact write-up of the search results.
* `CATALOGUE.md`: every box rule, polyomino and two-region pattern, drawn.
* `meowdoku_z3.py`: the experiments (`pip install z3-solver`, ~20 s).
* `make_catalogue.py`: renders `results.json` into `CATALOGUE.md`.
* `make_images.py` -> `img/*.png`; `make_rules.py` -> `RULES.md` and `rules.html` (self-contained page).
* `HARDEST.md`: the hardest boards found for sizes 5-10 under the rule-only solver (`hardest.py` -> `hardest.json`; `make_hardest.py` -> images, `HARDEST.md`, `hardest.html`).
* `play.html`: playable, phone-first version of the three hardest boards (`make_play.py`).
* `WALKTHROUGH.md`: narrated hand solution of the hardest 10x10 (`walkthrough.py`, also `walkthrough.html`).
* `QUESTIONS.md`: open questions for rectangular and 3D boards, with the numbers behind them (`variants.py`).
* `lean/`: a Lean 4 library (no Mathlib) with the definitions, every rule proven, a game engine, and the
  hardest 10x10 solved move by move with uniqueness verified by Lean's kernel (`make_lean_game.py` generates the game).
