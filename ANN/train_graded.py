#!/usr/bin/env python3
"""Train a network to encode a binary input as one graded output value.

Replaces the backprop variants in ``four_to_sixteen_architecture/`` (left in
place as originals). That folder's name describes the experiment: feed all
**four**-bit input patterns and ask for **sixteen** distinguishable output
levels from a single output neuron.

    input [0,0,0,0] -> 0.000
    input [0,0,0,1] -> 0.067
    input [0,0,1,0] -> 0.133
    ...
    input [1,1,1,1] -> 1.000

i.e. target = i/15 for the i-th input row. The 2019 ``fourthreeone.py`` used
exactly those rounded values; this script computes them, so ``--bits`` can
vary the width.

Because the sigmoid saturates near 0 and 1 and the levels are only 1/15
apart, this is a demanding target for one output unit -- which is the point
of the experiment.

USAGE
-----
    python3 train_graded.py                        4 bits, 6 hidden, 200k iters
    python3 train_graded.py --bits 3 --hidden 4
    python3 train_graded.py --iterations 1000000 --seed 7
    python3 train_graded.py --show                 print every row's output

STATE OF THE ORIGINALS
----------------------
``working.py`` does not run: an ``IndentationError`` on the weight
initialisation, plus Python-2 ``xrange`` and a ``np.`` prefix while importing
``numpy``. ``workin.py``, ``TwoOne.py``, ``fourthreeone.py`` and that
folder's ``ThreeLayerNeuralNetwork.py`` do parse.

``TwoOne.py`` is a different experiment again -- two inputs, one layer, and
the odd target ``[0.5, 0.51, 0.51, 0.0]``. It is not covered here.
"""

import argparse
import itertools

import numpy

from nncore import sigmoid


def dataset(bits: int):
    """All 2**bits input rows, and targets evenly spaced over [0, 1]."""
    rows = list(itertools.product([0, 1], repeat=bits))
    X = numpy.array(rows)
    n = len(rows) - 1
    y = numpy.array([[i / n] for i in range(len(rows))])
    return X, y


def train(X, y, hidden: int, iterations: int, seed: int, rate: float = 1.0):
    numpy.random.seed(seed)
    syn0 = 2 * numpy.random.random((X.shape[1], hidden)) - 1
    syn1 = 2 * numpy.random.random((hidden, 1)) - 1
    l2 = None
    for _ in range(iterations):
        l1 = sigmoid(numpy.dot(X, syn0))
        l2 = sigmoid(numpy.dot(l1, syn1))
        l2_delta = (y - l2) * sigmoid(l2, deriv=True)
        l1_delta = l2_delta.dot(syn1.T) * sigmoid(l1, deriv=True)
        syn1 += rate * l1.T.dot(l2_delta)
        syn0 += rate * X.T.dot(l1_delta)
    return syn0, syn1, l2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bits", type=int, default=4, help="input width (default 4)")
    ap.add_argument("--hidden", type=int, default=6, help="hidden units")
    ap.add_argument("--iterations", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--rate", type=float, default=1.0)
    ap.add_argument("--show", action="store_true", help="print every row")
    args = ap.parse_args()

    X, y = dataset(args.bits)
    syn0, syn1, l2 = train(X, y, args.hidden, args.iterations, args.seed, args.rate)

    err = numpy.abs(y - l2)
    step = 1.0 / (len(y) - 1)
    print(f"{args.bits} bits -> {len(y)} levels, {args.hidden} hidden units, "
          f"{args.iterations:,} iterations, seed {args.seed}")
    print(f"  mean |error| : {err.mean():.6f}")
    print(f"  max  |error| : {err.max():.6f}")
    print(f"  level spacing: {step:.6f}")
    print(f"  every level distinguishable: {bool(err.max() < step / 2)}")
    if args.show:
        print()
        for row, want, got in zip(X, y.reshape(-1), numpy.asarray(l2).reshape(-1)):
            print(f"  {''.join(map(str, row))}  want {want:.4f}  got {got:.4f}"
                  f"  err {abs(want-got):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
