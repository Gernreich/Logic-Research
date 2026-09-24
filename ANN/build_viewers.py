#!/usr/bin/env python3
"""Build the two point-cloud viewers, docs/shells.html and docs/cones.html.

Each viewer is a template in ``viewers/`` with one ``/*DATA*/`` line, which
this script replaces with ``const DATA={...};`` built from the point clouds:

    shells.html   gen  the generated cube clouds            (--gen)
                  arc  the 2019 archive, from the files in ARCHIVE below
    cones.html    cube the generated cube clouds            (--gen)
                  ball the ball-sampled clouds              (--ball)
                  dir  the direction-only clouds            (--dir)

Make the three cloud folders first with the ``generate_clouds.py`` commands
in the top-level README; the defaults below are the folders those write.
With those clouds this reproduces the published pages byte for byte.

USAGE
-----
    python3 ANN/build_viewers.py                   (from the repository root)
    python3 ANN/build_viewers.py --check           compare with docs/, write nothing

WHAT GOES INTO EACH CLOUD
-------------------------
    pts      a random subsample of at most SHOWN points (all of them when the
             cloud is smaller), each coordinate rounded with Python's round():
             2 decimals, 4 for the unit-length ``dir`` points. One
             random.Random stream per page (seed 11 for Shells, 21 for Cones)
             is drawn in function order, and within a function in the order
             of the keys above, so changing one cloud's size reshuffles every
             later sample on that page.
    n        the size of the whole cloud
    shown    how many points are in pts
    rmin     smallest and largest distance from the origin among the shown
    rmax     points, before rounding, to 2 decimals
    centroid (Shells) the mean of the shown points, before rounding
    cov      (Cones) percentage of the unit sphere the whole cloud's directions
             reach: the share of cells hit in a 40 x 40 equal-area grid
             (40 bands of equal height in z, 40 equal sectors in angle)

THE ARCHIVE
-----------
The 2019 clouds are read from ``iamtrask_boolean_function_runs/`` and joined
in the order listed. The lists record what the published page was built from,
including two quirks worth knowing before reading the Shells archive view:

  * The names follow the corrected labels in the README, not the filenames:
    ``R9IMPLICATION__*`` is drawn as CONVERSE_IMPL and ``revimplication_syn1``
    as IMPLICATION.
  * NAND joins seven files, and two of them are not points any run found.
    ``sorted_NAND_syn1.txt`` is ``NAND_syn1.txt`` with the three coordinates
    of every row sorted into ascending order, and the ``point5`` ``sorted_XYZ``
    file is the same to its ``notsorted_XYZ`` partner. Of those 1,179 rows,
    180 were already ascending and repeat a real point; the other 999 are
    permuted weights. They are kept here because the published page has them.
"""

import argparse
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from generate_clouds import FUNCTIONS  # noqa: E402  (order, bits and complements)

COLORS = {
    "FALSE": "#7A8699", "AND": "#5FBE8E", "P_AND_NOT_Q": "#3FC0C4", "P": "#E8D14F",
    "Q_AND_NOT_P": "#8FBF5F", "Q": "#E88BB4", "XOR": "#4FA8E8", "OR": "#5BD2A0",
    "NOR": "#E86A5C", "XNOR": "#C98BE0", "NOT_Q": "#F0985C", "CONVERSE_IMPL": "#E9A23B",
    "NOT_P": "#8C7BE8", "IMPLICATION": "#6FB0D8", "NAND": "#D96BA8", "TRUE": "#D8DDE4",
}

_S, _T = "Sixteen/", "Sixteen/tempp/"
_LETTERS = lambda base: [f"{_S}{base}{s}" for s in "abcdefz"]
ARCHIVE = {   # no AND: the 2019 runs never produced an AND cloud
    "FALSE": [_S + "false_syn1"],
    "P_AND_NOT_Q": _LETTERS("R9PMINUSQ__syn1") + [_T + "262k/R9PminusQ__syn1_262k",
                                                 _T + "R9FullPoints/R9PminusQ__syn1"],
    "P": _LETTERS("R9P__syn1"),
    "Q_AND_NOT_P": _LETTERS("R9QminusP__syn1"),
    "Q": ["q_syn1"],
    "XOR": [_T + "temek/xorsyn1", _T + "toot/xorsyn1", _T + "262k/R9XOR_syn1_262k",
            _T + "R9FullPoints/R9XOR__syn1"],
    "OR": ["or_syn1"],
    "NOR": [_T + "262k/R9NOR__syn1_262k", _T + "R9FullPoints/R9NOR__syn1"],
    "XNOR": [_T + "temek/iffsyn1", _T + "toot/iffsyn1", _T + "262k/R9IFF__syn1_262k",
             _T + "R9FullPoints/R9IFF__syn1"],
    "NOT_Q": ["notq_syn1"],
    "CONVERSE_IMPL": _LETTERS("R9IMPLICATION__syn1") + [_T + "262k/R9IMPLICATION__syn1_262k",
                                                       _T + "R9FullPoints/R9IMPLICATION__syn1"],
    "NOT_P": _LETTERS("R9NOTP__syn1"),
    "IMPLICATION": ["revimplication_syn1"],
    "NAND": ["nand_syn1", _T + "262k/R9NAND__syn1_262k", _T + "NAND/sorted_NAND_syn1.txt",
             _T + "NAND/NAND_syn1.txt", _T + "NAND/point5/NAND_point5_syn1_sorted_XYZ",
             _T + "NAND/point5/NAND_point5_syn1_notsorted_XYZ",
             _T + "R9FullPoints/R9NAND__syn1_combined_oneline"],
    "TRUE": [_S + "true_syn1"],
}

