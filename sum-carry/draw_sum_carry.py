#!/usr/bin/env python3
"""Draw a full adder's sum and carry as three-set Venn diagrams, three ways.

Redraws the hand drawings in this folder with every region computed:

    sum   = A XOR B XOR C      TRUE when an odd number of inputs are TRUE
    carry = majority(A, B, C)  TRUE when at least two are TRUE

Rows: round circles; the square Venn of the 1995 poster (A the top half, B
the left half, C the centre square, so "A and B" is top-left and "neither"
bottom-right, as on the poster); and sine curves, each set being the area
below its curve. Shaded means TRUE.

CHECKED ON EVERY RUN
-------------------
* each style has all eight combinations of A, B, C, each one connected region
* in the finished image, the pixel deepest inside every region of every
  panel has the colour its sum or carry value says

The sine curves (1, 2 and 4 half-waves) were chosen by search so that every
combination is one region: the simplest version, with the curves meeting on
a common midline, splits some combinations into two or three pieces.

USAGE
-----
    python3 draw_sum_carry.py        writes sum-carry.png beside this script
"""

import os
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'sum-carry.png')

FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
font = lambda size, bold=False: ImageFont.truetype(BOLD if bold else FONT, size)
PAPER, INK, MUTED, RULE = (255, 255, 255), (28, 35, 48), (93, 102, 117), (213, 217, 224)
FILL, EMPTY = (42, 120, 214), (246, 247, 249)

SS = 3                          # supersampling for smooth edges
PW, PH = 620, 440               # panel size in the output
FUNCS = {'sum': lambda a, b, c: a ^ b ^ c, 'carry': lambda a, b, c: (a & b) | (a & c) | (b & c)}
SINE = [(0.412, 1.441, 0.605, 1), (0.410, 1.383, 0.542, 2), (0.157, -1.109, 0.544, 4)]   # amp, phase, offset, half-waves


# ---------------------------------------------------------------- geometry
def grid(w, h):
    xs = (np.arange(w) + 0.5) / w
    ys = (np.arange(h) + 0.5) / h
    return np.meshgrid(xs, ys)


def circle_sets(w, h):
    X, Y = grid(w, h)
    X, Y = X * w / h, Y          # square units, height 1
    cx0 = w / h / 2
    r = 0.27
    centres = [(cx0 - 0.155, 0.40), (cx0 + 0.155, 0.40), (cx0, 0.66)]
    return [(X - x) ** 2 + (Y - y) ** 2 < r * r for x, y in centres], centres, r


def square_sets(w, h):
    X, Y = grid(w, h)
    side = 0.76 * h
    x0, y0 = (w - side) / 2 / w, (h - side) / 2 / h
    u, v = (X - x0) * w / side, (Y - y0) * h / side          # 0..1 inside the square
    inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    a = inside & (v < 0.5)                                   # top half
    b = inside & (u < 0.5)                                   # left half
    c = inside & (u >= 0.25) & (u < 0.75) & (v >= 0.25) & (v < 0.75)
    return [a, b, c], inside, (x0 * w, y0 * h, side)


def sine_y(k, x):
    amp, ph, off, n = SINE[k]
    return off + amp * np.sin(n * np.pi * x + ph)


def sine_label_point(k):
    """A spot just above curve k where it is farthest from the other curves and the frame."""
    xs = np.linspace(0.08, 0.92, 400)
    best, spot = -1, None
    for x in xs:
        y = sine_y(k, x) + 0.075
        room = min([abs(y - sine_y(j, x)) for j in range(3) if j != k] + [y - 0.07, 0.93 - y])
        if room > best:
            best, spot = room, (x, y)
    return spot


def sine_sets(w, h):
    X, Y = grid(w, h)
    up = 1 - Y
    return [up < sine_y(k, X) for k in range(3)]


# ---------------------------------------------------------------- checks
def components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    n = 0
    for i, j in zip(*np.nonzero(mask)):
        if seen[i, j]:
            continue
        n += 1
        q = deque([(i, j)]); seen[i, j] = True
        while q:
            a, b = q.popleft()
            for u, v in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= u < h and 0 <= v < w and mask[u, v] and not seen[u, v]:
                    seen[u, v] = True; q.append((u, v))
    return n


