//! Just enough JSON: parse parts.json, and write values exactly as JavaScript's
//! `JSON.stringify(value, null, indent)` lays them out -- keys in insertion order,
//! numbers by `String(x)`, NaN and Infinity as null -- so the committed .json files
//! stay byte-identical to what the JavaScript tools wrote.

use crate::jsfmt::num;

#[derive(Clone, Debug, PartialEq)]
pub enum J {
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    Arr(Vec<J>),
    Obj(Vec<(String, J)>),
}

impl J {
    pub fn obj(pairs: Vec<(&str, J)>) -> J {
        J::Obj(pairs.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
    }
    pub fn s(v: &str) -> J {
        J::Str(v.to_string())
    }
    pub fn nums<I: IntoIterator<Item = f64>>(v: I) -> J {
        J::Arr(v.into_iter().map(J::Num).collect())
    }
    pub fn opt(v: Option<f64>) -> J {
        v.map(J::Num).unwrap_or(J::Null)
    }
    pub fn get(&self, k: &str) -> Option<&J> {
        match self {
            J::Obj(m) => m.iter().find(|(key, _)| key == k).map(|(_, v)| v),
            _ => None,
        }
    }
    pub fn keys(&self) -> Vec<&str> {
        match self {
            J::Obj(m) => m.iter().map(|(k, _)| k.as_str()).collect(),
            _ => vec![],
        }
    }
    /// The number, if this is one (null and anything else are not).
    pub fn f(&self) -> Option<f64> {
        if let J::Num(x) = self { Some(*x) } else { None }
    }
    pub fn str(&self) -> Option<&str> {
        if let J::Str(s) = self { Some(s) } else { None }
    }
    pub fn arr(&self) -> Option<&[J]> {
        if let J::Arr(a) = self { Some(a) } else { None }
    }
    /// JavaScript truthiness.
    pub fn truthy(&self) -> bool {
        match self {
            J::Null => false,
            J::Bool(b) => *b,
            J::Num(x) => *x != 0.0 && !x.is_nan(),
            J::Str(s) => !s.is_empty(),
            _ => true,
        }
    }

    /// `JSON.stringify(self, null, indent)`; indent 0 is the compact form.
    pub fn stringify(&self, indent: usize) -> String {
        let mut out = String::new();
        self.write(&mut out, indent, 0);
        out
    }
    fn write(&self, out: &mut String, ind: usize, level: usize) {
        let pad = |n: usize| " ".repeat(ind * n);
        match self {
            J::Null => out.push_str("null"),
            J::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
            J::Num(x) => out.push_str(&if x.is_finite() { num(*x) } else { "null".into() }),
            J::Str(s) => quote(out, s),
            J::Arr(a) if a.is_empty() => out.push_str("[]"),
            J::Obj(m) if m.is_empty() => out.push_str("{}"),
            J::Arr(a) => {
                out.push('[');
                for (i, v) in a.iter().enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    if ind > 0 {
                        out.push('\n');
                        out.push_str(&pad(level + 1));
                    }
                    v.write(out, ind, level + 1);
                }
                if ind > 0 {
                    out.push('\n');
                    out.push_str(&pad(level));
                }
                out.push(']');
            }
            J::Obj(m) => {
                out.push('{');
                for (i, (k, v)) in m.iter().enumerate() {
                    if i > 0 {
                        out.push(',');
                    }
                    if ind > 0 {
                        out.push('\n');
                        out.push_str(&pad(level + 1));
                    }
                    quote(out, k);
                    out.push(':');
                    if ind > 0 {
                        out.push(' ');
                    }
                    v.write(out, ind, level + 1);
                }
                if ind > 0 {
                    out.push('\n');
                    out.push_str(&pad(level));
                }
                out.push('}');
            }
        }
    }

    pub fn parse(s: &str) -> Result<J, String> {
        let mut p = Parser { b: s.as_bytes(), i: 0 };
        let v = p.value()?;
        p.ws();
        if p.i != p.b.len() {
            return Err(format!("unexpected text at byte {}", p.i));
        }
        Ok(v)
    }
}

fn quote(out: &mut String, s: &str) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
}

