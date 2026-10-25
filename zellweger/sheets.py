"""The ten typed sheets, transcribed line by line from scans/page-04.jpg to page-13.jpg.

The script is Shea Zellweger's Logic Alphabet. The derivations are the author's:
each sheet takes one rule of propositional logic and works it, in Zellweger's
glyphs, down to x, the tautology. On the sheets the operators are red and the
values black; the colour matters where a glyph such as d can be either, so
a black glyph is written with a leading underscore. Every token is separated
by a space, and the order and
position of every token is kept exactly as printed, slips included (see
KNOWN_SLIPS in check_sheets.py).

Tokens
------
  c u ɔ n      the variables as glyphs, for the "compressed" lines:
               c = A, u = B, ɔ = not A, n = not B
  A B C D      the variables as letters, for the expanded lines
  ~A ~B ...    a letter printed with a tilde over it: not A, not B
  d h ч Ի q p  the glyphs used as operators (or, in compressed lines, as values):
               d AND, h NAND, ч OR, Ի A-implies-B, q A-and-not-B, p NOR
  _d _Ի ...   a glyph printed black, used as a value: _d is the value A AND B,
               _Ի the value A-implies-B. Unmarked glyphs are the red operators.
  x            the tautology, which ends every derivation
  ( ) [ ]      brackets

Ի stands in for Zellweger's implication letter, a vertical flip of h, which
Unicode lacks. The rest are the nearest Unicode shapes.

Each sheet is (title, heading as printed, notation, lines). Notation is what
the lines actually are; the heading is what the sheet says, which differs on
the Modus Tollens sheet.
"""

# Destructive Dilemma and Constructive Dilemma end in a 24-term line printed in
# very small type. Both expand the line above it, term by term, into the
# sixteen rows of four variables, so they are written out here the same way.
DD_ROWS = ["A ~B ~C ~D", "A ~B ~C D", "A ~B C ~D", "A ~B C D",
           "~A ~B C ~D", "~A B C ~D", "A ~B C ~D", "A B C ~D",
           "~A B ~C D", "~A B C D", "A B ~C D", "A B C D",
           "~A ~B C ~D", "~A ~B C D", "~A B C ~D", "~A B C D",
           "~A ~B ~C ~D", "~A ~B ~C D", "~A B ~C ~D", "~A B ~C D",
           "A ~B ~C ~D", "A ~B ~C D", "A B ~C ~D", "A B ~C D"]
CD_ROWS = ["A ~B ~C ~D", "A ~B ~C D", "A ~B C ~D", "A ~B C D",
           "~A ~B C ~D", "~A B C ~D", "A ~B C ~D", "A B C ~D",
           "~A ~B ~C ~D", "~A ~B ~C D", "~A B ~C ~D", "~A B ~C D",
           "~A ~B ~C D", "~A ~B C D", "A ~B ~C D", "A ~B C D",
           "~A B ~C D", "~A B C D", "A B ~C D", "A B C D",
           "~A B ~C ~D", "~A B C ~D", "A B ~C ~D", "A B C ~D"]


def infix_rows(rows):
    return " ч ".join("( " + " d ".join(r.split()) + " )" for r in rows)


def postfix_rows(rows, ors):
    return " ".join(r + " d d d" for r in rows) + " ч" * ors


