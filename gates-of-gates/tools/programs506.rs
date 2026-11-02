//! Builds programs506.html: every one of the 506 normal forms behind the 4,096
//! gates-of-gates cells, as a Tromp diagram and in eight notations. Every notation is
//! checked before the page is written. Reads tools/gates-data.json (run gates first).
//! (programs506.js until 2026-11-02; the page comes out byte for byte as it did.)

use lambda::core::{self, N};
use lambda::jsfmt::fixed;
use lambda::json::J;
use lambda::root;
use lambda::shortform as sf;
use std::rc::Rc;

// ---------- helpers on named trees ----------
fn long(n: &N) -> String {
    core::show(n)
}

/// de Bruijn, 1 = the nearest λ
fn deb(n: &N, env: &mut Vec<String>) -> String {
    match n {
        N::Var { v, .. } => (env.iter().rev().position(|e| e == v).map_or(0, |k| k + 1)).to_string(),
        N::Lam { v, body, .. } => {
            env.push(v.clone());
            let s = format!("λ{}", deb(body, env));
            env.pop();
            s
        }
        N::App { f, x, .. } => format!("({} {})", deb(f, env), deb(x, env)),
    }
}
/// binary lambda calculus: 00 = λ, 01 = application, n = 1…1 0 (n ones)
fn blc(n: &N, env: &mut Vec<String>) -> String {
    match n {
        N::Var { v, .. } => "1".repeat(env.iter().rev().position(|e| e == v).map_or(0, |k| k + 1)) + "0",
        N::Lam { v, body, .. } => {
            env.push(v.clone());
            let s = format!("00{}", blc(body, env));
            env.pop();
            s
        }
        N::App { f, x, .. } => format!("01{}{}", blc(f, env), blc(x, env)),
    }
}
/// ... and the decoder back to de Bruijn
fn blc_decode(bits: &str) -> Result<String, String> {
    let b = bits.as_bytes();
    let mut i = 0;
    fn r(b: &[u8], i: &mut usize) -> Result<String, String> {
        if b.get(*i) == Some(&b'0') {
            *i += 1;
            let c = b.get(*i).copied();
            *i += 1;
            if c == Some(b'0') {
                return Ok(format!("λ{}", r(b, i)?));
            }
            let f = r(b, i)?;
            let a = r(b, i)?;
            return Ok(format!("({f} {a})"));
        }
        let mut k = 0;
        while b.get(*i) == Some(&b'1') {
            k += 1;
            *i += 1;
        }
        *i += 1;
        if *i > b.len() {
            return Err("ran out of bits".into());
        }
        Ok(k.to_string())
    }
    let t = r(b, &mut i)?;
    if i != b.len() {
        return Err("leftover bits".into());
    }
    Ok(t)
}

/// Polish and reverse Polish, with @ = apply and λx as a one-argument operator
fn pn(n: &N, out: &mut Vec<String>) {
    match n {
        N::Var { v, .. } => out.push(v.clone()),
        N::Lam { v, body, .. } => {
            out.push(format!("λ{v}"));
            pn(body, out);
        }
        N::App { f, x, .. } => {
            out.push("@".into());
            pn(f, out);
            pn(x, out);
        }
    }
}
fn rpn(n: &N, out: &mut Vec<String>) {
    match n {
        N::Var { v, .. } => out.push(v.clone()),
        N::Lam { v, body, .. } => {
            rpn(body, out);
            out.push(format!("λ{v}"));
        }
        N::App { f, x, .. } => {
            rpn(f, out);
            rpn(x, out);
            out.push("@".into());
        }
    }
}
fn from_pn(t: &[String]) -> Result<N, String> {
    fn r(t: &[String], i: &mut usize) -> Result<N, String> {
        let k = t.get(*i).ok_or("PN ran out")?;
        *i += 1;
        if k == "@" {
            let f = r(t, i)?;
            let x = r(t, i)?;
            return Ok(N::app(f, x));
        }
        if let Some(v) = k.strip_prefix('λ') {
            return Ok(N::lam(v, r(t, i)?));
        }
        Ok(N::var(k))
    }
    let mut i = 0;
    let x = r(t, &mut i)?;
    if i != t.len() {
        return Err("PN left over".into());
    }
    Ok(x)
}
fn from_rpn(t: &[String]) -> Result<N, String> {
    let mut s: Vec<N> = Vec::new();
    for k in t {
        if k == "@" {
            let x = s.pop().ok_or("RPN stack")?;
            let f = s.pop().ok_or("RPN stack")?;
            s.push(N::app(f, x));
        } else if let Some(v) = k.strip_prefix('λ') {
            let b = s.pop().ok_or("RPN stack")?;
            s.push(N::lam(v, b));
        } else {
            s.push(N::var(k));
        }
    }
    if s.len() != 1 {
        return Err("RPN stack".into());
    }
    Ok(s.pop().unwrap())
}

