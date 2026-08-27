#!/usr/bin/env python3
"""The one script here that actually trains: backpropagation, learning NAND.

Refactored from the 2019 ``train_nand_seed_sweep.py`` (preserved in
``original_2019/``), which was the only one of the seven doing gradient
descent rather than random search.

WHAT IT DOES
------------
For each of a range of random seeds, initialise a 2-3-1 network, run
backpropagation for a fixed number of iterations against the NAND truth
table, then report whether it converged.

Convergence is not guaranteed. Some seeds land in a configuration where the
outputs all sit near 0.5 -- the network learns nothing. The 2019 run
recorded exactly that: ``run_a_l2_predictions.txt`` reads
``[0.4998, 0.5000, 0.5000, 0.4999]``, while
``training_log_2019-08-29_nand_converged.txt`` shows a successful run at
``[0.99998, 0.99902, 0.99902, 0.00154]``. Sweeping seeds is how you find the
ones that work.

A NOTE ON THE UPDATE RULE
-------------------------
There is no learning rate: the weight update is the full
``layer.T.dot(delta)``, exactly as in the original (and as in the iamtrask
tutorial it derives from). Adding one would change the results, so it is
left alone and simply exposed as ``--rate`` defaulting to 1.0.

USAGE
-----
    python3 train_nand_backprop.py                    seeds 1000-1009
    python3 train_nand_backprop.py --seeds 1000 1100  a wider sweep
    python3 train_nand_backprop.py --iterations 100000 --verbose
    python3 train_nand_backprop.py --target XOR       (a 2-3-1 net cannot do XOR reliably)
"""

import argparse

import numpy

from nncore import INPUTS, TARGETS, describe, sigmoid

CONVERGED_TOL = 0.1
"""How close every output must be to its target bit to count as converged."""


def train(seed: int, target, iterations: int, rate: float, hidden: int = 3):
    """Train one network from one seed. Returns (syn0, syn1, outputs)."""
    numpy.random.seed(seed)
    syn0 = 2 * numpy.random.random((2, hidden)) - 1
    syn1 = 2 * numpy.random.random((hidden, 1)) - 1
    y = numpy.array(target).reshape(-1, 1)

    l0 = INPUTS
    l2 = None
    for _ in range(iterations):
        l1 = sigmoid(numpy.dot(l0, syn0))
        l2 = sigmoid(numpy.dot(l1, syn1))

        l2_delta = (y - l2) * sigmoid(l2, deriv=True)
        l1_delta = l2_delta.dot(syn1.T) * sigmoid(l1, deriv=True)

        syn1 += rate * l1.T.dot(l2_delta)
        syn0 += rate * l0.T.dot(l1_delta)
    return syn0, syn1, l2


def converged(l2, target) -> bool:
    return all(abs(float(numpy.asarray(v).reshape(-1)[0]) - bit) < CONVERGED_TOL
               for v, bit in zip(l2, target))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", default="NAND", choices=sorted(TARGETS))
    ap.add_argument("--seeds", nargs=2, type=int, default=[1000, 1010],
                    metavar=("FIRST", "LAST"), help="seed range, end exclusive")
    ap.add_argument("--iterations", type=int, default=100_000,
                    help="backprop iterations per seed (2019 used 1,000,000)")
    ap.add_argument("--hidden", type=int, default=3, help="hidden units")
    ap.add_argument("--rate", type=float, default=1.0,
                    help="update scale; 1.0 reproduces the original")
    ap.add_argument("--verbose", action="store_true", help="print weights too")
    args = ap.parse_args()

    target = TARGETS[args.target]
    good = 0
    total = 0
    for seed in range(args.seeds[0], args.seeds[1]):
        total += 1
        syn0, syn1, l2 = train(seed, target, args.iterations, args.rate, args.hidden)
        ok = converged(l2, target)
        good += ok
        print(f"seed {seed:>6}  {describe(l2)}  {'converged' if ok else 'no'}")
        if args.verbose:
            print("  syn0:", numpy.array2string(syn0.T, precision=4))
            print("  syn1:", numpy.array2string(syn1.T, precision=4))
    print(f"\n{good}/{total} seeds converged on {args.target} {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