SHOWN = {"shells": 8500, "cones": 6000}
SEED = {"shells": 11, "cones": 21}


def read_csv(path):
    """A generate_clouds.py CSV: one x,y,z row per point."""
    with open(path) as f:
        return [[float(v) for v in line.split(",")] for line in f if line.strip()]


def read_archive(name):
    """A 2019 syn1 file, whichever of its formats: numpy's printed ``[[x y z]]``
    rows or comma-separated lines. Lines that do not hold exactly three numbers
    are skipped."""
    rows = []
    with open(os.path.join(HERE, "iamtrask_boolean_function_runs", name), errors="replace") as f:
        for line in f:
            parts = line.replace("[", " ").replace("]", " ").replace(",", " ").split()
            try:
                values = [float(p) for p in parts]
            except ValueError:
                continue
            if len(values) == 3:
                rows.append(values)
    return rows


def coverage(points):
    """Percentage of 40 x 40 equal-area sphere cells the points' directions hit."""
    cells = set()
    for x, y, z in points:
        r = math.sqrt(x * x + y * y + z * z)
        band = min(int((z / r + 1) / 2 * 40), 39)
        sector = min(int((math.atan2(y / r, x / r) + math.pi) / (2 * math.pi) * 40), 39)
        cells.add((band, sector))
    return round(100 * len(cells) / 1600, 1)


def cloud(points, rng, shown, decimals, extra):
    """One viewer cloud: the subsample, its size and radius stats, plus extras."""
    pick = [points[i] for i in rng.sample(range(len(points)), shown)] if len(points) > shown else points
    radii = [math.sqrt(sum(v * v for v in p)) for p in pick]
    out = {"pts": [[round(v, decimals) for v in p] for p in pick], "n": len(points),
           "shown": len(pick), "rmin": round(min(radii), 2), "rmax": round(max(radii), 2)}
    if "centroid" in extra:
        out["centroid"] = [round(sum(p[k] for p in pick) / len(pick), 2) for k in range(3)]
    if "cov" in extra:
        out["cov"] = coverage(points)
    return out


def page_data(page, folders):
    rng = random.Random(SEED[page])
    data = {}
    for table, name in FUNCTIONS.items():
        entry = {"bits": ",".join(map(str, table)), "color": COLORS[name],
                 "complement": FUNCTIONS[tuple(1 - b for b in table)]}
        if page == "shells":
            sources = [("gen", read_csv(os.path.join(folders["gen"], f"{name}_syn1.csv")), 2)]
            if name in ARCHIVE:
                sources.append(("arc", [r for f in ARCHIVE[name] for r in read_archive(f)], 2))
            extra = ("centroid",)
        else:
            sources = [(key, read_csv(os.path.join(folders[folder], f"{name}_syn1.csv")), dec)
                       for key, folder, dec in (("cube", "gen", 2), ("ball", "ball", 2), ("dir", "dir", 4))]
            extra = ("cov",)
        for key, points, decimals in sources:
            if not points:
                sys.exit(f"{page}: no points for {name} {key}")
            entry[key] = cloud(points, rng, SHOWN[page], decimals, extra)
        data[name] = entry
    return data


def render(page, data):
    with open(os.path.join(HERE, "viewers", f"{page}.template.html")) as f:
        template = f.read()
    if template.count("/*DATA*/\n") != 1:
        sys.exit(f"{page}.template.html: expected one /*DATA*/ line")
    line = "const DATA=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
    return template.replace("/*DATA*/\n", line)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gen", default=os.path.join(HERE, "generated_clouds"))
    ap.add_argument("--ball", default=os.path.join(HERE, "clouds_ball"))
    ap.add_argument("--dir", default=os.path.join(HERE, "clouds_dir"))
    ap.add_argument("--check", action="store_true", help="compare with docs/, write nothing")
    args = ap.parse_args()
    folders = {"gen": args.gen, "ball": args.ball, "dir": args.dir}
    for key, path in folders.items():
        if not os.path.isdir(path):
            sys.exit(f"no {path} -- make it with the generate_clouds.py commands in the README")

    same = True
    for page in ("shells", "cones"):
        html = render(page, page_data(page, folders))
        target = os.path.join(REPO, "docs", f"{page}.html")
        with open(target) as f:
            identical = f.read() == html
        same &= identical
        if args.check:
            print(f"{page}.html: {'identical to' if identical else 'DIFFERS from'} docs/")
        else:
            with open(target, "w") as f:
                f.write(html)
            print(f"wrote docs/{page}.html ({len(html) / 1e6:.1f} MB)"
                  f"{'' if identical else ', changed'}")
    return 0 if same or not args.check else 1


if __name__ == "__main__":
    sys.exit(main())
