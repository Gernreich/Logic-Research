//! Terms with stable ids, a normal-order reducer that tracks where every part goes,
//! the Tromp layout, and its SVG. (core.js until 2026-11-02. Its step-by-step
//! highlighting served animation pages that are not in this repository, and was
//! not carried over; the reducer still keeps every id the way core.js did.)

use crate::jsfmt::{fixed, number, round};
use crate::reference;
use std::cell::Cell;
use std::collections::HashMap;
use std::rc::Rc;

#[derive(Clone, Debug)]
pub enum N {
    Var { v: String, id: String },
    Lam { v: String, id: String, body: Rc<N> },
    App { id: String, f: Rc<N>, x: Rc<N> },
}
use N::*;

impl N {
    pub fn id(&self) -> &str {
        match self {
            Var { id, .. } | Lam { id, .. } | App { id, .. } => id,
        }
    }
    pub fn var(v: &str) -> N {
        Var { v: v.into(), id: String::new() }
    }
    pub fn lam(v: &str, body: N) -> N {
        Lam { v: v.into(), id: String::new(), body: Rc::new(body) }
    }
    pub fn app(f: N, x: N) -> N {
        App { id: String::new(), f: Rc::new(f), x: Rc::new(x) }
    }
}

thread_local!(static NID: Cell<u64> = const { Cell::new(0) });
fn next_id() -> String {
    NID.with(|c| {
        c.set(c.get() + 1);
        format!("n{}", c.get())
    })
}

/// The fully bracketed form. Ids are numbered in the order core.js gave them:
/// a λ before its body, an application after both of its parts.
pub fn parse(s: &str) -> Result<N, String> {
    let c: Vec<char> = s.chars().collect();
    let mut i = 0;
    fn ws(c: &[char], i: &mut usize) {
        while *i < c.len() && c[*i] == ' ' {
            *i += 1;
        }
    }
    fn term(c: &[char], i: &mut usize) -> Result<N, String> {
        ws(c, i);
        let at = |k: usize| c.get(k).copied();
        if at(*i) == Some('λ') {
            let v = at(*i + 1).ok_or("bad λ")?;
            if at(*i + 2) != Some('.') {
                return Err("bad λ".into());
            }
            *i += 3;
            let id = next_id();
            return Ok(Lam { v: v.to_string(), id, body: Rc::new(term(c, i)?) });
        }
        if at(*i) == Some('(') {
            *i += 1;
            let f = term(c, i)?;
            ws(c, i);
            if at(*i) == Some(')') {
                *i += 1;
                return Ok(f);
            }
            let x = term(c, i)?;
            ws(c, i);
            if at(*i) != Some(')') {
                return Err(format!("expected ) at {i}"));
            }
            *i += 1;
            return Ok(App { id: next_id(), f: Rc::new(f), x: Rc::new(x) });
        }
        let v = at(*i).ok_or("unexpected end")?;
        *i += 1;
        Ok(Var { v: v.to_string(), id: next_id() })
    }
    let r = term(&c, &mut i)?;
    ws(&c, &mut i);
    if i != c.len() {
        return Err("trailing".into());
    }
    Ok(r)
}

pub fn show(n: &N) -> String {
    match n {
        Var { v, .. } => v.clone(),
        Lam { v, body, .. } => match &**body {
            Var { v: w, .. } => format!("λ{v}.{w}"),
            _ => format!("λ{v}.({})", inner(body)),
        },
        App { f, x, .. } => format!("({} {})", arg(f), arg(x)),
    }
}
fn inner(n: &N) -> String {
    match n {
        App { .. } => {
            let s = show(n);
            s[1..s.len() - 1].to_string()
        }
        _ => show(n),
    }
}
fn arg(n: &N) -> String {
    match n {
        Lam { .. } => format!("({})", show(n)),
        _ => show(n),
    }
}

/// A and B are free names, shown as words.
pub fn name(v: &str) -> &str {
    match v {
        "A" => "apple",
        "B" => "banana",
        _ => v,
    }
}

