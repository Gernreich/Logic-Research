#!/usr/bin/env python3
"""Generate weight-space point clouds for all sixteen boolean functions.

Same method as the 2019 searches -- sample weights uniformly, run a forward
pass, keep the ones whose output matches a truth table within tolerance --
but vectorised, so millions of samples run per second instead of one per
Python loop iteration.

The 2019 scripts used several parameter regimes, which is why their yields
differ so much:

    top-level RandomWeightSearch_N.py   +/-6   n=0.976   almost never hits
    Sixteen/tempp/RandomWeightSearch*   +/-10  n=0.9     the 262k runs
    R9FullPoints                        +/-20            the biggest clouds

Wider ranges and a looser threshold hit far more often. ``--range`` and
``--n`` expose both.

USAGE
-----
    python3 generate_clouds.py --samples 20000000 --range 10 --n 0.9
    python3 generate_clouds.py --samples 50000000 --range 20 --n 0.9 --out clouds
    python3 generate_clouds.py --rates            # measure yield, write nothing

Output is one CSV per function, three columns, matching the 2019 syn1 format
so the files are interchangeable with the archived ones.
"""

import argparse
import os

import numpy

FUNCTIONS = {
    (0, 0, 0, 0): "FALSE", (0, 0, 0, 1): "AND", (0, 0, 1, 0): "P_AND_NOT_Q",
    (0, 0, 1, 1): "P", (0, 1, 0, 0): "Q_AND_NOT_P", (0, 1, 0, 1): "Q",
    (0, 1, 1, 0): "XOR", (0, 1, 1, 1): "OR", (1, 0, 0, 0): "NOR",
    (1, 0, 0, 1): "XNOR", (1, 0, 1, 0): "NOT_Q", (1, 0, 1, 1): "CONVERSE_IMPL",
    (1, 1, 0, 0): "NOT_P", (1, 1, 0, 1): "IMPLICATION", (1, 1, 1, 0): "NAND",
    (1, 1, 1, 1): "TRUE",
}
INPUTS = numpy.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=numpy.float64)


def draw(batch: int, half: float, shape: str, rs):
    """Sample syn1 from a cube or a ball.

    The solution set for any function is a **cone**: if a weight vector works,
    every positive multiple of it works too (scaling up drives the sigmoid
    harder, which can only sharpen an already-accepted pattern). The set is
    therefore unbounded, and whatever region you sample from draws the cloud's
    outer surface. A cube gives flat faces and straight edges; a ball gives a
    round hull. Neither boundary is real.

    Only the *directions* are intrinsic -- see ``--normalise``.
    """
    if shape == "cube":
        return 2.0 * half * rs.random((batch, 3, 1)) - half
    # uniform inside a ball of radius half*sqrt(3), matching the cube's corner reach
    v = rs.normal(size=(batch, 3))
    v /= numpy.linalg.norm(v, axis=1, keepdims=True)
    r = (half * numpy.sqrt(3.0)) * rs.random((batch, 1)) ** (1.0 / 3.0)
    return (v * r)[:, :, None]


def sweep(batch: int, rng_half: float, n: float, rs, shape="cube", normalise=False):
    """One vectorised batch. Returns {truth_table: syn1 array of hits}."""
    span = 2.0 * rng_half
    syn0 = span * rs.random((batch, 2, 3)) - rng_half
    syn1 = draw(batch, rng_half, shape, rs)

    l1 = 1.0 / (1.0 + numpy.exp(-numpy.einsum("ij,bjk->bik", INPUTS, syn0)))
    l2 = 1.0 / (1.0 + numpy.exp(-numpy.einsum("bij,bjk->bik", l1, syn1)))
    out = l2[:, :, 0]                                  # (batch, 4)

    high = out >= n
    low = out <= (1.0 - n)
    decided = numpy.all(high | low, axis=1)            # no value in the dead zone
    if not decided.any():
        return {}

    bits = high[decided].astype(numpy.uint8)
    keep = syn1[decided, :, 0]
    if normalise:
        keep = keep / numpy.linalg.norm(keep, axis=1, keepdims=True)
    codes = bits[:, 0] * 8 + bits[:, 1] * 4 + bits[:, 2] * 2 + bits[:, 3]

    found = {}
    for code in numpy.unique(codes):
        table = tuple(int(b) for b in f"{code:04b}")
        found[table] = keep[codes == code]
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--samples", type=int, default=10_000_000)
    ap.add_argument("--batch", type=int, default=500_000)
    ap.add_argument("--range", type=float, default=10.0,
                    help="weights drawn from [-range, +range] (2019 used 6, 10 or 20)")
    ap.add_argument("--n", type=float, default=0.9, help="high threshold")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None, help="directory to write CSVs into")
    ap.add_argument("--cap", type=int, default=40_000, help="max points kept per function")
    ap.add_argument("--shape", default="cube", choices=("cube", "ball"),
                    help="sample syn1 from a cube (2019 behaviour) or a ball")
    ap.add_argument("--normalise", action="store_true",
                    help="scale every hit to unit length -- the cone's cross-section "
                         "on the unit sphere, which is the only artefact-free view")
    ap.add_argument("--rates", action="store_true", help="measure yield only")
    args = ap.parse_args()

    rs = numpy.random.default_rng(args.seed)
    collected = {t: [] for t in FUNCTIONS}
    counts = {t: 0 for t in FUNCTIONS}
    done = 0
    while done < args.samples:
        b = min(args.batch, args.samples - done)
        for table, pts in sweep(b, args.range, args.n, rs,
                                args.shape, args.normalise).items():
            counts[table] += len(pts)
            have = sum(len(c) for c in collected[table])
            if have < args.cap:
                collected[table].append(pts[: args.cap - have])
        done += b

    print(f"{done:,} samples, {args.shape} +/-{args.range:g}, n={args.n}"
          f"{', unit-normalised' if args.normalise else ''}\n")
    print(f"{'function':<16}{'hits':>12}{'rate':>12}")
    print("-" * 40)
    for table, name in FUNCTIONS.items():
        c = counts[table]
        print(f"{name:<16}{c:>12,}{c/done:>12.2e}")
    total = sum(counts.values())
    print("-" * 40)
    print(f"{'total':<16}{total:>12,}{total/done:>12.2e}")

    if args.out and not args.rates:
        os.makedirs(args.out, exist_ok=True)
        for table, name in FUNCTIONS.items():
            if not collected[table]:
                continue
            arr = numpy.concatenate(collected[table])
            path = os.path.join(args.out, f"{name}_syn1.csv")
            numpy.savetxt(path, arr, delimiter=",", fmt="%.8f")
            print(f"  wrote {len(arr):>7,} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
