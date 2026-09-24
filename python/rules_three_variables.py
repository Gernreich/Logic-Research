#!/usr/bin/env python3
"""Inference rules on three variables whose statements each link two of them.

Every premise and the conclusion is a gate on two of P, Q, R: 38 distinct
tables. That is the shape of a syllogism, and where hypothetical syllogism
(P->Q, Q->R |- P->R) and resolution live. Premises about a single variable
(P, Q AND R, ...) are allowed; the rules with genuine relations are flagged.

TWO PREMISES
------------
Kept when non-trivial (as in rules_two_variables.py) and the premises between
them mention all three variables, so the rule is not a two-variable rule with a
third variable carried along. For each premise pair only its strongest
conclusions are kept.

THREE PREMISES
--------------
Kept when the three are distinct, consistent, mention all three variables,
and no two of them give the conclusion. Then each rule is tested for
splitting into two two-premise steps through one intermediate statement:
two premises give some I (one of the 38), and I with the third gives the
conclusion. That chaining is the Stoic cut rule. The test is shown able to
fail by finding a valid rule, with premises outside the 38, that does not
split.

USAGE
-----
    python3 rules_three_variables.py        about 3 seconds
"""

import itertools
import random

from truthtables import Space, families, readable, check

S = Space(3)
P, Q, R = S.var
F2 = S.pairwise()


def strongest(conclusions):
    return [c for c in conclusions if not any(d != c and S.implies(d, c) for d in conclusions)]


def is_fact(t):
    """A constant, a literal, or a conjunction of literals: facts, not a relation."""
    ones = bin(t).count('1')
    return ones in (0, 2, 4, 8) and (t in S.literals or ones != 4)


def show(rule):
    return ', '.join(S.name(t) for t in rule[:-1]) + '  ⊢  ' + S.name(rule[-1])


def two_premise_rules():
    valid = [(a, b, c) for a in F2 for b in F2 for c in F2 if S.implies(a & b, c)]
    nontrivial = [r for r in valid if r[0] & r[1] and r[2] != S.all
                  and not S.implies(r[0], r[2]) and not S.implies(r[1], r[2])]
    spanning = [r for r in nontrivial if S.depends_on(r[0]) | S.depends_on(r[1]) == {0, 1, 2}]
    by_pair = {}
    for a, b, c in spanning:
        by_pair.setdefault(tuple(sorted((a, b))), set()).add(c)
    rules = [(a, b, c) for (a, b), cs in by_pair.items() for c in strongest(cs)]
    return valid, nontrivial, spanning, by_pair, rules


def three_premise_rules():
    rules = []
    for a, b, c in itertools.combinations(F2, 3):
        abc = a & b & c
        if not abc or S.depends_on(a) | S.depends_on(b) | S.depends_on(c) != {0, 1, 2}:
            continue
        concl = [d for d in F2 if d != S.all and S.implies(abc, d)
                 and not S.implies(a & b, d) and not S.implies(a & c, d) and not S.implies(b & c, d)]
        rules += [(a, b, c, d) for d in strongest(concl)]
    return rules


def split(rule):
    """Two premises give an intermediate I (one of the 38); I and the third give the conclusion."""
    a, b, c, d = rule
    for (x, y), z in (((a, b), c), ((a, c), b), ((b, c), a)):
        for i in F2:
            if S.implies(x & y, i) and S.implies(i & z, d):
                return x, y, i, z
    return None


if __name__ == '__main__':
    check('tables linking at most two variables', len(F2), 38)

    valid, nontrivial, spanning, by_pair, rules2 = two_premise_rules()
    fam2 = families(S, rules2)
    print('TWO PREMISES')
    print(f'  premise, premise, conclusion: {len(F2) ** 3:,}; valid {len(valid):,}; non-trivial {len(nontrivial):,}; '
          f'premises span P, Q, R {len(spanning):,}')
    print(f'  strongest-conclusion rules {len(rules2)} over {len(by_pair)} premise pairs; families {len(fam2)}')
    for key, members in sorted(fam2.items(), key=lambda kv: -len(kv[1])):
        rep = readable(S, members)
        kind = 'relations ' if not any(is_fact(t) for t in rep[:2]) else 'has a fact'
        print(f'    {kind}  {show(rep):32} ({len(members)} rules)')
    for label, n in (('valid', len(valid)), ('non-trivial', len(nontrivial)), ('spanning', len(spanning)),
                     ('premise pairs', len(by_pair)), ('strongest rules', len(rules2)), ('families', len(fam2))):
        check(f'two premises: {label}', n, {'valid': 23_191, 'non-trivial': 2_292, 'spanning': 1_560,
                                            'premise pairs': 228, 'strongest rules': 348, 'families': 9}[label])
    hs = S.family_key((S.gate(0b1011, P, Q), S.gate(0b1011, Q, R)), S.gate(0b1011, P, R))
    res = S.family_key((S.gate(0b1110, P, Q), S.gate(0b1011, P, R)), S.gate(0b1110, Q, R))   # P∨Q, ¬P∨R ⊢ Q∨R
    check('hypothetical syllogism is a family', hs in fam2, True)
    check('resolution is the same family as hypothetical syllogism', res, hs)

    rules3 = three_premise_rules()
    fam3 = families(S, rules3)
    print('\nTHREE PREMISES')
    print(f'  premise sets {len(list(itertools.combinations(F2, 3))):,}; needing all three '
          f'{len({r[:3] for r in rules3}):,}; strongest-conclusion rules {len(rules3):,}; families {len(fam3)}')
    unsplit = [k for k, members in fam3.items() if split(members[0]) is None]
    for key, members in sorted(fam3.items(), key=lambda kv: -len(kv[1])):
        rep = readable(S, members)
        kind = 'relations ' if not any(is_fact(t) for t in rep[:3]) else 'has a fact'
        print(f'    {kind}  {show(rep):40} ({len(members)} rules)')
    print(f'  families that split into two two-premise steps: {len(fam3) - len(unsplit)} of {len(fam3)}')
    cd = (S.gate(0b1011, P, R), S.gate(0b1011, Q, R), S.gate(0b1110, P, Q), R)
    x, y, i, z = split(cd)
    print(f'  constructive dilemma splits: {S.name(x)}, {S.name(y)} ⊢ {S.name(i)}; then {S.name(i)}, {S.name(z)} ⊢ R')
    check('three premises: sets needing all three', len({r[:3] for r in rules3}), 728)
    check('three premises: rules', len(rules3), 1_128)
    check('three premises: families', len(fam3), 29)
    check('constructive dilemma is a family', S.family_key(cd[:3], cd[3]) in fam3, True)
    check('families that do not split', len(unsplit), 0)

    # the split test must be able to fail: a valid rule with premises outside the 38 that does not split
    rng = random.Random(1)
    example = None
    for _ in range(100_000):
        a, b, c = (rng.randrange(1, S.all) for _ in range(3))
        if not a & b & c:
            continue
        for d in F2:
            if (d != S.all and S.implies(a & b & c, d) and not S.implies(a & b, d)
                    and not S.implies(a & c, d) and not S.implies(b & c, d) and split((a, b, c, d)) is None):
                example = (a, b, c, d)
                break
        if example:
            break
    check('the split test can fail', example is not None, True)
    print(f'  the split test can fail: e.g. {show(example)} does not split')
    print('\nall counts as published')
