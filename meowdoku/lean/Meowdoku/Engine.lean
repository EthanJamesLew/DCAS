import Meowdoku.Rules

/-!
# Meowdoku: the game engine

A *state* is a candidate grid `Cand n`: the cells that may still hold a cat.
A *move* is a computable function on states.  Every move below comes with a
soundness theorem: if every solution is consistent with the state before the
move, every solution is consistent with the state after it.  Playing the game
is chaining moves; Lean checks the play by evaluating it.
-/

namespace Meowdoku

variable {n : Nat}

/-- Linear index of a cell. -/
def idx (x : Cell n) : Nat := x.1.val * n + x.2.val

theorem idx_inj {x y : Cell n} (h : idx x = idx y) : x = y := by
  obtain ⟨⟨a, ha⟩, ⟨b, hb⟩⟩ := x
  obtain ⟨⟨c, hc⟩, ⟨d, hd⟩⟩ := y
  simp only [idx] at h
  have h1 : (n * a + b) % n = (n * c + d) % n := by
    rw [Nat.mul_comm n a, Nat.mul_comm n c]; exact congrArg (· % n) h
  rw [Nat.mul_add_mod, Nat.mul_add_mod, Nat.mod_eq_of_lt hb, Nat.mod_eq_of_lt hd] at h1
  subst h1
  have h2 : a * n = c * n := by omega
  have h3 : a = c := Nat.eq_of_mul_eq_mul_right (by omega) h2
  subst h3; rfl

/-- All cells of the board. -/
def cells (n : Nat) : List (Cell n) :=
  (List.finRange n).flatMap fun r => (List.finRange n).map fun c => (r, c)

theorem mem_cells (x : Cell n) : x ∈ cells n := by
  unfold cells
  rw [List.mem_flatMap]
  exact ⟨x.1, List.mem_finRange _, List.mem_map.2 ⟨x.2, List.mem_finRange _, rfl⟩⟩

/-- Candidate grid, stored as a bitmask of the *crossed-out* cells
(so that a fresh board is the number 0 and states are plain numbers). -/
structure Cand (n : Nat) where
  crossed : Nat

/-- `cand.has x = true` iff `x` may still hold a cat. -/
def Cand.has (cand : Cand n) (x : Cell n) : Bool := !(cand.crossed.testBit (idx x))

/-- The starting state: everything is possible. -/
def Cand.all (n : Nat) : Cand n := ⟨0⟩

theorem Cand.has_all (x : Cell n) : (Cand.all n).has x = true := by
  simp [Cand.has, Cand.all, Nat.zero_testBit]

namespace Solution

variable {B : Board n}

/-- The solution `s` is consistent with the state `cand`. -/
def Holds (s : Solution B) (cand : Cand n) : Prop := ∀ r, cand.has (r, s.col r) = true

theorem Holds.cat {s : Solution B} {cand : Cand n} (h : s.Holds cand) {x : Cell n}
    (hx : s.cat x) : cand.has x = true := by
  have : (x.1, s.col x.1) = x := by
    obtain ⟨a, b⟩ := x
    unfold Solution.cat at hx
    simp only at hx
    rw [hx]
  rw [← this]; exact h x.1

end Solution

/-- Every solution of `B` is consistent with `cand`. -/
def Sound (B : Board n) (cand : Cand n) : Prop := ∀ s : Solution B, s.Holds cand

theorem Sound.all (B : Board n) : Sound B (Cand.all n) := fun _ _ => Cand.has_all _

/-! ## Units -/

/-- A unit is a set of cells (as a Boolean predicate) that always contains a cat. -/
structure Unit (B : Board n) where
  mem : Cell n → Bool
  has_cat : ∀ s : Solution B, ∃ y, s.cat y ∧ mem y = true

def rowU (B : Board n) (r : Fin n) : Unit B :=
  ⟨fun y => decide (y.1 = r), fun s => ⟨(r, s.col r), rfl, by simp⟩⟩