// SKI by bracket abstraction, with the K and η shortcuts
#[derive(Clone)]
enum S {
    Var(String),
    Comb(char),
    App(Box<S>, Box<S>),
}
fn sfree(e: &S, x: &str) -> bool {
    match e {
        S::Var(v) => v == x,
        S::Comb(_) => false,
        S::App(f, a) => sfree(f, x) || sfree(a, x),
    }
}
fn sapp(f: S, x: S) -> S {
    S::App(Box::new(f), Box::new(x))
}
fn ski(n: &N) -> S {
    match n {
        N::Var { v, .. } => S::Var(v.clone()),
        N::App { f, x, .. } => sapp(ski(f), ski(x)),
        N::Lam { v, body, .. } => abs(v, ski(body)),
    }
}
/// e contains no λ; returns a combinator term for λx.e
fn abs(x: &str, e: S) -> S {
    if !sfree(&e, x) {
        return sapp(S::Comb('K'), e);
    }
    match e {
        S::Var(_) => S::Comb('I'), // e is x itself
        S::App(f, a) => {
            if matches!(&*a, S::Var(v) if v == x) && !sfree(&f, x) {
                return *f; // η: λx.(f x) = f
            }
            sapp(sapp(S::Comb('S'), abs(x, *f)), abs(x, *a))
        }
        S::Comb(_) => unreachable!(),
    }
}
fn ski_str(n: &S, arg: bool) -> String {
    match n {
        S::Var(v) => v.clone(),
        S::Comb(c) => c.to_string(),
        S::App(f, x) => {
            let s = ski_str(f, false) + &ski_str(x, true);
            if arg { format!("({s})") } else { s }
        }
    }
}
fn ski_lambda(n: &S) -> String {
    match n {
        S::Var(v) => v.clone(),
        S::Comb('S') => "(λx.(λy.(λz.((x z) (y z)))))".into(),
        S::Comb('K') => "(λx.(λy.x))".into(),
        S::Comb(_) => "(λx.x)".into(),
        S::App(f, x) => format!("({} {})", ski_lambda(f), ski_lambda(x)),
    }
}

// JavaScript arrow form
fn js(n: &N) -> String {
    match n {
        N::Var { v, .. } => v.clone(),
        N::Lam { v, body, .. } => format!("{v} => {}", js(body)),
        N::App { f, x, .. } => {
            let fs = if matches!(**f, N::Lam { .. }) { format!("({})", js(f)) } else { js(f) };
            format!("{fs}({})", js(x))
        }
    }
}

