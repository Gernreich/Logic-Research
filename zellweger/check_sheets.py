#!/usr/bin/env python3
"""Check every line of the ten typed sheets (sheets.py).

For each line this parses it, as infix and as postfix, and evaluates it on
every row of the truth table of the sheet's variables. A derivation is sound
when every line is a tautology, so that is what is checked, together with:

  * the notation each block really is, found by which parser accepts it, set
    against the heading printed on the sheet;
  * that each block ends in x;
  * for the compressed lines, the glyph every operation produces, so that
    "c Ի u" can be seen to give Ի itself.

Two lines on the sheets do not parse as printed. They are listed in
KNOWN_SLIPS with the reading that the line above them implies; the check
confirms that each slip fails exactly as described and that the corrected
line is a tautology. Anything else that fails stops the script with exit 1.

    python3 check_sheets.py           # the report
    python3 check_sheets.py --quiet   # only failures and the summary
"""
import itertools
import sys

from sheets import SHEETS

# Glyphs as operators: a function of two truth values.
OPS = {
    "d": lambda a, b: a and b,            # AND
    "h": lambda a, b: not (a and b),      # NAND
    "ч": lambda a, b: a or b,             # OR
    "Ի": lambda a, b: (not a) or b,       # A implies B
    "q": lambda a, b: a and not b,        # A and not B
    "p": lambda a, b: not (a or b),       # NOR
}
ASSOCIATIVE = {"d", "ч"}
# Glyphs as values in the compressed lines: the connective applied to A and B,
# and the four variable glyphs.
GLYPH_VALUE = {g: (lambda f: lambda r: f(r["A"], r["B"]))(f) for g, f in OPS.items()}
GLYPH_VALUE.update({
    "c": lambda r: r["A"], "ɔ": lambda r: not r["A"],
    "u": lambda r: r["B"], "n": lambda r: not r["B"],
    "x": lambda r: True,
})
# The name of a two-variable truth table (rows TT, TF, FT, FF), for the
# compressed lines' intermediate values.
def _table(f):
    return tuple(bool(f({"A": a, "B": b})) for a, b in ((1, 1), (1, 0), (0, 1), (0, 0)))
GLYPH_OF_TABLE = {_table(GLYPH_VALUE[g]): g for g in "x d h ч Ի q p c ɔ u n".split()}

# A line on the sheet that does not parse, keyed by (sheet title, block heading,
# line number from 1), with what is wrong and the reading that would parse.
KNOWN_SLIPS = {
    ("Constructive Dilemma", "Postfix notation", 5): (
        "25 ORs close the 24 terms; 23 are needed, so the last two have "
        "nothing left to join",
        lambda line: line[: -len(" ч ч")]),
    ("Composition", "Postfix notation", 6): (
        "the last term A B C has no d d, so it is never joined into one "
        "term and nine ORs are two short of what twelve items need",
        lambda line: line.replace("A B C ч", "A B C d d ч", 1)),
}


class ParseError(Exception):
    pass


def literal(tok):
    """A value token as a function of the row, or None if it is not one."""
    if tok.startswith("_") and tok[1:] in OPS:
        return GLYPH_VALUE[tok[1:]]      # a glyph printed black: a value
    if tok in GLYPH_VALUE and tok not in OPS:
        return GLYPH_VALUE[tok]
    neg = tok.startswith("~")
    v = tok.lstrip("~")
    if v in "ABCD" and len(v) == 1:
        return (lambda r: not r[v]) if neg else (lambda r: r[v])
    return None


# ---- infix -----------------------------------------------------------------
# expr := term (op term)* ; term := value | ( expr ) | [ expr ]
# A chain without brackets must use one operator, and an associative one.

def parse_infix(tokens):
    pos = 0

    def term():
        nonlocal pos
        if pos >= len(tokens):
            raise ParseError("line ends where a value is expected")
        t = tokens[pos]
        if t in "([":
            close = ")" if t == "(" else "]"
            pos += 1
            node = expr()
            if pos >= len(tokens) or tokens[pos] != close:
                raise ParseError(f"missing {close}")
            pos += 1
            return node
        if literal(t) is None:
            raise ParseError(f"{t} where a value is expected")
        pos += 1
        return ("val", t)

    def expr():
        nonlocal pos
        node = term()
        ops = []
        while pos < len(tokens) and tokens[pos] in OPS:
            op = tokens[pos]
            pos += 1
            ops.append(op)
            node = ("op", op, node, term())
        if len(ops) > 1 and (len(set(ops)) > 1 or ops[0] not in ASSOCIATIVE):
            raise ParseError("a chain mixes operators without brackets: " + " ".join(ops))
        return node

    node = expr()
    if pos != len(tokens):
        raise ParseError(f"left over: {' '.join(tokens[pos:])}")
    return node


# ---- postfix ---------------------------------------------------------------
# Values push; a (red) operator pops two and pushes one. One value must be left.