struct Parser<'a> {
    b: &'a [u8],
    i: usize,
}
impl Parser<'_> {
    fn ws(&mut self) {
        while self.i < self.b.len() && matches!(self.b[self.i], b' ' | b'\n' | b'\r' | b'\t') {
            self.i += 1;
        }
    }
    fn err<T>(&self, what: &str) -> Result<T, String> {
        Err(format!("{what} at byte {}", self.i))
    }
    fn lit(&mut self, word: &str, v: J) -> Result<J, String> {
        if self.b[self.i..].starts_with(word.as_bytes()) {
            self.i += word.len();
            Ok(v)
        } else {
            self.err("bad literal")
        }
    }
    fn value(&mut self) -> Result<J, String> {
        self.ws();
        match self.b.get(self.i) {
            None => self.err("unexpected end"),
            Some(b'n') => self.lit("null", J::Null),
            Some(b't') => self.lit("true", J::Bool(true)),
            Some(b'f') => self.lit("false", J::Bool(false)),
            Some(b'"') => Ok(J::Str(self.string()?)),
            Some(b'[') => {
                self.i += 1;
                let mut a = Vec::new();
                self.ws();
                if self.b.get(self.i) == Some(&b']') {
                    self.i += 1;
                    return Ok(J::Arr(a));
                }
                loop {
                    a.push(self.value()?);
                    self.ws();
                    match self.b.get(self.i) {
                        Some(b',') => self.i += 1,
                        Some(b']') => {
                            self.i += 1;
                            return Ok(J::Arr(a));
                        }
                        _ => return self.err("expected , or ]"),
                    }
                }
            }
            Some(b'{') => {
                self.i += 1;
                let mut m: Vec<(String, J)> = Vec::new();
                self.ws();
                if self.b.get(self.i) == Some(&b'}') {
                    self.i += 1;
                    return Ok(J::Obj(m));
                }
                loop {
                    self.ws();
                    if self.b.get(self.i) != Some(&b'"') {
                        return self.err("expected a key");
                    }
                    let k = self.string()?;
                    self.ws();
                    if self.b.get(self.i) != Some(&b':') {
                        return self.err("expected :");
                    }
                    self.i += 1;
                    let v = self.value()?;
                    // a repeated key keeps its first position and takes the last value
                    match m.iter_mut().find(|(key, _)| *key == k) {
                        Some(e) => e.1 = v,
                        None => m.push((k, v)),
                    }
                    self.ws();
                    match self.b.get(self.i) {
                        Some(b',') => self.i += 1,
                        Some(b'}') => {
                            self.i += 1;
                            return Ok(J::Obj(m));
                        }
                        _ => return self.err("expected , or }"),
                    }
                }
            }
            _ => {
                let start = self.i;
                while self.i < self.b.len() && matches!(self.b[self.i], b'-' | b'+' | b'.' | b'e' | b'E' | b'0'..=b'9') {
                    self.i += 1;
                }
                let t = std::str::from_utf8(&self.b[start..self.i]).unwrap();
                t.parse::<f64>().map(J::Num).or_else(|_| self.err("bad number"))
            }
        }
    }
    fn string(&mut self) -> Result<String, String> {
        self.i += 1; // opening quote
        let mut s = String::new();
        loop {
            let Some(&c) = self.b.get(self.i) else { return self.err("unterminated string") };
            self.i += 1;
            match c {
                b'"' => return Ok(s),
                b'\\' => {
                    let Some(&e) = self.b.get(self.i) else { return self.err("bad escape") };
                    self.i += 1;
                    match e {
                        b'n' => s.push('\n'),
                        b'r' => s.push('\r'),
                        b't' => s.push('\t'),
                        b'b' => s.push('\u{8}'),
                        b'f' => s.push('\u{c}'),
                        b'u' => {
                            let h = std::str::from_utf8(&self.b[self.i..self.i + 4]).map_err(|e| e.to_string())?;
                            let v = u32::from_str_radix(h, 16).map_err(|e| e.to_string())?;
                            self.i += 4;
                            s.push(char::from_u32(v).unwrap_or('\u{fffd}'));
                        }
                        other => s.push(other as char),
                    }
                }
                _ => {
                    // copy one UTF-8 sequence
                    let start = self.i - 1;
                    let len = match c {
                        0..=0x7f => 1,
                        0xc0..=0xdf => 2,
                        0xe0..=0xef => 3,
                        _ => 4,
                    };
                    self.i = start + len;
                    s.push_str(std::str::from_utf8(&self.b[start..self.i]).map_err(|e| e.to_string())?);
                }
            }
        }
    }
}
