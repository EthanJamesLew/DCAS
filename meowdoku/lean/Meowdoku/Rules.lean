import Meowdoku.Basic

/-!
# Meowdoku: the rules of RULES.md, proven

All statements are about an arbitrary solution `s` of an arbitrary board, so
they hold on every board.  Rows and columns are `Fin n`; arithmetic goes
through `.val` and `omega`.
-/

namespace Meowdoku
namespace Solution

variable {n : Nat} {B : Board n} (s : Solution B)

/-! ## Rule 1: common attack -/

/-- **Rule 1 (common attack).** If the cat of some unit is known to lie in `K`
and every cell of `K` attacks `x`, then `x` holds no cat. -/
theorem common_attack {K : Cell n → Prop} (hK : ∃ k, K k ∧ s.cat k) {x : Cell n}
    (hx : ∀ k, K k → Attacks k x) : ¬ s.cat x := by
  obtain ⟨k, hk, hcat⟩ := hK
  exact s.not_cat_of_attacks hcat (hx k hk)

/-- A cat also excludes every other cell of its colour (used by "place a cat"). -/
theorem colour_exclusive {k x : Cell n} (hk : s.cat k) (hne : x ≠ k)
    (h : B.colour x = B.colour k) : ¬ s.cat x :=
  s.not_cat_of_colour hk (Ne.symm hne) h.symm

/-! ## Rule 2: the knight's move -/

/-- Two cats in consecutive rows are at least two columns apart. -/
theorem knight_cat {x y : Cell n} (hx : s.cat x) (hy : s.cat y) (h : y.1.val = x.1.val + 1) :
    x.2.val + 2 ≤ y.2.val ∨ y.2.val + 2 ≤ x.2.val := by
  have ht := s.not_touch hx hy
  have hne : x ≠ y := fun e => by rw [e] at h; omega
  have hc : ¬ (x.2.val ≤ y.2.val + 1 ∧ y.2.val ≤ x.2.val + 1) :=
    fun hcols => ht ⟨hne, ⟨by omega, by omega⟩, hcols⟩
  omega

/-- **Rule 2.** In the row-map form: `|col i - col (i+1)| ≥ 2`. -/
theorem knight (i j : Fin n) (hij : j.val = i.val + 1) :
    (s.col i).val + 2 ≤ (s.col j).val ∨ (s.col j).val + 2 ≤ (s.col i).val :=
  s.knight_cat (s.cat_row i) (s.cat_row j) hij

/-! ## Rule 3: capacities of small rectangles -/

/-- A 2 × 2 block never holds two cats. -/
theorem cap_2x2 {x y : Cell n} (hx : s.cat x) (hy : s.cat y) (hne : x ≠ y)
    (r c : Nat)
    (hxr : r ≤ x.1.val ∧ x.1.val ≤ r + 1) (hyr : r ≤ y.1.val ∧ y.1.val ≤ r + 1)
    (hxc : c ≤ x.2.val ∧ x.2.val ≤ c + 1) (hyc : c ≤ y.2.val ∧ y.2.val ≤ c + 1) : False := by
  have hrow : x.1.val ≠ y.1.val := fun e => hne (s.cat_eq_of_row hx hy (Fin.ext e))
  have k1 : y.1.val = x.1.val + 1 → x.2.val + 2 ≤ y.2.val ∨ y.2.val + 2 ≤ x.2.val :=
    fun h => s.knight_cat hx hy h
  have k2 : x.1.val = y.1.val + 1 → y.2.val + 2 ≤ x.2.val ∨ x.2.val + 2 ≤ y.2.val :=
    fun h => s.knight_cat hy hx h
  omega