def parse_postfix(tokens):
    if any(t in "()[]" for t in tokens):
        raise ParseError("brackets in a postfix line")
    stack = []
    for i, t in enumerate(tokens):
        if literal(t) is not None:
            stack.append(("val", t))
        elif t in OPS:
            if len(stack) < 2:
                rest = len(tokens) - i
                raise ParseError(f"operator {i + 1} of {len(tokens)} ({t}) finds "
                                 f"{len(stack)} value{'s' * (len(stack) != 1)} to join, "
                                 f"with {rest} token{'s' * (rest != 1)} still to come")
            b, a = stack.pop(), stack.pop()
            stack.append(("op", t, a, b))
        else:
            raise ParseError(f"unknown token {t}")
    if len(stack) != 1:
        raise ParseError(f"{len(stack)} values are left, not one")
    return stack[0]


# ---- evaluation ------------------------------------------------------------

def evaluate(node, row):
    if node[0] == "val":
        return bool(literal(node[1])(row))
    _, op, a, b = node
    return bool(OPS[op](evaluate(a, row), evaluate(b, row)))


def rows_of(variables):
    for bits in itertools.product((True, False), repeat=len(variables)):
        yield dict(zip(variables, bits))


def variables_of(lines):
    found = sorted({t.lstrip("~") for line in lines for t in line.split()} & set("ABCD"))
    return found or ["A", "B"]


def compressed_steps(node, out):
    """The glyph each operation in a compressed line produces, innermost first."""
    if node[0] == "val":
        return node[1].lstrip("_")
    _, op, a, b = node
    left, right = compressed_steps(a, out), compressed_steps(b, out)
    table = _table(lambda r: evaluate(node, r))
    glyph = GLYPH_OF_TABLE.get(table, "".join("1" if v else "0" for v in table))
    out.append(f"{left} {op} {right} = {glyph}")
    return glyph


def detect(lines):
    """Which notation every line of a block parses in."""
    kinds = []
    for name, parser in (("infix", parse_infix), ("postfix", parse_postfix)):
        try:
            for line in lines:
                parser(line.split())
            kinds.append(name)
        except ParseError:
            pass
    return kinds


def check(quiet=False):
    problems, slips_seen, lines_checked = [], [], 0
    say = (lambda *a: None) if quiet else print
    for title, page, blocks in SHEETS:
        variables = variables_of([l for _, _, ls in blocks for l in ls])
        say(f"\n{title}  (page {page}, variables {' '.join(variables)}, "
            f"{2 ** len(variables)} rows)")
        for heading, notation, lines in blocks:
            parser = parse_infix if notation == "infix" else parse_postfix
            body = lines[:-1]
            clean = [l for i, l in enumerate(body, 1)
                     if (title, heading, i) not in KNOWN_SLIPS]
            found = detect(clean)
            compressed = "compressed" in heading
            label = "postfix" if notation == "postfix" else "infix"
            note = "" if label in heading.lower() else f"  <- printed as \"{heading}\""
            say(f"  {heading}: parses as {' and '.join(found) or 'neither'}{note}")
            if notation not in found:
                problems.append(f"{title} / {heading}: does not parse as {notation}")
            if lines[-1] != "x":
                problems.append(f"{title} / {heading}: does not end in x")
            for i, line in enumerate(body, 1):
                lines_checked += 1
                key = (title, heading, i)
                try:
                    tree = parser(line.split())
                except ParseError as e:
                    if key in KNOWN_SLIPS:
                        why, fix = KNOWN_SLIPS[key]
                        tree = parser(fix(line).split())
                        ok = all(evaluate(tree, r) for r in rows_of(variables))
                        slips_seen.append(key)
                        say(f"    {i}. SLIP: {e}. {why}. Corrected, it is "
                            f"{'a tautology' if ok else 'NOT a tautology'}.")
                        if not ok:
                            problems.append(f"{title} / {heading} line {i}: correction fails")
                        continue
                    problems.append(f"{title} / {heading} line {i}: {e}")
                    say(f"    {i}. FAILS TO PARSE: {e}")
                    continue
                if key in KNOWN_SLIPS:
                    problems.append(f"{title} / {heading} line {i}: listed as a slip but parses")
                false_rows = [r for r in rows_of(variables) if not evaluate(tree, r)]
                if false_rows:
                    problems.append(f"{title} / {heading} line {i}: false on {len(false_rows)} rows")
                    say(f"    {i}. NOT A TAUTOLOGY: false on {false_rows[0]}")
                    continue
                extra = ""
                if compressed:
                    steps = []
                    compressed_steps(tree, steps)
                    extra = "   " + "; ".join(steps)
                say(f"    {i}. tautology{extra}")
    missing = set(KNOWN_SLIPS) - set(slips_seen)
    for key in missing:
        problems.append(f"known slip {key} not found")
    print(f"\n{lines_checked} lines on {len(SHEETS)} sheets; "
          f"{len(slips_seen)} known slips; {len(problems)} problems")
    for p in problems:
        print("  PROBLEM:", p)
    return not problems


if __name__ == "__main__":
    sys.exit(0 if check(quiet="--quiet" in sys.argv) else 1)
