#!/usr/bin/env python3
"""Core of the boolean-function enumeration.

BACKGROUND
----------
There are exactly sixteen boolean functions of two variables. If you encode a
two-variable truth table as the four bits of a nibble, every one of those
sixteen functions can be written as a bitwise expression on two 4-bit
operands ``p`` and ``q``. ``OPS`` below is that set, in the order the 2019
scripts used.

The order is not arbitrary: the list is arranged so that entry *i* and entry
*15 - i* are logical complements.

    idx  expression            name
    ---  -------------------   -----------------------
      0  0                     FALSE
      1  15 ^ ((q ^ 15) | p)   q AND NOT p
      2  p & q                 AND
      3  q                     Q
      4  15 ^ ((p ^ 15) | q)   p AND NOT q
      5  p ^ q                 XOR
      6  p                     P
      7  p | q                 OR
      8  15 ^ (p | q)          NOR
      9  p ^ 15                NOT P
     10  15 ^ (p ^ q)          XNOR
     11  (p ^ 15) | q          IMPLIES      (p -> q)
     12  q ^ 15                NOT Q
     13  15 ^ (p & q)          NAND
     14  (q ^ 15) | p          CONVERSE IMPLIES (q -> p)
     15  15                    TRUE

WHAT THE ENUMERATION DOES
-------------------------
Start with a set of seed values. Repeatedly expand: for every value ``p`` so
far, for every ``q`` in a chosen set, emit all sixteen (or a chosen subset)
of ``OPS`` applied to ``(p, q)``. Each expansion multiplies the population by
``len(q_values) * len(ops)``.

Three expansions give what the scripts call "first seven" — seven terms deep
in the expression tree.

    full run:      16 seeds -> 4,096 -> 1,048,576 -> 268,435,456  (2**28)
    narrowed run:   8 seeds ->   256 ->       8,192

A *tautology* is a position whose value is 15 (all four truth-table bits
set, i.e. true for every assignment of the two variables). The companion
"tau" file records the indices where that happens, in hex.

THE ``last=16`` QUIRK  -- IMPORTANT, DO NOT "FIX"
-------------------------------------------------
In the original full enumeration, the first two expansions end each block
with ``15`` (TRUE) but the third ends it with ``16``. Sixteen is not a valid
4-bit value and is almost certainly a typo.

It is nonetheless load-bearing. The tautology scan counts positions equal to
15, so that final slot in every block of the last expansion is never counted.
Changing 16 to 15 would alter the output and it would no longer match the
data recorded in 2019. The parameter is therefore explicit throughout this
module rather than hidden, and defaults are chosen to reproduce the original.

Verified 2026-08-26: reproduces the 2019 outputs exactly.
"""

from typing import Iterable, Iterator, Optional, Sequence

ALL_MASK = 15
"""Every bit set in a 4-bit truth table -- i.e. the value meaning TRUE."""

TAUTOLOGY = 15
"""A position is a tautology when its value equals this."""


def ops(p: int, q: int, last: int = ALL_MASK) -> tuple:
    """Apply all sixteen two-variable boolean functions to ``p`` and ``q``.

    Returns them in the canonical order documented at the top of this module.

    ``last`` is the value emitted in the final slot (the TRUE function). It
    exists solely so callers can reproduce the original ``16`` quirk; pass
    ``ALL_MASK`` for the mathematically correct value.
    """
    return (
        0,                        # FALSE
        15 ^ ((q ^ 15) | p),      # q AND NOT p
        p & q,                    # AND
        q,                        # Q
        15 ^ ((p ^ 15) | q),      # p AND NOT q
        p ^ q,                    # XOR
        p,                        # P
        p | q,                    # OR
        15 ^ (p | q),             # NOR
        p ^ 15,                   # NOT P
        15 ^ (p ^ q),             # XNOR
        (p ^ 15) | q,             # IMPLIES
        q ^ 15,                   # NOT Q
        15 ^ (p & q),             # NAND
        (q ^ 15) | p,             # CONVERSE IMPLIES
        last,                     # TRUE  (see the last=16 quirk above)
    )

# Indices into the tuple returned by ops(). Named so a subset can be
# described in the caller rather than as bare numbers.
FALSE, AND_NOT_P, AND, Q, P_AND_NOT_Q, XOR, P, OR = range(8)
NOR, NOT_P, XNOR, IMPLIES, NOT_Q, NAND, CONVERSE_IMPLIES, TRUE = range(8, 16)

NARROWED_OPS: tuple = (AND, P_AND_NOT_Q, XOR, OR, NOR, XNOR, IMPLIES, NAND)
"""The eight operations kept by the 2019 narrowed run.

The other eight were commented out there: the two constants (FALSE, TRUE),
the two projections (P, Q), the two negations (NOT P, NOT Q), and the pair
``q AND NOT p`` / ``CONVERSE IMPLIES``. What survives is the set that
genuinely combines both inputs.

Note the original seeded that run with ``[2, 4, 5, 7, 8, 10, 11, 13]`` --
numerically identical to these indices. Whether that was intentional or a
coincidence of reusing the same list is not recorded anywhere.
"""


def expand(source: Iterable[int],
           q_values: Sequence[int] = tuple(range(16)),
           keep: Optional[Sequence[int]] = None,
           last: int = ALL_MASK) -> Iterator[int]:
    """One expansion step, as a generator.

    For each ``p`` in ``source`` and each ``q`` in ``q_values``, yield the
    selected operations applied to that pair.

    ``keep`` selects which of the sixteen to emit (indices into ``ops()``);
    ``None`` means all sixteen. Generating rather than accumulating is what
    lets the full run -- 268 million values -- work in a few megabytes
    instead of the gigabytes the 2019 version needed.
    """
    for p in source:
        for q in q_values:
            row = ops(p, q, last)
            if keep is None:
                yield from row
            else:
                for i in keep:
                    yield row[i]


def tautology_indices(values: Iterable[int]) -> Iterator[str]:
    """Yield the hex index of every position holding a tautology."""
    for i, v in enumerate(values):
        if v == TAUTOLOGY:
            yield hex(i)
