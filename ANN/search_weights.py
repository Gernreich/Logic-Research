#!/usr/bin/env python3
"""Random weight search: hunt for weights that realise a boolean function.

Replaces five 2019 scripts that differed only in constants, activation, and
where they wrote output (all preserved in ``original_2019/``):

    train_sigmoid_1arg_gold.py       NOR, narrow ranges around +/-6 and -4
    train_sigmoid_1arg_variant.py    NOR, tighter ranges + a distance filter
    train_sigmoid_noargs_n0.981.py   NOR, wide ranges, appends to files
    train_sigmoid_noargs_scratch.py  identical to the above but a different suffix
    train_relu_5arg.py               XOR, ReLU, appends to <prefix>l2/syn0/syn1

There is no training here. Each iteration samples fresh weights uniformly
from the given ranges, runs one forward pass, and reports whenever all four
outputs land inside the tolerance window. It is brute force.

WHERE THE a-g FILES CAME FROM
-----------------------------
The ReLU script took an output prefix as its fourth argument and appended to
``<prefix>l2``, ``<prefix>syn0``, ``<prefix>syn1``. Running it with ``a``,
``b``, ... produced the ``run_a_*`` .. ``run_g_*`` files sitting beside this
script. The letters were nothing but command-line labels.

USAGE
-----
    # NOR, the "gold" configuration, seeded, print hits
    python3 search_weights.py --target NOR --seed 1 --preset gold

    # XOR with ReLU, appending to run_h_l2 / run_h_syn0 / run_h_syn1
    python3 search_weights.py --target XOR --activation relu \
        --preset relu --seed 1 --out-prefix run_h_

    # bounded run, so it terminates
    python3 search_weights.py --target NOR --preset gold --max-iter 200000

The 2019 scripts looped ``range(30000000000)`` -- effectively forever, to be
killed by hand. ``--max-iter`` defaults to 1,000,000 here; pass 0 for the
original unbounded behaviour.
"""

import argparse
import sys

import numpy

from nncore import ACTIVATIONS, TARGETS, describe, forward, matches

PRESETS = {
    # name -> (syn0 ranges (2x3), syn1 ranges (3x1), default n)
    # Each range is (low, high) for numpy.random.sample() * (high-low) + low.
    "gold": {
        "syn0": [[(4.5, 6.1), (-6.0, -4.9), (-6.0, -4.9)],
                 [(4.5, 6.1), (-6.0, -4.9), (-6.0, -4.9)]],
        "syn1": [[(-4.1, -3.9)], [(5.9, 6.1)], [(5.9, 6.1)]],
        "n": 0.98274,
        "note": "narrow ranges around a known NOR solution",
    },
    "tight": {
        "syn0": [[(5.99, 6.01), (-6.01, -5.99), (-6.01, -5.99)],
                 [(5.99, 6.01), (-6.01, -5.99), (-6.01, -5.99)]],
        "syn1": [[(-4.1, -3.9)], [(5.9, 6.1)], [(5.9, 6.1)]],
        "n": 0.9827,
        "note": "tighter still; the 2019 variant also applied a distance filter",
    },
    "wide": {
        "syn0": [[(2.0, 6.0), (-6.0, -2.0), (-6.0, -2.0)],
                 [(2.0, 6.0), (-6.0, -2.0), (-6.0, -2.0)]],
        "syn1": [[(-5.0, -4.0)], [(5.0, 6.0)], [(5.0, 6.0)]],
        "n": 0.981,
        "note": "wide ranges, the least constrained search",
    },
    "relu": {
        # The ReLU script scaled a symmetric range: z*sample() - z/2.
        "syn0": [[(-2.0, 2.0), (-2.0, 2.0)], [(-2.0, 2.0), (-2.0, 2.0)]],
        "syn1": [[(-2.0, 2.0)], [(-2.0, 2.0)]],
        "n": 0.9,
        "note": "2x2 / 2x1 shapes, symmetric ranges, ReLU activation",
    },
}


def sample(ranges) -> numpy.ndarray:
    """Fill a matrix by sampling each cell from its own range.

    Cells are drawn row by row, left to right -- the same order the 2019
    scripts used, so a given seed reproduces their weights exactly.
    """
    out = numpy.zeros((len(ranges), len(ranges[0])))
    for i, row in enumerate(ranges):
        for j, (low, high) in enumerate(row):
            out[i, j] = numpy.random.sample() * (high - low) + low
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", default="NOR", choices=sorted(TARGETS),
                    help="boolean function to search for (default NOR)")
    ap.add_argument("--preset", default="gold", choices=sorted(PRESETS),
                    help="weight-range preset (default gold)")
    ap.add_argument("--activation", default="sigmoid", choices=sorted(ACTIVATIONS))
    ap.add_argument("--seed", type=int, default=None, help="numpy random seed")
    ap.add_argument("--n", type=float, default=None,
                    help="high threshold; low is 1-n (default: the preset's)")
    ap.add_argument("--max-iter", type=int, default=1_000_000,
                    help="stop after this many samples; 0 means never stop")
    ap.add_argument("--out-prefix", default=None,
                    help="append hits to <prefix>l2, <prefix>syn0, <prefix>syn1")
    args = ap.parse_args()

    preset = PRESETS[args.preset]
    target = TARGETS[args.target]
    n = args.n if args.n is not None else preset["n"]
    act = ACTIVATIONS[args.activation]
    if args.seed is not None:
        numpy.random.seed(args.seed)

    print(f"searching for {args.target} {target} using preset '{args.preset}'"
          f" ({preset['note']}), activation={args.activation}, n={n}",
          file=sys.stderr)

    hits = 0
    i = 0
    try:
        while args.max_iter == 0 or i < args.max_iter:
            i += 1
            syn0 = sample(preset["syn0"])
            syn1 = sample(preset["syn1"])
            _, l2 = forward(syn0, syn1, act)
            if not matches(l2, target, n):
                continue
            hits += 1
            if args.out_prefix:
                for suffix, data in (("l2", l2.T), ("syn0", syn0), ("syn1", syn1.T)):
                    with open(f"{args.out_prefix}{suffix}", "a") as fh:
                        print(data, file=fh)
            else:
                print(f"hit {hits} at sample {i}: {describe(l2)}")
                print(syn0)
                print(syn1.T)
                print()
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)

    print(f"{hits} hit(s) in {i:,} samples", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
