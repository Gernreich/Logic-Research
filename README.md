# Sixteen Functions, Two Ways

There are exactly sixteen boolean functions of two variables. This asks two
questions about them at once.

**Symbolically** — compose them into deep expression trees and find which
compositions are tautologies. 2²⁸ expressions filter down to 32 irreducible
ones, rendered as English.

**Geometrically** — a 2–3–1 network's hidden→output weights are three numbers,
so every set of weights that computes a given function is a *point in 3D*.
Collect enough and each function has a visible solution region.

**[Read it and explore →](https://gernreich.github.io/Logic-Research/)**

- **[Weight Space Shells](https://gernreich.github.io/Logic-Research/shells.html)**
  — all sixteen functions as rotatable clouds, generated vs. the 2019 archive
- **[Sixteen Cones](https://gernreich.github.io/Logic-Research/cones.html)**
  — the same regions from a cube, a ball, and as pure directions
- **[Gates of Gates](https://gernreich.github.io/Logic-Research/gates-of-gates.html)**
  — every function applied to every pair of functions, 4,096 cells
- **[The 506 Programs](https://gernreich.github.io/Logic-Research/programs-506.html)**
  — the distinct lambda terms behind those cells, in eight notations
- **[Gates of Gates, the document](https://gernreich.github.io/Logic-Research/gates-of-gates-document.html)**
  — all of it in one self-contained file (10.5 MB)

## The sixteen functions in lambda calculus

[`lambda16.txt`](https://gernreich.github.io/Logic-Research/lambda16.txt) writes all sixteen functions as lambda terms and
reduces each one on all four inputs. [`gates-of-gates/`](gates-of-gates/)
applies every function to every pair of functions, 4,096 cells, computed from
those terms; its [interactive version](https://gernreich.github.io/Logic-Research/gates-of-gates.html)
is on the public site.

## Layout

    python/          enumeration and tautology filtering
    ANN/             weight-space search and the point clouds
    docs/            the viewer (GitHub Pages serves from here)
    gates-of-gates/  all 16 gates applied to every pair of gates (the 1995 poster, recomputed)
    lambda16.txt     the sixteen functions as lambda terms, with every β-reduction

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

    # ball-sampled and direction-only (used by the Cones viewer)
    python3 ANN/generate_clouds.py --samples 120000000 --range 20 --n 0.9 \
        --seed 2 --shape ball --cap 11000 --out ANN/clouds_ball
    python3 ANN/generate_clouds.py --samples 120000000 --range 20 --n 0.9 \
        --seed 3 --shape ball --normalise --cap 11000 --out ANN/clouds_dir

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
million samples at ±10.

The deeper reason: **each solution set is a cone.** If a weight vector works, so
does every positive multiple of it — verified on 400 accepted sets across five
scale factors, 2,000 checks, zero failures. The set is unbounded, so whatever
region you sample from draws the cloud's outer surface; a cube gives flat faces,
a ball gives a round hull, and neither is real. Only the directions are
intrinsic, and on the unit sphere:

| function | sphere covered |
|---|---|
| `TRUE` / `FALSE` | 47.2% |
| `IMPLICATION` and kin | 35.0% |
| `P`, `Q`, `NOT P`, `NOT Q` | 34.8% |
| `AND` / `NAND` | 28.4% |
| `XOR` / `XNOR` | **4.8%** |

`XOR` is hard because only 4.8% of directions work for it.

**Not novel.** Complementary functions have mirror-image solution regions
because `sigmoid(−x) = 1 − sigmoid(x)`; that is one line of algebra, not a
discovery. That `XOR` needs a hidden layer has been known since Minsky and
Papert (1969).

## Sum and carry, drawn three ways

Hand drawings of a full adder's two outputs, each a function of three inputs:
**sum** is TRUE when an odd number of inputs are TRUE, and **carry** is TRUE when
at least two are. Each is drawn as a three-set Venn diagram in three styles:
round circles, a square Venn (the same encoding as the 1995 poster in
[`gates-of-gates/`](gates-of-gates/)), and curves built from sine waves.

| Circles and square Venns | Adding the sine-wave Venns | Sine Venn, three sets |
|---|---|---|
| <img src="sum-carry-venn.jpg" width="260" alt="Sum and carry as three-circle Venn diagrams and as square Venn diagrams"> | <img src="sum-carry-venn-sine.jpg" width="260" alt="The same page with sum and carry also drawn as sine-wave Venn diagrams"> | <img src="sum-carry-Sine.jpg" width="260" alt="A coloured three-set Venn diagram built from sine waves, labelled Sine Venn 3 set"> |
| `sum-carry-venn.jpg` | `sum-carry-venn-sine.jpg` | `sum-carry-Sine.jpg` |

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

`docs/` holds three self-contained pages — an explanation at `index.html` and
the two viewers — with all data inlined, no build step, and no external requests
beyond Google Fonts. Pages serves from **main / docs**.