/-- A 3 × 3 block never holds three cats. -/
theorem cap_3x3 {x y z : Cell n} (hx : s.cat x) (hy : s.cat y) (hz : s.cat z)
    (hxy : x ≠ y) (hxz : x ≠ z) (hyz : y ≠ z) (r c : Nat)
    (hxr : r ≤ x.1.val ∧ x.1.val ≤ r + 2) (hyr : r ≤ y.1.val ∧ y.1.val ≤ r + 2)
    (hzr : r ≤ z.1.val ∧ z.1.val ≤ r + 2)
    (hxc : c ≤ x.2.val ∧ x.2.val ≤ c + 2) (hyc : c ≤ y.2.val ∧ y.2.val ≤ c + 2)
    (hzc : c ≤ z.2.val ∧ z.2.val ≤ c + 2) : False := by
  have rxy : x.1.val ≠ y.1.val := fun e => hxy (s.cat_eq_of_row hx hy (Fin.ext e))
  have rxz : x.1.val ≠ z.1.val := fun e => hxz (s.cat_eq_of_row hx hz (Fin.ext e))
  have ryz : y.1.val ≠ z.1.val := fun e => hyz (s.cat_eq_of_row hy hz (Fin.ext e))
  have cxy : x.2.val ≠ y.2.val := fun e => hxy (s.cat_eq_of_col hx hy (Fin.ext e))
  have cxz : x.2.val ≠ z.2.val := fun e => hxz (s.cat_eq_of_col hx hz (Fin.ext e))
  have cyz : y.2.val ≠ z.2.val := fun e => hyz (s.cat_eq_of_col hy hz (Fin.ext e))
  have kxy : y.1.val = x.1.val + 1 → x.2.val + 2 ≤ y.2.val ∨ y.2.val + 2 ≤ x.2.val :=
    fun h => s.knight_cat hx hy h
  have kyx : x.1.val = y.1.val + 1 → y.2.val + 2 ≤ x.2.val ∨ x.2.val + 2 ≤ y.2.val :=
    fun h => s.knight_cat hy hx h
  have kxz : z.1.val = x.1.val + 1 → x.2.val + 2 ≤ z.2.val ∨ z.2.val + 2 ≤ x.2.val :=
    fun h => s.knight_cat hx hz h
  have kzx : x.1.val = z.1.val + 1 → z.2.val + 2 ≤ x.2.val ∨ x.2.val + 2 ≤ z.2.val :=
    fun h => s.knight_cat hz hx h
  have kyz : z.1.val = y.1.val + 1 → y.2.val + 2 ≤ z.2.val ∨ z.2.val + 2 ≤ y.2.val :=
    fun h => s.knight_cat hy hz h
  have kzy : y.1.val = z.1.val + 1 → z.2.val + 2 ≤ y.2.val ∨ y.2.val + 2 ≤ z.2.val :=
    fun h => s.knight_cat hz hy h
  omega

/-! ## Rules 4-7: forced patterns inside small rectangles -/

/-- **Rule 4 (3 × 3).** A cat in the centre of a 3 × 3 block pushes the cats of
the rows above and below out of the block. -/
theorem centre_3x3 (i j k : Fin n) (hij : j.val = i.val + 1) (hjk : k.val = j.val + 1)
    (c : Nat) (hmid : (s.col j).val = c + 1) :
    ¬ (c ≤ (s.col i).val ∧ (s.col i).val ≤ c + 2) ∧
    ¬ (c ≤ (s.col k).val ∧ (s.col k).val ≤ c + 2) := by
  have h1 := s.knight i j hij
  have h2 := s.knight j k hjk
  omega

/-- **Rule 5 (2 × 3).** Two consecutive rows with cats inside three consecutive
columns use the two end columns. -/
theorem pattern_2x3 (i j : Fin n) (hij : j.val = i.val + 1) (c : Nat)
    (hi : c ≤ (s.col i).val ∧ (s.col i).val ≤ c + 2)
    (hj : c ≤ (s.col j).val ∧ (s.col j).val ≤ c + 2) :
    ((s.col i).val = c ∧ (s.col j).val = c + 2) ∨ ((s.col i).val = c + 2 ∧ (s.col j).val = c) := by
  have h := s.knight i j hij
  omega

/-- **Rule 6 (3 × 4).** Three consecutive rows with cats inside four consecutive
columns: the middle row is at an end, and both end columns are used. -/
theorem pattern_3x4 (i j k : Fin n) (hij : j.val = i.val + 1) (hjk : k.val = j.val + 1) (c : Nat)
    (hi : c ≤ (s.col i).val ∧ (s.col i).val ≤ c + 3)
    (hj : c ≤ (s.col j).val ∧ (s.col j).val ≤ c + 3)
    (hk : c ≤ (s.col k).val ∧ (s.col k).val ≤ c + 3) :
    ((s.col i).val = c ∧ (s.col j).val = c + 3 ∧ (s.col k).val = c + 1) ∨
    ((s.col i).val = c + 1 ∧ (s.col j).val = c + 3 ∧ (s.col k).val = c) ∨
    ((s.col i).val = c + 2 ∧ (s.col j).val = c ∧ (s.col k).val = c + 3) ∨
    ((s.col i).val = c + 3 ∧ (s.col j).val = c ∧ (s.col k).val = c + 2) := by
  have h1 := s.knight i j hij
  have h2 := s.knight j k hjk
  have hik : i ≠ k := fun e => by rw [e] at hij; omega
  have h3 : (s.col i).val ≠ (s.col k).val := fun e => s.col_inj i k hik (Fin.ext e)
  omega