/// The arrow functions, run as JavaScript runs them. programs506.js handed each one to
/// eval; this reads the same text with its own parser (names, `x => body`, calls
/// `f(a)`, brackets) and evaluates it the same way: arguments first, closures
/// capturing their scope. Nothing here is shared with the lambda code above.
mod arrow {
    use std::rc::Rc;
    pub enum E {
        Name(String),
        Arrow(String, Rc<E>),
        Call(Rc<E>, Rc<E>),
    }
    pub fn parse(src: &str) -> Result<E, String> {
        let toks = lex(src)?;
        let mut i = 0;
        let e = expr(&toks, &mut i)?;
        if i != toks.len() {
            return Err(format!("left over in {src}"));
        }
        Ok(e)
    }
    fn lex(src: &str) -> Result<Vec<String>, String> {
        let c: Vec<char> = src.chars().collect();
        let (mut out, mut i) = (Vec::new(), 0);
        while i < c.len() {
            match c[i] {
                ' ' => i += 1,
                '(' | ')' => {
                    out.push(c[i].to_string());
                    i += 1
                }
                '=' if c.get(i + 1) == Some(&'>') => {
                    out.push("=>".into());
                    i += 2
                }
                ch if ch.is_ascii_alphabetic() => {
                    let s = i;
                    while i < c.len() && c[i].is_ascii_alphanumeric() {
                        i += 1;
                    }
                    out.push(c[s..i].iter().collect());
                }
                ch => return Err(format!("unexpected {ch} in {src}")),
            }
        }
        Ok(out)
    }
    fn is_name(t: Option<&String>) -> bool {
        t.is_some_and(|s| s.chars().all(|c| c.is_ascii_alphanumeric()))
    }
    fn expr(t: &[String], i: &mut usize) -> Result<E, String> {
        if is_name(t.get(*i)) && t.get(*i + 1).map(String::as_str) == Some("=>") {
            let p = t[*i].clone();
            *i += 2;
            return Ok(E::Arrow(p, Rc::new(expr(t, i)?)));
        }
        let mut f = primary(t, i)?;
        while t.get(*i).map(String::as_str) == Some("(") {
            *i += 1;
            let a = expr(t, i)?;
            if t.get(*i).map(String::as_str) != Some(")") {
                return Err("expected )".into());
            }
            *i += 1;
            f = E::Call(Rc::new(f), Rc::new(a));
        }
        Ok(f)
    }
    fn primary(t: &[String], i: &mut usize) -> Result<E, String> {
        let k = t.get(*i).ok_or("ran out")?.clone();
        *i += 1;
        if k == "(" {
            let e = expr(t, i)?;
            if t.get(*i).map(String::as_str) != Some(")") {
                return Err("expected )".into());
            }
            *i += 1;
            return Ok(e);
        }
        if is_name(Some(&k)) {
            return Ok(E::Name(k));
        }
        Err(format!("unexpected {k}"))
    }

    #[derive(Clone)]
    pub enum V {
        Str(String),
        Fun(String, Rc<E>, Env),
    }
    #[derive(Clone)]
    pub enum Env {
        Empty,
        Bind(String, Rc<V>, Rc<Env>),
    }
    fn look(env: &Env, n: &str) -> Result<V, String> {
        match env {
            Env::Empty => Err(format!("ReferenceError: {n} is not defined")),
            Env::Bind(k, v, rest) => {
                if k == n {
                    Ok((**v).clone())
                } else {
                    look(rest, n)
                }
            }
        }
    }
    pub fn eval(e: &E, env: &Env) -> Result<V, String> {
        match e {
            E::Name(n) => look(env, n),
            E::Arrow(p, b) => Ok(V::Fun(p.clone(), b.clone(), env.clone())),
            E::Call(f, a) => {
                let fv = eval(f, env)?;
                let av = eval(a, env)?;
                call(&fv, av)
            }
        }
    }
    pub fn call(f: &V, a: V) -> Result<V, String> {
        match f {
            V::Fun(p, b, env) => eval(b, &Env::Bind(p.clone(), Rc::new(a), Rc::new(env.clone()))),
            V::Str(s) => Err(format!("TypeError: '{s}' is not a function")),
        }
    }
}

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}

const T: &str = "λx.(λy.x)";
const F: &str = "λx.(λy.y)";
const PAIRS: [(&str, &str); 4] = [(T, T), (T, F), (F, T), (F, F)];

