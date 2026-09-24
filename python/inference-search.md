# The search for a new inference rule: it came back empty

The 2019 enumeration in this folder was built to answer one question. Take
modus ponens, `((P → Q) ∧ P) → Q`, let every connective be any of the sixteen
gates and every input any truth table, and keep the tautologies. Somewhere in
that list, is there a rule like modus ponens or modus tollens that nobody has
found? The list was too long to read, so the question was never answered.

It has been answered now, in September 2026, and **the search came back
empty.** Every rule it produced is a classical one: modus ponens, modus
tollens, the other Stoic "indemonstrables", hypothetical syllogism, or a
short chain of those steps. That held for two variables, for three, for two
premises and for three, and for premises that tie all three variables
together. Nothing below is a new rule.

That result could have been predicted. Propositional logic is complete
(Post, 1921): every valid rule already follows from the classical ones. What
a search can still turn up is a rule nobody has *named*, and it did not find
one worth naming either.

## The count

Modus ponens has the shape `((A ∘ B) ∘ C) ∘ D`. With every gate at each `∘`
and every truth table at each input:

| Variables | Expressions | Tautologies |
|---|---|---|
| two (P, Q) | 268,435,456 (2²⁸) | **54,008,320** (20.12%) |
| three (P, Q, R) | 17,592,186,044,416 | **2,346,912,555,520** (13.34%) |

The 2019 full run counted 37,231,104 for two variables. The difference is
exactly 16⁶ = 16,777,216: the expressions whose outer connective is TRUE,
which the `last=16` quirk in `boolean16.py` never counts.

Almost all of these tautologies are trivially true, or the same rule written
a different way: 4,096 spellings of `A ∘ B` make only 16 truth tables. The
rest of this page removes both.

## Two variables

A rule "premise, premise ⊢ conclusion" is valid when the premises together
imply the conclusion on every row. A rule is trivial when the premises
contradict each other, when one premise alone gives the conclusion, or when
the conclusion is TRUE. A *family* is a rule together with every renaming of
it: P and Q swapped, either one negated.

| Stage | Count |
|---|---|
| `(A ∘ B) ∧ C → D`, every gate and table | 1,048,576 expressions, 633,512 tautologies |
| inputs only P, Q, ¬P, ¬Q | 4,096 expressions, 2,368 tautologies |
| as distinct rules, not spellings | 144 |
| non-trivial | **16** |
| families | **2** |

**Family 2**, the modus ponens family: `P→Q, P ⊢ Q` (modus ponens),
`P→Q, ¬Q ⊢ ¬P` (modus tollens), `¬(P∧Q), P ⊢ ¬Q`, `P∨Q, ¬P ⊢ Q`
(disjunctive syllogism), and the same with P and Q swapped.

**Family 1**, the biconditional family: `P⊕Q, P ⊢ ¬Q`, `P⊕Q, ¬P ⊢ Q`,
`P↔Q, P ⊢ Q`, `P↔Q, ¬P ⊢ ¬Q`, and the same with P and Q swapped.

These are Chrysippus's five indemonstrable arguments from the third century
BC (modus ponens, modus tollens, "not both; one; so not the other", and the
two exclusive-or rules), plus disjunctive syllogism with an inclusive "or" and
the biconditional rule. Stoic disjunction was exclusive (and, the source
adds, not truth-functional), so the match is in form.

Letting both premises and the conclusion be any of the sixteen tables adds
nothing new: 30 premise pairs in 6 families, the rules above plus
conjunction and definitions such as "at least one" and "not both" giving
"exactly one".

## Three variables, statements linking two of them

Here every premise and the conclusion is a gate on two of P, Q, R (38 tables),
the shape of a syllogism.

**Two premises.** 54,872 combinations, 23,191 valid, 2,292 non-trivial, 1,560
whose premises mention all three variables. Keeping each premise pair's
strongest conclusions leaves 348 rules in **9 families**. Only three of the nine families
have genuine relations for both premises:

* `P→Q, Q→R ⊢ P→R`: hypothetical syllogism, which Theophrastus stated in
  term-logical form. Resolution, `P∨Q, ¬P∨R ⊢ Q∨R`, the rule behind automated
  theorem proving, is the same family renamed.
* `P↔Q, P↔R ⊢ Q↔R`: transitivity of ↔, including `P⊕Q, P⊕R ⊢ Q↔R`.
* `P→Q, P↔R ⊢ R→Q`: substituting equivalents.

The other six have a premise like `P∧R`, which states two facts: each is a
two-variable rule, or plain bookkeeping of facts, with a third variable
carried along.

