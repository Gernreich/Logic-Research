//! A Tromp diagram as SVG, on the plain reducer's terms. Run on its own it prints
//! two example reductions and the diagram of TRUE. (tromp.js until 2026-11-02; the
//! pages draw with core's layout, which is this one keyed by node.)

use lambda::jsfmt::num;
use lambda::reference::{parse, reduce_steps, T};
use std::collections::HashMap;

const C: f64 = 30.0; // grid: column width, row height (px)
const R: f64 = 24.0;

fn free_name(v: &str) -> Option<&'static str> {
    match v {
        "A" => Some("apple"),
        "B" => Some("banana"),
        _ => None,
    }
}

#[derive(Clone)]
enum Part {
    Line { v: String, x: f64, y1: f64, y2: f64 },
    Bar { v: String, x1: f64, x2: f64, y: f64 },
    Link { x1: f64, x2: f64, y: f64 },
}
struct Out {
    x: f64,
    y: f64,
    v: String,
}
struct Laid {
    w: f64,
    h: f64,
    out: Out,
    parts: Vec<Part>,
    free: Vec<(f64, String)>,
}

/// Width and height in grid units, the output line (leftmost), and the drawing parts.
/// `gap` is extra columns before an argument block, room for bar labels.
fn lay(n: &T, env: &HashMap<String, f64>, x0: f64, y0: f64, gap: f64) -> Laid {
    match n {
        T::Var(v) => {
            let bound = env.contains_key(v);
            let x = x0 + 0.5;
            let top = if bound { env[v] } else { -0.6 };
            Laid {
                w: if bound { 1.0 } else { 2.0 },
                h: 0.0,
                out: Out { x, y: y0, v: v.clone() },
                parts: vec![Part::Line { v: v.clone(), x, y1: top, y2: y0 }],
                free: if bound { vec![] } else { vec![(x, v.clone())] },
            }
        }
        T::Lam(v, body) => {
            let mut e = env.clone();
            e.insert(v.clone(), y0);
            let b = lay(body, &e, x0, y0 + 1.0, gap);
            let w = lambda::jsfmt::max(1.0, b.w);
            let mut parts = vec![Part::Bar { v: v.clone(), x1: x0, x2: x0 + w, y: y0 }];
            parts.extend(b.parts);
            Laid { w, h: b.h + 1.0, out: b.out, parts, free: b.free }
        }
        T::App(f, x) => {
            let m = lay(f, env, x0, y0, gap);
            let nn = lay(x, env, x0 + m.w + gap, y0, gap);
            let yl = y0 + lambda::jsfmt::max(m.h, nn.h) + 1.0;
            let mut parts = m.parts;
            parts.extend(nn.parts);
            parts.push(Part::Line { v: m.out.v.clone(), x: m.out.x, y1: m.out.y, y2: yl });
            parts.push(Part::Line { v: nn.out.v.clone(), x: nn.out.x, y1: nn.out.y, y2: yl });
            parts.push(Part::Link { x1: m.out.x, x2: nn.out.x, y: yl });
            let mut free = m.free;
            free.extend(nn.free);
            Laid { w: m.w + gap + nn.w, h: yl - y0, out: Out { x: m.out.x, y: yl, v: m.out.v }, parts, free }
        }
    }
}

#[allow(dead_code)]
#[derive(PartialEq)]
enum Labels {
    All,
    None,
    /// only the bars at the left edge
    Left,
}

fn svg(term: &str, aria: &str, gap: f64, labels: Labels) -> Result<String, String> {
    let n = parse(term)?;
    let l = lay(&n, &HashMap::new(), 0.0, 0.0, gap);
    let mut parts = l.parts;
    parts.push(Part::Line { v: l.out.v.clone(), x: l.out.x, y1: l.out.y, y2: l.out.y + 0.8 });
    let pad_l = if labels == Labels::None { 12.0 } else { 34.0 };
    let pad_t = if l.free.is_empty() { 10.0 } else { 30.0 };
    let (pad_r, pad_b) = (12.0, 8.0);
    let w = pad_l + l.w * C + pad_r;
    let h = pad_t + (l.h + 0.8) * R + pad_b;
    let xs = |x: f64| pad_l + x * C;
    let ys = |y: f64| pad_t + y * R;
    let cls = |v: &str| if free_name(v).is_some() { "free".to_string() } else { format!("v-{v}") };
    let mut out =
        format!("<svg viewBox=\"0 0 {} {}\" width=\"{}\" height=\"{}\" role=\"img\" aria-label=\"{aria}\">", num(w), num(h), num(w), num(h));
    for p in &parts {
        match p {
            Part::Bar { v, x1, x2, y } => {
                out += &format!(
                    "<line class=\"bar {}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
                    cls(v),
                    num(xs(*x1) + 7.0),
                    num(ys(*y)),
                    num(xs(*x2) - 7.0),
                    num(ys(*y))
                );
                if labels != Labels::None && (labels != Labels::Left || *x1 == 0.0) {
                    out += &format!(
                        "<text class=\"lbl {}\" x=\"{}\" y=\"{}\" text-anchor=\"end\">λ{v}</text>",
                        cls(v),
                        num(xs(*x1) - 4.0),
                        num(ys(*y) + 4.0)
                    );
                }
            }
            Part::Link { x1, x2, y } => {
                out += &format!("<line class=\"link\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>", num(xs(*x1)), num(ys(*y)), num(xs(*x2)), num(ys(*y)));
            }
            Part::Line { v, x, y1, y2 } => {
                if y2 > y1 {
                    out += &format!(
                        "<line class=\"vl {}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
                        cls(v),
                        num(xs(*x)),
                        num(ys(*y1)),
                        num(xs(*x)),
                        num(ys(*y2))
                    );
                }
            }
        }
    }
    for (x, v) in &l.free {
        out += &format!(
            "<text class=\"lbl free\" x=\"{}\" y=\"{}\" text-anchor=\"middle\">{}</text>",
            num(xs(*x)),
            num(ys(-0.6) - 6.0),
            free_name(v).unwrap_or(v)
        );
    }
    Ok(out + "</svg>")
}

/// An array of strings as console.log printed it (short arrays only).
fn show_list(v: &[String]) -> String {
    format!("[ {} ]", v.iter().map(|s| format!("'{s}'")).collect::<Vec<_>>().join(", "))
}

fn main() -> Result<(), String> {
    println!("{}", show_list(&reduce_steps("(((λx.(λy.x)) A) B)")?));
    println!("{}", show_list(&reduce_steps("(((λx.(λy.y)) A) B)")?));
    println!("{}", svg("λx.(λy.x)", "TRUE", 0.0, Labels::All)?);
    Ok(())
}
