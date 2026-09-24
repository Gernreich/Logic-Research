#!/usr/bin/env python3
"""Every non-trivial inference rule on two variables, P and Q.

A rule "premise, premise |- conclusion" is valid when premise AND premise
implies the conclusion on every row. The 2019 search wrote these as the
modus ponens shape ((A o B) AND C) -> D and filtered the tautologies; this does
the same filtering exactly and to the end.

TRIVIAL RULES, DROPPED
----------------------
* the premises contradict each other (anything follows)
* one premise alone already gives the conclusion
* the conclusion is TRUE

Rules that are the same up to renaming (swap P and Q, negate either) form one
family.

USAGE
-----
    python3 rules_two_variables.py        under a second
"""

import itertools

from boolean16 import ops
from truthtables import Space, families, check

S = Space(2)
P, Q = S.var
LITERALS = sorted(S.literals)
AND, IMPLIES = 2, 11          # boolean16.OPS indices, for the 2019 shape


def trivial(premises, conclusion):
    both = S.all
    for p in premises:
        both &= p
    if both == 0:
        return 'the premises contradict'
    if conclusion == S.all:
        return 'the conclusion is TRUE'
    if any(S.implies(p, conclusion) for p in premises):
        return 'one premise alone gives it'
    return None


def show(rule):
    return ', '.join(S.name(t) for t in rule[:-1]) + '  ⊢  ' + S.name(rule[-1])


if __name__ == '__main__':
    # the 2019 shape, every gate and table: (A o B) AND C -> D
    shape = sum(1 for a, k, b, c, d in itertools.product(range(16), repeat=5)
                if ops(ops(ops(a, b)[k], c)[AND], d)[IMPLIES] == 15)
    # inputs only P, Q, NOT P, NOT Q
    spelled = [(a, k, b, c, d) for a, k, b, c, d in itertools.product(LITERALS, range(16), LITERALS, LITERALS, LITERALS)
               if ops(ops(ops(a, b)[k], c)[AND], d)[IMPLIES] == 15]
    rules = sorted({(ops(a, b)[k], c, d) for a, k, b, c, d in spelled})
    kept = [r for r in rules if not trivial(r[:2], r[2])]
    fam = families(S, kept)

    print('THE FILTER CHAIN')
    print(f'  (A o B) AND C -> D, every gate and table          {16 ** 5:>9,} expressions  {shape:>7,} tautologies')
    print(f'  inputs only P, Q, NOT P, NOT Q                     {16 * 4 ** 4:>9,} expressions  {len(spelled):>7,} tautologies')
    print(f'  as distinct rules, not spellings                   {len(rules):>9,}')
    reasons = {}
    for r in rules:
        why = trivial(r[:2], r[2])
        if why:
            reasons[why] = reasons.get(why, 0) + 1
    for why, n in sorted(reasons.items()):
        print(f'      dropped, {why:28} {n:>5}')
    print(f'  non-trivial                                        {len(kept):>9,}')
    print(f'  families up to renaming                            {len(fam):>9,}\n')
    for i, (_, members) in enumerate(sorted(fam.items(), key=lambda kv: kv[0]), 1):
        print(f'  family {i}')
        for r in members:
            print('     ', show(r))

    check('shape tautologies', shape, 633_512)
    check('literal-input tautologies', len(spelled), 2_368)
    check('distinct rules', len(rules), 144)
    check('non-trivial rules', len(kept), 16)
    check('families', len(fam), 2)
    mp = (S.gate(0b1011, P, Q), P, Q)
    check('modus ponens is among them', mp in kept, True)

    # premises and conclusion any of the 16 tables
    valid = [(a, b, c) for a in range(16) for b in range(16) for c in range(16) if S.implies(a & b, c)]
    nontrivial = [r for r in valid if not trivial(r[:2], r[2])]
    pairs = {tuple(sorted(r[:2])) for r in nontrivial}
    strongest = [(a, b, a & b) for a, b in pairs]
    fam16 = families(S, strongest)
    print('\nANY OF THE 16 TABLES AS PREMISE OR CONCLUSION')
    print(f'  triples {16 ** 3:,}; valid {len(valid):,}; non-trivial {len(nontrivial):,}; premise pairs {len(pairs)}; families {len(fam16)}')
    for key, members in sorted(fam16.items()):
        a, b, c = members[0]
        rep = min(({tuple(S.rename(t, *g) for t in r) for r in members for g in S.renamings}),
                  key=lambda r: ''.join(S.name(t) for t in r))
        print(f'      {show(rep):34} ({len(members)} premise pairs)')
    check('valid triples', len(valid), 2_401)
    check('non-trivial triples', len(nontrivial), 132)
    check('premise pairs', len(pairs), 30)
    check('families of the 16', len(fam16), 6)
    print('\nall counts as published')
