//! Builds gates.html: for every gate G, a 16x16 grid of G(X, Y), where X and Y are gates.
//! Each cell is the gate λp.λq. G (X p q) (Y p q). Its truth table is found by lambda
//! reduction on all four inputs, and cross-checked with plain bitwise arithmetic on the
//! truth tables. Writes tools/gates.html and tools/gates-data.json.
//! (gates.js until 2026-11-02; the Rust writes both files byte for byte as it did.)

use lambda::core::{self, N};
use lambda::json::J;
use lambda::shortform as sf;
use lambda::{read_gates, root, Gate};
use std::collections::{HashMap, HashSet};
use std::time::Instant;

const T: &str = "λx.(λy.x)";
const F: &str = "λx.(λy.y)";
const INPUTS: [(&str, &str); 4] = [(T, T), (T, F), (F, T), (F, F)]; // TT, TF, FT, FF: the bit order used everywhere

fn w(t: &str) -> String {
    format!("({t})")
}
/// α-rename a gate's variables so copies used inside another gate can't be captured
fn rename(t: &str, map: &[(char, char)]) -> String {
    t.chars().map(|c| map.iter().find(|m| m.0 == c).map_or(c, |m| m.1)).collect()
}
const RX: [(char, char); 4] = [('p', 'u'), ('q', 'v'), ('a', 'c'), ('b', 'd')];
const RY: [(char, char); 4] = [('p', 'm'), ('q', 'n'), ('a', 'e'), ('b', 'h')];

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let rows = read_gates()?;
    let true_db = sf::db(&core::parse("λa.(λb.a)")?);
    let false_db = sf::db(&core::parse("λa.(λb.b)")?);
    let bit_of = |term: &str| -> Result<char, String> {
        let d = sf::db(&core::normal(term, 1000)?);
        if d == true_db {
            Ok('1')
        } else if d == false_db {
            Ok('0')
        } else {
            Err(format!("not a boolean: {d}"))
        }
    };

    // sanity: every gate's own truth table, by reduction, matches the file
    for r in &rows {
        let b: String = INPUTS
            .iter()
            .map(|(p, q)| bit_of(&format!("(({} {}) {})", w(&r.term), w(p), w(q))))
            .collect::<Result<_, _>>()?;
        if b != r.bits {
            return Err(format!("{}: reduced to {b}, file says {}", r.name, r.bits));
        }
    }

    let by_bits: HashMap<&str, usize> = rows.iter().map(|r| (r.bits.as_str(), r.idx)).collect();
    let mut grid: Vec<Vec<Vec<usize>>> = Vec::new(); // grid[g][y][x] = index of the resulting gate
    let mut reductions = 0;
    let t0 = Instant::now();
    for g in &rows {
        let mut panel = Vec::new();
        for y in &rows {
            let mut line = Vec::new();
            for x in &rows {
                // lambda: G (X p q) (Y p q) for each of the four inputs
                let mut bits = String::new();
                for (p, q) in INPUTS {
                    reductions += 1;
                    bits.push(bit_of(&format!(
                        "(({} (({} {}) {})) (({} {}) {}))",
                        w(&g.term),
                        w(&rename(&x.term, &RX)),
                        w(p),
                        w(q),
                        w(&rename(&y.term, &RY)),
                        w(p),
                        w(q)
                    ))?);
                }
                // cross-check: bitwise, row by row. G's bit for inputs (x, y) sits at position (x ? 0 : 2) + (y ? 0 : 1)
                let gb = g.bits.as_bytes();
                let check: String = (0..4)
                    .map(|k| {
                        let i = (if x.bits.as_bytes()[k] == b'1' { 0 } else { 2 }) + (if y.bits.as_bytes()[k] == b'1' { 0 } else { 1 });
                        gb[i] as char
                    })
                    .collect();
                if bits != check {
                    return Err(format!("mismatch at G={} X={} Y={}: lambda {bits}, bitwise {check}", g.idx, x.idx, y.idx));
                }
                line.push(by_bits[bits.as_str()]);
            }
            panel.push(line);
        }
        grid.push(panel);
    }
    // the two claims in the request: FALSE's square is all FALSE, TRUE's square is all TRUE
    if !grid[0].iter().flatten().all(|&v| v == 0) {
        return Err("FALSE square is not all FALSE".into());
    }
    if !grid[15].iter().flatten().all(|&v| v == 15) {
        return Err("TRUE square is not all TRUE".into());
    }
    let n_claims = claims(&grid, &rows)?;
    println!("all {n_claims} pattern claims hold");
    println!(
        "{reductions} reductions in {}s, all 4096 cells match bitwise",
        lambda::jsfmt::fixed(t0.elapsed().as_secs_f64(), 1)
    );

    // ---- the programs: each cell's own lambda term, reduced to normal form ----
    let ap = |ts: &[&str]| -> String {
        let mut it = ts.iter().map(|t| if t.starts_with('λ') { format!("({t})") } else { t.to_string() });
        let first = it.next().unwrap();
        it.fold(first, |f, x| format!("({f} {x})"))
    };
    let cell_term = |g: usize, x: usize, y: usize| {
        let xt = ap(&[&rename(&rows[x].term, &RX), "i", "j"]);
        let yt = ap(&[&rename(&rows[y].term, &RY), "i", "j"]);
        format!("λi.(λj.(λk.(λl.{})))", ap(&[&rows[g].term, &xt, &yt, "k", "l"]))
    };
    // rename the four outer binders i j k l back to p q a b, the names lambda16.txt uses
    fn back(v: &str) -> &str {
        match v {
            "i" => "p",
            "j" => "q",
            "k" => "a",
            "l" => "b",
            _ => v,
        }
    }
    fn rename_tree(n: &N) -> N {
        match n {
            N::Var { v, .. } => N::var(back(v)),
            N::Lam { v, body, .. } => N::lam(back(v), rename_tree(body)),
            N::App { f, x, .. } => N::app(rename_tree(f), rename_tree(x)),
        }
    }
    let file_dbs: Vec<String> = rows.iter().map(|r| core::parse(&r.term).map(|n| sf::db(&n))).collect::<Result<_, _>>()?;
    struct Nf {
        short: String,
        gate: usize,
        exact: bool,
        count: usize,
        first: [usize; 3],
    }
    let mut nf_index: HashMap<String, usize> = HashMap::new();
    let mut nfs: Vec<Nf> = Vec::new();
    let mut nf_grid: Vec<Vec<Vec<usize>>> = Vec::new();
    for g in 0..16 {
        let mut panel = Vec::new();
        for y in 0..16 {
            let mut line = Vec::new();
            for x in 0..16 {
                let n = rename_tree(&core::normal(&cell_term(g, x, y), 1000)?);
                let d = sf::db(&n);
                let gate = grid[g][y][x];
                let k = match nf_index.get(&d) {
                    Some(&k) => k,
                    None => {
                        let k = nfs.len();
                        nf_index.insert(d.clone(), k);
                        nfs.push(Nf { short: sf::short_checked(&n)?, gate, exact: file_dbs[gate] == d, count: 0, first: [g, x, y] });
                        k
                    }
                };
                nfs[k].count += 1;
                // a normal form must always behave like the gate the grid says
                if nfs[k].gate != gate {
                    return Err("one normal form, two behaviours".into());
                }
                line.push(k);
            }
            panel.push(line);
        }
        nf_grid.push(panel);
    }
    let exact_cells = nf_grid.iter().flatten().flatten().filter(|&&k| nfs[k].exact).count();
    if nfs.len() != 506 {
        return Err(format!("expected 506 normal forms, got {}", nfs.len()));
    }
    if exact_cells != 2064 {
        return Err(format!("expected 2064 exact cells, got {exact_cells}"));
    }
    for g in 0..16 {
        if nfs.iter().filter(|f| f.gate == g && f.exact).count() != 1 {
            return Err(format!("gate {g} should have its file term exactly once"));
        }
    }
    println!("{} normal forms, {exact_cells} cells reduce to exactly the lambda16.txt term; every short form reads back", nfs.len());

    const SHORT: [&str; 16] =
        ["FALSE", "q∧¬p", "AND", "Q", "p∧¬q", "XOR", "P", "OR", "NOR", "¬P", "XNOR", "p→q", "¬Q", "NAND", "q→p", "TRUE"];
    let num = |x: usize| J::Num(x as f64);
    let grid3 = |gr: &Vec<Vec<Vec<usize>>>| {
        J::Arr(gr.iter().map(|p| J::Arr(p.iter().map(|l| J::Arr(l.iter().map(|&v| num(v)).collect())).collect())).collect())
    };
    let data = J::obj(vec![
        (
            "gates",
            J::Arr(
                rows.iter()
                    .map(|r| {
                        J::obj(vec![
                            ("idx", num(r.idx)),
                            ("bits", J::s(&r.bits)),
                            ("name", J::s(&r.name)),
                            ("short", J::s(SHORT[r.idx])),
                            ("term", J::s(&r.term)),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("grid", grid3(&grid)),
        (
            "nfs",
            J::Arr(
                nfs.iter()
                    .map(|f| {
                        J::obj(vec![
                            ("short", J::s(&f.short)),
                            ("gate", num(f.gate)),
                            ("exact", J::Bool(f.exact)),
                            ("count", num(f.count)),
                            ("first", J::Arr(f.first.iter().map(|&v| num(v)).collect())),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("nfGrid", grid3(&nf_grid)),
    ]);
    let tools = root().join("tools");
    let tpl = std::fs::read_to_string(tools.join("gates.template.html")).map_err(|e| e.to_string())?;
    let json = data.stringify(0);
    let page = tpl.replacen("/*DATA*/", &format!("const DATA = {json};"), 1);
    std::fs::write(tools.join("gates.html"), page).map_err(|e| e.to_string())?;
    std::fs::write(tools.join("gates-data.json"), json).map_err(|e| e.to_string())?;
    println!("gates.html and gates-data.json written");
    Ok(())
}

/// The patterns the page describes, proved here. Returns how many hold; any that
/// fails is an error.
fn claims(grid: &[Vec<Vec<usize>>], rows: &[Gate]) -> Result<usize, String> {
    let all = |g: usize, f: &dyn Fn(usize, usize, usize) -> bool| {
        grid[g].iter().enumerate().all(|(y, line)| line.iter().enumerate().all(|(x, &v)| f(v, x, y)))
    };
    let latin = |g: usize| {
        grid[g].iter().all(|r| r.iter().collect::<HashSet<_>>().len() == 16)
            && (0..16).all(|x| grid[g].iter().map(|r| r[x]).collect::<HashSet<_>>().len() == 16)
    };
    let checkerboards = || {
        let mut tt = [0usize; 16];
        for r in rows {
            tt[usize::from_str_radix(&r.bits, 2).unwrap()] = r.idx;
        }
        (0..4).all(|k| {
            let w = 8 >> k;
            (0..16).all(|y| {
                (0..16).all(|x| {
                    (rows[grid[5][tt[y]][tt[x]]].bits.as_bytes()[k] == b'1') == ((x / w + y / w) % 2 == 1)
                })
            })
        })
    };
    // the eight gates with one or three TRUE rows are AND with its inputs and/or output flipped
    let triangle = || {
        // g is in the family if, for some flips a, b, c: g(p, q) = c XOR ((p XOR a) AND (q XOR b)) on all four rows
        let is_and_like = |g: usize| {
            (0..2).any(|a| {
                (0..2).any(|b| {
                    (0..2).any(|c| {
                        [(1, 1), (1, 0), (0, 1), (0, 0)]
                            .iter()
                            .enumerate()
                            .all(|(k, &(p, q))| (rows[g].bits.as_bytes()[k] == b'1') == ((c ^ ((p ^ a) & (q ^ b))) & 1 == 1))
                    })
                })
            })
        };
        // control: every other gate must fail the test, so the test is not vacuous
        [1, 2, 4, 7, 8, 11, 13, 14].into_iter().all(is_and_like)
            && [0, 3, 5, 6, 9, 10, 12, 15].into_iter().all(|g| !is_and_like(g))
    };
    let list: Vec<(&str, bool)> = vec![
        ("P copies X", all(6, &|v, x, _| v == x)),
        ("Q copies Y", all(3, &|v, _, y| v == y)),
        ("NOT P is 15 - X", all(9, &|v, x, _| v == 15 - x)),
        ("NOT Q is 15 - Y", all(12, &|v, _, y| v == 15 - y)),
        ("symmetric gates", [0, 2, 5, 7, 8, 10, 13, 15].into_iter().all(|g| all(g, &|v, x, y| v == grid[g][x][y]))),
        ("AND diagonal is X", all(2, &|v, x, y| x != y || v == x)),
        ("XOR diagonal is FALSE", all(5, &|v, x, y| x != y || v == 0)),
        ("complement squares", (0..16).all(|g| all(15 - g, &|v, x, y| v == 15 - grid[g][y][x]))),
        ("XOR, XNOR Latin squares", latin(5) && latin(10)),
        (
            "XOR diagonal FALSE, XNOR diagonal TRUE",
            all(5, &|v, x, y| x != y || v == 0) && all(10, &|v, x, y| x != y || v == 15),
        ),
        ("XOR quarters are checkerboards", checkerboards()),
        ("triangle family is AND reflected or inverted", triangle()),
    ];
    for (k, ok) in &list {
        if !ok {
            return Err(format!("claim failed: {k}"));
        }
    }
    Ok(list.len())
}
