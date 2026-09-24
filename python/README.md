# Boolean function enumeration / tautology search

Work from Feb–Sep 2019: enumerate compositions of the sixteen two-variable
boolean functions over 4-bit operands, then filter the results down to a
minimal set of tautologies.

Refactored to documented Python 3 on 2026-08-26. **The 2019 originals are
preserved untouched in `original_2019/`.**

## Code

| file | what |
|---|---|
| `boolean16.py` | the core. The sixteen operations with their names, the expansion generator, the tautology scan. Read this first — it documents the encoding and the `last=16` quirk |
| `enumerate_full.py` | all sixteen ops, three expansions → 268,435,456 values. Writes `TotalFirstSeven` + `TotalTau` |
| `enumerate_narrowed.py` | eight ops, four q-values, **two** expansions → 8,192 values. Writes `FirstSeven` |
| `test_boolean16.py` | self-checks, no framework needed. `python3 test_boolean16.py` |
| `original_2019/` | the untouched Python 2 originals |

    python3 test_boolean16.py                    # verify everything still works
    python3 enumerate_narrowed.py --verify       # regenerate and diff vs 2019
    python3 enumerate_full.py --count            # sizes without writing
    python3 enumerate_full.py                    # ~1 GB of output

## Two things that will bite you

**The `last=16` quirk.** The full run's third expansion ends each block with
`16`, not `15`. Sixteen isn't a valid 4-bit value and is almost certainly a
2019 typo — but the tautology scan counts values equal to 15, so that slot is
never counted, and the archived data depends on it. It is preserved by
default. `enumerate_full.py --correct` uses 15 instead and produces output
that will **not** match the 2019 files. Full explanation in `boolean16.py`.

**The narrowed run does two expansions, not three.** In the original,
`firstthree` was a literal list of eight seeds with its expansion commented
out. A third expansion gives 262,144 values rather than 8,192. The refactor
got this wrong at first and `--verify` caught it.

## Data — the filter chain

`narrowed_enumeration_8192_values.txt` is `enumerate_narrowed.py`'s output as
recorded in 2019. **Do not delete it**: it is the only end-to-end proof that
the refactor preserves behaviour, and `test_boolean16.py` checks against it.

Each file below is a verified strict subset of the one above:

| file | entries | meaning |
|---|---|---|
| `tautologies_1_all_17744.hex` | 17,744 | every tautology in the full run's third expansion that uses only the eight narrowed operations and the four narrowed q-values (131,072 positions) |
| `tautologies_2_and_implies_1176.hex` | 1,176 | restricted to and/implies forms |
| `tautologies_3_pq_and_implies_70.hex` | 70 | restricted to P,Q and/implies |
| `tautologies_4_deduped_38.hex` | 38 | duplicates removed |
| `tautologies_5_no_reflections_32.hex` | 32 | P↔Q reflections removed |
| `tautologies_6_english_39.txt` | 32 | rendered as English, in 39 lines (blank lines separate the groups), e.g. `P and Q and Q -> P   reduces to P and Q -> P` |
| `tautologies_english_draft_incomplete.txt` | 32 | earlier rendering attempt; placeholders never substituted |

The scripts that produced the filter chain were not kept — only their output.
The first file can be recomputed: it is exactly the value-15 positions of the
full run with the seed and every q drawn from `Q_VALUES` and every operation
from `NARROWED_OPS` (4 × 32³ = 131,072 positions). Its
entries are full-run indices (seven hex digits), not positions in the
8,192-value narrowed run, which holds only 980 tautologies.

## Deleted, and how to get it back

`TotalFirstSeven` (648 MB) and `TotalTau` (370 MB) were deleted 2026-08-26
after being verified reproducible. Run `enumerate_full.py` to recreate them.

## Provenance

`enumerate_full.py` replaces a Python 3 port written on 2026-08-26 that was
verified byte-identical against the original data *before* that data was
deleted; this version was in turn verified identical to that port. The
narrowed script is verified directly against 2019 output.