/// behaviour check: apply to the four boolean pairs and two free names A, B; must
/// give A or B per the truth table
fn lam_bits(term: &str) -> Result<String, String> {
    let mut out = String::new();
    for (p, q) in PAIRS {
        let mut n = core::parse(&format!("(((((({term})) ({p})) ({q})) A) B)"))?;
        for _ in 0..5000 {
            match core::step(&n)? {
                Some(m) => n = m,
                None => break,
            }
        }
        let s = core::show(&n);
        if s != "A" && s != "B" {
            return Err(format!("not A or B: {s}"));
        }
        out.push(if s == "A" { '1' } else { '0' });
    }
    Ok(out)
}

fn js_bits(src: &str) -> Result<String, String> {
    use arrow::{call, eval, parse, Env, V};
    let f = eval(&parse(src)?, &Env::Empty)?;
    let t = eval(&parse("x => y => x")?, &Env::Empty)?;
    let fl = eval(&parse("x => y => y")?, &Env::Empty)?;
    let mut out = String::new();
    for (p, q) in [(&t, &t), (&t, &fl), (&fl, &t), (&fl, &fl)] {
        let mut r = call(&f, p.clone())?;
        r = call(&r, q.clone())?;
        r = call(&r, V::Str("A".into()))?;
        r = call(&r, V::Str("B".into()))?;
        match r {
            V::Str(s) if s == "A" => out.push('1'),
            V::Str(s) if s == "B" => out.push('0'),
            V::Str(s) => return Err(format!("js gave {s}")),
            V::Fun(..) => return Err("js gave a function".into()),
        }
    }
    Ok(out)
}

struct Gate {
    idx: usize,
    bits: String,
    name: String,
    short: String,
}
struct Nf {
    short: String,
    gate: usize,
    exact: bool,
    count: usize,
    first: [usize; 3],
}
struct Prog {
    k: usize,
    gate: usize,
    exact: bool,
    count: usize,
    first: [usize; 3],
    bits: String,
    short: String,
    long: String,
    deb: String,
    blc: String,
    pn: String,
    rpn: String,
    ski: String,
    js: String,
    svg: String,
}
impl Prog {
    fn note(&self, key: &str) -> String {
        match key {
            "short" => self.short.clone(),
            "long" => self.long.clone(),
            "deb" => self.deb.clone(),
            "blc" => format!("{}  ({} bits)", self.blc, self.blc.len()),
            "pn" => self.pn.clone(),
            "rpn" => self.rpn.clone(),
            "ski" => self.ski.clone(),
            _ => self.js.clone(),
        }
    }
}

fn esc(s: &str) -> String {
    s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;")
}
fn plural(n: usize, w: &str) -> String {
    format!("{n} {w}{}", if n == 1 { "" } else { "s" })
}
fn u16len(s: &str) -> usize {
    s.encode_utf16().count()
}