**Three premises.** Of 8,436 premise sets, 728 need all three premises for
some conclusion, giving 1,128 rules in **29 families**. Constructive dilemma,
`P→R, Q→R, P∨Q ⊢ R`, is one. **All 29 split into two steps of two premises each**
through an intermediate two-variable statement: constructive dilemma is
`P→R, P∨Q ⊢ Q∨R`, then `Q∨R, Q→R ⊢ R`. That chaining is the Stoic cut rule
(their third *thema*), so three premises add nothing that two did not have.
The split test is not a formality: with premises outside the 38 it finds
valid rules that do not split.

## Three variables, premises tying all three together

The last place a new rule could have been hiding: premises that depend on all
three variables at once, such as `P⊕Q⊕R`. Of the 256 tables, 218 do, and 34
of those say nothing about any pair on its own.

A rule counts as **irreducible** when its conclusion does not follow from
what the premises say about pairs, so none of the searches above could have
found it. There are **14,814** such rules, in 380 families. Sorted by the
second premise, as modus ponens is:

| Second premise | Rules | What every one of them is |
|---|---|---|
| a plain fact | 336 | the fact substituted into the first premise (336 of 336). Boole's expansion (1854), of which modus ponens is the simplest case |
| two facts | 768 | both facts substituted (768 of 768) |
| an equivalence | 600 | one variable substituted for the other (600 of 600) |
| an implication | 768 | 96 are an earlier rule under a shared hypothesis, among them Frege's second axiom from the *Begriffsschrift* (1879), `P→(Q→R), P→Q ⊢ P→R`; the other 672 split into two cases |
| also three-way | 12,342 | below |

Restricting the last row to natural connectives, those written with each
variable once (`P∨Q∨R`, `P⊕(Q∧R)`, `P→(Q↔R)` and so on), leaves 2,868 rules in
80 families. **47** are an old two-variable elimination rule with compound
parts: `P∨(Q↔R), P∨(Q⊕R) ⊢ P` is "X or A, X or not A, so X" with A = `Q↔R`.
The other **33** each need exactly two rounds of classical steps (split off a
fact, substitute it, apply a two-variable rule) and none can be done in one.
**All 14,814** irreducible rules are derived within six rounds.

The tidiest three-way rule is `P⊕Q⊕R, P ⊢ Q↔R`: fix one input of a three-way
XOR and the other two must match. It is substitution, the first row of the
table, and not new.

## How the numbers were checked

Every count on this page is asserted by the script that produces it; a
script stops with an error if any number changes. Three of the checks were
wrong at first, and the fixes matter for how far to trust the rest:

* **Two cases.** For a valid rule whose second premise is "x or y", each case
  must follow, so the 672 two-case rules could not have come out otherwise.
  The split is reported, not offered as evidence.
* **Chains.** An early version counted the premises themselves as derived,
  which made every rule pass. Now the conclusion must follow from derived
  facts and two-variable statements alone. With zero or one round of steps,
  none of the 33 is derived, which shows the check can fail.
* **What "derived" proves.** The steps include modus ponens on compound parts,
  which is strong. By completeness every valid rule is derivable anyway, so
  the chain result measures depth (two steps) rather than proving anything
  new.

## What was not searched

Four or more variables; conclusions that themselves tie three variables
together; more than three premises. Completeness says none of these can hold
a new *valid* rule. They could hold a useful rule nobody has named, and this
search does not rule that out.

## Files

| File | What it does | Time |
|---|---|---|
| `truthtables.py` | truth tables on two or three variables, gates, renaming, families, readable formulas | — |
| `tautology_count.py` | the two tautology counts, and the 2019 figure | under a second |
| `rules_two_variables.py` | the two-variable filter chain and both families | about a second |
| `rules_three_variables.py` | two and three premises linking pairs of P, Q, R; the split test | about 3 seconds |
| `rules_three_way.py` | premises tying all three together; tiers, eliminations, chains | about 45 seconds |

Modus ponens with sixteen-valued P and Q, a related question, is in
[`modus-ponens-16.md`](modus-ponens-16.md).

    python3 tautology_count.py
    python3 rules_two_variables.py
    python3 rules_three_variables.py
    python3 rules_three_way.py

## Sources

* Chrysippus's indemonstrables, Stoic exclusive disjunction, Theophrastus's
  hypothetical syllogisms and the Stoic *themata*: [Ancient Logic](https://plato.stanford.edu/entries/logic-ancient/),
  *Stanford Encyclopedia of Philosophy*.
* Frege's Axiom 2: [Frege's Logic](https://plato.stanford.edu/entries/frege-logic/),
  *Stanford Encyclopedia of Philosophy*.
* Boole's expansion, *Laws of Thought* (1854): [Boole's expansion theorem](https://en.wikipedia.org/wiki/Boole%27s_expansion_theorem).
* Post's completeness proof (1921): [Emil Leon Post](https://en.wikipedia.org/wiki/Emil_Leon_Post).