SHEETS = [
    ("Modus Ponens", 4, [
        ("Infix notation (compressed)", "infix", [
            "[ ( c Ի u ) d c ] Ի u",
            "[ _Ի d c ] Ի u",
            "_d Ի u",
            "x"]),
        ("Postfix notation (compressed)", "postfix", [
            "c u Ի c d u Ի",
            "_Ի c d u Ի",
            "_d u Ի",
            "x"]),
        ("Infix notation", "infix", [
            "[ ( A Ի B ) d A ] Ի B",
            "[ ( A Ի B ) h A ] ч B",
            "( A q B ) ч ~A ч B",
            "( A d ~B ) ч ~A ч B",
            "( A d ~B ) ч ( ~A d B ) ч ( ~A d ~B ) ч ( ~A d B ) ч ( A d B )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի A d B Ի",
            "A B Ի A h B ч",
            "A B q ~A ч B ч",
            "A ~B d ~A ч B ч",
            "A ~B d ~A ~B d ~A B d ~A B d A B d ч ч ч ч",
            "x"]),
    ]),
    ("Modus Tollens", 5, [
        ("Prefix notation (compressed)", "infix", [
            "[ ( c Ի u ) d n ] Ի ɔ",
            "[ _Ի d n ] Ի ɔ",
            "_p Ի ɔ",
            "x"]),
        ("Infix notation (compressed)", "postfix", [
            "c u Ի n d ɔ Ի",
            "_Ի n d ɔ Ի",
            "_p ɔ Ի",
            "x"]),
        ("Prefix notation", "infix", [
            "[ ( A Ի B ) d ~B ] Ի ~A",
            "[ ( A Ի B ) h ~B ] ч ~A",
            "( A q B ) ч B ч ~A",
            "( A d ~B ) ч B ч ~A",
            "( A d ~B ) ч ( A d B ) ч ( ~A d B ) ч ( ~A d B ) ч ( ~A d ~B )",
            "x"]),
        ("Infix notation", "postfix", [
            "A B Ի ~B d ~A Ի",
            "A B Ի ~B h ~A ч",
            "A B q B ч ~A ч",
            "A ~B d B ч ~A ч",
            "A ~B d A B d ~A B d ~A B d ~A ~B d ч ч ч ч",
            "x"]),
    ]),
    ("Hypothetical Syllogism", 6, [
        ("Infix notation", "infix", [
            "[ ( A Ի B ) d ( B Ի C ) ] Ի ( A Ի C )",
            "[ ( A Ի B ) h ( B Ի C ) ] ч ( A Ի C )",
            "( A q B ) ч ( B q C ) ч ( A Ի C )",
            "( A d ~B ) ч ( B d ~C ) ч ( A Ի C )",
            "( A d ~B ) ч ( B d ~C ) ч ( ~A ч C )",
            "( A d ~B ) ч ( B d ~C ) ч ( A d C ) ч ( ~A d C ) ч ( ~A d ~C )",
            "( A d ~B d C ) ч ( A d ~B d ~C ) ч ( A d B d ~C ) ч ( ~A d B d ~C ) ч "
            "( A d B d C ) ч ( A d ~B d C ) ч ( ~A d B d C ) ч ( ~A d ~B d C ) ч "
            "( ~A d B d ~C ) ч ( ~A d ~B d ~C )",
            "( ~A d ~B d ~C ) ч ( ~A d ~B d C ) ч ( ~A d B d ~C ) ч ( ~A d B d C ) ч "
            "( A d ~B d ~C ) ч ( A d ~B d C ) ч ( A d B d ~C ) ч ( A d B d C )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի B C Ի d A C Ի Ի",
            "A B Ի B C Ի h A C Ի ч",
            "A B q B C q ч A C Ի ч",
            "A ~B d B ~C d ч A C Ի ч",
            "A ~B d B ~C d ч ~A C ч ч",
            "A ~B d B ~C d ~A C ч ч ч",
            "A ~B d B ~C d A C d ~A C d ~A ~C d ч ч ч ч",
            "A ~B C d d A ~B ~C d d A B ~C d d ~A B ~C d d A B C d d "
            "A ~B C d d ~A B C d d ~A ~B C d d ~A B ~C d d ~A ~B ~C d d"
            + " ч" * 9,
            "~A ~B ~C d d ~A ~B C d d ~A B ~C d d ~A B C d d "
            "A ~B ~C d d A ~B C d d A B ~C d d A B C d d" + " ч" * 7,
            "x"]),
    ]),
    ("Disjunction Introduction", 7, [
        ("Infix notation (compressed)", "infix", [
            "c Ի ( c ч u )",
            "c Ի _ч",
            "x"]),
        ("Postfix notation (compressed)", "postfix", [
            "c c u ч Ի",
            "c _ч Ի",
            "x"]),
        ("Infix notation", "infix", [
            "A Ի ( A ч B )",
            "~A ч A ч B",
            "( ~A d B ) ч ( ~A d ~B ) ч ( A d B ) ч ( A d ~B ) ч ( A d B ) ч ( ~A d B )",
            "x"]),
        ("Postix notation", "postfix", [
            "A A B ч Ի",
            "~A A B ч ч",
            "~A B d ~A ~B d A B d A ~B d A B d ~A B d ч ч ч ч ч",
            "x"]),
    ]),
    ("Simplification", 8, [
        ("Infix notation (compressed)", "infix", [
            "( c d u ) Ի c",
            "_d Ի c",
            "x"]),
        ("Postfix notation (compressed)", "postfix", [
            "c u d c Ի",
            "_d c Ի",
            "x"]),
        ("Infix notation", "infix", [
            "( A d B ) Ի A",
            "( A h B ) ч A",
            "~A ч ~B ч A",
            "( ~A d ~B ) ч ( ~A d B ) ч ( ~A d ~B ) ч ( A d ~B ) ч ( A d ~B ) ч ( A d B )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B d A Ի",
            "A B h A ч",
            "~A ~B ч A ч",
            "~A ~B d ~A B d ~A ~B d A ~B d A ~B d A B d ч ч ч ч ч",
            "x"]),
    ]),
    ("Absorption", 9, [
        ("Infix notation (compressed)", "infix", [
            "( c Ի u ) Ի ( c Ի ( c d u ) )",
            "( c Ի u ) Ի ( c Ի _d )",
            "_Ի Ի _Ի",
            "x"]),
        ("Postfix notation (compressed)", "postfix", [
            "c u Ի c c u d Ի Ի",
            "_Ի c c u d Ի Ի",
            "_Ի c _d Ի Ի",
            "_Ի _Ի Ի",
            "x"]),
        ("Infix notation", "infix", [
            "( A Ի B ) Ի [ A Ի ( A d B ) ]",
            "( A Ի B ) Ի [ ~A ч ( A d B ) ]",
            "( A q B ) ч ~A ч ( A d B )",
            "( A d ~B ) ч ~A ч ( A d B )",
            "( A d ~B ) ч ( ~A d B ) ч ( ~A d ~B ) ч ( A d B )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի A A B d Ի Ի",
            "A B Ի ~A A B d ч Ի",
            "A B q ~A A B d ч ч",
            "A ~B d ~A A B d ч ч",
            "A ~B d ~A B d ~A ~B d A B d ч ч ч",
            "x"]),
    ]),
    ("Destructive Dilemma", 10, [
        ("Infix notation", "infix", [
            "[ ( A Ի B ) d ( C Ի D ) d ( ~B ч ~D ) ] Ի ( ~A ч ~C )",
            "( A d ~B ) ч ( C d ~D ) ч ( B d D ) ч ( ~A ч ~C )",
            "( A d ~B ) ч ( C d ~D ) ч ( B d D ) ч ( ~A d C ) ч ( ~A d ~C ) ч ( A d ~C )",
            infix_rows(DD_ROWS),
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի C D Ի ~B ~D ч d d ~A ~C ч Ի",
            "A ~B d C ~D d B D d ~A ~C ч ч ч ч",
            "A ~B d C ~D d B D d ~A C d ~A ~C d A ~C d ч ч ч ч ч",
            postfix_rows(DD_ROWS, 23),
            "x"]),
    ]),
    ("Constructive Dilemma", 11, [
        ("Infix notation", "infix", [
            "[ ( A Ի B ) d ( C Ի D ) d ( A ч C ) ] Ի ( B ч D )",
            "( A q B ) ч ( C q D ) ч ( A p C ) ч ( B ч D )",
            "( A d ~B ) ч ( C d ~D ) ч ( ~A d ~C ) ч ( B ч D )",
            "( A d ~B ) ч ( C d ~D ) ч ( ~A d ~C ) ч ( ~B d D ) ч ( B d D ) ч ( B d ~D )",
            infix_rows(CD_ROWS),
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի C D Ի A C ч d d B D ч Ի",
            "A B q C D q A C p B D ч ч ч ч",
            "A ~B d C ~D d ~A ~C d B D ч ч ч ч",
            "A ~B d C ~D d ~A ~C d ~B D d B D d B ~D d ч ч ч ч ч",
            postfix_rows(CD_ROWS, 25),
            "x"]),
    ]),
    ("Composition", 12, [
        ("Infix notation", "infix", [
            "[ ( A Ի B ) d ( A Ի C ) ] Ի [ A Ի ( B d C ) ]",
            "[ ( A Ի B ) d ( A Ի C ) ] Ի [ ~A ч ( B d C ) ]",
            "[ ( A Ի B ) h ( A Ի C ) ] ч [ ~A ч ( B d C ) ]",
            "( A q B ) ч ( A q C ) ч ~A ч ( B d C )",
            "( A d ~B ) ч ( A d ~C ) ч ~A ч ( B d C )",
            "( A d ~B d ~C ) ч ( A d ~B d C ) ч ( A d ~B d ~C ) ч ( A d B d ~C ) ч "
            "( ~A d ~B d ~C ) ч ( ~A d ~B d C ) ч ( ~A d B d ~C ) ч ( ~A d B d C ) ч "
            "( ~A d B d C ) ч ( A d B d C )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B Ի A C Ի d A B C d Ի Ի",
            "A B Ի A C Ի d ~A B C d ч Ի",
            "A B Ի A C Ի h ~A B C d ч ч",
            "A B q A C q ~A B C d ч ч ч",
            "A ~B d A ~C d ~A B C d ч ч ч",
            "A ~B ~C d d A ~B C d d A ~B ~C d d A B ~C d d ~A ~B ~C d d "
            "~A ~B C d d ~A B ~C d d ~A B C d d ~A B C d d A B C" + " ч" * 9,
            "x"]),
    ]),
    ("Resolution", 13, [
        ("Infix notation", "infix", [
            "[ ( A ч B ) d ( ~A ч C ) ] Ի ( B ч C )",
            "[ ( A ч B ) h ( ~A ч C ) ] ч ( B ч C )",
            "( A p B ) ч ( ~A p C ) ч ( B ч C )",
            "( ~A d ~B ) ч ( A d ~C ) ч ( B ч C )",
            "( ~A d ~B ) ч ( A d ~C ) ч ( ~B d C ) ч ( B d C ) ч ( B d ~C )",
            "( ~A d ~B d C ) ч ( ~A d ~B d ~C ) ч ( A d ~B d ~C ) ч ( A d B d ~C ) ч "
            "( ~A d ~B d C ) ч ( A d ~B d C ) ч ( ~A d B d C ) ч ( A d B d C ) ч "
            "( ~A d B d ~C ) ч ( A d B d ~C )",
            "x"]),
        ("Postfix notation", "postfix", [
            "A B ч ~A C ч d B C ч Ի",
            "A B ч ~A C ч h B C ч ч",
            "A B p ~A C p B C ч ч ч",
            "~A ~B d A ~C d B C ч ч ч",
            "~A ~B d A ~C d ~B C d B C d B ~C d ч ч ч ч",
            "~A ~B C d d ~A ~B ~C d d A ~B ~C d d A B ~C d d ~A ~B C d d "
            "A ~B C d d ~A B C d d A B C d d ~A B ~C d d A B ~C d d" + " ч" * 9,
            "x"]),
    ]),
]
