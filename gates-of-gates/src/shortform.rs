//! The short (conventional) form of a lambda term, its parser, and de Bruijn form
//! for α-equality. (shortform.js until 2026-11-02.)

use crate::core::{name, N};

/// De Bruijn form, 1 = the nearest λ; free names written as words.
pub fn db(n: &N) -> String {
    fn go(n: &N, env: &mut Vec<String>) -> String {
        match n {
            N::Var { v, .. } => match env.iter().rev().position(|e| e == v) {
                Some(k) => (k + 1).to_string(),
                None => name(v).to_string(),
            },
            N::Lam { v, body, .. } => {
                env.push(v.clone());
                let s = format!("λ{}", go(body, env));
                env.pop();
                s
            }
            N::App { f, x, .. } => format!("({} {})", go(f, env), go(x, env)),
        }
    }
    go(n, &mut Vec::new())
}

#[derive(Clone, Copy, PartialEq)]
enum Ctx {
    Top,
    Fun,
    Arg,
}

/// λpq.p q (λab.a): binders run together, application by juxtaposition.
pub fn short(n: &N) -> String {
    fn go(n: &N, ctx: Ctx) -> String {
        match n {
            N::Var { v, .. } => name(v).to_string(),
            N::Lam { v, body, .. } => {
                let mut vs = v.clone();
                let mut b = &**body;
                while let N::Lam { v, body, .. } = b {
                    vs += v;
                    b = body;
                }
                let s = format!("λ{vs}.{}", go(b, Ctx::Top));
                if ctx == Ctx::Top { s } else { format!("({s})") }
            }
            N::App { f, x, .. } => {
                let s = format!("{} {}", go(f, Ctx::Fun), go(x, Ctx::Arg));
                if ctx == Ctx::Arg { format!("({s})") } else { s }
            }
        }
    }
    go(n, Ctx::Top)
}

/// Tokens: `λvars.`, brackets, and lower-case words.
fn tokens(src: &str) -> Vec<String> {
    let c: Vec<char> = src.chars().collect();
    let mut out = Vec::new();
    let mut i = 0;
    while i < c.len() {
        let ch = c[i];
        if ch == 'λ' {
            let mut j = i + 1;
            while j < c.len() && c[j].is_ascii_lowercase() {
                j += 1;
            }
            if j > i + 1 && j < c.len() && c[j] == '.' {
                out.push(c[i..=j].iter().collect());
                i = j + 1;
                continue;
            }
            i += 1;
        } else if ch == '(' || ch == ')' {
            out.push(ch.to_string());
            i += 1;
        } else if ch.is_ascii_lowercase() {
            let mut j = i;
            while j < c.len() && c[j].is_ascii_lowercase() {
                j += 1;
            }
            out.push(c[i..j].iter().collect());
            i = j;
        } else {
            i += 1;
        }
    }
    out
}

pub fn parse_short(src: &str) -> Result<N, String> {
    let toks = tokens(src);
    let mut i = 0;
    fn term(t: &[String], i: &mut usize, src: &str) -> Result<N, String> {
        if t.get(*i).is_some_and(|k| k.starts_with('λ')) {
            let k = &t[*i];
            *i += 1;
            let vs: Vec<char> = k.chars().skip(1).take(k.chars().count() - 2).collect();
            let mut body = term(t, i, src)?;
            for v in vs.iter().rev() {
                body = N::lam(&v.to_string(), body);
            }
            return Ok(body);
        }
        let mut f = atom(t, i, src)?;
        while *i < t.len() && t[*i] != ")" {
            let x = if t[*i].starts_with('λ') { term(t, i, src)? } else { atom(t, i, src)? };
            f = N::app(f, x);
        }
        Ok(f)
    }
    fn atom(t: &[String], i: &mut usize, src: &str) -> Result<N, String> {
        let k = t.get(*i).ok_or_else(|| format!("ran out in {src}"))?.clone();
        *i += 1;
        if k == "(" {
            let x = term(t, i, src)?;
            let close = t.get(*i).cloned();
            *i += 1;
            if close.as_deref() != Some(")") {
                return Err(format!("expected ) in {src}"));
            }
            return Ok(x);
        }
        Ok(N::var(match k.as_str() {
            "apple" => "A",
            "banana" => "B",
            _ => &k,
        }))
    }
    let x = term(&toks, &mut i, src)?;
    if i != toks.len() {
        return Err(format!("left over in {src}"));
    }
    Ok(x)
}

/// The short form, checked: it must parse back to the same term.
pub fn short_checked(n: &N) -> Result<String, String> {
    let s = short(n);
    if db(&parse_short(&s)?) != db(n) {
        return Err(format!("short form does not read back: {s}"));
    }
    Ok(s)
}