def colU (B : Board n) (c : Fin n) : Unit B :=
  ⟨fun y => decide (y.2 = c), fun s => by
    obtain ⟨y, hy, hc⟩ := s.exists_cat_col c
    exact ⟨y, hy, by simp [hc]⟩⟩

def colourU (B : Board n) (g : Fin n) : Unit B :=
  ⟨fun y => decide (B.colour y = g), fun s => by
    obtain ⟨y, hy, hg⟩ := s.exists_cat_colour g
    exact ⟨y, hy, by simp [hg]⟩⟩

/-! ## Moves -/

/-- The bits of all cells that `p` flags. -/
def bitsOf (p : Cell n → Bool) : Nat :=
  (cells n).foldl (fun m x => if p x then m ||| (1 <<< idx x) else m) 0

theorem testBit_foldl_of {p : Cell n → Bool} {x : Cell n} (hx : p x = false) :
    ∀ (l : List (Cell n)) (m : Nat), m.testBit (idx x) = false →
      (l.foldl (fun m y => if p y then m ||| (1 <<< idx y) else m) m).testBit (idx x) = false := by
  intro l
  induction l with
  | nil => intro m hm; exact hm
  | cons y l ih =>
    intro m hm
    simp only [List.foldl_cons]
    apply ih
    split
    · rename_i hpy
      rw [Nat.testBit_or, hm, Nat.one_shiftLeft, Nat.testBit_two_pow]
      simp only [Bool.false_or, decide_eq_false_iff_not]
      intro e
      have := idx_inj e
      subst this
      rw [hpy] at hx; exact absurd hx (by decide)
    · exact hm

theorem testBit_bitsOf_of {p : Cell n → Bool} {x : Cell n} (hx : p x = false) :
    (bitsOf p).testBit (idx x) = false :=
  testBit_foldl_of hx (cells n) 0 (Nat.zero_testBit _)

/-- Remove every cell that `p` flags. -/
def Cand.removeWhere (cand : Cand n) (p : Cell n → Bool) : Cand n :=
  ⟨cand.crossed ||| bitsOf p⟩

