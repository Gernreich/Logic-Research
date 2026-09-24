#!/usr/bin/env python3
"""Inference rules that need a premise tying all three variables together.

Premises may be any of the 256 tables on P, Q, R; 218 depend on all three.
Conclusions are gates on two of the variables, as in the other searches.

IRREDUCIBLE
-----------
The pairwise shadow of a premise is everything it says about pairs: the AND
of every two-variable statement it implies. P XOR Q XOR R has an empty
shadow. A valid, non-trivial rule is irreducible when its conclusion does not
follow from the premises' shadows, so no pairwise search could find it.

WHAT EACH RULE TURNS OUT TO BE
------------------------------
The rules are sorted by the second (minor) premise, as modus ponens is:

* a plain fact           the fact substituted into the major premise
* two facts              both substituted
* an equivalence         one variable substituted for the other
* an implication         an earlier rule under a shared hypothesis, or two
                         cases. The two-case count cannot come out otherwise:
                         for a valid rule whose minor premise is x OR y, each
                         case follows automatically. It is reported, not
                         offered as evidence.

For rules whose premises are both natural three-way connectives (a formula
using each variable once), each is tested as (1) an old two-variable
elimination rule (literal conclusion) with compound parts, then (2) a chain
of classical steps: split off facts, substitute them, apply such an
elimination. The conclusion must follow from the derived facts and
two-variable statements alone, never from the three-way premises themselves;
counting those made an earlier version of this check pass everything. With
zero or one round of steps nothing is derived, which shows the check can fail.

USAGE
-----
    python3 rules_three_way.py        about 45 seconds, mostly building the elimination index
"""

import itertools

from truthtables import Space, families, readable, check

S = Space(3)
P, Q, R = S.var
F2 = S.pairwise()
LIT = S.literals
THREE_WAY = [t for t in range(256) if S.depends_on(t) == {0, 1, 2}]


def shadow(t):
    s = S.all
    for f in F2:
        if S.implies(t, f):
            s &= f
    return s


def show(rule):
    return ', '.join(S.name(t) for t in rule[:-1]) + '  ⊢  ' + S.name(rule[-1])


def irreducible_rules():
    rules = []
    for a, b in itertools.combinations(range(1, 256), 2):
        if a not in THREE_WAY and b not in THREE_WAY:
            continue
        ab = a & b
        if not ab:
            continue
        sh = shadow(a) & shadow(b)
        concl = [c for c in F2 if c != S.all and S.implies(ab, c) and not S.implies(a, c)
                 and not S.implies(b, c) and not S.implies(sh, c)]
        rules += [(a, b, c) for c in concl if not any(e != c and S.implies(e, c) for e in concl)]
    return rules


def minor_kind(t):
    return {2: 'two facts', 4: 'an equivalence', 6: 'an implication'}.get(bin(t).count('1'))


def tiers(rules):
    out = {'a plain fact': [], 'two facts': [], 'an equivalence': [], 'an implication': [], 'three-way': []}
    for a, b, c in rules:
        if a in THREE_WAY and b in THREE_WAY:
            out['three-way'].append((a, b, c))
            continue
        major, minor = (a, b) if a in THREE_WAY else (b, a)
        out['a plain fact' if minor in LIT else minor_kind(minor)].append((major, minor, c))
    return out


def substituted_equivalence(t, rel):
    for x, y in itertools.permutations(range(3), 2):
        for neg in (0, 1):
            if rel == (S.var[x] ^ S.var[y] ^ (0 if neg else S.all)):
                return S.table(lambda r: S.bit(t, tuple(r[x] ^ neg if k == y else v for k, v in enumerate(r))))
    return None


def under_hypothesis(rule):
    return any(all(S.implies(h ^ S.all, t) for t in rule) for h in LIT)


# ---- old two-variable eliminations (literal conclusion, both premises needed), with compound parts
T2 = Space(2)
ELIMINATIONS = [(f, g, h) for f in range(16) for g in range(16) for h in T2.literals
                if f & g and T2.implies(f & g, h) and not T2.implies(f, h) and not T2.implies(g, h)]


def elimination_index():
    index = {}
    for s in range(256):
        for t in range(256):
            vals = [S.gate(k, s, t) for k in range(16)]
            for f, g, h in ELIMINATIONS:
                index.setdefault((vals[f], vals[g]), set()).add(vals[h])
    return index


def closure(index, premises, rounds):
    known = set(premises)
    for _ in range(rounds):
        new = set()
        for x in known:
            new |= {l for l in LIT if S.implies(x, l)}                       # split off facts
            new |= {S.substitute(x, l) for l in LIT if l in known}             # substitute facts
        for x in known:
            for y in known:
                new |= index.get((x, y), set())                               # eliminate
        new -= known
        if not new:
            break
        known |= new
    return known