/-- **Rule 7 (4 × 4, the knight ring).** Four consecutive rows with cats inside
four consecutive columns admit exactly two patterns. -/
theorem pattern_4x4 (i j k l : Fin n) (hij : j.val = i.val + 1) (hjk : k.val = j.val + 1)
    (hkl : l.val = k.val + 1) (c : Nat)
    (hi : c ≤ (s.col i).val ∧ (s.col i).val ≤ c + 3)
    (hj : c ≤ (s.col j).val ∧ (s.col j).val ≤ c + 3)
    (hk : c ≤ (s.col k).val ∧ (s.col k).val ≤ c + 3)
    (hl : c ≤ (s.col l).val ∧ (s.col l).val ≤ c + 3) :
    ((s.col i).val = c + 1 ∧ (s.col j).val = c + 3 ∧ (s.col k).val = c ∧ (s.col l).val = c + 2) ∨
    ((s.col i).val = c + 2 ∧ (s.col j).val = c ∧ (s.col k).val = c + 3 ∧ (s.col l).val = c + 1) := by
  have h1 := s.knight i j hij
  have h2 := s.knight j k hjk
  have h3 := s.knight k l hkl
  have hik : i ≠ k := fun e => by rw [e] at hij; omega
  have hil : i ≠ l := fun e => by rw [e] at hij; omega
  have hjl : j ≠ l := fun e => by rw [e] at hjk; omega
  have d1 : (s.col i).val ≠ (s.col k).val := fun e => s.col_inj i k hik (Fin.ext e)
  have d2 : (s.col i).val ≠ (s.col l).val := fun e => s.col_inj i l hil (Fin.ext e)
  have d3 : (s.col j).val ≠ (s.col l).val := fun e => s.col_inj j l hjl (Fin.ext e)
  omega

/-! ## Impossible layouts -/

/-- Two colours confined to one 2 × 2 block: no solution. -/
theorem impossible_2x2 (g h : Fin n) (hgh : g ≠ h) (r c : Nat)
    (hg : ∀ x, s.cat x → B.colour x = g →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 1) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 1))
    (hh : ∀ x, s.cat x → B.colour x = h →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 1) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 1)) : False := by
  obtain ⟨x, hx, hxg⟩ := s.exists_cat_colour g
  obtain ⟨y, hy, hyh⟩ := s.exists_cat_colour h
  have hne : x ≠ y := fun e => hgh (by rw [← hxg, ← hyh, e])
  obtain ⟨hxr, hxc⟩ := hg x hx hxg
  obtain ⟨hyr, hyc⟩ := hh y hy hyh
  exact s.cap_2x2 hx hy hne r c hxr hyr hxc hyc

/-- Three colours confined to one 3 × 3 block: no solution. -/
theorem impossible_3x3 (g h k : Fin n) (hgh : g ≠ h) (hgk : g ≠ k) (hhk : h ≠ k) (r c : Nat)
    (hg : ∀ x, s.cat x → B.colour x = g →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 2) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 2))
    (hh : ∀ x, s.cat x → B.colour x = h →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 2) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 2))
    (hk : ∀ x, s.cat x → B.colour x = k →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 2) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 2)) : False := by
  obtain ⟨x, hx, hxg⟩ := s.exists_cat_colour g
  obtain ⟨y, hy, hyh⟩ := s.exists_cat_colour h
  obtain ⟨z, hz, hzk⟩ := s.exists_cat_colour k
  have hxy : x ≠ y := fun e => hgh (by rw [← hxg, ← hyh, e])
  have hxz : x ≠ z := fun e => hgk (by rw [← hxg, ← hzk, e])
  have hyz : y ≠ z := fun e => hhk (by rw [← hyh, ← hzk, e])
  obtain ⟨hxr, hxc⟩ := hg x hx hxg
  obtain ⟨hyr, hyc⟩ := hh y hy hyh
  obtain ⟨hzr, hzc⟩ := hk z hz hzk
  exact s.cap_3x3 hx hy hz hxy hxz hyz r c hxr hyr hzr hxc hyc hzc

