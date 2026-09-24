"""Draw the gates-of-gates figures from gates-data.json (the verified cell values).

Every picture is built only from the data: grid[g][y][x] is the gate G(X, Y), and gates[i].bits is
its truth table (TT, TF, FT, FF). Output: JPEG files in the folder given as the first argument.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'images')
os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(HERE, 'gates-data.json')))
G, GRID, NFS, NFG = D['gates'], D['grid'], D['nfs'], D['nfGrid']

FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
MONO = '/System/Library/Fonts/Menlo.ttc'
f = lambda size, mono=False: ImageFont.truetype(MONO if mono else FONT, size)

PAPER, INK, MUTED, LINE = '#ffffff', '#1c2330', '#5d6675', '#d5d9e0'
FILL, EMPTY = '#2a78d6', '#e6e9ee'
VENN = ['#d0408a', '#1a9fc2', '#3d9a2a', '#9a2f1f']          # p and q, p only, q only, neither
GRIDLINE, HDR, GP = '#c3c7cf', '#555d6b', '#fbfaf6'
COMP = list(range(16))                                          # boolean16.py order
TT = [None] * 16
for g in G: TT[int(g['bits'], 2)] = g['idx']                    # truth-table value order
val = lambda i: int(G[i]['bits'], 2)


def wrap(d, text, font, width):
    """Split text into lines that fit the given pixel width."""
    lines, cur = [], ''
    for word in text.split(' '):
        t = (cur + ' ' + word).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = word
    return lines + [cur]


def header(im_w, title, sub, pad):
    """Measure a title + wrapped subtitle; returns (lines, height)."""
    probe = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = wrap(probe, sub, f(15), im_w - 2 * pad)
    return lines, 58 + 22 * len(lines) + 16


def draw_header(d, title, lines, pad):
    d.text((pad, 20), title, font=f(26), fill=INK)
    for i, l in enumerate(lines): d.text((pad, 58 + 22 * i), l, font=f(15), fill=MUTED)


def square(g, order, style, cell=16, headers=False):
    """One gate's 16 x 16 square as an image. style: bits | venn | square | value | same."""
    off = cell + 4 if headers else 0
    im = Image.new('RGB', (off + 16 * cell, off + 16 * cell), PAPER)
    d = ImageDraw.Draw(im)

    def venn(x0, y0, bits, colour):
        d.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=GRIDLINE)
        q = (cell - 3) // 2
        for k in range(4):
            x = x0 + 1 + (k % 2) * (q + 1); y = y0 + 1 + (k // 2) * (q + 1)
            d.rectangle([x, y, x + q - 1, y + q - 1], fill=colour(k) if bits[k] == '1' else GP)

    if headers:
        venn(1, 1, G[g]['bits'], lambda k: HDR)
        for i in range(16):
            venn(off + i * cell, 1, G[order[i]]['bits'], lambda k: HDR)
            venn(1, off + i * cell, G[order[i]]['bits'], lambda k: HDR)
    for py in range(16):
        for px in range(16):
            X, Y = order[px], order[py]
            r = GRID[g][Y][X]; bits = G[r]['bits']
            x0, y0 = off + px * cell, off + py * cell
            if style == 'square':
                venn(x0, y0, bits, lambda k: VENN[k])
            elif style in ('bits', 'venn'):
                h = (cell - 3) / 2
                for k in range(4):
                    c = (VENN[k] if style == 'venn' else FILL) if bits[k] == '1' else EMPTY
                    x = x0 + (k % 2) * (h + 1); y = y0 + (k // 2) * (h + 1)
                    d.rectangle([x, y, x + h - 1, y + h - 1], fill=c)
            elif style == 'value':                                   # sequential shade by the result's 4-bit value
                v = val(r) / 15
                c = tuple(round(a + (b - a) * v) for a, b in zip((236, 240, 247), (18, 64, 140)))
                d.rectangle([x0, y0, x0 + cell - 2, y0 + cell - 2], fill=c)
            elif style[0] == 'q':                                    # one quarter: truth-table row k only
                k = int(style[1])
                on = bits[k] == '1'
                # quarter k of G(X, Y) is G applied to row k of X and row k of Y
                gx, gy = G[X]['bits'][k] == '1', G[Y]['bits'][k] == '1'
                assert on == (G[g]['bits'][(0 if gx else 2) + (0 if gy else 1)] == '1')
                d.rectangle([x0, y0, x0 + cell - 2, y0 + cell - 2], fill=VENN[k] if on else EMPTY)
            elif style == 'same':
                if NFS[NFG[g][Y][X]]['exact']: d.rectangle([x0, y0, x0 + cell - 2, y0 + cell - 2], fill=FILL)
                else: d.rectangle([x0 + 1, y0 + 1, x0 + cell - 3, y0 + cell - 3], outline=FILL, width=1)
    return im


def sheet(order, style, title, sub, name, cell=12, headers=False, panels=None):
    """A 4 x 4 sheet of squares with titles, in the given gate order."""
    panels = panels or order
    sq = square(0, order, style, cell, headers).size[0]
    pad, th, cols = 26, 34, 4 if len(panels) > 4 else len(panels)
    rows = (len(panels) + cols - 1) // cols
    W = pad + cols * (sq + pad)
    lines, top = header(W, title, sub, pad)
    H = top + rows * (sq + th + pad)
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    draw_header(d, title, lines, pad)
    for n, g in enumerate(panels):
        cx = pad + (n % cols) * (sq + pad); cy = top + (n // cols) * (sq + th + pad)
        d.text((cx, cy + 4), f"G = {g} {G[g]['short']}", font=f(16), fill=INK)
        d.text((cx + sq, cy + 6), G[g]['bits'], font=f(13, True), fill=MUTED, anchor='ra')
        im.paste(square(g, order, style, cell, headers), (cx, cy + th))
    im.save(os.path.join(OUT, name), 'JPEG', quality=90)
    return name


def and_mask():
    """AND in truth-table order: where the result is FALSE. Plus the same rule on 6-bit numbers."""
    cell, pad = 22, 30
    s16 = 16 * cell
    big_cell = 6; s64 = 64 * big_cell
    W = pad * 3 + s16 + s64
    lines, top = header(W, '', 'Dark cells: AND(X, Y) = FALSE, i.e. the truth tables of X and Y share no TRUE row (X AND Y = 0 as 4-bit numbers). Left: your 16 gates, from the verified grid. Right: the same rule on 6-bit numbers 0–63, computed bitwise, to show the pattern continuing.', pad)
    y0 = top + 14; H = y0 + 16 + max(s16, s64) + 30
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    draw_header(d, 'AND in truth-table order: the Sierpiński-style triangle', lines, pad)
    d.text((pad, y0 - 6), '16 gates (0000 … 1111)', font=f(14), fill=INK)
    for y in range(16):
        for x in range(16):
            r = GRID[2][TT[y]][TT[x]]
            assert val(r) == (x & y)                                  # the grid really is bitwise AND here
            c = INK if val(r) == 0 else EMPTY
            d.rectangle([pad + x * cell, y0 + 16 + y * cell, pad + x * cell + cell - 2, y0 + 16 + y * cell + cell - 2], fill=c)
    x1 = pad * 2 + s16
    d.text((x1, y0 - 6), 'extension: 64 × 64, X AND Y = 0', font=f(14), fill=INK)
    for y in range(64):
        for x in range(64):
            c = INK if (x & y) == 0 else EMPTY
            d.rectangle([x1 + x * big_cell, y0 + 16 + y * big_cell, x1 + x * big_cell + big_cell - 1, y0 + 16 + y * big_cell + big_cell - 1], fill=c)
    im.save(os.path.join(OUT, 'and-sierpinski.jpg'), 'JPEG', quality=92)


def xor_table():
    """XOR in truth-table order, as numbers, shaded by value: copies of itself at half size."""
    cell, pad = 34, 30
    W = pad * 2 + 17 * cell
    lines, top = header(W, '', 'Each cell is XOR(X, Y) as a hex digit (its truth table read as binary). The 16 × 16 table is four 8 × 8 copies, each made of 4 × 4 copies, and so on: nested, like rule 90.', pad)
    y0 = top; H = y0 + 17 * cell + 30
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    draw_header(d, 'XOR in truth-table order', lines, pad)
    for i in range(16):
        d.text((pad + (i + 1) * cell + cell / 2, y0 + cell / 2), format(i, 'x'), font=f(13, True), fill=MUTED, anchor='mm')
        d.text((pad + cell / 2, y0 + (i + 1) * cell + cell / 2), format(i, 'x'), font=f(13, True), fill=MUTED, anchor='mm')
    for y in range(16):
        for x in range(16):
            v = val(GRID[5][TT[y]][TT[x]]); assert v == (x ^ y)
            t = v / 15
            c = tuple(round(a + (b - a) * t) for a, b in zip((236, 240, 247), (18, 64, 140)))
            bx, by = pad + (x + 1) * cell, y0 + (y + 1) * cell
            d.rectangle([bx, by, bx + cell - 3, by + cell - 3], fill=c)
            d.text((bx + (cell - 2) / 2, by + (cell - 2) / 2), format(v, 'x'), font=f(13, True), fill='#ffffff' if t > 0.45 else INK, anchor='mm')
    im.save(os.path.join(OUT, 'xor-nested.jpg'), 'JPEG', quality=92)


def xor_checkerboards():
    """XOR in truth-table order, one quarter (truth-table row) at a time: four checkerboards."""
    cell, pad, gap = 13, 30, 34
    names = ['TT · p and q', 'TF · p only', 'FT · q only', 'FF · neither']
    side = 16 * cell
    W = pad * 2 + 4 * side + 3 * gap
    lines, top = header(W, '', 'Each quarter of every cell, drawn on its own: XOR is TRUE where a TRUE stripe from X crosses a FALSE stripe from Y. In truth-table order the four quarters are checkerboards with squares 8, 4, 2 and 1 cells wide. XNOR is the same with TRUE and FALSE swapped.', pad)
    y0 = top + 26; H = y0 + side + 30
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    draw_header(d, 'XOR in truth-table order: four checkerboards', lines, pad)
    for k in range(4):
        x0 = pad + k * (side + gap)
        d.text((x0, y0 - 22), names[k], font=f(14), fill=INK)
        w = 8 >> k
        for y in range(16):
            for x in range(16):
                on = G[GRID[5][TT[y]][TT[x]]]['bits'][k] == '1'
                assert on == ((x // w + y // w) % 2 == 1)          # really a checkerboard of squares w wide
                d.rectangle([x0 + x * cell, y0 + y * cell, x0 + x * cell + cell - 2, y0 + y * cell + cell - 2], fill=VENN[k] if on else EMPTY)
    im.save(os.path.join(OUT, 'xor-checkerboards.jpg'), 'JPEG', quality=92)


made = [
    sheet(COMP, 'bits', 'All 16 squares — truth-table cells, complement order',
          'Each cell is G(X, Y); its 2×2 truth table is shown filled for TRUE (TT TF / FT FF). Order: boolean16.py, gate i and 15 − i complements.', 'all16-truth-table.jpg'),
    sheet(COMP, 'square', 'All 16 squares — square Venn diagrams, 1995 style',
          'Grey Venns along the top and left are the inputs X and Y; the corner is G. Cell quarters: p and q, p only, q only, neither.', 'all16-square-venn.jpg', cell=13, headers=True),
    sheet(COMP, 'venn', 'All 16 squares — Venn colours',
          'Magenta: p and q · cyan: p only · green: q only · dark red: neither. A coloured quarter means the result is TRUE there.', 'all16-venn-colours.jpg'),
    sheet(TT, 'value', 'All 16 squares — truth-table order, shaded by value',
          'Axes and squares sorted by truth table read as binary (0000 … 1111). Shade = the result as a 4-bit number. Nested patterns appear.', 'all16-truth-table-order.jpg'),
    sheet(COMP, 'same', 'Same term? — which cells reduce to the lambda16.txt term',
          'Filled: the cell reduces to exactly its gate’s lambda16.txt term. Hollow: same truth table, a different program (one of the 506).', 'all16-same-term.jpg'),
    sheet(COMP, 'bits', 'Stripes: P, Q, NOT P, NOT Q',
          'P copies X (every column one gate), Q copies Y (every row one gate); NOT P and NOT Q give the complement.', 'stripes.jpg', cell=16, panels=[6, 3, 9, 12]),
    sheet(COMP, 'bits', 'Complements: gate G and gate 15 − G',
          'AND and NAND, XOR and XNOR: every cell of one is the flipped truth table of the other. Symmetric gates mirror across the diagonal.', 'complements.jpg', cell=16, panels=[2, 13, 5, 10]),
]
QNAMES = [('tt', 'TT · p and q'), ('tf', 'TF · p only'), ('ft', 'FT · q only'), ('ff', 'FF · neither')]
for k, (slug, label) in enumerate(QNAMES):
    made.append(sheet(TT, 'q%d' % k, f'One quarter, all 16 squares: {label}',
        f'Only truth-table row {label.split(" ")[0]} of every cell, filled in its Venn colour when TRUE. Truth-table order: '
        'blank for FALSE and TRUE, stripes for P, Q, NOT P, NOT Q, one block in four for AND, NOR, p∧¬q and q∧¬p, '
        'three in four for OR, NAND, p→q and q→p, and checkerboards for XOR and XNOR.',
        f'quarter-{slug}.jpg'))
and_mask(); xor_table(); xor_checkerboards()
print('figures:', ', '.join(made + ['and-sierpinski.jpg', 'xor-nested.jpg', 'xor-checkerboards.jpg']))
