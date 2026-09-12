/-!
# Meowdoku: basic definitions

Meowdoku (the "Queens" / Star Battle puzzle with cats): an `n × n` grid is
partitioned into `n` colours; place `n` cats with one per row, one per column,
one per colour, and no two cats touching (not even diagonally).

A placement is encoded as the column of the cat in each row, so "one cat per
row" is built into the type.
-/

namespace Meowdoku

/-- A cell of an `n × n` board: (row, column), counted from 0. -/
abbrev Cell (n : Nat) := Fin n × Fin n

/-- Two distinct cells touch when both coordinates differ by at most one. -/
def Touch {n : Nat} (a b : Cell n) : Prop :=
  a ≠ b ∧ (a.1.val ≤ b.1.val + 1 ∧ b.1.val ≤ a.1.val + 1)
        ∧ (a.2.val ≤ b.2.val + 1 ∧ b.2.val ≤ a.2.val + 1)

/-- `a` attacks `b`: same row, same column, or touching (and `a ≠ b`). -/
def Attacks {n : Nat} (a b : Cell n) : Prop :=
  a ≠ b ∧ (a.1 = b.1 ∨ a.2 = b.2 ∨ Touch a b)

instance {n : Nat} : DecidableRel (Touch (n := n)) := by
  unfold Touch; infer_instance

instance {n : Nat} : DecidableRel (Attacks (n := n)) := by
  unfold Attacks; infer_instance

theorem Touch.symm {n : Nat} {a b : Cell n} (h : Touch a b) : Touch b a := by
  obtain ⟨hne, h1, h2⟩ := h
  exact ⟨fun e => hne e.symm, by omega, by omega⟩

theorem Attacks.symm {n : Nat} {a b : Cell n} (h : Attacks a b) : Attacks b a := by
  obtain ⟨hne, h⟩ := h
  refine ⟨fun e => hne e.symm, ?_⟩
  rcases h with h | h | h
  · exact Or.inl h.symm
  · exact Or.inr (Or.inl h.symm)
  · exact Or.inr (Or.inr h.symm)

/-- A board is a colouring of the cells with `n` colours. -/
structure Board (n : Nat) where
  colour : Cell n → Fin n

/-- A solution of a board. `col i` is the column of the cat in row `i`. -/
structure Solution {n : Nat} (B : Board n) where
  col : Fin n → Fin n
  /-- one cat per column: no two rows share a column ... -/
  col_inj : ∀ i j, i ≠ j → col i ≠ col j
  /-- ... and every column has one -/
  col_all : ∀ c, ∃ i, col i = c
  /-- one cat per colour: no two cats share a colour ... -/
  colour_inj : ∀ i j, i ≠ j → B.colour (i, col i) ≠ B.colour (j, col j)
  /-- ... and every colour has one -/
  colour_all : ∀ g, ∃ i, B.colour (i, col i) = g
  /-- no two cats touch -/
  noTouch : ∀ i j, i ≠ j → ¬ Touch (i, col i) (j, col j)

namespace Solution

variable {n : Nat} {B : Board n} (s : Solution B)

/-- The cell `x` holds a cat. -/
def cat (x : Cell n) : Prop := s.col x.1 = x.2

theorem cat_row (i : Fin n) : s.cat (i, s.col i) := rfl

/-- Two cats in the same row are the same cat. -/
theorem cat_eq_of_row {a b : Cell n} (ha : s.cat a) (hb : s.cat b) (h : a.1 = b.1) : a = b := by
  unfold cat at ha hb
  obtain ⟨a1, a2⟩ := a
  obtain ⟨b1, b2⟩ := b
  simp only at ha hb h
  subst h
  subst ha
  subst hb
  rfl

/-- Two cats in the same column are the same cat. -/
theorem cat_eq_of_col {a b : Cell n} (ha : s.cat a) (hb : s.cat b) (h : a.2 = b.2) : a = b := by
  by_cases hr : a.1 = b.1
  · exact s.cat_eq_of_row ha hb hr
  · exfalso
    apply s.col_inj a.1 b.1 hr
    unfold cat at ha hb
    rw [ha, hb, h]

/-- Two cats of the same colour are the same cat. -/
theorem cat_eq_of_colour {a b : Cell n} (ha : s.cat a) (hb : s.cat b)
    (h : B.colour a = B.colour b) : a = b := by
  by_cases hr : a.1 = b.1
  · exact s.cat_eq_of_row ha hb hr
  · exfalso
    apply s.colour_inj a.1 b.1 hr
    unfold cat at ha hb
    have ea : (a.1, s.col a.1) = a := by rw [ha]
    have eb : (b.1, s.col b.1) = b := by rw [hb]
    rw [ea, eb, h]

/-- Two cats never touch. -/
theorem not_touch {a b : Cell n} (ha : s.cat a) (hb : s.cat b) : ¬ Touch a b := by
  intro ht
  by_cases hr : a.1 = b.1
  · exact ht.1 (s.cat_eq_of_row ha hb hr)
  · apply s.noTouch a.1 b.1 hr
    unfold cat at ha hb
    have ea : (a.1, s.col a.1) = a := by rw [ha]
    have eb : (b.1, s.col b.1) = b := by rw [hb]
    rw [ea, eb]; exact ht

/-- **Rule 0.** A cat rules out everything it attacks. -/
theorem not_cat_of_attacks {a b : Cell n} (ha : s.cat a) (hab : Attacks a b) : ¬ s.cat b := by
  intro hb
  obtain ⟨hne, h⟩ := hab
  rcases h with h | h | h
  · exact hne (s.cat_eq_of_row ha hb h)
  · exact hne (s.cat_eq_of_col ha hb h)
  · exact s.not_touch ha hb h

/-- A cat also rules out the rest of its colour. -/
theorem not_cat_of_colour {a b : Cell n} (ha : s.cat a) (hne : a ≠ b)
    (h : B.colour a = B.colour b) : ¬ s.cat b :=
  fun hb => hne (s.cat_eq_of_colour ha hb h)

/-- Every colour has a cat somewhere. -/
theorem exists_cat_colour (g : Fin n) : ∃ x, s.cat x ∧ B.colour x = g := by
  obtain ⟨i, hi⟩ := s.colour_all g
  exact ⟨(i, s.col i), rfl, hi⟩

/-- Every column has a cat somewhere. -/
theorem exists_cat_col (c : Fin n) : ∃ x, s.cat x ∧ x.2 = c := by
  obtain ⟨i, hi⟩ := s.col_all c
  exact ⟨(i, s.col i), rfl, hi⟩

end Solution
end Meowdoku
