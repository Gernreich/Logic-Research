#!/usr/bin/env python3
"""Build docs/zellweger.html, and copy the scans to docs/zellweger/.

The page shows the letter and the ten sheets: each scan beside its
transcription, the operators in red as on the sheets, and every line marked
with what check_sheets.py finds. It stops if the check fails.

    python3 build_page.py
"""
import html
import os
import shutil
import sys

import check_sheets as ck
from sheets import SHEETS

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")

# glyph, what it means, its rows TT TF FT FF
GLYPHS = [
    ("x", "tautology: always true", "1111"),
    ("d", "A and B", "1000"),
    ("h", "not (A and B)", "0111"),
    ("ч", "A or B", "1110"),
    ("p", "neither A nor B", "0001"),
    ("Ի", "A implies B", "1011"),
    ("q", "A and not B", "0100"),
    ("c", "A", "1100"),
    ("ɔ", "not A", "0011"),
    ("u", "B", "1010"),
    ("n", "not B", "0101"),
]


def sq(bits):
    cells = "".join(f'<i class="{"on" if b == "1" else ""}"></i>' for b in bits)
    return f'<span class="sq" aria-hidden="true">{cells}</span>'


def token(t):
    if t in ck.OPS:
        return f'<span class="op">{html.escape(t)}</span>'
    if t.startswith("~"):
        return f'<span class="v">{t[1:]}̃</span>'
    if t in "()[]":
        return f'<span class="br">{t}</span>'
    return f'<span class="v">{html.escape(t.lstrip("_"))}</span>'


def render_line(line):
    return "".join(token(t) for t in line.split())


def sheet_rows(title, heading, notation, lines, variables):
    parser = ck.parse_infix if notation == "infix" else ck.parse_postfix
    out = []
    for i, line in enumerate(lines, 1):
        if line == "x":
            out.append(f'<li><span class="ln">{render_line(line)}</span>'
                       f'<span class="ok">end</span></li>')
            continue
        key = (title, heading, i)
        try:
            tree = parser(line.split())
        except ck.ParseError as e:
            why, fix = ck.KNOWN_SLIPS[key]
            out.append(f'<li class="slip"><span class="ln">{render_line(line)}</span>'
                       f'<span class="bad">slip</span>'
                       f'<span class="note">As printed: {html.escape(str(e))}. '
                       f'{html.escape(why[0].upper() + why[1:])}. Corrected, '
                       f'the line is a tautology.</span></li>')
            continue
        steps = ""
        if "compressed" in heading:
            s = []
            ck.compressed_steps(tree, s)
            steps = '<span class="note mono">' + html.escape("  ·  ".join(s)) + "</span>"
        rows = 2 ** len(variables)
        out.append(f'<li><span class="ln">{render_line(line)}</span>'
                   f'<span class="ok" title="true on all {rows} rows">✓</span>{steps}</li>')
    return "\n".join(out)


