#!/usr/bin/env python3
"""Modus ponens when P and Q are sixteen-valued, checked exactly.

Each value is one of the sixteen truth tables, numbered in the gate order of
``lambda16.txt`` (value i and value 15 - i are complements), and every
connective works row by row, as in Gates of Gates. P is value 6, Q is value 3.

WHAT IS CHECKED
---------------
From P and R = P -> Q:
* ``(P AND (P -> Q)) -> Q`` is TRUE for all 256 pairs (P, Q)
* a pair (P, R) is possible exactly when P OR R is TRUE: 81 of 256
* the Q that fit are exactly the interval  P AND R <= Q <= R  (<= meaning
  "implies on every row"), and the answers total 256
* a P with k false rows leaves 2^k answers, on C(4, k) * 2^(4 - k) pairs

From P OR Q and P -> Q:
* ``(P OR Q) AND (P -> Q)`` equals Q for all 256 pairs
* exactly 8 first premises X make ``(X AND (P -> Q)) -> Q`` a tautology,
  and they are the values inside P OR Q; P is one of them
* this premise pair pins Q to one value on every possible pair; P, P -> Q
  pins it only when P is TRUE

These are the numbers on ``modus-ponens-16.html`` and ``modus-ponens-or.html``,
which compute them again in the browser when they load.

USAGE
-----
    python3 modus_ponens_16.py        under a second
"""

from math import comb

from truthtables import check

BITS = ['0000', '0010', '1000', '1010', '0100', '0110', '1100', '1110',
        '0001', '0011', '1001', '1011', '0101', '0111', '1101', '1111']
NAME = ['FALSE', 'q∧¬p', 'AND', 'Q', 'p∧¬q', 'XOR', 'P', 'OR',
        'NOR', '¬P', 'XNOR', 'P→Q', '¬Q', 'NAND', 'Q→P', 'TRUE']
ALL = range(16)
TRUE, P_VAR, Q_VAR = 15, 6, 3


def rows(i):
    return [int(c) for c in BITS[i]]


def value(r):
    return BITS.index(''.join(map(str, r)))


def op(f):
    return lambda x, y: value([f(a, b) for a, b in zip(rows(x), rows(y))])


AND = op(lambda a, b: a & b)
OR = op(lambda a, b: a | b)
IMP = op(lambda a, b: (1 - a) | b)
LE = lambda a, b: IMP(a, b) == TRUE


def fits(p, r):
    return [q for q in ALL if IMP(p, q) == r]


if __name__ == '__main__':
    check('names agree with the table', (NAME[P_VAR], NAME[Q_VAR], NAME[IMP(P_VAR, Q_VAR)]), ('P', 'Q', 'P→Q'))

    taut = sum(1 for p in ALL for q in ALL if IMP(AND(p, IMP(p, q)), q) == TRUE)
    possible, answers, interval_ok, by_count = 0, 0, 0, {}
    for p in ALL:
        for r in ALL:
            qs = fits(p, r)
            if (OR(p, r) == TRUE) != bool(qs):
                raise SystemExit(f'possible-iff-P∨R fails at P={NAME[p]}, R={NAME[r]}')
            if not qs:
                continue
            possible += 1
            answers += len(qs)
            interval = [q for q in ALL if LE(AND(p, r), q) and LE(q, r)]
            interval_ok += interval == qs
            by_count[len(qs)] = by_count.get(len(qs), 0) + 1
    print('FROM P AND R = P→Q')
    print(f'  (P ∧ (P→Q)) → Q is TRUE on {taut} of 256 (P, Q) pairs')
    print(f'  possible (P, R) pairs: {possible}; answers in total: {answers}')
    print(f'  Q is exactly the interval P∧R ≤ Q ≤ R on {interval_ok} of {possible}')
    print(f'  pairs by number of answers: {dict(sorted(by_count.items()))}')
    check('tautology', taut, 256)
    check('possible pairs', possible, 81)
    check('answers', answers, 256)
    check('interval law', interval_ok, 81)
    check('pairs by answers', by_count, {2 ** k: comb(4, k) * 2 ** (4 - k) for k in range(5)})
    check('classical case: P = TRUE pins Q', all(len(fits(TRUE, r)) == 1 for r in ALL), True)

    identity = sum(1 for p in ALL for q in ALL if AND(OR(p, q), IMP(p, q)) == q)
    r0 = IMP(P_VAR, Q_VAR)
    works = [x for x in ALL if IMP(AND(x, r0), Q_VAR) == TRUE]
    inside = [x for x in ALL if LE(x, OR(P_VAR, Q_VAR))]
    from_or, from_p = {}, {}
    for p in ALL:
        for q in ALL:
            from_or.setdefault((OR(p, q), IMP(p, q)), set()).add(q)
            from_p.setdefault((p, IMP(p, q)), set()).add(q)
    pinned = lambda m: sum(1 for s in m.values() if len(s) == 1)
    print('\nFROM P∨Q AND P→Q')
    print(f'  (P∨Q) ∧ (P→Q) = Q on {identity} of 256 pairs')
    print(f'  first premises X that work in place of P: {len(works)} ({", ".join(NAME[x] for x in works)})')
    print(f'  possible premise pairs: P, P→Q {len(from_p)}; P∨Q, P→Q {len(from_or)}')
    print(f'  pairs that pin Q to one value: P, P→Q {pinned(from_p)}; P∨Q, P→Q {pinned(from_or)}')
    check('identity', identity, 256)
    check('premises that work', len(works), 8)
    check('they are the values inside P∨Q', works, inside)
    check('P is one of them', P_VAR in works, True)
    check('P∨Q pins every possible pair', pinned(from_or), len(from_or))
    check('P pins only when P is TRUE', pinned(from_p), 16)
    print('\nall counts as published')
