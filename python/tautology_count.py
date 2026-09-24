#!/usr/bin/env python3
"""Count the tautologies of the modus ponens shape, exactly.

Modus ponens is ((P -> Q) AND P) -> Q: the shape ((A o B) o C) o D. Letting
every connective be any of the sixteen gates and every input any truth table
gives, for two variables, 16^3 * 16^4 = 2^28 = 268,435,456 expressions: the
2019 full run (``enumerate_full.py``). For three variables the inputs are any of
256 tables, 16^3 * 256^4 expressions.

Nothing is listed. The count carries, level by level, how many expressions
reach each table, so the result is exact without generating 2^28 values.

THE 2019 QUIRK
--------------
The full run's third expansion writes 16 instead of 15 in the TRUE slot
(``boolean16.py``), so it never counts the 16^6 expressions whose outer
connective is TRUE. Both counts are printed.

USAGE
-----
    python3 tautology_count.py        under a second
"""

from collections import Counter

from boolean16 import ops
from truthtables import Space, check


def count_two_variables(last):
    """Through the 2019 ops(), in the 2019 order: (((a o1 b) o2 c) o3 d)."""
    level = Counter()
    for a in range(16):
        for b in range(16):
            for v in ops(a, b):
                level[v] += 1
    for final in (False, True):
        nxt = Counter()
        for v, n in level.items():
            for d in range(16):
                for w in ops(v, d, last if final else 15):
                    nxt[w] += n
        level = nxt
    return sum(level.values()), level[15]


def count(space):
    tables = range(1 << space.size)
    gates = [[[space.gate(k, a, b) for b in tables] for a in tables] for k in range(16)]
    level = Counter()
    for a in tables:
        for k in range(16):
            for v in gates[k][a]:
                level[v] += 1
    for _ in range(2):
        nxt = Counter()
        for v, n in level.items():
            for k in range(16):
                for w in gates[k][v]:
                    nxt[w] += n
        level = nxt
    return sum(level.values()), level[space.all]


if __name__ == '__main__':
    total, correct = count_two_variables(15)
    _, quirk = count_two_variables(16)
    print('two variables, ((A o B) o C) o D, every gate and every table')
    print(f'  expressions                  {total:>22,}')
    print(f'  tautologies                  {correct:>22,}  ({100 * correct / total:.2f}%)')
    print(f'  counted by the 2019 run      {quirk:>22,}  (misses the {16 ** 6:,} with outer TRUE)')
    check('two-variable expressions', total, 16 ** 7)
    check('two-variable tautologies', correct, 54_008_320)
    check('2019 count', quirk, 37_231_104)
    check('quirk difference', correct - quirk, 16 ** 6)
    check('same result through truthtables.gate', count(Space(2)), (16 ** 7, 54_008_320))

    total3, taut3 = count(Space(3))
    print('three variables, same shape, inputs any of 256 tables')
    print(f'  expressions                  {total3:>22,}')
    print(f'  tautologies                  {taut3:>22,}  ({100 * taut3 / total3:.2f}%)')
    check('three-variable expressions', total3, 16 ** 3 * 256 ** 4)
    check('three-variable tautologies', taut3, 2_346_912_555_520)
    print('all counts as published')