def derivable(index, rule, rounds):
    a, b, c = rule
    known = closure(index, (a, b), rounds)
    simple = S.all
    for t in known:
        if t in F2 or t in LIT:
            simple &= t
    return S.implies(simple, c)


if __name__ == '__main__':
    empty = [t for t in THREE_WAY if shadow(t) == S.all]
    print(f'tables depending on all three variables: {len(THREE_WAY)}; saying nothing about any pair: {len(empty)}')
    check('three-way tables', len(THREE_WAY), 218)
    check('empty shadows', len(empty), 34)

    rules = irreducible_rules()
    fam = families(S, rules)
    print(f'irreducible two-premise rules: {len(rules):,} over {len({r[:2] for r in rules}):,} premise pairs; '
          f'families {len(fam)}')
    check('irreducible rules', len(rules), 14_814)
    check('families', len(fam), 380)
    parity = (P ^ Q ^ R, P, Q ^ R ^ S.all)                          # P⊕Q⊕R, P ⊢ Q↔R
    check('P⊕Q⊕R, P ⊢ Q↔R is irreducible', S.family_key(parity[:2], parity[2]) in fam, True)

    t = tiers(rules)
    print('\nBY THE MINOR PREMISE')
    subst = sum(1 for a, b, c in t['a plain fact'] if c == S.substitute(a, b))
    print(f"  a plain fact     {len(t['a plain fact']):>6,} rules; the fact substituted into the major premise: {subst:,}")
    check('plain fact rules', len(t['a plain fact']), 336)
    check('plain fact: all substitution', subst, 336)
    two = sum(1 for a, b, c in t['two facts'] if any(x & y == b and S.implies(S.substitute(S.substitute(a, x), y) & b, c)
                                                   for x, y in itertools.combinations(sorted(LIT), 2)))
    print(f"  two facts        {len(t['two facts']):>6,} rules; both substituted: {two:,}")
    check('two-fact rules', len(t['two facts']), 768)
    check('two facts: all substitution', two, 768)
    eq = sum(1 for a, b, c in t['an equivalence'] if S.implies(substituted_equivalence(a, b) & b, c))
    print(f"  an equivalence   {len(t['an equivalence']):>6,} rules; one variable substituted for the other: {eq:,}")
    check('equivalence rules', len(t['an equivalence']), 600)
    check('equivalence: all substitution', eq, 600)
    hyp = sum(1 for r in t['an implication'] if under_hypothesis(r))
    print(f"  an implication   {len(t['an implication']):>6,} rules; under a shared hypothesis {hyp:,}, "
          f"two cases {len(t['an implication']) - hyp:,} (automatic, see the docstring)")
    check('implication rules', len(t['an implication']), 768)
    check('under a hypothesis', hyp, 96)
    frege = (S.gate(0b1011, P, S.gate(0b1011, Q, R)), S.gate(0b1011, P, Q), S.gate(0b1011, P, R))
    check("Frege's P→(Q→R), P→Q ⊢ P→R is among them", S.family_key(frege[:2], frege[2]) in fam, True)
    print(f"  both three-way   {len(t['three-way']):>6,} rules")

    occurrences = lambda x: sum(S.name(x).count(v) for v in 'PQR')
    natural = {x for x in THREE_WAY if occurrences(x) == 3}
    both = [r for r in rules if r[0] in natural and r[1] in natural]
    fb = families(S, both)
    print(f'\nBOTH PREMISES NATURAL THREE-WAY ({len(natural)} connectives written with each variable once)')
    print(f'  {len(both):,} rules, {len(fb)} families')
    check('natural connectives', len(natural), 114)
    check('natural families', len(fb), 80)

    print('  building the elimination index ...', flush=True)
    index = elimination_index()
    single = {k for k, members in fb.items()
              if all(any(S.implies(h, r[2]) for key in ((r[0], r[1]), (r[1], r[0])) for h in index.get(key, ()))
                     for r in members)}
    print(f'  one old elimination rule with compound parts: {len(single)} families')
    check('single-elimination families', len(single), 47)
    rest = [k for k in fb if k not in single]
    for rounds in (0, 1, 2):
        left = [k for k in rest if not all(derivable(index, r, rounds) for r in fb[k])]
        print(f'  of the other {len(rest)}: not derived in {rounds} round(s) of classical steps: {len(left)}')
        check(f'{rounds} rounds', len(left), {0: 33, 1: 33, 2: 0}[rounds])
    for k in rest:
        print(f'      {show(readable(S, fb[k]))}')
    underived = sum(1 for r in rules if not derivable(index, r, 6))
    print(f'\nall {len(rules):,} irreducible rules: not derived within 6 rounds: {underived}')
    check('all rules derived', underived, 0)
    print('\nall counts as published; no rule found that is not a known step or a short chain of them')