fn run() -> Result<(), String> {
    let tools = root().join("tools");
    let text = std::fs::read_to_string(tools.join("gates-data.json")).map_err(|e| format!("gates-data.json: {e}"))?;
    let d = J::parse(&text)?;
    let u = |j: &J| j.f().unwrap() as usize;
    let s = |j: &J, k: &str| j.get(k).and_then(J::str).unwrap().to_string();
    let g: Vec<Gate> = d
        .get("gates")
        .and_then(J::arr)
        .unwrap()
        .iter()
        .map(|x| Gate { idx: u(x.get("idx").unwrap()), bits: s(x, "bits"), name: s(x, "name"), short: s(x, "short") })
        .collect();
    let nfs: Vec<Nf> = d
        .get("nfs")
        .and_then(J::arr)
        .unwrap()
        .iter()
        .map(|x| {
            let fst: Vec<usize> = x.get("first").and_then(J::arr).unwrap().iter().map(u).collect();
            Nf {
                short: s(x, "short"),
                gate: u(x.get("gate").unwrap()),
                exact: matches!(x.get("exact"), Some(J::Bool(true))),
                count: u(x.get("count").unwrap()),
                first: [fst[0], fst[1], fst[2]],
            }
        })
        .collect();
    let nf_grid: Vec<usize> = d
        .get("nfGrid")
        .and_then(J::arr)
        .unwrap()
        .iter()
        .flat_map(|p| p.arr().unwrap().iter().flat_map(|l| l.arr().unwrap().iter().map(u)))
        .collect();
    let mut wh = vec![[0usize; 16]; nfs.len()];
    for (i, &k) in nf_grid.iter().enumerate() {
        wh[k][i / 256] += 1;
    }
    for (k, f) in nfs.iter().enumerate() {
        if wh[k].iter().sum::<usize>() != f.count {
            return Err(format!("cell count mismatch for program #{}", k + 1));
        }
    }
    if wh.iter().flatten().sum::<usize>() != 4096 {
        return Err("the programs do not account for all 4096 cells".into());
    }

    // ---------- build every program ----------
    let mut progs = Vec::new();
    for (k, f) in nfs.iter().enumerate() {
        let n = sf::parse_short(&f.short)?;
        let bits = g[f.gate].bits.clone();
        let l = long(&n);
        if sf::short_checked(&n)? != f.short {
            return Err(format!("short form mismatch #{}", k + 1));
        }
        let dd = deb(&n, &mut vec![]);
        let b = blc(&n, &mut vec![]);
        let (mut p, mut r) = (vec![], vec![]);
        pn(&n, &mut p);
        rpn(&n, &mut r);
        let sk = ski(&n);
        let jsrc = js(&n);
        if blc_decode(&b)? != dd {
            return Err(format!("binary does not decode #{}", k + 1));
        }
        if deb(&from_pn(&p)?, &mut vec![]) != dd || deb(&from_rpn(&r)?, &mut vec![]) != dd {
            return Err(format!("PN/RPN do not read back #{}", k + 1));
        }
        if lam_bits(&l)? != bits {
            return Err(format!("lambda behaviour wrong #{}", k + 1));
        }
        if lam_bits(&ski_lambda(&sk))? != bits {
            return Err(format!("SKI behaviour wrong #{}", k + 1));
        }
        if js_bits(&jsrc)? != bits {
            return Err(format!("JavaScript behaviour wrong #{}", k + 1));
        }
        let frame = core::first_frame(&l)?;
        let svg = core::render_svg(&frame, 1.0, &format!("Tromp diagram of program {}", k + 1));
        progs.push(Prog {
            k,
            gate: f.gate,
            exact: f.exact,
            count: f.count,
            first: f.first,
            bits,
            short: f.short.clone(),
            long: l,
            deb: dd,
            blc: b,
            pn: p.join(" "),
            rpn: r.join(" "),
            ski: ski_str(&sk, false),
            js: jsrc,
            svg,
        });
    }
    println!(
        "{} programs: short, long, de Bruijn, binary, PN, RPN read back; lambda, SKI and JavaScript all give the right truth table",
        progs.len()
    );

    // ---------- page ----------
    let progs: Vec<Rc<Prog>> = progs.into_iter().map(Rc::new).collect();
    let mut by_gate: Vec<Vec<Rc<Prog>>> = vec![vec![]; g.len()];
    for p in &progs {
        by_gate[p.gate].push(p.clone());
    }
    for list in &mut by_gate {
        list.sort_by(|a, b| {
            (b.exact as i64 - a.exact as i64)
                .cmp(&0)
                .then((b.count as i64 - a.count as i64).cmp(&0))
                .then((u16len(&a.short) as i64 - u16len(&b.short) as i64).cmp(&0))
        });
    }
    const NOTES: [(&str, &str); 8] = [
        ("short", "Lambda, short form"),
        ("long", "Lambda, fully bracketed"),
        ("deb", "De Bruijn"),
        ("blc", "Tromp binary"),
        ("pn", "Polish (prefix)"),
        ("rpn", "Reverse Polish"),
        ("ski", "SKI combinators"),
        ("js", "JavaScript"),
    ];
    let card = |p: &Prog| {
        let [cg, cx, cy] = p.first;
        let tag = if p.exact {
            "<span class=\"badge\">lambda16.txt</span>".to_string()
        } else {
            format!("<span class=\"eg\">e.g. {}({}, {})</span>", esc(&g[cg].short), esc(&g[cx].short), esc(&g[cy].short))
        };
        let dl: String = NOTES
            .iter()
            .map(|(key, label)| format!("<div class=\"n-{key}\"><dt>{label}</dt><dd><code>{}</code></dd></div>", esc(&p.note(key))))
            .collect();
        let wh_line = wh[p.k]
            .iter()
            .enumerate()
            .filter(|(_, &n)| n > 0)
            .map(|(gi, n)| format!("{} ×{n}", esc(&g[gi].short)))
            .collect::<Vec<_>>()
            .join(" · ");
        format!(
            "<article class=\"prog{}\" id=\"p{}\">
  <header><b>#{}</b><span>{} · {}</span><span>{}</span>{tag}</header>
  <div class=\"body\"><div class=\"draw\">{}</div><dl>{dl}</dl>
  <figure class=\"where n-where\"><figcaption>Where it comes from</figcaption><canvas class=\"map\" data-k=\"{}\" width=\"204\" height=\"204\" role=\"img\"
    aria-label=\"The cells, across all 16 squares, that reduce to program {}\"></canvas>
    <p>{wh_line}</p></figure></div></article>",
            if p.exact { " exact" } else { "" },
            p.k + 1,
            p.k + 1,
            g[p.gate].name,
            p.bits,
            plural(p.count, "cell"),
            p.svg,
            p.k,
            p.k + 1,
        )
    };
    let sections = by_gate
        .iter()
        .enumerate()
        .map(|(gi, list)| {
            format!(
                "<section class=\"gate\" id=\"g{gi}\" data-gate=\"{gi}\">
  <h2>{gi} {} <span>{} · {} · {} cells</span></h2>
  {}
</section>",
                esc(&g[gi].name),
                g[gi].bits,
                plural(list.len(), "program"),
                list.iter().map(|p| p.count).sum::<usize>(),
                list.iter().map(|p| card(p)).collect::<Vec<_>>().join("\n")
            )
        })
        .collect::<Vec<_>>()
        .join("\n");

    let css = std::fs::read_to_string(tools.join("programs506.css")).map_err(|e| e.to_string())?;
    let gate_options: String = g.iter().map(|x| format!("<option value=\"{}\">{} {}</option>", x.idx, x.idx, esc(&x.name))).collect();
    let toggles: String = NOTES
        .iter()
        .chain([("where", "Where it comes from")].iter())
        .map(|(key, label)| format!("<label for=\"t-{key}\"><input type=\"checkbox\" id=\"t-{key}\" data-n=\"{key}\" checked> {label}</label>"))
        .collect();
    let jump: String =
        g.iter().map(|x| format!("<a href=\"#g{}\">{} {} <span>{}</span></a>", x.idx, x.idx, esc(&x.short), by_gate[x.idx].len())).collect();
    let nfg = J::nums(nf_grid.iter().map(|&v| v as f64)).stringify(0);
    let bits_js = J::Arr(nfs.iter().map(|f| J::s(&g[f.gate].bits)).collect()).stringify(0);
    let mut tt = vec![0usize; 16];
    for x in &g {
        tt[usize::from_str_radix(&x.bits, 2).unwrap()] = x.idx;
    }
    let tt_js = J::nums(tt.iter().map(|&v| v as f64)).stringify(0);

    let html = fill(
        PAGE,
        &[
            ("css", &css),
            ("gate_options", &gate_options),
            ("toggles", &toggles),
            ("jump", &jump),
            ("sections", &sections),
            ("NFG", &nfg),
            ("BITS", &bits_js),
            ("TT", &tt_js),
        ],
    )?;
    std::fs::write(tools.join("programs506.html"), &html).map_err(|e| e.to_string())?;
    println!(
        "programs506.html {} MB, {} diagrams",
        fixed(u16len(&html) as f64 / 1e6, 2),
        html.matches("<svg").count()
    );
    Ok(())
}

