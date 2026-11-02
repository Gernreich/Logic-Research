//! The plain reducer: terms without ids, normal order, and a note of what each step
//! replaced. allreduce prints its steps; `core::trace` checks itself against it.
//! (This was the reducer in allreduce.js, which tromp.js and core.js loaded from there.)

#[derive(Clone, Debug, PartialEq)]
pub enum T {
    Var(String),
    Lam(String, Box<T>),
    App(Box<T>, Box<T>),
}

/// The fully bracketed form, e.g. `λx.(λy.x)`; one character per variable.
pub fn parse(s: &str) -> Result<T, String> {
    let c: Vec<char> = s.chars().collect();
    let mut i = 0;
    fn ws(c: &[char], i: &mut usize) {
        while *i < c.len() && c[*i] == ' ' {
            *i += 1;
        }
    }
    fn term(c: &[char], i: &mut usize) -> Result<T, String> {
        ws(c, i);
        let at = |k: usize| c.get(k).copied();
        if at(*i) == Some('λ') {
            let v = at(*i + 1).ok_or("bad λ")?;
            if at(*i + 2) != Some('.') {
                return Err("bad λ".into());
            }
            *i += 3;
            return Ok(T::Lam(v.to_string(), Box::new(term(c, i)?)));
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
            return Ok(T::App(Box::new(f), Box::new(x)));
        }
        let v = at(*i).ok_or("unexpected end")?;
        *i += 1;
        Ok(T::Var(v.to_string()))
    }
    let r = term(&c, &mut i)?;
    ws(&c, &mut i);
    if i != c.len() {
        return Err("trailing".into());
    }
    Ok(r)
}

pub fn show(n: &T) -> String {
    match n {
        T::Var(v) => v.clone(),
        T::Lam(v, b) => match &**b {
            T::Var(w) => format!("λ{v}.{w}"),
            _ => format!("λ{v}.({})", inner(b)),
        },
        T::App(f, x) => format!("({} {})", arg(f), arg(x)),
    }
}
fn inner(n: &T) -> String {
    match n {
        T::App(..) => {
            let s = show(n);
            s[1..s.len() - 1].to_string()
        }
        _ => show(n),
    }
}
fn arg(n: &T) -> String {
    match n {
        T::Lam(..) => format!("({})", show(n)),
        _ => show(n),
    }
}

pub fn free(n: &T, v: &str) -> bool {
    match n {
        T::Var(w) => w == v,
        T::Lam(w, b) => w != v && free(b, v),
        T::App(f, x) => free(f, v) || free(x, v),
    }
}

/// Every argument substituted is closed or uses only a and b, which are never
/// rebound inside the x/y terms: no capture is possible, so none is checked here.
fn subst(n: &T, v: &str, a: &T) -> T {
    match n {
        T::Var(w) => if w == v { a.clone() } else { n.clone() },
        T::Lam(w, b) => if w == v { n.clone() } else { T::Lam(w.clone(), Box::new(subst(b, v, a))) },
        T::App(f, x) => T::App(Box::new(subst(f, v, a)), Box::new(subst(x, v, a))),
    }
}

/// What a step did: the variable, the argument it took, and whether the
/// variable was used (if not, the argument is thrown away).
pub struct Note {
    pub v: String,
    pub arg: T,
    pub used: bool,
}

/// One normal-order step: the leftmost, outermost redex.
pub fn step(n: &T) -> Option<(T, Note)> {
    if let T::App(f, x) = n {
        if let T::Lam(v, body) = &**f {
            let note = Note { v: v.clone(), arg: (**x).clone(), used: free(body, v) };
            return Some((subst(body, v, x), note));
        }
        if let Some((g, note)) = step(f) {
            return Some((T::App(Box::new(g), x.clone()), note));
        }
        if let Some((y, note)) = step(x) {
            return Some((T::App(f.clone(), Box::new(y)), note));
        }
    }
    if let T::Lam(v, b) = n {
        if let Some((c, note)) = step(b) {
            return Some((T::Lam(v.clone(), Box::new(c)), note));
        }
    }
    None
}

/// Every term on the way to normal form, the first one included.
pub fn reduce_steps(term: &str) -> Result<Vec<String>, String> {
    let mut n = parse(term)?;
    let mut steps = vec![show(&n)];
    while let Some((m, _)) = step(&n) {
        n = m;
        steps.push(show(&n));
    }
    Ok(steps)
}

/// The terms of at most `max` steps (the first term included, so max + 1 of them).
pub fn reduce_terms(term: &str, max: usize) -> Result<Vec<String>, String> {
    let mut n = parse(term)?;
    let mut out = vec![show(&n)];
    while out.len() <= max {
        match step(&n) {
            Some((m, _)) => {
                n = m;
                out.push(show(&n));
            }
            None => break,
        }
    }
    Ok(out)
}