/// The term as nested spans, one per node (the pages hover on these). Used here only
/// to check that its text is the term.
pub fn term_html(n: &N, paren: bool, strip: bool) -> String {
    match n {
        Var { v, id } => format!("<span data-n=\"{id}\" data-v=\"{id}\">{}</span>", name(v)),
        Lam { v, id, body } => {
            let b = match &**body {
                Var { .. } => term_html(body, false, false),
                App { id: bid, .. } => format!(
                    "<span data-app=\"{bid}\">(</span>{}<span data-app=\"{bid}\">)</span>",
                    term_html(body, false, true)
                ),
                _ => format!("({})", term_html(body, false, false)),
            };
            let (o, c) = if paren { ("(", ")") } else { ("", "") };
            format!("<span data-n=\"{id}\">{o}<span data-bar=\"{id}\">λ{v}.</span>{b}{c}</span>")
        }
        App { id, f, x } => {
            let a = |m: &N| term_html(m, matches!(m, Lam { .. }), false);
            let (o, c) = if strip {
                (String::new(), String::new())
            } else {
                (format!("<span data-app=\"{id}\">(</span>"), format!("<span data-app=\"{id}\">)</span>"))
            };
            format!("<span data-n=\"{id}\">{o}{} {}{c}</span>", a(f), a(x))
        }
    }
}

fn copy(n: &N, suffix: Option<&str>) -> N {
    let id = |i: &str| match suffix {
        Some(s) => format!("{i}|{s}"),
        None => i.to_string(),
    };
    match n {
        Var { v, id: i } => Var { v: v.clone(), id: id(i) },
        Lam { v, id: i, body } => Lam { v: v.clone(), id: id(i), body: Rc::new(copy(body, suffix)) },
        App { id: i, f, x } => App { id: id(i), f: Rc::new(copy(f, suffix)), x: Rc::new(copy(x, suffix)) },
    }
}

/// Substitute a for v. The first occurrence keeps a's ids (so it slides into place);
/// later ones are copies suffixed with the id of the occurrence they replace.
/// `afree` is a's free variables, in the order core.js's Set listed them; `bound`
/// the λs passed on the way down.
fn subst(n: &N, v: &str, a: &N, afree: &[String], count: &mut usize, bound: &mut Vec<String>) -> Result<N, String> {
    Ok(match n {
        Var { v: w, id } => {
            if w != v {
                return Ok(n.clone());
            }
            if let Some(f) = afree.iter().find(|f| bound.contains(f)) {
                return Err(format!("capture of {f}"));
            }
            let c = *count;
            *count += 1;
            copy(a, if c > 0 { Some(id) } else { None })
        }
        Lam { v: w, id, body } => {
            if w == v {
                return Ok(n.clone());
            }
            bound.push(w.clone());
            let b = subst(body, v, a, afree, count, bound);
            bound.pop();
            Lam { v: w.clone(), id: id.clone(), body: Rc::new(b?) }
        }
        App { id, f, x } => App {
            id: id.clone(),
            f: Rc::new(subst(f, v, a, afree, count, bound)?),
            x: Rc::new(subst(x, v, a, afree, count, bound)?),
        },
    })
}

/// Free variables in first-seen order, each once.
fn free_list(n: &N, bound: &mut Vec<String>, out: &mut Vec<String>) {
    match n {
        Var { v, .. } => {
            if !bound.contains(v) && !out.contains(v) {
                out.push(v.clone());
            }
        }
        Lam { v, body, .. } => {
            bound.push(v.clone());
            free_list(body, bound, out);
            bound.pop();
        }
        App { f, x, .. } => {
            free_list(f, bound, out);
            free_list(x, bound, out);
        }
    }
}

/// One normal-order step, or None at normal form. A substitution that would
/// capture a variable is an error, not a silent wrong answer.
pub fn step(n: &N) -> Result<Option<N>, String> {
    if let App { id, f, x } = n {
        if let Lam { v, body, .. } = &**f {
            let mut afree = Vec::new();
            free_list(x, &mut Vec::new(), &mut afree);
            return Ok(Some(subst(body, v, x, &afree, &mut 0, &mut Vec::new())?));
        }
        if let Some(g) = step(f)? {
            return Ok(Some(App { id: id.clone(), f: Rc::new(g), x: x.clone() }));
        }
        if let Some(y) = step(x)? {
            return Ok(Some(App { id: id.clone(), f: f.clone(), x: Rc::new(y) }));
        }
    }
    if let Lam { v, id, body } = n {
        if let Some(b) = step(body)? {
            return Ok(Some(Lam { v: v.clone(), id: id.clone(), body: Rc::new(b) }));
        }
    }
    Ok(None)
}