/-- **Rule 10 for the 3 × 3.** Two colours confined to a 3 × 3 block: no cat of
any third colour lies inside the block. -/
theorem full_3x3 (g h : Fin n) (hgh : g ≠ h) (r c : Nat)
    (hg : ∀ x, s.cat x → B.colour x = g →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 2) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 2))
    (hh : ∀ x, s.cat x → B.colour x = h →
      (r ≤ x.1.val ∧ x.1.val ≤ r + 2) ∧ (c ≤ x.2.val ∧ x.2.val ≤ c + 2)) :
    ∀ z, s.cat z → B.colour z ≠ g → B.colour z ≠ h →
      ¬ ((r ≤ z.1.val ∧ z.1.val ≤ r + 2) ∧ (c ≤ z.2.val ∧ z.2.val ≤ c + 2)) := by
  intro z hz hzg hzh hzin
  obtain ⟨x, hx, hxg⟩ := s.exists_cat_colour g
  obtain ⟨y, hy, hyh⟩ := s.exists_cat_colour h
  have hxy : x ≠ y := fun e => hgh (by rw [← hxg, ← hyh, e])
  have hxz : x ≠ z := fun e => hzg (by rw [← e, hxg])
  have hyz : y ≠ z := fun e => hzh (by rw [← e, hyh])
  obtain ⟨hxr, hxc⟩ := hg x hx hxg
  obtain ⟨hyr, hyc⟩ := hh y hy hyh
  exact s.cap_3x3 hx hy hz hxy hxz hyz r c hxr hyr hzin.1 hxc hyc hzin.2

/-! ## Rules 8-9: counting (Hall) rules

Rows, columns and colours are all *separating*: two cats with the same row (or
column, or colour) are the same cat.  One abstract lemma therefore gives all
four counting rules: colours locked in rows / columns, and rows / columns made
of few colours. -/

/-- A map on cells that never sends two different cats to the same value. -/
def Separating (f : Cell n → Fin n) : Prop :=
  ∀ a b, s.cat a → s.cat b → f a = f b → a = b

theorem separating_row : s.Separating Prod.fst := fun _ _ ha hb h => s.cat_eq_of_row ha hb h
theorem separating_col : s.Separating Prod.snd := fun _ _ ha hb h => s.cat_eq_of_col ha hb h
theorem separating_colour : s.Separating B.colour := fun _ _ ha hb h => s.cat_eq_of_colour ha hb h

/-- **Hall, one class.** If every cat with `e`-value `g` has `f`-value `a`, then
every cat with `f`-value `a` has `e`-value `g`.  (`f`, `e` separating; a cat with
`e = g` exists.) -/
theorem hall1 {f e : Cell n → Fin n} (hf : s.Separating f) (a g : Fin n)
    (ex : ∃ y, s.cat y ∧ e y = g)
    (hg : ∀ x, s.cat x → e x = g → f x = a) :
    ∀ x, s.cat x → f x = a → e x = g := by
  intro x hx hxa
  obtain ⟨y, hy, hyg⟩ := ex
  have := hf x y hx hy (by rw [hxa, hg y hy hyg])
  rw [this]; exact hyg