def deepest(mask):
    """A pixel farthest from the region's edge: erode until one more step would empty it."""
    m = mask.copy()
    while True:
        e = m.copy()
        e[1:, :] &= m[:-1, :]; e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        e[0, :] = e[-1, :] = False; e[:, 0] = e[:, -1] = False
        if not e.any():
            i, j = np.argwhere(m)[len(np.argwhere(m)) // 2]
            return i, j
        m = e


def region_codes(sets, frame=None):
    code = sets[0] * 4 + sets[1] * 2 + sets[2] * 1
    if frame is not None:
        code = np.where(frame, code, -1)
    return code


def check_style(name, code):
    for k in range(8):
        n = components(code == k)
        if n != 1:
            raise SystemExit(f'CHECK FAILED: {name}: combination {k:03b} is {n} regions')


# ---------------------------------------------------------------- drawing
def shade(code, func):
    img = np.full(code.shape + (3,), PAPER, np.uint8)
    for k in range(8):
        a, b, c = (k >> 2) & 1, (k >> 1) & 1, k & 1
        img[code == k] = FILL if func(a, b, c) else EMPTY
    return Image.fromarray(img)


def panel(style, fname):
    w, h = PW * SS, PH * SS
    if style == 'circles':
        sets, centres, r = circle_sets(w, h)
        code = region_codes(sets)
        code = np.where(code == 0, 0, code)
    elif style == 'square':
        sets, inside, box = square_sets(w, h)
        code = region_codes(sets, inside)
    else:
        sets = sine_sets(w, h)
        code = region_codes(sets)
    img = shade(np.where(code < 0, 0, code), FUNCS[fname])
    if style == 'square':
        arr = np.array(img); arr[code < 0] = PAPER; img = Image.fromarray(arr)
    if style == 'circles':
        arr = np.array(img); arr[code == 0] = PAPER if not FUNCS[fname](0, 0, 0) else FILL; img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    lw = 3 * SS
    lab = font(34 * SS, True)
    if style == 'circles':
        for (x, y), name, (dx, dy) in zip(centres, 'ABC', ((-0.33, -0.28), (0.29, -0.28), (-0.30, 0.25))):
            cx, cy, rr = x * h, y * h, r * h
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=INK, width=lw)
            d.text((cx + dx * h, cy + dy * h), name, font=lab, fill=INK, anchor='mm')
    elif style == 'square':
        x0, y0, side = box
        d.rectangle((x0, y0, x0 + side, y0 + side), outline=INK, width=lw)
        d.line((x0, y0 + side / 2, x0 + side, y0 + side / 2), fill=INK, width=lw)
        d.line((x0 + side / 2, y0, x0 + side / 2, y0 + side), fill=INK, width=lw)
        q = side / 4
        d.rectangle((x0 + q, y0 + q, x0 + 3 * q, y0 + 3 * q), outline=INK, width=lw)
        d.text((x0 - 26 * SS, y0 + side / 4), 'A', font=lab, fill=INK, anchor='mm')
        d.text((x0 + side / 4, y0 - 22 * SS), 'B', font=lab, fill=INK, anchor='mm')
        d.text((x0 + 3 * q - 22 * SS, y0 + 3 * q - 26 * SS), 'C', font=font(28 * SS, True), fill=INK, anchor='mm')
    else:
        xs = np.linspace(0, 1, 800)
        for k, name in enumerate('ABC'):
            pts = [(x * w, (1 - sine_y(k, x)) * h) for x in xs]
            d.line(pts, fill=INK, width=lw, joint='curve')
        d.rectangle((0, 0, w - 1, h - 1), outline=INK, width=lw)
        for k, name in enumerate('ABC'):
            x, y = sine_label_point(k)
            d.text((x * w, (1 - y) * h), name, font=lab, fill=INK, anchor='mm')
    small = img.resize((PW, PH), Image.LANCZOS)
    return small, code