/// Reduce to normal form in at most `max` steps.
pub fn normal(term: &str, max: usize) -> Result<N, String> {
    let mut n = parse(term)?;
    for _ in 0..max {
        match step(&n)? {
            None => return Ok(n),
            Some(m) => n = m,
        }
    }
    Err(format!("no normal form: {term}"))
}

// ---- Tromp layout with keys ----

const GAP: f64 = 0.8; // room for bar labels between side-by-side blocks

#[derive(Clone, Debug)]
pub struct El {
    pub k: String,
    pub t: &'static str,
    pub x1: f64,
    pub x2: f64,
    pub y1: f64,
    pub y2: f64,
    pub c: String,
}
pub struct Label {
    pub x: f64,
    pub text: String,
}
pub struct Frame {
    pub w: f64,
    pub h: f64,
    pub el: Vec<El>,
    pub labels: Vec<Label>,
    pub term: String,
}

struct Line {
    x: f64,
    y1: f64,
    y2: f64,
    cls: String,
}
struct Lay {
    lines: Vec<(String, Line)>, // in the order they were made, as the object's keys were
    at: HashMap<String, usize>,
    bars: Vec<El>,
    links: Vec<El>,
    labels: Vec<Label>,
}
struct Box3 {
    w: f64,
    h: f64,
    out: String,
}

impl Lay {
    fn line(&mut self, k: &str) -> &mut Line {
        let i = self.at[k];
        &mut self.lines[i].1
    }
    fn lay(&mut self, n: &N, env: &HashMap<String, f64>, x0: f64, y0: f64) -> Box3 {
        match n {
            Var { v, id } => {
                let bound = env.contains_key(v);
                let x = x0 + 0.5;
                let line = Line {
                    x,
                    y1: if bound { env[v] } else { -0.6 },
                    y2: y0,
                    cls: if bound { format!("v-{v}") } else { "free".into() },
                };
                if let Some(&i) = self.at.get(id) {
                    self.lines[i].1 = line;
                } else {
                    self.at.insert(id.clone(), self.lines.len());
                    self.lines.push((id.clone(), line));
                }
                if !bound {
                    self.labels.push(Label { x, text: name(v).to_string() });
                }
                Box3 { w: if bound { 1.0 } else { 2.0 }, h: 0.0, out: id.clone() }
            }
            Lam { v, id, body } => {
                let mut e = env.clone();
                e.insert(v.clone(), y0);
                let b = self.lay(body, &e, x0, y0 + 1.0);
                let w = crate::jsfmt::max(1.0, b.w);
                self.bars.push(El { k: id.clone(), t: "bar", x1: x0, x2: x0 + w, y1: y0, y2: y0, c: format!("v-{v}") });
                Box3 { w, h: b.h + 1.0, out: b.out }
            }
            App { id, f, x } => {
                let m = self.lay(f, env, x0, y0);
                let nn = self.lay(x, env, x0 + m.w + GAP, y0);
                let yl = y0 + crate::jsfmt::max(m.h, nn.h) + 1.0;
                self.line(&m.out).y2 = yl;
                self.line(&nn.out).y2 = yl;
                let (x1, x2) = (self.line(&m.out).x, self.line(&nn.out).x);
                self.links.push(El { k: id.clone(), t: "link", x1, x2, y1: yl, y2: yl, c: String::new() });
                Box3 { w: m.w + GAP + nn.w, h: yl - y0, out: m.out }
            }
        }
    }
}

/// Replace the free names A and B by words where they stand alone, as
/// `/\bA\b/g` did (an ASCII word boundary).
pub fn named(s: &str) -> String {
    let c: Vec<char> = s.chars().collect();
    let word = |k: Option<&char>| k.is_some_and(|ch| ch.is_ascii_alphanumeric() || *ch == '_');
    let mut out = String::new();
    for (i, ch) in c.iter().enumerate() {
        let alone = !word(if i == 0 { None } else { c.get(i - 1) }) && !word(c.get(i + 1));
        match ch {
            'A' if alone => out += "apple",
            'B' if alone => out += "banana",
            _ => out.push(*ch),
        }
    }
    out
}

fn strip_tags(s: &str) -> String {
    let mut out = String::new();
    let mut rest = s;
    while let Some(i) = rest.find('<') {
        out += &rest[..i];
        match rest[i + 1..].find('>') {
            Some(j) if j > 0 => rest = &rest[i + 1 + j + 1..],
            _ => {
                out.push('<');
                rest = &rest[i + 1..];
            }
        }
    }
    out + rest
}

