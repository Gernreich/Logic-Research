# Sixteen Functions, Two Ways

There are exactly sixteen boolean functions of two variables. This asks two
questions about them at once.

**Symbolically** — compose them into deep expression trees and find which
compositions are tautologies. 2²⁸ expressions filter down to 32 irreducible
ones, rendered as English.

**Geometrically** — a 2–3–1 network's hidden→output weights are three numbers,
so every set of weights that computes a given function is a *point in 3D*.
Collect enough and each function has a visible solution region.

**[Interactive viewer →](https://gernreich.github.io/weight-space-shells/)** — all sixteen
functions, rotatable, comparing generated clouds against the 2019 archive.

## Layout

    python/   enumeration and tautology filtering
    ANN/      weight-space search and the point clouds
    docs/     the viewer (GitHub Pages serves from here)

Both halves have their own README with file-by-file detail. Original 2019
scripts are preserved untouched in each `original_2019/`.

## Quick start

    python3 python/test_boolean16.py          # 18 checks
    python3 ANN/test_nncore.py                # 29 checks

    # measure how hard each function is to hit
    python3 ANN/generate_clouds.py --samples 4000000 --range 20 --rates

    # regenerate the clouds the viewer uses (~46s)
    python3 ANN/generate_clouds.py --samples 200000000 --range 20 --n 0.9 \
        --seed 1 --cap 12000 --out ANN/generated_clouds

## What this is and isn't

The useful parts are empirical and pedagogical, not novel.

**Worth having.** Random search makes function difficulty *measurable*.
Sampling uniformly from ±20:

| function | hit rate |
|---|---|
| `TRUE` / `FALSE` | 2.0 × 10⁻¹ |
| `IMPLICATION` and kin | 1.3 × 10⁻² |
| `P`, `Q`, `NOT P`, `NOT Q` | ~1.0 × 10⁻² |
| `AND`, `NAND` | 1.6 × 10⁻³ |
| `XOR`, `XNOR` | 4.4 × 10⁻⁵ |

Below about ±15, `XOR` is not merely rare — it is **absent**: zero hits in four
million samples at ±10. That is a sharper statement of "XOR is hard" than the
usual hand-wave, and the viewer makes it visible.

**Not novel.** Complementary functions have mirror-image solution regions
because `sigmoid(−x) = 1 − sigmoid(x)`; that is one line of algebra, not a
discovery. That `XOR` needs a hidden layer has been known since Minsky and
Papert (1969).

## Notes on the 2019 data

The archived clouds are kept because they are **not** reproducible — the exact
parameters of those runs were never recorded. Generated data is gitignored.

Some archived filenames do not describe their contents. Verified by running the
forward pass rather than trusting names:

| output | filename | actually is |
|---|---|---|
| `(1,0,0,0)` | `R9NAND__*` | **NOR** |
| `(1,0,1,1)` | `R9IMPLICATION__*` | **Q → P**, the converse |
| `(1,1,0,1)` | `R9REVIMPLICATION__*` | **P → Q**, implication |

Real `NAND` was never searched for in those scripts. The errors are not
uniform — the `262k` folder's names are correct, from a later fix.

Two scripts have never run: `ANN/original_2019/train_random_weight_search_v4.py`
(`TypeError`, string arithmetic on `sys.argv`) and
`ANN/four_to_sixteen_architecture/working.py` (`IndentationError`, plus Python-2
`xrange`).

## Publishing the viewer

`docs/index.html` is self-contained — data inlined, no build step, no external
requests beyond Google Fonts. In repository settings, set Pages to serve from
**main / docs**, then update the viewer link above.
