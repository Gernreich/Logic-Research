#!/usr/bin/env python3
"""Self-checks for the network experiments. ``python3 test_nncore.py``.

The load-bearing test is ``test_sampling_matches_2019``: it reproduces the
weight sampling of the original gold script inline and asserts the refactored
``sample()`` produces identical numbers from the same seed. That is what
shows the refactor preserved behaviour rather than merely resembling it.
"""

import sys

import numpy

import search_all_functions as saf
import search_weights as sw
import train_graded as tg
from nncore import (ACTIVATIONS, INPUTS, TARGETS, forward, matches, relu,
                    sigmoid)
import train_nand_backprop as tnb

FAILURES = []


def check(name, got, want):
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got  {got!r}\n          want {want!r}")
        FAILURES.append(name)


def test_truth_tables():
    """Targets must line up with INPUTS row order."""
    check("INPUTS order", INPUTS.tolist(), [[0, 0], [0, 1], [1, 0], [1, 1]])
    check("AND", TARGETS["AND"], (0, 0, 0, 1))
    check("NAND", TARGETS["NAND"], (1, 1, 1, 0))
    check("NOR", TARGETS["NOR"], (1, 0, 0, 0))
    check("XOR", TARGETS["XOR"], (0, 1, 1, 0))
    for name, table in TARGETS.items():
        if len(table) != 4:
            check(f"{name} length", len(table), 4)


def test_activations():
    check("sigmoid(0)", round(float(sigmoid(numpy.array([0.0]))[0]), 6), 0.5)
    check("relu clips negatives", relu(numpy.array([-3.0, 2.0])).tolist(), [0.0, 2.0])
    check("relu derivative is a step, not sigmoid's",
          relu(numpy.array([-1.0, 1.0]), deriv=True).tolist(), [0.0, 1.0])


def test_matches_window():
    """A '1' bit must exceed n; a '0' bit must fall below 1-n."""
    n = 0.98
    check("exact hit", matches(numpy.array([0.99, 0.01, 0.01, 0.01]),
                               TARGETS["NOR"], n), True)
    check("one output too low", matches(numpy.array([0.97, 0.01, 0.01, 0.01]),
                                        TARGETS["NOR"], n), False)
    check("one output too high", matches(numpy.array([0.99, 0.05, 0.01, 0.01]),
                                         TARGETS["NOR"], n), False)


def test_sampling_matches_2019():
    """sample() must reproduce the original gold script's weights exactly."""
    def original_gold():
        s0 = numpy.zeros((2, 3)); s1 = numpy.zeros((3, 1))
        s0[0, 0] = numpy.random.sample() * (6.1 - 4.5) + 4.5
        s0[0, 1] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
        s0[0, 2] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
        s0[1, 0] = numpy.random.sample() * (6.1 - 4.5) + 4.5
        s0[1, 1] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
        s0[1, 2] = numpy.random.sample() * (-4.9 + 6.0) - 6.0
        s1[0, 0] = numpy.random.sample() * (-3.9 + 4.1) - 4.1
        s1[1, 0] = numpy.random.sample() * (6.1 - 5.9) + 5.9
        s1[2, 0] = numpy.random.sample() * (6.1 - 5.9) + 5.9
        return s0, s1

    g = sw.PRESETS["gold"]
    allsame = True
    for seed in (0, 1, 42, 12345):
        numpy.random.seed(seed); o0, o1 = original_gold()
        numpy.random.seed(seed); n0 = sw.sample(g["syn0"]); n1 = sw.sample(g["syn1"])
        if not (numpy.array_equal(o0, n0) and numpy.array_equal(o1, n1)):
            allsame = False
    check("sample() reproduces 2019 weights across 4 seeds", allsame, True)


def test_backprop_learns_nand():
    """The one real trainer should converge on NAND for a known-good seed."""
    _, _, l2 = tnb.train(1000, TARGETS["NAND"], iterations=60_000, rate=1.0)
    check("seed 1000 converges on NAND", tnb.converged(l2, TARGETS["NAND"]), True)


def test_backprop_can_fail():
    """Seed 1001 is the documented failure: output stuck near 0.5."""
    _, _, l2 = tnb.train(1001, TARGETS["NAND"], iterations=60_000, rate=1.0)
    stuck = abs(float(numpy.asarray(l2).reshape(-1)[3]) - 0.5) < 0.05
    check("seed 1001 gets stuck near 0.5", stuck, True)
    check("...and is reported as not converged",
          tnb.converged(l2, TARGETS["NAND"]), False)


def test_all_functions_table_is_complete():
    """All 16 truth tables present, each mapped to a distinct name."""
    check("16 functions listed", len(saf.ALL_FUNCTIONS), 16)
    check("names unique", len(set(saf.ALL_FUNCTIONS.values())), 16)
    import itertools
    every = set(itertools.product((0, 1), repeat=4))
    check("covers every truth table", set(saf.ALL_FUNCTIONS) == every, True)


def test_legacy_labels_are_wrong_where_documented():
    """The three known 2019 mislabels, asserted so they stay documented."""
    check("R9NAND is really NOR", saf.ALL_FUNCTIONS[(1, 0, 0, 0)], "NOR")
    check("R9NAND label exists on that output", saf.LEGACY_NAMES[(1, 0, 0, 0)], "R9NAND")
    check("R9IMPLICATION is really the converse",
          saf.ALL_FUNCTIONS[(1, 0, 1, 1)], "CONVERSE_IMPLICATION")
    check("R9REVIMPLICATION is really implication",
          saf.ALL_FUNCTIONS[(1, 1, 0, 1)], "IMPLICATION")
    check("real NAND was never searched for in 2019",
          (1, 1, 1, 0) in saf.LEGACY_NAMES, False)


def test_classify():
    check("clean NOR classified", saf.classify(numpy.array([0.99, 0.01, 0.01, 0.01]), 0.976),
          (1, 0, 0, 0))
    check("dead-zone value rejected",
          saf.classify(numpy.array([0.5, 0.01, 0.01, 0.01]), 0.976), None)


def test_graded_dataset():
    X, y = tg.dataset(4)
    check("16 input rows", X.shape, (16, 4))
    check("first target", round(float(y[0][0]), 4), 0.0)
    check("last target", round(float(y[-1][0]), 4), 1.0)
    check("even spacing", round(float(y[1][0]), 4), round(1/15, 4))


def test_presets_wellformed():
    for name, p in sw.PRESETS.items():
        rows = p["syn0"]
        widths = {len(r) for r in rows}
        if len(widths) != 1:
            check(f"{name} syn0 rows equal width", widths, "one width")
        if not 0.5 < p["n"] < 1.0:
            check(f"{name} threshold in range", p["n"], "0.5..1.0")
    check("all presets structurally valid", True, True)


if __name__ == "__main__":
    for fn in sorted((v for k, v in list(globals().items()) if k.startswith("test_")),
                     key=lambda f: f.__code__.co_firstlineno):
        print(f"\n{fn.__name__}")
        fn()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        sys.exit(1)
    print("all checks passed")
