#!/usr/bin/env python3
"""Shared core for the 2-input boolean-function network experiments.

THE NETWORK
-----------
Every experiment here uses the same tiny feed-forward network:

    layer 0   the four possible inputs   [[0,0],[0,1],[1,0],[1,1]]
    layer 1   hidden, via syn0
    layer 2   output, via syn1  -- four numbers, one per input row

The output is compared against a boolean function's truth table. Because the
activations are continuous, "matches" means *within a tolerance window*: each
output must be >= n where the target bit is 1, and <= 1-n where it is 0.

TWO DIFFERENT EXPERIMENTS
-------------------------
The 2019 scripts fall into two kinds that their names did not distinguish:

* **Backprop training** -- one script only. Initialises weights randomly and
  descends the gradient for a million iterations. See ``train_nand_backprop.py``.

* **Random weight search** -- the other six. No training at all: sample
  weights uniformly from hand-chosen ranges, run one forward pass, and record
  the weights whenever the output lands inside the tolerance window. This is
  a brute-force hunt for weight vectors that realise a function, not learning.
  See ``search_weights.py``.

Naming the difference matters: the originals were all called ``train_*`` by a
later renaming pass, which was wrong for six of the seven.
"""

from typing import Callable, Dict, Sequence

import numpy

INPUTS = numpy.array([[0, 0], [0, 1], [1, 0], [1, 1]])
"""The four input rows, in the order every truth table below assumes."""

TARGETS: Dict[str, tuple] = {
    #                (0,0) (0,1) (1,0) (1,1)
    "FALSE":          (0, 0, 0, 0),
    "AND":            (0, 0, 0, 1),
    "XOR":            (0, 1, 1, 0),
    "OR":             (0, 1, 1, 1),
    "NOR":            (1, 0, 0, 0),
    "XNOR":           (1, 0, 0, 1),
    "NAND":           (1, 1, 1, 0),
    "TRUE":           (1, 1, 1, 1),
}
"""Truth tables indexed by name, aligned to ``INPUTS``.

Worth knowing when reading the 2019 output files: several are named
``R9NAND__*`` but the acceptance condition in the scripts that wrote them
selects ``(1,0,0,0)``, which is **NOR**, not NAND ``(1,1,1,0)``. Either the
filenames are mislabelled or the condition was not the one intended. The
data cannot tell us which; this module keeps the names honest.
"""


def sigmoid(x, deriv: bool = False):
    """Logistic activation. ``deriv=True`` expects ``x`` to already be sigmoid(x)."""
    if deriv:
        return x * (1 - x)
    return 1 / (1 + numpy.exp(-x))


def relu(x, deriv: bool = False):
    """Rectified linear activation.

    NOTE: the 2019 ReLU script kept the *sigmoid* derivative ``x*(1-x)`` in
    the ``deriv`` branch, which is wrong for ReLU. It never mattered there
    because random search does no backward pass. The correct derivative is
    given here, so this function is safe to use for training too.
    """
    if deriv:
        return (x > 0).astype(float)
    return x * (x > 0)


ACTIVATIONS: Dict[str, Callable] = {"sigmoid": sigmoid, "relu": relu}


def forward(syn0, syn1, activation: Callable = sigmoid):
    """Run the four input rows through the network. Returns (layer1, layer2)."""
    l1 = activation(numpy.dot(INPUTS, syn0))
    l2 = activation(numpy.dot(l1, syn1))
    return l1, l2


def matches(l2, target: Sequence[int], n: float) -> bool:
    """Is every output inside the tolerance window for ``target``?

    ``n`` is the high threshold; ``1 - n`` is the low one. With n=0.98274, a
    '1' bit must exceed 0.98274 and a '0' bit must fall below 0.01726.
    """
    low = 1.0 - n
    flat = numpy.asarray(l2).reshape(-1)
    for value, bit in zip(flat, target):
        if bit and value < n:
            return False
        if not bit and value > low:
            return False
    return True


def describe(l2) -> str:
    """Render the four outputs compactly, for logs."""
    flat = numpy.asarray(l2).reshape(-1)
    return "[" + ", ".join(f"{float(v):.6f}" for v in flat) + "]"
