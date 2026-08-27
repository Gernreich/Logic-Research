#!/usr/bin/env python3
"""Search for every two-input boolean function in a single pass.

Replaces the six near-identical ``RandomWeightSearch_N.py`` files in
``iamtrask_boolean_function_runs/`` (1,050 lines between them). They differed
in exactly two characters' worth of content: the random seed, and a letter
appended to every output filename.

    _0 -> seed 0, suffix "z"     _3 -> seed 3, suffix "c"
    _1 -> seed 1, suffix "a"     _5 -> seed 5, suffix "e"
    _2 -> seed 2, suffix "b"     _6 -> seed 6, suffix "f"

(There is no ``_4``; that variant lives at the top level as
``original_2019/train_random_weight_search_v4.py`` and has never run -- it
crashes on line 16.)

HOW IT WORKS
------------
Sample one pair of weight matrices, run a single forward pass, then test the
four outputs against all sixteen truth tables. Any that match within the
tolerance window are recorded. One sample can therefore satisfy at most one
function, but all sixteen are checked each time.

THE 2019 LABELS ARE WRONG IN THREE PLACES
-----------------------------------------
Derived by reading the accept conditions rather than trusting the filenames:

    output       2019 filename        what that output actually is
    (1,0,0,0)    R9NAND__*            NOR
    (1,0,1,1)    R9IMPLICATION__*     Q->P  (converse implication)
    (1,1,0,1)    R9REVIMPLICATION__*  P->Q  (implication)

So ``R9IMPLICATION`` and ``R9REVIMPLICATION`` are swapped, and the files
named for NAND hold NOR solutions. Worse: **real NAND (1,1,1,0) was never
searched for at all.** There is no accept condition for it anywhere in those
scripts, despite ``nand_syn0`` / ``nand_syn1`` existing on disk.

This script uses correct names by default. ``--legacy-names`` reproduces the
2019 filenames exactly, wrong labels included, for comparison against the
archived output.

USAGE
-----
    python3 search_all_functions.py --seed 0 --max-iter 500000
    python3 search_all_functions.py --seed 1 --out-suffix a --write
    python3 search_all_functions.py --seed 0 --legacy-names --write
"""

import argparse
import sys
from collections import Counter

import numpy

from nncore import INPUTS, TARGETS, describe, sigmoid

ALL_FUNCTIONS = {
    (0, 0, 0, 0): "FALSE",
    (0, 0, 0, 1): "AND",
    (0, 0, 1, 0): "P_AND_NOT_Q",
    (0, 0, 1, 1): "P",
    (0, 1, 0, 0): "Q_AND_NOT_P",
    (0, 1, 0, 1): "Q",
    (0, 1, 1, 0): "XOR",
    (0, 1, 1, 1): "OR",
    (1, 0, 0, 0): "NOR",
    (1, 0, 0, 1): "XNOR",
    (1, 0, 1, 0): "NOT_Q",
    (1, 0, 1, 1): "CONVERSE_IMPLICATION",
    (1, 1, 0, 0): "NOT_P",
    (1, 1, 0, 1): "IMPLICATION",
    (1, 1, 1, 0): "NAND",
    (1, 1, 1, 1): "TRUE",
}

LEGACY_NAMES = {
    (0, 0, 0, 1): "R9AND", (0, 0, 1, 0): "R9PMINUSQ", (0, 0, 1, 1): "R9P",
    (0, 1, 0, 0): "R9QminusP", (0, 1, 0, 1): "R9Q", (0, 1, 1, 0): "R9XOR",
    (0, 1, 1, 1): "R9OR",
    (1, 0, 0, 0): "R9NAND",            # actually NOR
    (1, 0, 0, 1): "R9IFF", (1, 0, 1, 0): "R9NOTQ",
    (1, 0, 1, 1): "R9IMPLICATION",     # actually converse
    (1, 1, 0, 0): "R9NOTP",
    (1, 1, 0, 1): "R9REVIMPLICATION",  # actually implication
}
"""The 2019 filenames. FALSE and TRUE were commented out; NAND was absent."""

# Sampling constants from the 2019 scripts: syn = z*random(shape) - zz
Z, ZZ = 12.0, 6.0
DEFAULT_N = 0.976


def classify(l2, n: float):
    """Return the truth table this output matches, or None."""
    low = 1.0 - n
    flat = numpy.asarray(l2).reshape(-1)
    bits = []
    for v in flat:
        if v >= n:
            bits.append(1)
        elif v <= low:
            bits.append(0)
        else:
            return None          # in the dead zone: matches nothing
    return tuple(bits)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n", type=float, default=DEFAULT_N,
                    help=f"high threshold, low is 1-n (default {DEFAULT_N})")
    ap.add_argument("--max-iter", type=int, default=1_000_000,
                    help="0 means run until interrupted, as the originals did")
    ap.add_argument("--write", action="store_true",
                    help="append hits to files instead of printing")
    ap.add_argument("--out-suffix", default="",
                    help="letter appended to output filenames, as in 2019")
    ap.add_argument("--legacy-names", action="store_true",
                    help="use the 2019 filenames, including the wrong labels")
    args = ap.parse_args()

    numpy.random.seed(args.seed)
    found = Counter()
    i = 0
    try:
        while args.max_iter == 0 or i < args.max_iter:
            i += 1
            syn0 = Z * numpy.random.random((2, 3)) - ZZ
            syn1 = Z * numpy.random.random((3, 1)) - ZZ
            l1 = sigmoid(numpy.dot(INPUTS, syn0))
            l2 = sigmoid(numpy.dot(l1, syn1))

            bits = classify(l2, args.n)
            if bits is None:
                continue
            found[bits] += 1

            if args.legacy_names:
                name = LEGACY_NAMES.get(bits)
                if name is None:
                    continue      # 2019 did not record FALSE, TRUE or real NAND
            else:
                name = ALL_FUNCTIONS[bits]

            if args.write:
                for suffix, data in (("l2", l2.T), ("syn0", syn0), ("syn1", syn1.T)):
                    with open(f"{name}__{suffix}{args.out_suffix}", "a") as fh:
                        print(data, file=fh)
            else:
                print(f"{ALL_FUNCTIONS[bits]:<22} {bits}  {describe(l2)}")
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)

    print(f"\n{sum(found.values())} hit(s) in {i:,} samples", file=sys.stderr)
    for bits, count in sorted(found.items(), key=lambda kv: -kv[1]):
        legacy = LEGACY_NAMES.get(bits, "-")
        flag = ""
        if legacy != "-" and not legacy[2:].upper().startswith(ALL_FUNCTIONS[bits][:3].upper()):
            flag = f"   (2019 called this {legacy})"
        print(f"  {ALL_FUNCTIONS[bits]:<22} {count:>6}{flag}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