/-- **Hall, two classes.** Two `e`-classes `g ≠ h` whose cats have `f`-values in
`{a, b}` own those two `f`-values: every cat with `f ∈ {a, b}` has `e ∈ {g, h}`. -/
theorem hall2 {f e : Cell n → Fin n} (hf : s.Separating f) (_he : s.Separating e)
    (a b g h : Fin n) (hgh : g ≠ h)
    (exg : ∃ y, s.cat y ∧ e y = g) (exh : ∃ y, s.cat y ∧ e y = h)
    (hg : ∀ x, s.cat x → e x = g → f x = a ∨ f x = b)
    (hh : ∀ x, s.cat x → e x = h → f x = a ∨ f x = b) :
    ∀ x, s.cat x → (f x = a ∨ f x = b) → e x = g ∨ e x = h := by
  intro x hx hxab
  obtain ⟨y, hy, hyg⟩ := exg
  obtain ⟨z, hz, hzh⟩ := exh
  have hyz : (f y).val ≠ (f z).val := fun e' =>
    hgh (by rw [← hyg, ← hzh, hf y z hy hz (Fin.ext e')])
  have hy' := hg y hy hyg
  have hz' := hh z hz hzh
  have hxv : (f x).val = a.val ∨ (f x).val = b.val := by
    rcases hxab with e' | e' <;> simp [e']
  have hyv : (f y).val = a.val ∨ (f y).val = b.val := by
    rcases hy' with e' | e' <;> simp [e']
  have hzv : (f z).val = a.val ∨ (f z).val = b.val := by
    rcases hz' with e' | e' <;> simp [e']
  have key : (f x).val = (f y).val ∨ (f x).val = (f z).val := by omega
  rcases key with e' | e'
  · left; rw [hf x y hx hy (Fin.ext e')]; exact hyg
  · right; rw [hf x z hx hz (Fin.ext e')]; exact hzh

/-- **Hall, three classes.** -/
theorem hall3 {f e : Cell n → Fin n} (hf : s.Separating f) (_he : s.Separating e)
    (a b c g h k : Fin n) (hgh : g ≠ h) (hgk : g ≠ k) (hhk : h ≠ k)
    (exg : ∃ y, s.cat y ∧ e y = g) (exh : ∃ y, s.cat y ∧ e y = h) (exk : ∃ y, s.cat y ∧ e y = k)
    (hg : ∀ x, s.cat x → e x = g → f x = a ∨ f x = b ∨ f x = c)
    (hh : ∀ x, s.cat x → e x = h → f x = a ∨ f x = b ∨ f x = c)
    (hk : ∀ x, s.cat x → e x = k → f x = a ∨ f x = b ∨ f x = c) :
    ∀ x, s.cat x → (f x = a ∨ f x = b ∨ f x = c) → e x = g ∨ e x = h ∨ e x = k := by
  intro x hx hxabc
  obtain ⟨y, hy, hyg⟩ := exg
  obtain ⟨z, hz, hzh⟩ := exh
  obtain ⟨w, hw, hwk⟩ := exk
  have hyz : (f y).val ≠ (f z).val := fun e' =>
    hgh (by rw [← hyg, ← hzh, hf y z hy hz (Fin.ext e')])
  have hyw : (f y).val ≠ (f w).val := fun e' =>
    hgk (by rw [← hyg, ← hwk, hf y w hy hw (Fin.ext e')])
  have hzw : (f z).val ≠ (f w).val := fun e' =>
    hhk (by rw [← hzh, ← hwk, hf z w hz hw (Fin.ext e')])
  have hxv : (f x).val = a.val ∨ (f x).val = b.val ∨ (f x).val = c.val := by
    rcases hxabc with e' | e' | e' <;> simp [e']
  have hyv : (f y).val = a.val ∨ (f y).val = b.val ∨ (f y).val = c.val := by
    rcases hg y hy hyg with e' | e' | e' <;> simp [e']
  have hzv : (f z).val = a.val ∨ (f z).val = b.val ∨ (f z).val = c.val := by
    rcases hh z hz hzh with e' | e' | e' <;> simp [e']
  have hwv : (f w).val = a.val ∨ (f w).val = b.val ∨ (f w).val = c.val := by
    rcases hk w hw hwk with e' | e' | e' <;> simp [e']
  have key : (f x).val = (f y).val ∨ (f x).val = (f z).val ∨ (f x).val = (f w).val := by omega
  rcases key with e' | e' | e'
  · left; rw [hf x y hx hy (Fin.ext e')]; exact hyg
  · right; left; rw [hf x z hx hz (Fin.ext e')]; exact hzh
  · right; right; rw [hf x w hx hw (Fin.ext e')]; exact hwk

/-! ## Rule 11: a rectangle that cannot be empty -/

/-- The two cats of two consecutive rows cannot both sit in the last two columns
(they would touch), so a `2 × (n-2)` block at the left edge contains a cat.
Stated for the first two rows and the two rightmost columns. -/
theorem edge_2xn (i j : Fin n) (hij : j.val = i.val + 1) :
    (s.col i).val + 2 ≤ n - 1 ∨ (s.col j).val + 2 ≤ n - 1 := by
  have h := s.knight i j hij
  have hi := (s.col i).isLt
  have hj := (s.col j).isLt
  omega

/-! ## Rule 12: a what-if is sound -/

/-- If assuming a cat on `x` leads to a contradiction, `x` is empty.  (Trivial,
but this is the licence for every what-if move in the game.) -/
theorem what_if {x : Cell n} (h : s.cat x → False) : ¬ s.cat x := h

end Solution
end Meowdoku