theorem Cand.has_removeWhere_of {cand : Cand n} {p : Cell n → Bool} {x : Cell n}
    (h : cand.has x = true) (hp : p x = false) : (cand.removeWhere p).has x = true := by
  simp only [Cand.has, Cand.removeWhere, Nat.testBit_or, Bool.not_eq_true'] at *
  rw [Bool.or_eq_false_iff]
  exact ⟨h, testBit_bitsOf_of hp⟩

theorem holds_removeWhere {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (p : Cell n → Bool) (hp : ∀ x, p x = true → ¬ s.cat x) : s.Holds (cand.removeWhere p) := by
  intro r
  have h1 := hs r
  have h2 : p (r, s.col r) = false := by
    cases hpx : p (r, s.col r)
    · rfl
    · exact absurd (s.cat_row r) (hp _ hpx)
  exact Cand.has_removeWhere_of h1 h2

/-- **Common attack.** Remove every cell attacked by all remaining cells of the unit. -/
def commonAttack {B : Board n} (U : Unit B) (cand : Cand n) : Cand n :=
  cand.removeWhere fun x =>
    decide (∀ r c, cand.has (r, c) = true → U.mem (r, c) = true → Attacks (r, c) x)

theorem holds_commonAttack {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (U : Unit B) : s.Holds (commonAttack U cand) := by
  apply holds_removeWhere hs
  intro x hx
  have hx' := of_decide_eq_true hx
  obtain ⟨y, hy, hyU⟩ := U.has_cat s
  exact s.not_cat_of_attacks hy (hx' y.1 y.2 (hs.cat hy) hyU)

/-- **Colour mates.** Remove every cell whose colour is shared by all remaining cells of the
unit (and which is none of them): the unit's cat is a different cell of that colour. -/
def colourMates {B : Board n} (U : Unit B) (cand : Cand n) : Cand n :=
  cand.removeWhere fun x =>
    decide (∀ r c, cand.has (r, c) = true → U.mem (r, c) = true →
      (r, c) ≠ x ∧ B.colour (r, c) = B.colour x)

theorem holds_colourMates {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (U : Unit B) : s.Holds (colourMates U cand) := by
  apply holds_removeWhere hs
  intro x hx
  have hx' := of_decide_eq_true hx
  obtain ⟨y, hy, hyU⟩ := U.has_cat s
  obtain ⟨hne, hcol⟩ := hx' y.1 y.2 (hs.cat hy) hyU
  exact s.colour_exclusive hy (Ne.symm hne) hcol.symm

/-- **Place the cat** of a unit that has a single candidate: common attack + colour mates. -/
def placeCat {B : Board n} (U : Unit B) (cand : Cand n) : Cand n :=
  colourMates U (commonAttack U cand)

theorem holds_placeCat {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (U : Unit B) : s.Holds (placeCat U cand) :=
  holds_colourMates (holds_commonAttack hs U) U

/-- A separating coordinate: rows, columns, or colours. -/
structure Coord (B : Board n) where
  f : Cell n → Fin n
  sep : ∀ s : Solution B, s.Separating f
  ex : ∀ (s : Solution B) (v : Fin n), ∃ y, s.cat y ∧ f y = v

def rowC (B : Board n) : Coord B :=
  ⟨Prod.fst, fun s => s.separating_row, fun s r => ⟨(r, s.col r), rfl, rfl⟩⟩
def colC (B : Board n) : Coord B :=
  ⟨Prod.snd, fun s => s.separating_col, fun s c => s.exists_cat_col c⟩
def colourC (B : Board n) : Coord B :=
  ⟨B.colour, fun s => s.separating_colour, fun s g => s.exists_cat_colour g⟩

/-- **Hall, one class** (a colour locked in one row, a row made of one colour, ...):
if every remaining cell with `e = g` has `f = a`, remove the cells with `f = a` and `e ≠ g`. -/
def hall1 {B : Board n} (F E : Coord B) (a g : Fin n) (cand : Cand n) : Cand n :=
  if ∀ r c, cand.has (r, c) = true → E.f (r, c) = g → F.f (r, c) = a then
    cand.removeWhere fun x => decide (F.f x = a ∧ E.f x ≠ g)
  else cand

theorem holds_hall1 {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (F E : Coord B) (a g : Fin n) : s.Holds (hall1 F E a g cand) := by
  unfold hall1
  split
  · rename_i hpre
    apply holds_removeWhere hs
    intro x hx
    have ⟨hxa, hxg⟩ := of_decide_eq_true hx
    intro hcat
    apply hxg
    exact s.hall1 (F.sep s) a g (E.ex s g)
      (fun y hy hyg => hpre y.1 y.2 (hs.cat hy) hyg) x hcat hxa
  · exact hs

/-- **Hall, two classes.** -/
def hall2 {B : Board n} (F E : Coord B) (a b g h : Fin n) (cand : Cand n) : Cand n :=
  if g ≠ h ∧ ∀ r c, cand.has (r, c) = true → (E.f (r, c) = g ∨ E.f (r, c) = h) →
      (F.f (r, c) = a ∨ F.f (r, c) = b) then
    cand.removeWhere fun x => decide ((F.f x = a ∨ F.f x = b) ∧ E.f x ≠ g ∧ E.f x ≠ h)
  else cand

theorem holds_hall2 {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (F E : Coord B) (a b g h : Fin n) : s.Holds (hall2 F E a b g h cand) := by
  unfold hall2
  split
  · rename_i hpre
    obtain ⟨hgh, hpre⟩ := hpre
    apply holds_removeWhere hs
    intro x hx
    have ⟨hxab, hxg, hxh⟩ := of_decide_eq_true hx
    intro hcat
    have := s.hall2 (F.sep s) (E.sep s) a b g h hgh (E.ex s g) (E.ex s h)
      (fun y hy hyg => hpre y.1 y.2 (hs.cat hy) (Or.inl hyg))
      (fun y hy hyh => hpre y.1 y.2 (hs.cat hy) (Or.inr hyh)) x hcat hxab
    rcases this with e | e
    · exact hxg e
    · exact hxh e
  · exact hs

/-- **Hall, three classes.** -/
def hall3 {B : Board n} (F E : Coord B) (a b c g h k : Fin n) (cand : Cand n) : Cand n :=
  if g ≠ h ∧ g ≠ k ∧ h ≠ k ∧ ∀ r c', cand.has (r, c') = true →
      (E.f (r, c') = g ∨ E.f (r, c') = h ∨ E.f (r, c') = k) →
      (F.f (r, c') = a ∨ F.f (r, c') = b ∨ F.f (r, c') = c) then
    cand.removeWhere fun x =>
      decide ((F.f x = a ∨ F.f x = b ∨ F.f x = c) ∧ E.f x ≠ g ∧ E.f x ≠ h ∧ E.f x ≠ k)
  else cand

theorem holds_hall3 {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    (F E : Coord B) (a b c g h k : Fin n) : s.Holds (hall3 F E a b c g h k cand) := by
  unfold hall3
  split
  · rename_i hpre
    obtain ⟨hgh, hgk, hhk, hpre⟩ := hpre
    apply holds_removeWhere hs
    intro x hx
    have ⟨hxabc, hxg, hxh, hxk⟩ := of_decide_eq_true hx
    intro hcat
    have := s.hall3 (F.sep s) (E.sep s) a b c g h k hgh hgk hhk (E.ex s g) (E.ex s h) (E.ex s k)
      (fun y hy hyg => hpre y.1 y.2 (hs.cat hy) (Or.inl hyg))
      (fun y hy hyh => hpre y.1 y.2 (hs.cat hy) (Or.inr (Or.inl hyh)))
      (fun y hy hyk => hpre y.1 y.2 (hs.cat hy) (Or.inr (Or.inr hyk))) x hcat hxabc
    rcases this with e | e | e
    · exact hxg e
    · exact hxh e
    · exact hxk e
  · exact hs

/-! ## What-if -/

/-- Assume a cat on `x`: remove everything it attacks and the rest of its colour. -/
def assume (B : Board n) (x : Cell n) (cand : Cand n) : Cand n :=
  cand.removeWhere fun y => decide (Attacks x y ∨ (y ≠ x ∧ B.colour y = B.colour x))

theorem holds_assume {B : Board n} {s : Solution B} {cand : Cand n} (hs : s.Holds cand)
    {x : Cell n} (hx : s.cat x) : s.Holds (assume B x cand) := by
  intro r
  have h1 := hs r
  have h2 : decide (Attacks x (r, s.col r) ∨ ((r, s.col r) ≠ x ∧ B.colour (r, s.col r) = B.colour x)) = false := by
    apply decide_eq_false
    rintro (hatt | ⟨hne, hcol⟩)
    · exact s.not_cat_of_attacks hx hatt (s.cat_row r)
    · exact s.colour_exclusive hx hne hcol (s.cat_row r)
  exact Cand.has_removeWhere_of h1 h2

/-- Some unit has no candidate left: no solution is consistent with `cand`. -/
def dead (B : Board n) (cand : Cand n) : Bool :=
  decide (∃ r, ∀ c, cand.has (r, c) = false) ||
  decide (∃ c, ∀ r, cand.has (r, c) = false) ||
  decide (∃ g, ∀ r c, B.colour (r, c) = g → cand.has (r, c) = false)

theorem not_holds_of_dead {B : Board n} {cand : Cand n} (hd : dead B cand = true) (s : Solution B) :
    ¬ s.Holds cand := by
  intro hs
  unfold dead at hd
  simp only [Bool.or_eq_true, decide_eq_true_eq] at hd
  rcases hd with (⟨r, hr⟩ | ⟨c, hc⟩) | ⟨g, hg⟩
  · have := hs r; rw [hr] at this; exact Bool.false_ne_true this
  · obtain ⟨y, hy, hyc⟩ := s.exists_cat_col c
    have := hs.cat hy
    obtain ⟨y1, y2⟩ := y
    simp only at hyc; subst hyc
    rw [hc] at this; exact Bool.false_ne_true this
  · obtain ⟨y, hy, hyg⟩ := s.exists_cat_colour g
    have := hs.cat hy
    rw [hg y.1 y.2 hyg] at this; exact Bool.false_ne_true this

/-- A move together with its soundness proof: it never discards a cell that holds a cat of
any solution consistent with the state. -/
structure Move (B : Board n) where
  run : Cand n → Cand n
  holds : ∀ (s : Solution B) (cand : Cand n), s.Holds cand → s.Holds (run cand)

/-- Play a list of moves. -/
def play {B : Board n} (ms : List (Move B)) (cand : Cand n) : Cand n :=
  ms.foldl (fun c m => m.run c) cand

theorem holds_play {B : Board n} {s : Solution B} (ms : List (Move B)) :
    ∀ cand, s.Holds cand → s.Holds (play ms cand) := by
  induction ms with
  | nil => intro cand h; exact h
  | cons m ms ih => intro cand h; exact ih _ (m.holds s cand h)

theorem sound_play {B : Board n} (ms : List (Move B)) : Sound B (play ms (Cand.all n)) :=
  fun s => holds_play ms _ (Sound.all B s)

/-! ### The moves of the game -/

def Move.commonAttack {B : Board n} (U : Unit B) : Move B :=
  ⟨Meowdoku.commonAttack U, fun _ _ hs => holds_commonAttack hs U⟩

def Move.colourMates {B : Board n} (U : Unit B) : Move B :=
  ⟨Meowdoku.colourMates U, fun _ _ hs => holds_colourMates hs U⟩

def Move.placeCat {B : Board n} (U : Unit B) : Move B :=
  ⟨Meowdoku.placeCat U, fun _ _ hs => holds_placeCat hs U⟩

def Move.hall1 {B : Board n} (F E : Coord B) (a g : Fin n) : Move B :=
  ⟨Meowdoku.hall1 F E a g, fun _ _ hs => holds_hall1 hs F E a g⟩

def Move.hall2 {B : Board n} (F E : Coord B) (a b g h : Fin n) : Move B :=
  ⟨Meowdoku.hall2 F E a b g h, fun _ _ hs => holds_hall2 hs F E a b g h⟩

def Move.hall3 {B : Board n} (F E : Coord B) (a b c g h k : Fin n) : Move B :=
  ⟨Meowdoku.hall3 F E a b c g h k, fun _ _ hs => holds_hall3 hs F E a b c g h k⟩

/-- **What-if.** Assume a cat on `x`, play `ms`; if some unit dies, `x` is empty. -/
def Move.whatIf {B : Board n} (x : Cell n) (ms : List (Move B)) : Move B :=
  ⟨fun cand => if dead B (play ms (assume B x cand)) then cand.removeWhere (fun y => decide (y = x)) else cand,
   fun s cand hs => by
    split
    · rename_i hd
      apply holds_removeWhere hs
      intro y hy hcat
      have hyx : y = x := of_decide_eq_true hy
      subst hyx
      exact not_holds_of_dead hd s (holds_play ms _ (holds_assume hs hcat))
    · exact hs⟩

/-! ## Reading off the answer -/

/-- If the final state leaves exactly the cells of `sol`, every solution is `sol`. -/
theorem unique_of_play {B : Board n} (ms : List (Move B)) (sol : Fin n → Fin n)
    (h : ∀ r c, (play ms (Cand.all n)).has (r, c) = true → c = sol r) :
    ∀ s : Solution B, s.col = sol := by
  intro s
  funext r
  exact h r (s.col r) (sound_play ms s r)

/-- Pretty-print a state: `#` candidate, `.` crossed out. -/
def Cand.show (cand : Cand n) : String :=
  String.intercalate "\n" <| (List.finRange n).map fun r =>
    String.ofList <| (List.finRange n).map fun c => if cand.has (r, c) then '#' else '.'

/-- The cells a move removes from a state. -/
def Move.removed {B : Board n} (m : Move B) (cand : Cand n) : List (Cell n) :=
  ((List.finRange n).flatMap fun r => (List.finRange n).map fun c => (r, c)).filter
    fun x => cand.has x && !((m.run cand).has x)

end Meowdoku
