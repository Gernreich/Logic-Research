# Modus ponens in sixteen values

What happens to modus ponens when P and Q are not just TRUE or FALSE, but
each one of the sixteen two-input functions, combined row by row as in Gates
of Gates? These are the answers, from September 2026. Like the rest of this
folder's search ([`inference-search.md`](inference-search.md)), they are not a
new rule: they are classical modus ponens and resolution, seen on four rows at
once.

Values are numbered in the gate order of `lambda16.txt`. P is value 6, Q is
value 3, and "A ≤ B" means A implies B on every row.

## From P and P→Q

Given P and R = P→Q, which Q are possible?

* **The rule:** `P∧R ≤ Q ≤ R`. On rows where P is true, Q is pinned (it equals
  R there); on rows where P is false, Q is free. The Q that fit are exactly
  that interval.
* **Possible only when `P∨R = TRUE`.** On a row where p = 0, r = P→Q is always
  1, so a pair with p = 0 and r = 0 on any row is impossible. Of the 256
  pairs (P, R), 81 are possible (3⁴: three allowed combinations per row).
* **256 answers in all** (4⁴), one for every (P, Q), since each (P, Q) gives
  exactly one R. A P with k false rows leaves 2ᵏ answers, on
  C(4, k)·2⁴⁻ᵏ pairs: 16, 32, 24, 8 and 1 pairs for k = 0 to 4.
* **Classical modus ponens is the case P = TRUE.** Every row is pinned and
  exactly one Q is left: Q = R.
* **The tautology still holds:** `(P ∧ (P→Q)) → Q` is TRUE for all 256 pairs,
  because it is TRUE on every row.

## From P∨Q and P→Q

Replacing the first premise P by the weaker P∨Q gives back all of Q:

* **`(P∨Q) ∧ (P→Q) = Q`** for all 256 pairs. On rows where P is true, P→Q
  reduces to Q; on rows where P is false, P∨Q does. Classical modus ponens
  combines to the smaller P∧Q instead.
* **Eight first premises work** in place of P: exactly the values inside
  P∨Q, with P∨Q the weakest and P among them.
* **It pins Q on every possible pair (81 of 81);** starting from P pins it
  only when P is TRUE (16 pairs).

This is resolution, `P∨Q, ¬P∨Q ⊢ Q`, or proof by cases.

## Files

| File | What it is |
|---|---|
| `modus_ponens_16.py` | checks every number on this page; stops with an error if one changes |
| `modus-ponens-16.html` | interactive page for P and P→Q: the rule in squares, an explorer for any pair, the 16 × 16 map, the counts |
| `modus-ponens-or.html` | interactive page for P∨Q and P→Q: the identity in squares, the eight premises that work, a picker for any P and Q |

Both pages compute everything in the browser and check the counts when they
load. They are self-contained apart from Google Fonts; open them in any
browser. The public site serves copies from `docs/`:
[Modus Ponens in Sixteen Values](https://gernreich.github.io/Logic-Research/modus-ponens-16.html)
and [Modus Ponens from P∨Q](https://gernreich.github.io/Logic-Research/modus-ponens-or.html).
The files here are the source; after changing one, copy it over:

    cp modus-ponens-16.html modus-ponens-or.html ../docs/

Run the checks with `python3 modus_ponens_16.py`.
