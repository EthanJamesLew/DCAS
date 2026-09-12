import Meowdoku.Engine

/-!
# Boards

The hardest 10 × 10 board found by the rule-based search (`hardest.json`),
as data.  Colour ids: 0 purple, 1 yellow, 2 pink, 3 brown, 4 orange, 5 green,
6 dark green, 7 blue, 8 rose, 9 gold.
-/

namespace Meowdoku

/-- Rows of the hardest 10 × 10 board. -/
def grid10 : List (List Nat) :=
  [[1,1,1,1,1,1,5,5,0,0],
   [1,1,1,1,1,1,5,5,3,0],
   [2,2,2,1,5,5,5,3,3,3],
   [2,1,1,1,1,5,3,3,9,9],
   [2,2,1,4,4,5,3,5,9,9],
   [6,2,1,4,4,5,5,5,9,9],
   [6,6,1,1,1,9,5,5,9,9],
   [1,7,7,1,9,9,9,9,9,9],
   [1,7,1,1,1,1,9,8,9,9],
   [1,1,1,1,1,1,1,9,9,9]]

/-- A board from a list of rows of colour ids (out-of-range entries wrap). -/
def Board.ofGrid (n : Nat) (h : 0 < n) (g : List (List Nat)) : Board n :=
  ⟨fun x => ⟨((g.getD x.1.val []).getD x.2.val 0) % n, Nat.mod_lt _ h⟩⟩

def hardest10 : Board 10 := Board.ofGrid 10 (by decide) grid10

/-- The unique solution (column of the cat in each row). -/
def sol10 : Fin 10 → Fin 10 := fun r => ⟨([8, 4, 1, 6, 3, 5, 0, 2, 7, 9].getD r.val 0) % 10, Nat.mod_lt _ (by decide)⟩

end Meowdoku
