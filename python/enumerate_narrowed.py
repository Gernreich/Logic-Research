#!/usr/bin/env python3
"""Narrowed enumeration: eight operations, four q-values, two expansions.

Replaces the 2019 ``2_enumerate_narrowed_8_ops.py`` (kept in
``original_2019/``). That version reached the narrowing by commenting out
lines; here the choices are named and explicit.

WHAT IS NARROWED
----------------
* **Seeds** -- ``[2, 4, 5, 7, 8, 10, 11, 13]`` instead of all sixteen values.
* **q values** -- ``[3, 6, 9, 12]`` instead of all sixteen. As 4-bit patterns
  these are ``0011``, ``0110``, ``1001``, ``1100``.
* **Operations** -- eight of the sixteen (``boolean16.NARROWED_OPS``): the
  constants, projections and negations are dropped, keeping only functions
  that genuinely combine both inputs.
* **No ``last`` quirk** -- the TRUE slot is among the dropped operations, so
  the ``16`` oddity that affects the full run cannot arise here.

Each expansion multiplies the population by ``4 * 8 = 32``. Note there are
only **two** expansions here, not the three of the full run: in the original
the first level was a literal list of eight seeds, with its expansion
commented out. Doing three would give 262,144 values, not the 8,192 recorded
in 2019.

    8 seeds -> 256 -> 8,192

OUTPUT
------
``FirstSeven`` -- 8,192 values, one per line.

The 2019 output of this script is archived beside it as
``narrowed_enumeration_8192_values.txt``. This script reproduces that file
exactly; ``--verify`` checks it.

USAGE
-----
    python3 enumerate_narrowed.py            write FirstSeven here
    python3 enumerate_narrowed.py --stdout   print the values instead
    python3 enumerate_narrowed.py --verify   compare against the 2019 archive
"""

import argparse
import os
import sys

from boolean16 import NARROWED_OPS, expand

SEEDS = (2, 4, 5, 7, 8, 10, 11, 13)
Q_VALUES = (3, 6, 9, 12)
EXPECTED_TOTAL = 8_192
ARCHIVE = "narrowed_enumeration_8192_values.txt"


def enumerate_narrowed() -> list:
    """Run the two expansions and return all 8,192 values.

    Two, not three -- ``SEEDS`` is already the first level.
    """
    values = SEEDS
    for _ in range(2):
        values = list(expand(values, Q_VALUES, keep=NARROWED_OPS))
    return values


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stdout", action="store_true", help="print instead of writing")
    ap.add_argument("--verify", action="store_true",
                    help=f"compare output against {ARCHIVE}")
    args = ap.parse_args()

    values = enumerate_narrowed()
    if len(values) != EXPECTED_TOTAL:
        print(f"expected {EXPECTED_TOTAL} values, produced {len(values)}", file=sys.stderr)
        return 1

    if args.verify:
        if not os.path.exists(ARCHIVE):
            print(f"{ARCHIVE} not found", file=sys.stderr)
            return 1
        archived = [int(line) for line in open(ARCHIVE)]
        same = archived == values
        print(f"  archived : {len(archived):,} values")
        print(f"  generated: {len(values):,} values")
        print(f"  identical: {same}")
        return 0 if same else 1

    if args.stdout:
        for v in values:
            print(v)
        return 0

    if os.path.exists("FirstSeven"):
        print("refusing to overwrite FirstSeven", file=sys.stderr)
        return 1
    with open("FirstSeven", "w") as f:
        for v in values:
            f.write(f"{v}\n")
    print(f"wrote {len(values):,} values -> FirstSeven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