def verify(style, fname, img, code):
    """Sample the deepest pixel of every region in the finished panel."""
    sub = code[::SS, ::SS][:PH, :PW]
    arr = np.array(img)
    for k in range(8):
        mask = sub == k
        if not mask.any():
            raise SystemExit(f'CHECK FAILED: {style} {fname}: combination {k:03b} missing')
        i, j = deepest(mask)
        want = FILL if FUNCS[fname]((k >> 2) & 1, (k >> 1) & 1, k & 1) else EMPTY
        if style == 'circles' and k == 0:
            want = FILL if FUNCS[fname](0, 0, 0) else PAPER
        got = tuple(int(v) for v in arr[i, j][:3])
        if max(abs(g - w) for g, w in zip(got, want)) > 12:
            raise SystemExit(f'CHECK FAILED: {style} {fname}: region {k:03b} is {got}, expected {want}')


def truth_table(w, h):
    img = Image.new('RGB', (w, h), PAPER)
    d = ImageDraw.Draw(img)
    head, cell = font(26, True), font(26)
    cols = ['A', 'B', 'C', 'sum', 'carry']
    xs = [40, 100, 160, 250, 350]
    y = 20
    for x, c in zip(xs, cols):
        d.text((x, y), c, font=head, fill=INK, anchor='mm')
    d.line((10, y + 22, w - 10, y + 22), fill=RULE, width=2)
    for k in range(8):
        a, b, c = (k >> 2) & 1, (k >> 1) & 1, k & 1
        yy = y + 50 + k * 38
        s, cr = FUNCS['sum'](a, b, c), FUNCS['carry'](a, b, c)
        for x, v in zip(xs, (a, b, c, s, cr)):
            if x >= 250 and v:
                d.rounded_rectangle((x - 22, yy - 16, x + 22, yy + 16), 5, fill=FILL)
                d.text((x, yy), '1', font=cell, fill=PAPER, anchor='mm')
            else:
                d.text((x, yy), str(v), font=cell, fill=INK if x < 250 else MUTED, anchor='mm')
    return img


def main():
    styles = [('circles', 'Circles'), ('square', 'Square Venn'), ('sine', 'Sine curves')]
    # every combination one connected region, per style (checked at output resolution)
    check_style('circles', region_codes(circle_sets(PW, PH)[0]))
    s, inside, _ = square_sets(PW, PH)
    check_style('square', region_codes(s, inside))
    check_style('sine', region_codes(sine_sets(PW, PH)))

    left, top, gap = 300, 300, 40
    table_w = 420
    W = left + 2 * PW + gap + 60 + table_w + 40
    H = top + 3 * PH + 2 * gap + 220
    page = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(page)
    d.text((60, 60), 'Sum and carry of a full adder, drawn three ways', font=font(52, True), fill=INK)
    d.text((60, 132), 'sum = A ⊕ B ⊕ C  (an odd number of inputs TRUE)      carry = at least two of A, B, C TRUE',
           font=font(30), fill=MUTED)
    d.text((60, 176), 'Shaded regions are TRUE.', font=font(30), fill=MUTED)
    for col, fname in enumerate(('sum', 'carry')):
        d.text((left + col * (PW + gap) + PW / 2, top - 30), fname, font=font(40, True), fill=INK, anchor='mm')
    for row, (style, label) in enumerate(styles):
        y = top + row * (PH + gap)
        d.text((60, y + PH / 2), label, font=font(32, True), fill=INK, anchor='lm')
        for col, fname in enumerate(('sum', 'carry')):
            img, code = panel(style, fname)
            verify(style, fname, img, code)
            x = left + col * (PW + gap)
            page.paste(img, (x, y))
            d.rectangle((x - 1, y - 1, x + PW, y + PH), outline=RULE, width=2)
    tx = left + 2 * PW + gap + 60
    d.text((tx, top - 30), 'truth table', font=font(40, True), fill=INK, anchor='lm')
    page.paste(truth_table(table_w, 380), (tx, top + 10))
    notes = ['The square Venn is drawn as on the 1995 poster: A is the top half, B the left half,',
             'C the centre square, so "A and B" is top-left and "neither" bottom-right.',
             'Sine curves: each set is the area below its curve; each of the eight combinations',
             'of A, B, C is exactly one region.']
    for i, line in enumerate(notes):
        d.text((60, top + 3 * PH + 2 * gap + 40 + i * 34), line, font=font(26), fill=MUTED)
    page.save(OUT, optimize=True)
    print(f'wrote {os.path.relpath(OUT, os.getcwd())} ({W} x {H}); every region of all six panels checked')


if __name__ == '__main__':
    main()