/// The page around the cards (the template literal programs506.js wrote it with).
/// `{name}` marks where run() puts each piece.
const PAGE: &str = include_str!("programs506.page.html");

/// Put each piece in its place in one pass, so nothing inserted is read again; every
/// placeholder must be there exactly once.
fn fill(tpl: &str, pieces: &[(&str, &str)]) -> Result<String, String> {
    let mut out = String::new();
    let mut rest = tpl;
    let mut used = vec![0; pieces.len()];
    'scan: while let Some(i) = rest.find('{') {
        for (k, (name, text)) in pieces.iter().enumerate() {
            let tag = format!("{{{name}}}");
            if rest[i..].starts_with(&tag) {
                out += &rest[..i];
                out += text;
                rest = &rest[i + tag.len()..];
                used[k] += 1;
                continue 'scan;
            }
        }
        out += &rest[..=i];
        rest = &rest[i + 1..];
    }
    out += rest;
    match used.iter().position(|&n| n != 1) {
        Some(k) => Err(format!("{{{}}} is in the page template {} times", pieces[k].0, used[k])),
        None => Ok(out),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // AND is p q p: TRUE only on the first row
    const AND_JS: &str = "p => q => a => b => p(q)(p)(a)(b)";
    const AND_LAM: &str = "λp.(λq.((p q) p))";

    #[test]
    fn arrow_functions_run_as_javascript_would() {
        assert_eq!(js_bits(AND_JS).unwrap(), "1000");
        assert_eq!(js_bits("p => q => p").unwrap(), "1100");
        assert_eq!(js_bits("p => q => a => b => q(b)(a)").unwrap(), "0101"); // NOT Q
        // a wrong program gives a wrong truth table, not a pass
        assert_eq!(js_bits("p => q => p(p)(q)").unwrap(), "1110"); // OR, not AND
        // a free name is an error, as in JavaScript
        assert!(js_bits("p => q => r").is_err());
        // returning a function where a string should come is an error
        assert!(js_bits("p => q => a => b => c => a").is_err());
        // bad text does not parse
        assert!(js_bits("p => => q").is_err());
    }

    #[test]
    fn lambda_and_ski_checks_tell_gates_apart() {
        assert_eq!(lam_bits(AND_LAM).unwrap(), "1000");
        let n = core::parse(AND_LAM).unwrap();
        assert_eq!(lam_bits(&ski_lambda(&ski(&n))).unwrap(), "1000");
        assert_eq!(js_bits(&js(&n)).unwrap(), "1000");
        assert_eq!(lam_bits("λp.(λq.((p p) q))").unwrap(), "1110"); // OR
    }

    #[test]
    fn notations_read_back() {
        let n = core::parse(AND_LAM).unwrap();
        let d = deb(&n, &mut vec![]);
        assert_eq!(d, "λλ((2 1) 2)");
        let b = blc(&n, &mut vec![]);
        assert_eq!(blc_decode(&b).unwrap(), d);
        assert!(blc_decode(&(b.clone() + "0")).is_err());
        let (mut p, mut r) = (vec![], vec![]);
        pn(&n, &mut p);
        rpn(&n, &mut r);
        assert_eq!(p.join(" "), "λp λq @ @ p q p");
        assert_eq!(deb(&from_pn(&p).unwrap(), &mut vec![]), d);
        assert_eq!(deb(&from_rpn(&r).unwrap(), &mut vec![]), d);
    }

    #[test]
    fn fill_wants_each_piece_once() {
        assert_eq!(fill("a{x}b{y}", &[("x", "{y}"), ("y", "1")]).unwrap(), "a{y}b1");
        assert!(fill("a{x}{x}", &[("x", "1")]).is_err());
        assert!(fill("a", &[("x", "1")]).is_err());
    }
}