def main():
    if not ck.check(quiet=True):
        sys.exit("check_sheets.py fails; not building the page")
    os.makedirs(os.path.join(DOCS, "zellweger"), exist_ok=True)
    for n in range(1, 14):
        name = f"page-{n:02d}.jpg"
        shutil.copyfile(os.path.join(HERE, "scans", name),
                        os.path.join(DOCS, "zellweger", name))

    glyph_rows = "\n".join(
        f'<tr><td class="g">{html.escape(g)}</td><td>{sq(b)}</td>'
        f'<td class="mono small">{b}</td><td>{html.escape(m)}</td></tr>'
        for g, m, b in GLYPHS)

    sheets_html = []
    for title, page, blocks in SHEETS:
        variables = ck.variables_of([l for _, _, ls in blocks for l in ls])
        blocks_html = []
        for heading, notation, lines in blocks:
            actual = notation + (" (compressed)" if "compressed" in heading else "")
            printed = "" if heading.lower().startswith(notation) else (
                f' <span class="printed">printed as “{html.escape(heading)}”</span>')
            blocks_html.append(
                f'<div class="block"><h4>{html.escape(actual.capitalize())}{printed}</h4>'
                f'<ol class="lines">{sheet_rows(title, heading, notation, lines, variables)}</ol></div>')
        img = f"zellweger/page-{page:02d}.jpg"
        sheets_html.append(f'''
<section class="sheet" id="{title.lower().replace(' ', '-')}">
  <h3>{html.escape(title)} <span class="muted small">· {len(variables)} variables, {2 ** len(variables)} rows · scan page {page}</span></h3>
  <div class="pair">
    <a class="thumb" href="{img}"><img src="{img}" loading="lazy" alt="Scan of the typed {html.escape(title)} sheet"></a>
    <div class="blocks">{"".join(blocks_html)}</div>
  </div>
</section>''')

    page = TEMPLATE.replace("{{GLYPHS}}", glyph_rows).replace("{{SHEETS}}", "\n".join(sheets_html))
    with open(os.path.join(DOCS, "zellweger.html"), "w") as f:
        f.write(page)
    print("wrote docs/zellweger.html and docs/zellweger/page-01.jpg to page-13.jpg")


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zellweger's Logic Alphabet</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root {
  --bg: #f6f7f9; --surface: #fcfcfb; --ink: #0b0b0b; --muted: #52514e; --line: #dde1e8;
  --fill: #2a78d6; --empty: #e3e6eb; --red: #d0202a; --ok: #2f7d32; --bad: #c0392b; --paper: #fbfaf6;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #121212; --surface: #1a1a19; --ink: #ffffff; --muted: #c3c2b7; --line: #2e2e2c;
    --fill: #3987e5; --empty: #2c2c2a; --red: #ff5a5f; --ok: #6cc070; --bad: #e0604f; --paper: #20201e;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #121212; --surface: #1a1a19; --ink: #ffffff; --muted: #c3c2b7; --line: #2e2e2c;
  --fill: #3987e5; --empty: #2c2c2a; --red: #ff5a5f; --ok: #6cc070; --bad: #e0604f; --paper: #20201e;
}
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.6 "IBM Plex Sans", system-ui, sans-serif; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 36px 16px 72px; display: grid; gap: 44px; }
.wrap > *, section > * { min-width: 0; }
header, section { display: grid; gap: 14px; }
h1 { font-size: 32px; line-height: 1.15; margin: 0; text-wrap: balance; }
h2 { font-size: 21px; line-height: 1.25; margin: 0; }
h3 { font-size: 17px; margin: 0; }
h4 { font-size: 13px; margin: 0 0 6px; font-weight: 600; color: var(--muted); }
p { margin: 0; max-width: 70ch; }
a { color: var(--fill); }
.lede { font-size: 17px; color: var(--muted); }
.muted { color: var(--muted); } .small { font-size: 13px; }
.mono, code { font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; font-size: 0.92em; }
.credit { background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--red); border-radius: 8px; padding: 14px 18px; display: grid; gap: 8px; }
table.glyphs { border-collapse: collapse; width: auto; max-width: 100%; }
table.glyphs td { padding: 4px 12px 4px 0; vertical-align: middle; border-bottom: 1px solid var(--line); }
td.g { font: 600 22px "IBM Plex Mono", monospace; width: 2ch; text-align: center; }
.sq { display: inline-grid; grid-template-columns: 1fr 1fr; gap: 2px; width: 26px; aspect-ratio: 1; vertical-align: middle; }
.sq i { background: var(--empty); border-radius: 2px; }
.sq i.on { background: var(--fill); }
.letter { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.letter figure { margin: 0; display: grid; gap: 6px; }
.letter img, .thumb img { width: 100%; height: auto; display: block; border: 1px solid var(--line); border-radius: 6px; background: #fff; }
figcaption { font-size: 13px; color: var(--muted); }
.sheet { border-top: 1px solid var(--line); padding-top: 22px; }
.pair { display: grid; grid-template-columns: minmax(0, 220px) minmax(0, 1fr); gap: 20px; align-items: start; }
@media (max-width: 680px) { .pair { grid-template-columns: minmax(0, 1fr); } .thumb { max-width: 220px; } }
.blocks { display: grid; gap: 14px; }
.printed { font-weight: 400; color: var(--bad); }
ol.lines { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
ol.lines li { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; }
.ln { font: 17px/1.5 "IBM Plex Mono", ui-monospace, Menlo, monospace; overflow-wrap: anywhere; min-width: 0; }
.ln .op { color: var(--red); font-weight: 600; }
.ln .v, .ln .br { color: var(--ink); }
.ln > span { margin-right: 0.18em; }
.ok { color: var(--ok); font-size: 13px; }
.bad { color: var(--bad); font-size: 13px; font-weight: 600; }
.note { flex-basis: 100%; font-size: 13px; color: var(--muted); }
li.slip .ln { text-decoration: underline wavy var(--bad); text-underline-offset: 5px; }
footer { font-size: 13px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 18px; }
</style>
</head>
<body>
<div class="wrap">
<header>
  <p class="small"><a href="https://gernreich.github.io/">← All projects</a> · <a href="index.html">Sixteen Functions, Three Ways</a></p>
  <h1>Zellweger's Logic Alphabet</h1>
  <p class="lede">Ten rules of inference worked in Shea Zellweger's script for the sixteen two-variable functions, and his 2006 letter about doing modus ponens that way. Every line is checked here on every row of its truth table.</p>
  <div class="credit">
    <p><strong>The script is Shea Zellweger's.</strong> Zellweger (1925–2022), who chaired psychology at Mount Union College in Alliance, Ohio, created the Logic Alphabet: a letter for each of the sixteen binary connectives, shaped so that flipping or turning a letter performs the matching logical operation. The glyphs, their shapes and their names are his. So is the handwritten letter.</p>
    <p><strong>The derivations are this repository's author's.</strong> The ten typed sheets take Zellweger's script and work common rules of propositional logic in it, from the rule down to <span class="mono">x</span>, in a colour glyph font of the author's with the operators in red.</p>
  </div>
</header>

<section>
  <h2>How the script works</h2>
  <p>Each glyph stands on a little square of four places, one for each row of the truth table: A and B both true, A true and B false, A false and B true, both false. A stem stands where the function is true. So a glyph <em>is</em> its truth table, and A and B themselves can be written as glyphs (c and u). Then a whole formula can be computed on shapes: a left–right flip negates, overlaying two glyphs and keeping every stem gives <em>or</em>, keeping only the stems they share gives <em>and</em>. A formula that comes out as x, a stem in every place, is a tautology.</p>
  <table class="glyphs">
    <tbody>
{{GLYPHS}}
    </tbody>
  </table>
  <p class="small muted">Squares read TT TF / FT FF. The glyphs are set here in the nearest Unicode letters: Ի stands in for Zellweger's implication letter, a vertical flip of his h, and ч for his OR. On the sheets, and below, a letter with a tilde (Ã) is <em>not A</em>: once the variables are letters rather than glyphs there is nothing to flip, so the tilde carries the negation. That lets every operator but <em>and</em> and <em>or</em> drop away, and in the last lines each bracket names one row of the truth table. The rule holds when the brackets cover every row.</p>
</section>

<section>
  <h2>The letter, 17 February 2006</h2>
  <p>Zellweger does modus ponens twice: the textbook way, which needs you to remember that A ⊃ B means not-A or B, and then in his script, where c Ի u gives back Ի (“comes right back, needless side show”), Ի d c gives d, and d Ի u is plainly x, because d's one stem lies among the two stems of u. <a href="https://github.com/Gernreich/Logic-Research/blob/main/zellweger/transcription.md">Transcription</a>.</p>
  <div class="letter">
    <figure><a href="zellweger/page-02.jpg"><img src="zellweger/page-02.jpg" loading="lazy" alt="Zellweger's handwritten page 1 of 2: Modus Ponens and the Logic Alphabet, done the standard way"></a><figcaption>Page 1 of 2: the standard way.</figcaption></figure>
    <figure><a href="zellweger/page-03.jpg"><img src="zellweger/page-03.jpg" loading="lazy" alt="Zellweger's handwritten page 2 of 2: modus ponens recast in the Logic Alphabet, with notes in red, blue, green and orange"></a><figcaption>Page 2 of 2: recast in the Logic Alphabet.</figcaption></figure>
    <figure><a href="zellweger/page-01.jpg"><img src="zellweger/page-01.jpg" loading="lazy" alt="The envelope from S. Zellweger, Mount Union College, Alliance, Ohio, postmarked Canton, Ohio, with the street address blacked out"></a><figcaption>The envelope, postmarked Canton, Ohio. The street address and barcodes are blacked out.</figcaption></figure>
  </div>
</section>

<section>
  <h2>The ten sheets</h2>
  <p>Each rule is worked four ways where it has two variables (compressed and expanded, infix and postfix) and two ways where it has three or four. The compressed lines compute on glyphs, and the steps under them show what each operation gives. The expanded lines rewrite every operator as <em>and</em>, <em>or</em> and tildes, then spell out the rows. All 130 lines were parsed and evaluated on every row: 128 are tautologies as printed, and two have a slip in the small print (marked), each a tautology once corrected. The Modus Tollens sheet has its headings one notation off; the true notation is shown with the printed one beside it.</p>
{{SHEETS}}
</section>

<footer>
  Scans, transcription and checker: <a href="https://github.com/Gernreich/Logic-Research/tree/main/zellweger">github.com/Gernreich/Logic-Research/zellweger</a>. Built by <code>zellweger/build_page.py</code>, which stops if <code>check_sheets.py</code> finds a problem. The Logic Alphabet and the letter are Shea Zellweger's, and the repository's CC0 dedication does not cover them.
</footer>
</div>
</body>
</html>
'''

if __name__ == "__main__":
    main()
