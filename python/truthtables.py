#!/usr/bin/env python3
"""Truth tables on two or three variables, for the inference-rule search.

A truth table is an int whose bits are the rows, first row first: for two
variables the rows are (p, q) = TT TF FT FF, the order ``lambda16.txt`` uses,
so P is ``1100`` and Q is ``1010``. For three variables the rows run TTT down
to FFF. Everything else here is built on that one convention.

The sixteen gates are numbered by their own truth table read in the same row
order, so gate ``0b1011`` is p -> q and gate ``0b0110`` is p XOR q. (This is not
the ``boolean16.OPS`` numbering; the tautology count uses that one directly.)

``Space(n)`` bundles what the searches need for n variables: the variables as
tables, the literals, which variables a table depends on, the renamings (any
permutation of the variables, any of them negated) and a readable name.

USAGE
-----
    from truthtables import Space
    S = Space(3)
    S.implies(S.var[0] & S.var[1], S.var[0])      # True
"""

import itertools

GATE_NAMES = {0: 'FALSE', 8: 'x∧y', 4: 'x∧¬y', 2: '¬x∧y', 1: '¬(x∨y)', 12: 'x', 10: 'y', 3: '¬x',
              5: '¬y', 6: 'x⊕y', 9: 'x↔y', 14: 'x∨y', 11: 'x→y', 13: 'y→x', 7: '¬(x∧y)', 15: 'TRUE'}


class Space:
    def __init__(self, n: int):
        self.n = n
        self.rows = list(itertools.product((1, 0), repeat=n))
        self.size = len(self.rows)
        self.all = (1 << self.size) - 1
        self.names = 'PQR'[:n]
        self.var = [self.table(lambda r, j=j: r[j]) for j in range(n)]
        self.literals = set(self.var) | {v ^ self.all for v in self.var}
        self.renamings = [(perm, neg) for perm in itertools.permutations(range(n))
                          for neg in itertools.product((0, 1), repeat=n)]
        self._formula = None

    def table(self, f) -> int:
        """The table of a function of one row (a tuple of 0/1 values)."""
        return sum(1 << (self.size - 1 - i) for i, r in enumerate(self.rows) if f(r))

    def bit(self, t: int, row: tuple) -> int:
        return (t >> (self.size - 1 - self.rows.index(row))) & 1

    def implies(self, a: int, b: int) -> bool:
        """a -> b is a tautology: every row where a is true, b is true."""
        return a & ~b & self.all == 0

    def gate(self, k: int, a: int, b: int) -> int:
        """Gate k (its own truth table, TT TF FT FF as bits 8 4 2 1) applied row by row."""
        out = 0
        for bit, (x, y) in zip((8, 4, 2, 1), ((1, 1), (1, 0), (0, 1), (0, 0))):
            if k & bit:
                out |= (a if x else ~a & self.all) & (b if y else ~b & self.all)
        return out

    def depends_on(self, t: int) -> set:
        out = set()
        for j in range(self.n):
            for r in self.rows:
                flipped = tuple(v ^ (i == j) for i, v in enumerate(r))
                if self.bit(t, r) != self.bit(t, flipped):
                    out.add(j)
                    break
        return out

    def rename(self, t: int, perm: tuple, neg: tuple) -> int:
        """The table with variables permuted by perm and those in neg negated."""
        return self.table(lambda r: self.bit(t, tuple(r[perm[j]] ^ neg[j] for j in range(self.n))))

    def substitute(self, t: int, literal: int) -> int:
        """t with the variable of this literal fixed to make the literal true."""
        j = next(k for k in range(self.n) if literal in (self.var[k], self.var[k] ^ self.all))
        value = 1 if literal == self.var[j] else 0
        return self.table(lambda r: self.bit(t, tuple(value if k == j else v for k, v in enumerate(r))))

    def pairwise(self) -> list:
        """Every table depending on at most two variables: a gate on two of them."""
        return sorted({self.gate(k, self.var[x], self.var[y])
                       for x, y in itertools.combinations(range(self.n), 2) for k in range(16)})

    def family_key(self, premises, conclusion):
        """The same key for a rule and every renaming of it; premise order ignored."""
        return min((tuple(sorted(self.rename(p, *g) for p in premises)), self.rename(conclusion, *g))
                   for g in self.renamings)

    def name(self, t: int) -> str:
        """A shortest formula for t, using ¬ ∧ ∨ → ↔ ⊕ (fewest variable occurrences)."""
        if self._formula is None:
            self._build_formulas()
        return self._formula[t]

    def _build_formulas(self):
        a = self.all
        found = {a: 'TRUE', 0: 'FALSE'}
        by_size = {1: {}}
        for j, v in enumerate(self.var):
            by_size[1][v] = self.names[j]
            by_size[1][v ^ a] = '¬' + self.names[j]
        found.update(by_size[1])
        ops = [('∧', lambda x, y: x & y), ('∨', lambda x, y: x | y), ('→', lambda x, y: (x ^ a) | y),
               ('↔', lambda x, y: x ^ y ^ a), ('⊕', lambda x, y: x ^ y)]
        wrap = lambda s: s if len(s) <= 2 else '(' + s + ')'
        size = 1
        while len(found) < 1 << self.size:
            size += 1
            new = {}
            for i in range(1, size):
                for x, sx in by_size[i].items():
                    for y, sy in by_size[size - i].items():
                        for sym, f in ops:
                            v = f(x, y)
                            if v not in found and v not in new:
                                new[v] = wrap(sx) + sym + wrap(sy)
            for v, s in list(new.items()):
                if v ^ a not in found and v ^ a not in new:
                    new[v ^ a] = '¬(' + s + ')'
            by_size[size] = new
            found.update(new)
        self._formula = found


def families(space, rules):
    """Group (premises..., conclusion) rules into families under renaming."""
    out = {}
    for r in rules:
        out.setdefault(space.family_key(r[:-1], r[-1]), []).append(r)
    return out


def readable(space, members):
    """The family member (over all renamings) with the shortest, least negated text."""
    every = {tuple(space.rename(t, *g) for t in r) for r in members for g in space.renamings}
    def score(r):
        text = ''.join(space.name(t) for t in r)
        return (len(text), text.count('¬'), text)
    return min(every, key=score)


def check(name, got, want):
    """Stop the script if a published number has changed."""
    if got != want:
        raise SystemExit(f'CHECK FAILED: {name}: got {got}, expected {want}')
