# Rules of inference in Zellweger's Logic Alphabet

**[← All projects](https://gernreich.github.io/)**

**The script is Shea Zellweger's.** Zellweger (1925–2022), who chaired
psychology at Mount Union College in Alliance, Ohio, created the Logic
Alphabet: a letter for each of the sixteen binary connectives, shaped so that
flipping or turning a letter performs the matching logical operation. The
glyphs, their shapes and their names are his, and so is the handwritten letter
here.

**The derivations are this repository's author's.** The ten typed sheets take
Zellweger's script and work common rules of propositional logic in it, from the
rule down to x, the tautology. They are set in the author's colour glyph font,
with the operators in red.

**[See it all on one page →](https://gernreich.github.io/Logic-Research/zellweger.html)**

## How the script works

Each glyph stands on a square of four places, one for each row of the truth
table (TT, TF, FT, FF), with a stem wherever the function is true. A glyph *is*
its truth table, so A and B can be written as glyphs too, and a formula can be
computed on shapes:

| glyph | rows TT TF FT FF | meaning |
|---|---|---|
| x | 1111 | tautology |
| d | 1000 | A and B |
| h | 0111 | not (A and B) |
| ч | 1110 | A or B |
| p | 0001 | neither A nor B |
| Ի | 1011 | A implies B |
| q | 0100 | A and not B |
| c, ɔ | 1100, 0011 | A, not A |
| u, n | 1010, 0101 | B, not B |

The letters are Unicode stand-ins. Ի stands for Zellweger's implication
letter, a vertical flip of his h.

A letter with a tilde, such as Ã, means *not A*. In the expanded lines the
variables are letters, not glyphs, so there is nothing to flip and the tilde
carries the negation. That lets every operator but *and* and *or* drop out. In
the last lines each bracket then names one row of the truth table, and the rule
holds when the brackets cover every row.

## What the check finds

Each of the ten sheets is worked four ways when it has two variables
(compressed and expanded, each in infix and in postfix) and two ways when it
has three or four. `check_sheets.py` parses all 130 lines and evaluates each on
every row of its truth table:

- **128 lines are tautologies as printed.** Every block ends in x.
- **The compressed lines compute as the sheets say.** In modus ponens, c Ի u
  gives Ի back, Ի d c gives d, and d Ի u gives x. In absorption the line comes
  down to Ի Ի Ի, which is x.
- **Two lines in the small print have a slip.** Both are tautologies once
  corrected:
  - Constructive Dilemma, last postfix line: 25 ORs join 24 terms, where 23
    are needed.
  - Composition, last postfix line: the last term, A B C, is missing its
    `d d`.
- **The Modus Tollens headings are one notation off.** Its infix blocks are
  headed "Prefix notation" and its postfix blocks "Infix notation". The parser
  confirms which notation each block really is.
- **Disjunction Introduction says "Postix" for Postfix.**

Colour matters on the sheets: a black glyph is a value and a red one is an
operator. Absorption's compressed postfix line Ի c d Ի Ի reads only one way
once that is kept, so the transcription marks black glyphs (`_d`, `_Ի`).

## Files

| File | What it is |
|---|---|
| `scans/page-01.jpg` … `page-13.jpg` | the envelope, Zellweger's two handwritten pages, then the ten typed sheets |
| `transcription.md` | the envelope and the letter, transcribed, with what the letter says |
| `sheets.py` | the ten typed sheets, transcribed token by token |
| `check_sheets.py` | parses and evaluates every line; exits 1 on any problem apart from the two known slips |
| `build_page.py` | writes `../docs/zellweger.html` and copies the scans to `../docs/zellweger/`; stops if the check fails |

    python3 check_sheets.py
    python3 build_page.py

The scans are made from a scanned PDF at 2400 pixels on the long side. They
are converted to sRGB and saved with no metadata. On the envelope, the street
address and the post office's barcodes are blacked out. The two sheets that
were scanned upside down (Hypothetical Syllogism and Constructive Dilemma) are
turned upright.

## Licence

The Logic Alphabet is Shea Zellweger's (U.S. Patent 4,273,542), and so are his
letter and its scans. The repository's CC0 dedication does not cover them. It
covers the transcription method, the checker and the page.
