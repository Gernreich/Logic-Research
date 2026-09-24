# Neural nets learning boolean functions

Companion to `../python/` (the exhaustive enumeration). Here small networks
are pointed at the same boolean functions. Sep 2019.

Refactored to documented Python 3 on 2026-08-26. **The 2019 originals are
preserved untouched in `original_2019/`.**

## The correction that matters

The seven original scripts were all named `train_*` by an earlier renaming
pass. **That was wrong for six of them.** Only one does backpropagation. The
other six perform *random weight search*: sample weights from hand-picked
ranges, run a single forward pass, record the weights whenever the output
lands inside a tolerance window. No gradient, no learning.

## Code

| file | what |
|---|---|
| `nncore.py` | shared core — the four inputs, truth tables by name, sigmoid and ReLU, the forward pass, the tolerance test |
| `train_nand_backprop.py` | the one real trainer. Sweeps seeds, reports which converge |
| `search_weights.py` | random weight search — replaces five scripts that differed only in constants |
| `search_all_functions.py` | searches for **all sixteen** functions in one pass — replaces the six `RandomWeightSearch_N.py` (1,050 lines) |
| `train_graded.py` | 4-bit input → one graded output, 16 levels — replaces the `four_to_sixteen_architecture/` backprop variants |
| `test_nncore.py` | self-checks. `python3 test_nncore.py` |
| `original_2019/` | the seven untouched originals |

    python3 test_nncore.py
    python3 train_nand_backprop.py --seeds 1000 1010
    python3 search_weights.py --target NOR --preset gold --max-iter 200000

## Three things found while refactoring

**Where the `a`–`g` files came from.** `train_relu_5arg.py` took an output
prefix as `argv[4]` and appended to `<prefix>l2`, `<prefix>syn0`,
`<prefix>syn1`. Running it as `... a`, `... b` produced `run_a_*` through
`run_g_*`. An earlier README here claimed that mapping was "lost"; it was in
the source all along. The letters are command-line labels, nothing more.

**`train_random_weight_search_v4.py` has never run.** Line 16 is
`zz=int(arg2/2)` where `arg2` is a string from `sys.argv` — `TypeError:
unsupported operand type(s) for /: 'str' and 'int'`. Line 18 (`o=1-arg3`)
would fail the same way. It is preserved as-is; `search_weights.py` covers
what it was meant to do.

**The `R9NAND__*` files were written by a NOR search.** Those scripts accept
when the output is `(1,0,0,0)` — that is NOR. NAND is `(1,1,1,0)`. Either the
filenames are mislabelled or the condition was not the intended one; the data
cannot say which. `nncore.TARGETS` keeps the names honest.

## Run outputs — `run_{a..g}_*`

Seven recorded searches. For each letter:

- `run_X_syn0_layer0_weights.txt` — input→hidden weights
- `run_X_syn1_layer1_weights.txt` — hidden→output weights
- `run_X_l2_predictions.txt` — the four outputs

The predictions say whether anything was found. Run `a` is
`[0.4998, 0.5000, 0.5000, 0.4999]` — all ≈0.5, nothing learned. Compare
`training_log_2019-08-29_nand_converged.txt`:
`[0.99998, 0.99902, 0.99902, 0.00154]`, a clean NAND.

`train_nand_backprop.py` reproduces both outcomes: seed 1000 converges,
seed 1001 sticks at 0.5. Both are asserted in the test suite.

## Search presets

`gold` and `tight` sample narrow ranges around a known solution; `wide` is
less constrained; `relu` uses 2×2/2×1 shapes with ReLU. Hit rates are very
low by design — the 2019 scripts looped `range(30000000000)` and were killed
by hand. `search_weights.py` defaults to 1,000,000 samples; pass
`--max-iter 0` for the original unbounded behaviour.

## Directories

| dir | size | contents |
|---|---|---|
| `iamtrask_boolean_function_runs/` | 28M | weights per function — `nand`, `or`, `implication`, `revimplication`, `notp`, `notq`, `p`, `q`, `pminusq`, `qminusp`, `R9XOR`; plus the six `RandomWeightSearch_N.py`: `RandomWeightSearch_0.py`, `RandomWeightSearch_1.py`, `RandomWeightSearch_2.py`, `RandomWeightSearch_3.py`, `RandomWeightSearch_5.py` and `RandomWeightSearch_6.py` (there is no `_4`) |
| `identity_function_runs/` | 5.2M | identity-function experiments (was `IDENITY`) |
| `relu_activation_runs/` | 128K | the same `a..g` layout, ReLU |
| `four_to_sixteen_architecture/` | 28K | 4→16 width experiments |

### Subdirectory scripts (refactored 2026-08-26)

The 22 scripts inside those folders collapsed into two:

**`search_all_functions.py`** replaces the six `RandomWeightSearch_N.py`
(175 lines each). They differed in exactly two things: the seed, and a letter
appended to every filename — `_0`→seed 0/`z`, `_1`→1/`a`, `_2`→2/`b`,
`_3`→3/`c`, `_5`→5/`e`, `_6`→6/`f`. **So the `a`–`g` suffixes encode the
random seed**, confirming from a second direction what `argv[4]` showed.

**`train_graded.py`** replaces the `four_to_sixteen_architecture/` variants.
That folder's name is literal: feed all sixteen 4-bit patterns, ask one
output neuron for sixteen distinguishable levels (target = i/15). It works —
120,000 iterations gives max error 0.0065 against a level spacing of 0.0667.

Not covered: `TwoOne.py` (a different experiment — two inputs, one layer,
target `[0.5, 0.51, 0.51, 0.0]`) and the `Sixteen/tempp/` variants. All
originals remain where they were.

### Three labelling errors in the 2019 output files

Derived by reading the accept conditions, not the filenames:

| output | 2019 filename | what it actually is |
|---|---|---|
| `(1,0,0,0)` | `R9NAND__*` | **NOR** |
| `(1,0,1,1)` | `R9IMPLICATION__*` | **Q→P**, the converse |
| `(1,1,0,1)` | `R9REVIMPLICATION__*` | **P→Q**, implication |

So implication and its converse are swapped, and the NAND-named files hold
NOR solutions. **Real NAND `(1,1,1,0)` was never searched for at all** — no
accept condition exists for it, despite `nand_syn0` / `nand_syn1` on disk.
`search_all_functions.py` uses correct names; `--legacy-names` reproduces the
2019 filenames, errors included, for comparison. Asserted in the tests.

### Why the search was so slow

Over 3,000,000 samples with the 2019 constants: **295,704 hits were FALSE or
TRUE** — the trivial constants — and just two were anything else (one
`NOT_Q`, one `OR`). That is why those two were commented out of the originals
and why they looped `range(30000000000)`.

### Scripts that have never run

- `original_2019/train_random_weight_search_v4.py` — `TypeError` on line 16
- `four_to_sixteen_architecture/working.py` — `IndentationError`, plus
  Python-2 `xrange` and a `np.` prefix while importing `numpy`

## Other files

- `numpy_array_to_csv.sed` — strips brackets, spaces to commas
- `scratch_weight_dumps.txt` — loose matrices, no run attached
- `*.nb` — Mathematica notebooks: `xor.nb`, `xor_narrow.nb`, `simpleXOR.nb`,
  `gaussian.nb`

## Verification

`test_nncore.py` reproduces the original gold sampling inline and asserts the
refactored `sample()` yields identical weights across four seeds, and checks
both backprop outcomes. Hit rates were compared directly against the 2019
code over 50,000 samples: both find 0 hits with the `gold` preset, confirming
the refactor is faithful rather than merely similar.