pub fn layout(n: &N) -> Result<Frame, String> {
    let mut l = Lay { lines: vec![], at: HashMap::new(), bars: vec![], links: vec![], labels: vec![] };
    let b = l.lay(n, &HashMap::new(), 0.0, 0.0);
    l.line(&b.out).y2 = b.h + 0.8;
    let bottom = l.lines.iter().map(|(_, x)| x.y2).fold(f64::NEG_INFINITY, crate::jsfmt::max);
    if l.lines.iter().filter(|(_, x)| x.y2 == bottom).count() != 1 {
        return Err(format!("not exactly one line at the bottom: {}", show(n)));
    }
    let r3 = |v: f64| round(v * 1000.0) / 1000.0;
    let mut el: Vec<El> = l.bars.clone();
    for (k, x) in &l.lines {
        el.push(El { k: k.clone(), t: "vl", x1: x.x, x2: x.x, y1: x.y1, y2: x.y2, c: x.cls.clone() });
    }
    el.extend(l.links.iter().cloned());
    for e in &mut el {
        (e.x1, e.x2, e.y1, e.y2) = (r3(e.x1), r3(e.x2), r3(e.y1), r3(e.y2));
    }
    let term = show(n);
    if strip_tags(&term_html(n, false, false)) != named(&term) {
        return Err(format!("term html differs: {term}"));
    }
    Ok(Frame { w: b.w, h: b.h, el, labels: l.labels, term })
}

/// The first frame of a term (its Tromp layout before any step), checked against
/// the reference reducer as core.js's trace(term, 0) was.
pub fn first_frame(term: &str) -> Result<Frame, String> {
    NID.with(|c| c.set(0));
    let f = layout(&parse(term)?)?;
    let r = reference::reduce_terms(term, 0)?;
    if r.len() != 1 || r[0] != f.term {
        return Err(format!("{term} differs from the reference reducer"));
    }
    Ok(f)
}

/// Static SVG of one frame. Same geometry as the animation page.
pub fn render_svg(frame: &Frame, scale: f64, aria: &str) -> String {
    let (c, r, padl, padr, padb) = (30.0, 24.0, 34.0, 16.0, 10.0);
    let pt = if frame.labels.is_empty() { 12.0 } else { 34.0 };
    let w = padl + frame.w * c + padr;
    let h = pt + (frame.h + 0.8) * r + padb;
    let xs = |x: f64| fixed(padl + x * c, 1);
    let ys = |y: f64| fixed(pt + y * r, 1);
    let order = |t: &str| match t {
        "bar" => 1,
        "vl" => 2,
        _ => 3,
    };
    let mut els: Vec<&El> = frame.el.iter().collect();
    els.sort_by_key(|e| order(e.t));
    let mut s = format!(
        "<svg viewBox=\"0 0 {} {}\" width=\"{}\" height=\"{}\" role=\"img\" aria-label=\"{aria}\">",
        fixed(w, 1),
        fixed(h, 1),
        fixed(w * scale, 0),
        fixed(h * scale, 0)
    );
    for e in &els {
        let cls = format!("{} {}", e.t, e.c).trim().to_string();
        let inset = if e.t == "bar" { 7.0 } else { 0.0 };
        s += &format!(
            "<line class=\"{cls}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
            fixed(number(&xs(e.x1)) + inset, 1),
            ys(e.y1),
            fixed(number(&xs(e.x2)) - inset, 1),
            ys(e.y2)
        );
    }
    for e in els.iter().filter(|e| e.t == "bar") {
        s += &format!(
            "<text class=\"lbl {}\" x=\"{}\" y=\"{}\" text-anchor=\"end\">λ{}</text>",
            e.c,
            fixed(number(&xs(e.x1)) - 2.0, 1),
            fixed(number(&ys(e.y1)) + 4.0, 1),
            &e.c[2..]
        );
    }
    for lb in &frame.labels {
        s += &format!(
            "<text class=\"lbl free\" x=\"{}\" y=\"{}\" text-anchor=\"middle\">{}</text>",
            xs(lb.x),
            fixed(pt - 0.6 * r - 6.0, 1),
            lb.text
        );
    }
    s + "</svg>"
}
