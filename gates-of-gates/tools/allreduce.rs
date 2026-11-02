//! Rebuilds the reduction half of lambda16.txt: every gate on all four inputs, step by
//! step. Run from any folder; it writes reductions.txt there, and that file appears
//! verbatim in lambda16.txt from the "Beta reduction of all sixteen" heading on.
//! (allreduce.js until 2026-11-02.)

use lambda::read_gates;
use lambda::reference::{parse, show, step, T};

const TRUE: &str = "λx.(λy.x)";
const FALSE: &str = "λx.(λy.y)";

fn label(a: &T) -> String {
    let s = show(a);
    if s == TRUE {
        "TRUE".into()
    } else if s == FALSE {
        "FALSE".into()
    } else {
        s
    }
}

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let rows = read_gates()?;
    let mut out: Vec<String> = [
        "",
        "",
        "Beta reduction of all sixteen, on all four inputs",
        "==================================================",
        "",
        "TRUE = λx.(λy.x) and FALSE = λx.(λy.y) use x and y so they cannot clash with a and b.",
        "Normal order: the leftmost, outermost redex is reduced first.",
        "Each step says which variable was replaced and by what. \"(thrown away)\" means",
        "the bound variable did not appear in the body, so the argument vanishes unreduced.",
        "Every reduction ends at λa.(λb.a) = TRUE or λa.(λb.b) = FALSE.",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();
    let (mut bad, mut total) = (0, 0);
    for r in &rows {
        let term = r.term.trim();
        out.extend(["".into(), "".into(), format!("--- {}  {}   {}", r.idx, r.name, term)]);
        for k in 0..4 {
            let pn = if k < 2 { "TRUE" } else { "FALSE" };
            let qn = if k % 2 == 0 { "TRUE" } else { "FALSE" };
            let p = if pn == "TRUE" { TRUE } else { FALSE };
            let q = if qn == "TRUE" { TRUE } else { FALSE };
            let mut n = parse(&format!("(({term} ({p})) ({q}))"))?;
            let mut i = 0;
            let mut lines = vec![format!("  {:>2}  {}", i, show(&n))];
            while let Some((m, note)) = step(&n) {
                n = m;
                i += 1;
                lines.push(format!("  {:>2}  {}", i, show(&n)));
                lines.push(format!(
                    "        {} := {}{}",
                    note.v,
                    label(&note.arg),
                    if note.used { "" } else { "   (thrown away)" }
                ));
                if i > 50 {
                    return Err("runaway".into());
                }
            }
            let one = r.bits.as_bytes()[k] == b'1';
            let want = if one { "λa.(λb.a)" } else { "λa.(λb.b)" };
            if show(&n) != want {
                bad += 1;
            }
            total += i;
            out.push(String::new());
            out.push(format!("  p = {pn}, q = {qn}  →  {}", if one { "TRUE" } else { "FALSE" }));
            out.extend(lines);
        }
    }
    eprintln!("{} gates, {} reductions, {total} steps, {bad} wrong results", rows.len(), rows.len() * 4);
    if bad > 0 {
        std::process::exit(1);
    }
    std::fs::write("reductions.txt", out.join("\n") + "\n").map_err(|e| e.to_string())
}
