#!/usr/bin/env python3
"""Self-checks for the enumeration.

Run with ``python3 test_boolean16.py``. No test framework required.

The important test is ``test_narrowed_matches_2019_archive``: it regenerates
the narrowed enumeration and compares it against the file produced in 2019.
That is the only end-to-end proof that the refactor preserved behaviour, and
it is why the archive file must not be deleted.
"""

import sys

from boolean16 import (ALL_MASK, NARROWED_OPS, TAUTOLOGY, expand, ops,
                       tautology_indices)
import enumerate_full
import enumerate_narrowed

FAILURES = []


def check(name, got, want):
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got  {got!r}\n          want {want!r}")
        FAILURES.append(name)


def test_ops_are_complement_pairs():
    """Entry i and entry 15-i should be logical complements, for every input."""
    bad = []
    for p in range(16):
        for q in range(16):
            row = ops(p, q)
            for i in range(16):
                if row[i] ^ ALL_MASK != row[15 - i]:
                    bad.append((p, q, i))
    check("ops() form complement pairs", bad, [])


def test_ops_identities():
    """Spot-check the named operations against their definitions."""
    p, q = 0b1100, 0b1010
    row = ops(p, q)
    check("AND", row[2], p & q)
    check("OR", row[7], p | q)
    check("XOR", row[5], p ^ q)
    check("NAND", row[13], ALL_MASK ^ (p & q))
    check("NOR", row[8], ALL_MASK ^ (p | q))
    check("IMPLIES p->q", row[11], (p ^ ALL_MASK) | q)
    check("FALSE / TRUE", (row[0], row[15]), (0, ALL_MASK))


def test_expansion_sizes():
    """Each expansion multiplies by len(q_values) * len(ops)."""
    three = list(expand(range(16), tuple(range(16))))
    check("expansion 1 size", len(three), 4_096)
    five = list(expand(three[:16], tuple(range(16))))
    check("expansion of 16 values", len(five), 16 * 16 * 16)
    narrowed = list(expand((2, 4), (3, 6, 9, 12), keep=NARROWED_OPS))
    check("narrowed step size", len(narrowed), 2 * 4 * 8)


def test_tautology_indices():
    check("tautology_indices finds 15s",
          list(tautology_indices([0, 15, 3, 15])), ["0x1", "0x3"])


def test_narrowed_matches_2019_archive():
    """The refactor must reproduce the 2019 output exactly."""
    values = enumerate_narrowed.enumerate_narrowed()
    check("narrowed count", len(values), enumerate_narrowed.EXPECTED_TOTAL)
    try:
        archived = [int(line) for line in open(enumerate_narrowed.ARCHIVE)]
    except OSError as exc:
        check(f"read {enumerate_narrowed.ARCHIVE}", str(exc), "readable")
        return
    check("narrowed matches 2019 archive", values, archived)


def test_full_quirk_is_preserved():
    """The last=16 quirk must survive, and --correct must actually differ."""
    _, _, seven_quirk = enumerate_full.levels(16)
    _, _, seven_fixed = enumerate_full.levels(ALL_MASK)
    a = [v for _, v in zip(range(64), seven_quirk)]
    b = [v for _, v in zip(range(64), seven_fixed)]
    check("quirk value 16 appears", 16 in a, True)
    check("corrected run has no 16", 16 in b, False)
    check("quirk changes the output", a != b, True)


if __name__ == "__main__":
    for fn in sorted(
        (v for k, v in list(globals().items()) if k.startswith("test_")),
        key=lambda f: f.__code__.co_firstlineno,
    ):
        print(f"\n{fn.__name__}")
        fn()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        sys.exit(1)
    print("all checks passed")
