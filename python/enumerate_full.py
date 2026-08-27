#!/usr/bin/env python3
"""Full enumeration: all sixteen boolean operations, three expansions deep.

Replaces the 2019 ``1_enumerate_all_16_ops.py`` (kept in ``original_2019/``),
which was Python 2 and accumulated a 268-million-element list in memory --
several gigabytes, and unrunnable on current macOS. This version streams.

OUTPUT
------
``TotalFirstSeven``   every value, one per line -- 268,435,456 lines, ~650 MB
``TotalTau``          hex index of each tautology  -- ~37 million lines, ~370 MB

Both were deleted on 2026-08-26 as reproducible. This script is how you get
them back; it is the reason deleting them was safe.

USAGE
-----
    python3 enumerate_full.py                 write both files here
    python3 enumerate_full.py --out DIR       write them somewhere else
    python3 enumerate_full.py --check 200000  print the first N values only
    python3 enumerate_full.py --count         report sizes without writing

Expect the full run to take a while and to produce a gigabyte of text.

REPRODUCING THE 2019 OUTPUT
---------------------------
The third expansion uses ``last=16`` rather than 15. That is almost certainly
a typo in the original, but the 2019 data depends on it -- see the extended
note in ``boolean16.py``. It is preserved by default. Passing ``--correct``
uses 15 instead, which yields *different*, arguably more correct output that
will NOT match the archived files.
"""

import argparse
import os
import sys

from boolean16 import ALL_MASK, TAUTOLOGY, expand

SEEDS = range(16)
Q_VALUES = tuple(range(16))

EXPECTED_LEVEL_SIZES = (4_096, 1_048_576, 268_435_456)
"""Population after each of the three expansions -- 16 * 16 * 16, then x256, x256."""


def levels(last_final: int):
    """Build the three expansions.

    The first two are materialised as lists: 4,096 and 1,048,576 values are
    small enough to hold, and the third expansion needs to iterate the second
    one repeatedly. Only the third is streamed.
    """
    three = list(expand(SEEDS, Q_VALUES, last=ALL_MASK))
    five = list(expand(three, Q_VALUES, last=ALL_MASK))
    seven = expand(five, Q_VALUES, last=last_final)
    return three, five, seven


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=".", help="directory to write into")
    ap.add_argument("--check", type=int, metavar="N",
                    help="print the first N values and exit")
    ap.add_argument("--count", action="store_true",
                    help="report level sizes without writing files")
    ap.add_argument("--correct", action="store_true",
                    help="use 15 in the final slot instead of the original 16 "
                         "(output will NOT match the 2019 data)")
    args = ap.parse_args()

    last_final = ALL_MASK if args.correct else 16
    three, five, seven = levels(last_final)

    if args.count:
        print(f"  expansion 1: {len(three):>12,}")
        print(f"  expansion 2: {len(five):>12,}")
        print(f"  expansion 3: {len(five) * 16 * 16:>12,}  (streamed)")
        return 0

    if args.check is not None:
        for i, v in enumerate(seven):
            if i >= args.check:
                break
            print(v)
        return 0

    os.makedirs(args.out, exist_ok=True)
    values_path = os.path.join(args.out, "TotalFirstSeven")
    tau_path = os.path.join(args.out, "TotalTau")
    for p in (values_path, tau_path):
        if os.path.exists(p):
            print(f"refusing to overwrite {p}", file=sys.stderr)
            return 1

    written = taus = 0
    with open(values_path, "w") as vf, open(tau_path, "w") as tf:
        for i, v in enumerate(seven):
            vf.write(f"{v}\n")
            written += 1
            if v == TAUTOLOGY:
                tf.write(f"{hex(i)}\n")
                taus += 1

    print(f"wrote {written:,} values -> {values_path}")
    print(f"wrote {taus:,} tautology indices -> {tau_path}")
    if written != EXPECTED_LEVEL_SIZES[2]:
        print(f"WARNING: expected {EXPECTED_LEVEL_SIZES[2]:,} values", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
